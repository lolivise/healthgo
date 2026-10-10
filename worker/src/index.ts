import { Answers, applyPress, finalText, firstStep, nextStep, rawAnswers, render, summarize } from "./feel";

export interface Env {
  DB: D1Database;
  BOT_TOKEN: string;
  CHAT_ID: string;
  WEBHOOK_SECRET: string;
  PULL_TOKEN: string;
  AI: Ai;
}

const LABELS: Record<string, string> = {
  eat: "外食",
  weight: "體重",
  note: "備註",
  blood: "驗血",
  feel: "身體狀況",
};

// Asked after a bare command tapped from the menu; the next message gets that kind.
const PROMPTS: Record<string, string> = {
  eat: "🍽 吃了什麼？哪一天、哪一餐、大概內容（也可以傳照片）",
  weight: "⚖️ 體重多少？（例：90.8）",
  blood: "🩸 請傳驗血報告照片或文字",
  note: "📝 要記什麼？",
};
const PENDING_TTL_S = 30 * 60;

const HELP =
  "healthgo 收件匣指令：\n" +
  "/eat 外食內容（例：/eat 朋友聚餐，韓式烤肉）\n" +
  "/feel 身體狀況回報（點選回答）\n" +
  "/weight 體重數字\n" +
  "/blood 驗血結果（文字或照片）\n" +
  "/note 其他備註（不加指令也會當備註）\n" +
  "/cancel 取消\n\n" +
  "🎙 也可以傳語音（會自動轉成文字）\n" +
  "也可以從選單點指令，再輸入內容或傳照片。";

const COMMAND = /^\/(eat|feel|weight|note|blood|help|start|cancel)(?:@\w+)?(?:\s+([\s\S]*))?$/i;

function safeEqual(a: string, b: string): boolean {
  const enc = new TextEncoder();
  const x = enc.encode(a);
  const y = enc.encode(b);
  let diff = x.length ^ y.length;
  for (let i = 0; i < Math.max(x.length, y.length); i++) diff |= (x[i] ?? 0) ^ (y[i] ?? 0);
  return diff === 0;
}

