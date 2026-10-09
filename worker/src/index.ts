export interface Env {
  DB: D1Database;
  BOT_TOKEN: string;
  CHAT_ID: string;
  WEBHOOK_SECRET: string;
  PULL_TOKEN: string;
}

const LABELS: Record<string, string> = {
  eat: "外食",
  inbody: "InBody",
  weight: "體重",
  note: "備註",
  blood: "驗血",
};

// Asked after a bare command tapped from the menu; the next message gets that kind.
const PROMPTS: Record<string, string> = {
  eat: "🍽 吃了什麼？哪一天、哪一餐、大概內容（也可以傳照片）",
  inbody: "📊 請傳 InBody 結果照片",
  weight: "⚖️ 體重多少？（例：90.8）",
  blood: "🩸 請傳驗血報告照片或文字",
  note: "📝 要記什麼？",
};
const PENDING_TTL_S = 30 * 60;

const HELP =
  "healthgo 收件匣指令：\n" +
  "/eat 外食內容（例：/eat 朋友聚餐，韓式烤肉）\n" +
  "/inbody 附上 InBody 結果照片\n" +
  "/weight 體重數字\n" +
  "/blood 驗血結果（文字或照片）\n" +
  "/note 其他備註（不加指令也會當備註）\n" +
  "/cancel 取消\n\n" +
  "也可以從選單點指令，再輸入內容或傳照片。";

const COMMAND = /^\/(eat|inbody|weight|note|blood|help|start|cancel)(?:@\w+)?(?:\s+([\s\S]*))?$/i;

function safeEqual(a: string, b: string): boolean {
  const enc = new TextEncoder();
  const x = enc.encode(a);
  const y = enc.encode(b);
  let diff = x.length ^ y.length;
  for (let i = 0; i < Math.max(x.length, y.length); i++) diff |= (x[i] ?? 0) ^ (y[i] ?? 0);
  return diff === 0;
}

async function reply(env: Env, chatId: string, text: string, extra: object = {}): Promise<void> {
  const res = await fetch(`https://api.telegram.org/bot${env.BOT_TOKEN}/sendMessage`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ chat_id: chatId, text, ...extra }),
  });
  if (!res.ok) console.error("sendMessage failed", res.status);
}

async function handle(update: any, env: Env): Promise<void> {
  const msg = update?.message;
  if (!msg || String(msg.chat?.id) !== String(env.CHAT_ID)) return;

  const chatId = String(msg.chat.id);
  const raw: string = (msg.text ?? msg.caption ?? "").trim();
  const m = COMMAND.exec(raw);
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

  let fileId: string | null = null;
  if (Array.isArray(msg.photo) && msg.photo.length) {
    const largest = msg.photo.reduce((a: any, b: any) =>
      (b.file_size ?? b.width * b.height) >= (a.file_size ?? a.width * a.height) ? b : a);
    fileId = largest.file_id;
  } else if (msg.document?.file_id) {
    fileId = msg.document.file_id;
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
      if (Date.now() / 1000 - pending.set_at <= PENDING_TTL_S) kind = pending.kind;
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
  const res = await env.DB.prepare(
    "INSERT OR IGNORE INTO entries (tg_message_id, received_at, kind, text, file_id, media_group_id, raw) " +
      "VALUES (?, ?, ?, ?, ?, ?, ?)",
  ).bind(msg.message_id, receivedAt, kind, text, fileId, group, JSON.stringify(msg)).run();

  // A Telegram retry inserts nothing: don't reply twice.
  if (res.meta.changes > 0 && firstOfGroup) {
    await reply(env, chatId, `✅ 已記錄（${LABELS[kind]}）`);
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