async function tg(env: Env, method: string, body: object): Promise<any> {
  const res = await fetch(`https://api.telegram.org/bot${env.BOT_TOKEN}/${method}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) console.error(`${method} failed`, res.status);
  return res.ok ? res.json().catch(() => null) : null;
}

async function reply(env: Env, chatId: string, text: string, extra: object = {}): Promise<void> {
  await tg(env, "sendMessage", { chat_id: chatId, text, ...extra });
}

// ---- /feel check-in: one bot message edited in place, state in D1 `checkins` ----

const CHECKIN_TTL_S = 2 * 60 * 60;
const nowS = () => Math.floor(Date.now() / 1000);

interface Checkin { message_id: number; step: string; answers: Answers; started_at: number }

async function loadCheckin(env: Env, chatId: string): Promise<Checkin | null> {
  const r = await env.DB.prepare("SELECT message_id, step, answers, started_at FROM checkins WHERE chat_id = ?")
    .bind(chatId).first<{ message_id: number; step: string; answers: string; started_at: number }>();
  return r ? { ...r, answers: JSON.parse(r.answers) } : null;
}

async function saveCheckin(env: Env, chatId: string, c: Checkin): Promise<void> {
  await env.DB.prepare(
    "INSERT OR REPLACE INTO checkins (chat_id, message_id, step, answers, started_at) VALUES (?, ?, ?, ?, ?)",
  ).bind(chatId, c.message_id, c.step, JSON.stringify(c.answers), c.started_at).run();
}

async function editCheckin(env: Env, chatId: string, messageId: number, text: string, markup: object): Promise<void> {
  await tg(env, "editMessageText", { chat_id: chatId, message_id: messageId, text, reply_markup: markup });
}

/** Store the check-in as one `feel` entry (negative tg_message_id can't collide with real ones), close it. */
async function finishCheckin(env: Env, chatId: string, c: Checkin, extra: Answers = {}): Promise<void> {
  const a = { ...c.answers, ...extra };
  await env.DB.prepare(
    "INSERT OR IGNORE INTO entries (tg_message_id, received_at, kind, text, file_id, media_group_id, raw) " +
      "VALUES (?, ?, 'feel', ?, NULL, NULL, ?)",
  ).bind(-c.message_id, new Date().toISOString(), summarize(a), JSON.stringify(rawAnswers(a))).run();
  await env.DB.prepare("DELETE FROM checkins WHERE chat_id = ?").bind(chatId).run();
  await editCheckin(env, chatId, c.message_id, finalText(a), { inline_keyboard: [] });
}

/** An open check-in is being abandoned (new command, or stale): keep it if Q1 was answered. */
async function settleCheckin(env: Env, chatId: string, c: Checkin): Promise<void> {
  if (c.step !== firstStep) return finishCheckin(env, chatId, c, { partial: true });
  await env.DB.prepare("DELETE FROM checkins WHERE chat_id = ?").bind(chatId).run();
  await editCheckin(env, chatId, c.message_id, "已取消", { inline_keyboard: [] });
}

const isStale = (c: Checkin) => nowS() - c.started_at > CHECKIN_TTL_S;

async function startCheckin(env: Env, chatId: string): Promise<void> {
  const v = render(firstStep, {});
  const res = await tg(env, "sendMessage", { chat_id: chatId, text: v.text, reply_markup: v.reply_markup });
  const id = res?.result?.message_id;
  if (id) await saveCheckin(env, chatId, { message_id: id, step: firstStep, answers: {}, started_at: nowS() });
}

async function handleCallback(cq: any, env: Env): Promise<void> {
  const chatId = String(cq.message?.chat?.id ?? "");
  let toast: string | undefined;
  try {
    if (chatId !== String(env.CHAT_ID) || String(cq.from?.id) !== String(env.CHAT_ID)) return;
    const [, stepId, code] = String(cq.data ?? "").split(":");
    let c = await loadCheckin(env, chatId);
    if (!c || c.message_id !== cq.message.message_id) { toast = "已過期"; return; }
    if (isStale(c)) { await settleCheckin(env, chatId, c); toast = "已過期"; return; }
    if (stepId !== c.step) { toast = "已過期"; return; }

    const p = applyPress(c.step, code, c.answers);
    toast = p.toast;
    if (p.urgent) { await finishCheckin(env, chatId, c, { urgent: true }); return; }
    c = { ...c, answers: p.answers };
    if (p.advance) {
      const next = nextStep(c.step, c.answers);
      if (!next) { await finishCheckin(env, chatId, c); return; }
      c.step = next;
    }
    await saveCheckin(env, chatId, c);
    const v = render(c.step, c.answers);
    await editCheckin(env, chatId, c.message_id, v.text, v.reply_markup);
  } finally {
    await tg(env, "answerCallbackQuery", { callback_query_id: cq.id, ...(toast ? { text: toast } : {}) });
  }
}

// ---- Voice messages: Telegram getFile -> Workers AI Whisper -> text ----

const WHISPER = "@cf/openai/whisper-large-v3-turbo";
const WHISPER_PROMPT = "以下是繁體中文的健康紀錄，可能夾雜英文，例如 leg day。";
const MAX_VOICE_S = 5 * 60;
const MAX_VOICE_BYTES = 20 * 1024 * 1024;

function toBase64(buf: ArrayBuffer): string {
  const bytes = new Uint8Array(buf);
  let bin = "";
  for (let i = 0; i < bytes.length; i += 0x8000) bin += String.fromCharCode(...bytes.subarray(i, i + 0x8000));
  return btoa(bin);
}

/** Returns the transcript; throws a short, URL-free error message on any failure. Never logs the file URL (it holds the token). */
async function transcribe(env: Env, voice: any): Promise<string> {
  if ((voice.duration ?? 0) > MAX_VOICE_S) throw new Error("voice too long");
  if ((voice.file_size ?? 0) > MAX_VOICE_BYTES) throw new Error("voice too large");
  const info = await tg(env, "getFile", { file_id: voice.file_id });
  const path: string | undefined = info?.result?.file_path;
  if (!path) throw new Error("getFile failed");
  const res = await fetch(`https://api.telegram.org/file/bot${env.BOT_TOKEN}/${path}`);
  if (!res.ok) throw new Error(`download failed ${res.status}`);
  const buf = await res.arrayBuffer();
  if (buf.byteLength > MAX_VOICE_BYTES) throw new Error("voice too large");
  const out = await env.AI.run(WHISPER, { audio: toBase64(buf), initial_prompt: WHISPER_PROMPT });
  const text = (out?.text ?? "").trim();
  if (!text) throw new Error("empty transcript");
  return text;
}

async function handle(update: any, env: Env): Promise<void> {
  if (update?.callback_query) return handleCallback(update.callback_query, env);
  const msg = update?.message;
  if (!msg || String(msg.chat?.id) !== String(env.CHAT_ID)) return;

  const chatId = String(msg.chat.id);
  const raw: string = (msg.text ?? msg.caption ?? "").trim();
  const m = COMMAND.exec(raw);

  // Voice note: transcribe up front so a /feel Q5 answer and a normal entry share the result.
  const voice = msg.voice?.file_id ? msg.voice : msg.audio?.file_id ? msg.audio : null;
  const control = m && /^(help|start|cancel|feel)$/i.test(m[1]);
  let transcript = "";
  let transcribeError = "";
  if (voice && !control) {
    try {
      transcript = await transcribe(env, voice);
    } catch (e) {
      transcribeError = (e instanceof Error ? e.message : String(e)).slice(0, 80);
      console.error("transcribe failed", transcribeError);
    }
  }

  // An open check-in: a stale one is settled; /cancel drops it; any other command saves it as partial;
  // plain text at the last question is the free-text answer.
  const open = await loadCheckin(env, chatId);
  if (open) {
    const cmd = m?.[1].toLowerCase();
    if (isStale(open) || (m && cmd !== "cancel")) {
      await settleCheckin(env, chatId, open);
    } else if (cmd === "cancel") {
      await env.DB.prepare("DELETE FROM checkins WHERE chat_id = ?").bind(chatId).run();
      await editCheckin(env, chatId, open.message_id, "已取消", { inline_keyboard: [] });
    } else if (!m && open.step === "q5" && (raw || transcript) && !msg.photo && !msg.document) {
      await finishCheckin(env, chatId, { ...open, answers: { ...open.answers, note: raw || transcript } });
      if (transcript) await reply(env, chatId, `🎙 ${transcript}`);
      return;
    }
  }
  if (m && m[1].toLowerCase() === "feel") {
    await env.DB.prepare("DELETE FROM pending WHERE chat_id = ?").bind(chatId).run();
    await startCheckin(env, chatId);
    return;
  }

  let kind = "note";
  let text = raw;
  if (m) {
    const cmd = m[1].toLowerCase();
    if (cmd === "help" || cmd === "start") {
      await reply(env, chatId, HELP);
      return;
    }
    if (cmd === "cancel") {
      await env.DB.prepare("DELETE FROM pending WHERE chat_id = ?").bind(chatId).run();
      await reply(env, chatId, "已取消");
      return;
    }
    kind = cmd;
    text = (m[2] ?? "").trim();
  }
  if (voice) text = [text, transcript].filter(Boolean).join("\n");

  let fileId: string | null = null;
  if (Array.isArray(msg.photo) && msg.photo.length) {
    const largest = msg.photo.reduce((a: any, b: any) =>
      (b.file_size ?? b.width * b.height) >= (a.file_size ?? a.width * a.height) ? b : a);
    fileId = largest.file_id;
  } else if (msg.document?.file_id) {
    fileId = msg.document.file_id;
  } else if (voice) {
    fileId = voice.file_id;
  }

  // Bare command (tapped from the menu): remember it and ask for the content.
  if (m && !text && !fileId) {
    await env.DB.prepare("INSERT OR REPLACE INTO pending (chat_id, kind, set_at) VALUES (?, ?, ?)")
      .bind(chatId, kind, Math.floor(Date.now() / 1000)).run();
    await reply(env, chatId, PROMPTS[kind], {
      reply_markup: { force_reply: true, input_field_placeholder: LABELS[kind] },
    });
    return;
  }

  // No command: use the kind the previous bare command asked for, if recent.
  if (!m) {
    const pending = await env.DB.prepare("SELECT kind, set_at FROM pending WHERE chat_id = ?")
      .bind(chatId).first<{ kind: string; set_at: number }>();
    if (pending) {
      await env.DB.prepare("DELETE FROM pending WHERE chat_id = ?").bind(chatId).run();
      if (Date.now() / 1000 - pending.set_at <= PENDING_TTL_S && pending.kind in PROMPTS) kind = pending.kind;
    }
  }

  const group: string | null = msg.media_group_id ? String(msg.media_group_id) : null;
  let firstOfGroup = true;
  if (group) {
    const prior = await env.DB.prepare(
      "SELECT kind FROM entries WHERE media_group_id = ? ORDER BY id LIMIT 1",
    ).bind(group).first<{ kind: string }>();
    if (prior) {
      firstOfGroup = false;
      if (!m) kind = prior.kind; // later photos carry no caption: inherit
    }
  }

  const receivedAt = new Date((msg.date ?? Math.floor(Date.now() / 1000)) * 1000).toISOString();
  const stored = voice
    ? { ...msg, ...(transcribeError ? { transcribe_error: transcribeError } : { transcribed: true, duration: voice.duration ?? null }) }
    : msg;
  const res = await env.DB.prepare(
    "INSERT OR IGNORE INTO entries (tg_message_id, received_at, kind, text, file_id, media_group_id, raw) " +
      "VALUES (?, ?, ?, ?, ?, ?, ?)",
  ).bind(msg.message_id, receivedAt, kind, text, fileId, group, JSON.stringify(stored)).run();

  // A Telegram retry inserts nothing: don't reply twice.
  if (res.meta.changes > 0 && firstOfGroup) {
    if (voice && transcribeError) {
      await reply(env, chatId, "⚠️ 已收到語音，但轉錄失敗，review 時會再處理。");
    } else {
      await reply(env, chatId, `✅ 已記錄（${LABELS[kind]}）` + (voice ? `\n🎙 ${transcript}` : ""));
    }
  }
}

export default {
  async fetch(req: Request, env: Env): Promise<Response> {
    const url = new URL(req.url);

    if (req.method === "POST" && url.pathname === "/telegram") {
      const secret = req.headers.get("X-Telegram-Bot-Api-Secret-Token") ?? "";
      if (!env.WEBHOOK_SECRET || !safeEqual(secret, env.WEBHOOK_SECRET)) {
        return new Response("unauthorized", { status: 401 });
      }
      try {
        await handle(await req.json(), env);
      } catch (e) {
        console.error("handle failed", e instanceof Error ? e.message : String(e));
      }
      return new Response("ok");
    }

    if (req.method === "GET" && url.pathname === "/pull") {
      const auth = req.headers.get("Authorization") ?? "";
      if (!env.PULL_TOKEN || !safeEqual(auth, `Bearer ${env.PULL_TOKEN}`)) {
        return new Response("unauthorized", { status: 401 });
      }
      const since = Number.parseInt(url.searchParams.get("since_id") ?? "0", 10) || 0;
      const { results } = await env.DB.prepare(
        "SELECT id, tg_message_id, received_at, kind, text, file_id, media_group_id, raw " +
          "FROM entries WHERE id > ? ORDER BY id LIMIT 500",
      ).bind(since).all();
      return Response.json({ entries: results });
    }

    return new Response("not found", { status: 404 });
  },
} satisfies ExportedHandler<Env>;
