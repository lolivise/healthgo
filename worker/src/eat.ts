// /eat: log a Cargill Cafe meal from the recipe-based menu (pushed to D1 `menu` by `healthgo menu-push`).
// One bot message is edited in place (menu path, kitchen bowl, favourites), plus text shortcuts.
// The flow state lives in D1 `eat_sessions`; saved entries land in `entries` (kind `eat`, negative tg_message_id).

import type { Env } from "./index";

export type Tg = (method: string, body: object) => Promise<any>;
export interface Ctx { env: Env; tg: Tg }

const SHOP = "cargill-cafe";
const SESSION_TTL_S = 2 * 60 * 60;
const NAMING_TTL_S = 10 * 60;
const PAGE = 8;
const nowS = () => Math.floor(Date.now() / 1000);

// ---------------------------------------------------------------- menu data

interface Row {
  code: number; kind: string; item_ref: string; ref_id: string; category: string;
  name_zh: string; name_en: string | null; variant: string | null;
  kcal: number | null; protein: number | null; fat: number | null; carb: number | null;
  grams: number | null; serve_g: number | null; sort: number; addon_combos: string | null; est: number;
}
interface Combo { name: string; min: number; max: number; items: number[] }

interface Menu {
  byCode: Map<number, Row>;
  dishes: Row[];
  comps: Row[];
  addons: Row[];
  cats: string[];
}

const COLS = "code, kind, item_ref, ref_id, category, name_zh, name_en, variant, kcal, protein, fat, carb, grams, serve_g, sort, addon_combos, est";

async function loadMenu(env: Env): Promise<Menu> {
  const { results } = await env.DB.prepare(`SELECT ${COLS} FROM menu WHERE shop = ? ORDER BY kind, sort`)
    .bind(SHOP).all<Row>();
  const byCode = new Map(results.map((r) => [r.code, r]));
  const dishes = results.filter((r) => r.kind === "dish");
  const first = new Map<string, number>();
  for (const d of dishes) first.set(d.category, Math.min(first.get(d.category) ?? Infinity, d.sort));
  return {
    byCode, dishes,
    comps: results.filter((r) => r.kind === "component"),
    addons: results.filter((r) => r.kind === "addon"),
    cats: [...first.entries()].sort((a, b) => a[1] - b[1]).map((e) => e[0]),
  };
}

const combosOf = (d: Row): Combo[] => (d.addon_combos ? JSON.parse(d.addon_combos) : []);
const variantsOf = (m: Menu, d: Row) => m.dishes.filter((x) => x.item_ref === d.item_ref);

/** One representative row (the first variant) per dish in a category, in menu order. */
function itemsInCat(m: Menu, cat: string): Row[] {
  const seen = new Set<string>();
  const out: Row[] = [];
  for (const d of m.dishes) {
    if (d.category !== cat || seen.has(d.item_ref)) continue;
    seen.add(d.item_ref);
    out.push(d);
  }
  return out;
}

// ---------------------------------------------------------------- numbers and text

const fmt = (n: number) => Math.round(n).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
const r1 = (n: number) => Math.round(n * 10) / 10;
const qtyText = (q: number) => String(r1(q));
const PORTION_TEXT: Record<number, string> = { 75: "¾", 50: "½", 25: "¼" };

interface Line { code: number; qty: number }
type Mode = "menu" | "bowl" | "favourite" | "text";
interface Totals { kcal: number | null; protein: number | null; fat: number | null; carb: number | null }
interface ItemOut {
  code: number; ref_id: string; kind: string; name: string; qty: number;
  kcal: number | null; protein: number | null; fat: number | null; carb: number | null;
}
interface Computed { items: ItemOut[]; total: Totals; summary: string; est: boolean; portion: number }

const dishName = (m: Menu, r: Row) =>
  r.name_zh + (r.variant && r.variant !== r.name_zh && variantsOf(m, r).length > 1 ? `（${r.variant}）` : "");

function compute(m: Menu, lines: Line[], portion: number): Computed {
  const items: ItemOut[] = [];
  const names: string[] = [];
  let est = false;
  const sum = { kcal: 0, protein: 0, fat: 0, carb: 0 };
  for (const l of lines) {
    const r = m.byCode.get(l.code);
    if (!r) continue;
    const name = r.kind === "dish" ? dishName(m, r) : r.name_zh;
    const scale = (v: number | null) => (v == null || r.est ? null : r1(v * l.qty));
    items.push({
      code: r.code, ref_id: r.ref_id, kind: r.kind, name, qty: l.qty,
      kcal: scale(r.kcal), protein: scale(r.protein), fat: scale(r.fat), carb: scale(r.carb),
    });
    names.push(r.kind === "component" ? `${name}×${qtyText(l.qty)}` : name);
    if (r.est && r.kind === "dish") est = true;
    if (!r.est) {
      sum.kcal += (r.kcal ?? 0) * l.qty;
      sum.protein += (r.protein ?? 0) * l.qty;
      sum.fat += (r.fat ?? 0) * l.qty;
      sum.carb += (r.carb ?? 0) * l.qty;
    }
  }
  const f = portion / 100;
  let summary = names.join(" + ");
  if (portion < 100) summary += `（吃 ${PORTION_TEXT[portion] ?? `${portion}%`}）`;
  return {
    items, est, portion: f, summary,
    total: est
      ? { kcal: null, protein: null, fat: null, carb: null } // a dish without a recipe: nothing is known
      : { kcal: r1(sum.kcal * f), protein: r1(sum.protein * f), fat: r1(sum.fat * f), carb: r1(sum.carb * f) },
  };
}

const NO_RECIPE = "(無食譜，需估算)";
const entryText = (c: Computed) => (c.est ? `${c.summary} ${NO_RECIPE}` : c.summary);
const resultText = (c: Computed) =>
  c.est
    ? `✅ 已記錄：${c.summary} ${NO_RECIPE}`
    : `✅ 已記錄：${c.summary} ≈ ${fmt(c.total.kcal ?? 0)} kcal · 蛋白質 ${fmt(c.total.protein ?? 0)} g（食譜計算）`;
const lineStat = (c: Computed) => `≈ ${fmt(c.total.kcal ?? 0)} kcal · 蛋白質 ${fmt(c.total.protein ?? 0)} g`;

/** Perth is UTC+8 all year. Meal by local time; date = today there. */
function perthNow(): { date: string; meal: string } {
  const d = new Date(Date.now() + 8 * 3600 * 1000);
  const mins = d.getUTCHours() * 60 + d.getUTCMinutes();
  const meal = mins < 10 * 60 + 30 ? "breakfast" : mins < 15 * 60 ? "lunch" : mins < 17 * 60 + 30 ? "snack" : "dinner";
  return { date: d.toISOString().slice(0, 10), meal };
}

// ---------------------------------------------------------------- session

interface Tok { name: string; qty: number; forced?: number }
interface Tx { bowl: boolean; toks: Tok[]; portion: number; amb?: number }
interface Saved { mode: Mode; lines: Line[]; portion: number; fav?: boolean }
interface Naming { fav_id: number; prompt_id: number | null; at: number }
interface Orig { message_id: number; date: number; text: string }

interface State {
  v: "home" | "cat" | "dishes" | "variant" | "addons" | "portion" | "bowl" | "mult" | "fav" | "tx" | "txpick" | "saved";
  cat?: number; page?: number;
  dish?: number;                 // chosen dish row code
  addons?: number[];
  bowl?: Record<string, number>; // component code -> multiplier
  sel?: number;
  tx?: Tx;
  orig?: Orig;
  saved?: Saved;
  naming?: Naming;
}
interface Session { message_id: number; state: State; started_at: number }

async function loadSession(env: Env, chatId: string): Promise<Session | null> {
  const r = await env.DB.prepare("SELECT message_id, state, started_at FROM eat_sessions WHERE chat_id = ?")
    .bind(chatId).first<{ message_id: number; state: string; started_at: number }>();
  return r ? { message_id: r.message_id, state: JSON.parse(r.state), started_at: r.started_at } : null;
}

async function saveSession(env: Env, chatId: string, s: Session): Promise<void> {
  await env.DB.prepare("INSERT OR REPLACE INTO eat_sessions (chat_id, message_id, state, started_at) VALUES (?, ?, ?, ?)")
    .bind(chatId, s.message_id, JSON.stringify(s.state), s.started_at).run();
}

const dropSession = (env: Env, chatId: string) =>
  env.DB.prepare("DELETE FROM eat_sessions WHERE chat_id = ?").bind(chatId).run();

const isStale = (s: Session) => nowS() - s.started_at > SESSION_TTL_S;

const NONE = { inline_keyboard: [] as object[] };
type Btn = { text: string; callback_data: string };
const b = (text: string, data: string): Btn => ({ text, callback_data: data });
const kb = (rows: Btn[][]) => ({ inline_keyboard: rows });
function grid(btns: Btn[], cols: number): Btn[][] {
  const rows: Btn[][] = [];
  for (let i = 0; i < btns.length; i += cols) rows.push(btns.slice(i, i + cols));
  return rows;
}

async function edit(ctx: Ctx, chatId: string, messageId: number, text: string, markup: object): Promise<void> {
  await ctx.tg("editMessageText", { chat_id: chatId, message_id: messageId, text, reply_markup: markup });
}

/** Close an open session: an unfinished one is cancelled, a saved one just loses its buttons. */
export async function settleEat(ctx: Ctx, chatId: string, s: Session): Promise<void> {
  await dropSession(ctx.env, chatId);
  if (s.state.v === "saved") {
    await ctx.tg("editMessageReplyMarkup", { chat_id: chatId, message_id: s.message_id, reply_markup: NONE });
  } else {
    await edit(ctx, chatId, s.message_id, "已取消", NONE);
  }
}

export { loadSession };
export const eatIsStale = isStale;

// ---------------------------------------------------------------- screens

interface View { text: string; markup: object }

const BACK_HOME = b("‹ 返回", "e:home");

function homeView(): View {
  return {
    text: "🍽 外食紀錄：記哪一種？",
    markup: kb([
      [b("🍱 Cargill 菜單", "e:m"), b("🥣 廚房自己配", "e:b")],
      [b("⭐ 常吃", "e:f"), b("✏️ 其他外食", "e:o")],
      [b("取消", "e:x")],
    ]),
  };
}

function catView(m: Menu): View {
  const rows = grid(m.cats.map((c, i) => b(c, `e:c:${i}:0`)), 2);
  rows.push([BACK_HOME]);
  return { text: "🍱 Cargill 菜單：選分類", markup: kb(rows) };
}

function nav(prefix: string, page: number, total: number): Btn[] {
  const row: Btn[] = [];
  if (page > 0) row.push(b("◀", `${prefix}:${page - 1}`));
  if ((page + 1) * PAGE < total) row.push(b("▶", `${prefix}:${page + 1}`));
  return row;
}

function dishesView(m: Menu, ci: number, page: number): View {
  const cat = m.cats[ci] ?? "";
  const items = itemsInCat(m, cat);
  const slice = items.slice(page * PAGE, (page + 1) * PAGE);
  const rows = slice.map((d) => {
    const vs = variantsOf(m, d);
    const tag = vs.length > 1 ? "" : d.est ? " · 無食譜" : ` · ${fmt(d.kcal ?? 0)} kcal`;
    return [b(`${d.name_zh}${tag}`, `e:d:${d.code}`)];
  });
  const n = nav(`e:c:${ci}`, page, items.length);
  if (n.length) rows.push(n);
  rows.push([b("‹ 分類", "e:m")]);
  const pages = Math.max(1, Math.ceil(items.length / PAGE));
  return { text: `🍱 ${cat}（${page + 1}/${pages}）：選一道`, markup: kb(rows) };
}

function variantView(m: Menu, d: Row, ci: number): View {
  const rows = variantsOf(m, d).map((v) => [
    b(`${v.variant || v.name_zh}${v.est ? " · 無食譜" : ` · ${fmt(v.kcal ?? 0)} kcal`}`, `e:v:${v.code}`),
  ]);
  rows.push([b("‹ 返回", `e:c:${ci}:0`)]);
  return { text: `${d.name_zh}：選規格`, markup: kb(rows) };
}

function addonsView(m: Menu, dish: Row, picked: number[]): View {
  const combos = combosOf(dish);
  const rows: Btn[][] = [];
  const lines: string[] = [];
  for (const c of combos) {
    lines.push(`【${c.name}】${c.min > 0 ? `至少 ${c.min}、` : ""}最多 ${c.max}`);
    const btns = c.items.flatMap((code) => {
      const a = m.byCode.get(code);
      return a ? [b(`${picked.includes(code) ? "✅ " : ""}${a.name_zh}`, `e:a:${code}`)] : [];
    });
    rows.push(...grid(btns, 2));
  }
  rows.push([b("完成 ➡️", "e:ad")]);
  return { text: `${dish.name_zh}：要加料嗎？（可略過，直接按完成）\n${lines.join("\n")}`, markup: kb(rows) };
}

function portionView(c: Computed): View {
  return {
    text: `${c.summary}${c.est ? ` ${NO_RECIPE}` : ` ${lineStat(c)}`}\n吃了多少？`,
    markup: kb([[b("全部", "e:p:100"), b("¾", "e:p:75"), b("½", "e:p:50"), b("¼", "e:p:25")], [b("‹ 返回", "e:m")]]),
  };
}

function bowlLines(bowl: Record<string, number>): Line[] {
  return Object.entries(bowl).filter(([, q]) => q > 0).map(([code, qty]) => ({ code: Number(code), qty }));
}

function bowlView(m: Menu, bowl: Record<string, number>, page: number): View {
  const slice = m.comps.slice(page * PAGE, (page + 1) * PAGE);
  const btns = slice.map((c) => b(bowl[c.code] ? `✅ ${c.name_zh} ×${qtyText(bowl[c.code])}` : c.name_zh, `e:bc:${c.code}`));
  const rows = grid(btns, 2);
  const n = nav("e:b", page, m.comps.length);
  if (n.length) rows.push(n);
  const lines = bowlLines(bowl);
  rows.push([b("完成 ✅ 記錄", "e:bd"), BACK_HOME]);
  const pages = Math.max(1, Math.ceil(m.comps.length / PAGE));
  const c = lines.length ? compute(m, lines, 100) : null;
  const sum = c ? `\n${c.summary} ${lineStat(c)}` : "";
  return { text: `🥣 廚房自己配（${page + 1}/${pages}）：點食材選份量（1 份 = 廚房標準一份）${sum}`, markup: kb(rows) };
}

function multView(c: Row, cur: number): View {
  const mk = (q: number, t: string) => b(cur === q ? `✅ ${t}` : t, `e:bm:${c.code}:${Math.round(q * 10)}`);
  return {
    text: `${c.name_zh}：1 份 = ${fmt(c.serve_g ?? 0)} g ≈ ${fmt(c.kcal ?? 0)} kcal · 蛋白質 ${fmt(c.protein ?? 0)} g\n要幾份？`,
    markup: kb([[mk(0.5, "½"), mk(1, "1"), mk(1.5, "1½"), mk(2, "2"), mk(3, "3")], [b("移除", `e:bm:${c.code}:0`)]]),
  };
}

interface Fav { id: number; name: string; items: string }
const favPayload = (f: Fav): { mode: Mode; lines: Line[]; portion: number } => JSON.parse(f.items);

async function loadFavs(env: Env, chatId: string): Promise<Fav[]> {
  const { results } = await env.DB.prepare(
    "SELECT id, name, items FROM favourites WHERE chat_id = ? ORDER BY id DESC LIMIT 20",
  ).bind(chatId).all<Fav>();
  return results;
}

function favView(m: Menu, favs: Fav[]): View {
  const rows = favs.map((f) => {
    const p = favPayload(f);
    const c = compute(m, p.lines, p.portion);
    return [b(`${f.name}${c.est ? "" : ` · ${fmt(c.total.kcal ?? 0)} kcal`}`, `e:fu:${f.id}`), b("🗑", `e:fx:${f.id}`)];
  });
  rows.push([BACK_HOME]);
  return { text: favs.length ? "⭐ 常吃：點一下直接記錄（🗑 刪除）" : "⭐ 還沒有常吃。記錄後按「存成常吃」就會出現在這裡。", markup: kb(rows) };
}

function txConfirmView(m: Menu, lines: Line[], portion: number, bowl: boolean): View {
  const c = compute(m, lines, portion);
  return {
    text: `🍽 ${bowl ? "廚房自己配：" : ""}${c.summary} ${c.est ? NO_RECIPE : lineStat(c)}\n要記錄嗎？`,
    markup: kb([[b("✅ 記錄", "e:tc"), b("✏️ 當成一般外食", "e:tn")]]),
  };
}

// ---------------------------------------------------------------- save

async function insertEntry(ctx: Ctx, tgId: number, text: string, raw: object): Promise<void> {
  await ctx.env.DB.prepare(
    "INSERT OR IGNORE INTO entries (tg_message_id, received_at, kind, text, file_id, media_group_id, raw) " +
      "VALUES (?, ?, 'eat', ?, NULL, NULL, ?)",
  ).bind(tgId, new Date().toISOString(), text, JSON.stringify(raw)).run();
}

/** Store one recipe-based entry and turn the session message into the receipt. */
async function saveMeal(ctx: Ctx, chatId: string, s: Session, m: Menu, mode: Mode, lines: Line[], portionPct: number): Promise<void> {
  const c = compute(m, lines, portionPct);
  if (!c.items.length) {
    await edit(ctx, chatId, s.message_id, "沒有可記錄的項目（菜單可能已更新），請重新開始 /eat", NONE);
    await dropSession(ctx.env, chatId);
    return;
  }
  const { date, meal } = perthNow();
  await insertEntry(ctx, -s.message_id, entryText(c), {
    source: SHOP, mode, items: c.items, portion: c.portion, total: c.total, meal, date,
  });
  s.state = { v: "saved", saved: { mode, lines, portion: portionPct, fav: mode === "favourite" } };
  await saveSession(ctx.env, chatId, s);
  await edit(ctx, chatId, s.message_id, resultText(c),
    mode === "favourite" ? NONE : kb([[b("⭐ 存成常吃", "e:sf")]]));
}

// ---------------------------------------------------------------- start and callbacks

const FRESH = (): State => ({ v: "home" });

export async function startEat(ctx: Ctx, chatId: string, state: State = FRESH()): Promise<void> {
  const old = await loadSession(ctx.env, chatId);
  if (old) await settleEat(ctx, chatId, old);
  const m = state.v === "bowl" ? await loadMenu(ctx.env) : null;
  const v = state.v === "bowl" && m ? bowlView(m, state.bowl ?? {}, 0) : homeView();
  const res = await ctx.tg("sendMessage", { chat_id: chatId, text: v.text, reply_markup: v.markup });
  const id = res?.result?.message_id;
  if (id) await saveSession(ctx.env, chatId, { message_id: id, state, started_at: nowS() });
}

async function render(ctx: Ctx, chatId: string, s: Session, v: View): Promise<void> {
  await saveSession(ctx.env, chatId, s);
  await edit(ctx, chatId, s.message_id, v.text, v.markup);
}

/** The "其他外食" button: back to the plain free-text / photo prompt. */
async function otherEat(ctx: Ctx, chatId: string, s: Session): Promise<void> {
  await dropSession(ctx.env, chatId);
  await ctx.env.DB.prepare("INSERT OR REPLACE INTO pending (chat_id, kind, set_at) VALUES (?, 'eat', ?)")
    .bind(chatId, nowS()).run();
  await edit(ctx, chatId, s.message_id, "✏️ 其他外食", NONE);
  await ctx.tg("sendMessage", {
    chat_id: chatId, text: "🍽 吃了什麼？哪一天、哪一餐、大概內容（也可以傳照片）",
    reply_markup: { force_reply: true, input_field_placeholder: "外食" },
  });
}

export async function handleEatCallback(cq: any, ctx: Ctx): Promise<void> {
  const chatId = String(cq.message?.chat?.id ?? "");
  const { env } = ctx;
  let toast: string | undefined;
  try {
    if (chatId !== String(env.CHAT_ID) || String(cq.from?.id) !== String(env.CHAT_ID)) return;
    const [, act, ...a] = String(cq.data ?? "").split(":");
    const s = await loadSession(env, chatId);
    if (!s || s.message_id !== cq.message.message_id) { toast = "已過期"; return; }
    if (isStale(s)) { await settleEat(ctx, chatId, s); toast = "已過期"; return; }
    const st = s.state;
    const num = (i: number) => Number(a[i]);

    if (st.v === "saved") {
      if (act === "sf" && st.saved && !st.saved.fav) {
        await saveFavourite(ctx, chatId, s);
      } else toast = "已過期";
      return;
    }
    if (act === "x") { await settleEat(ctx, chatId, s); return; }
    if (act === "o") { await otherEat(ctx, chatId, s); return; }

    const m = await loadMenu(env);
    switch (act) {
      case "home":
        s.state = FRESH();
        return await render(ctx, chatId, s, homeView());
      case "m":
        s.state = { v: "cat" };
        return await render(ctx, chatId, s, catView(m));
      case "c": {
        const ci = num(0), page = num(1) || 0;
        s.state = { v: "dishes", cat: ci, page };
        return await render(ctx, chatId, s, dishesView(m, ci, page));
      }
      case "d": {
        const d = m.byCode.get(num(0));
        if (!d) { toast = "菜單已更新，請重選"; return; }
        if (variantsOf(m, d).length > 1) {
          s.state = { v: "variant", cat: st.cat, dish: d.code };
          return await render(ctx, chatId, s, variantView(m, d, st.cat ?? 0));
        }
        return await chooseDish(ctx, chatId, s, m, d);
      }
      case "v": {
        const d = m.byCode.get(num(0));
        if (!d) { toast = "菜單已更新，請重選"; return; }
        return await chooseDish(ctx, chatId, s, m, d);
      }
      case "a": {
        const dish = st.dish != null ? m.byCode.get(st.dish) : undefined;
        if (st.v !== "addons" || !dish) { toast = "已過期"; return; }
        const code = num(0);
        const combo = combosOf(dish).find((c) => c.items.includes(code));
        if (!combo) { toast = "已過期"; return; }
        let picked = st.addons ?? [];
        if (picked.includes(code)) picked = picked.filter((x) => x !== code);
        else {
          const inCombo = picked.filter((x) => combo.items.includes(x));
          if (inCombo.length >= combo.max) {
            if (combo.max === 1) picked = picked.filter((x) => !combo.items.includes(x));
            else { toast = `【${combo.name}】最多 ${combo.max} 項`; return; }
          }
          picked = [...picked, code];
        }
        s.state = { ...st, addons: picked };
        return await render(ctx, chatId, s, addonsView(m, dish, picked));
      }
      case "ad": {
        const dish = st.dish != null ? m.byCode.get(st.dish) : undefined;
        if (st.v !== "addons" || !dish) { toast = "已過期"; return; }
        for (const c of combosOf(dish)) {
          if ((st.addons ?? []).filter((x) => c.items.includes(x)).length < c.min) {
            toast = `【${c.name}】至少選 ${c.min} 項`;
            return;
          }
        }
        s.state = { ...st, v: "portion" };
        return await render(ctx, chatId, s, portionView(compute(m, menuLines(st), 100)));
      }
      case "p": {
        if (st.v !== "portion") { toast = "已過期"; return; }
        return await saveMeal(ctx, chatId, s, m, "menu", menuLines(st), num(0));
      }
      case "b": {
        const page = num(0) || 0;
        s.state = { v: "bowl", page, bowl: st.bowl ?? {} };
        return await render(ctx, chatId, s, bowlView(m, s.state.bowl!, page));
      }
      case "bc": {
        const c = m.byCode.get(num(0));
        if (!c || c.kind !== "component") { toast = "菜單已更新，請重選"; return; }
        s.state = { v: "mult", page: st.page, bowl: st.bowl ?? {}, sel: c.code };
        return await render(ctx, chatId, s, multView(c, s.state.bowl![c.code] ?? 0));
      }
      case "bm": {
        if (!st.bowl) { toast = "已過期"; return; }
        const code = num(0), q = num(1) / 10;
        const bowl = { ...st.bowl };
        if (q > 0) bowl[code] = q; else delete bowl[code];
        s.state = { v: "bowl", page: st.page ?? 0, bowl };
        return await render(ctx, chatId, s, bowlView(m, bowl, st.page ?? 0));
      }
      case "bd": {
        const lines = bowlLines(st.bowl ?? {});
        if (!lines.length) { toast = "先選至少一樣食材"; return; }
        return await saveMeal(ctx, chatId, s, m, "bowl", lines, 100);
      }
      case "f": {
        s.state = { v: "fav" };
        return await render(ctx, chatId, s, favView(m, await loadFavs(env, chatId)));
      }
      case "fu": {
        const f = await env.DB.prepare("SELECT id, name, items FROM favourites WHERE id = ? AND chat_id = ?")
          .bind(num(0), chatId).first<Fav>();
        if (!f) { toast = "找不到這個常吃"; return; }
        const p = favPayload(f);
        return await saveMeal(ctx, chatId, s, m, "favourite", p.lines, p.portion);
      }
      case "fx": {
        await env.DB.prepare("DELETE FROM favourites WHERE id = ? AND chat_id = ?").bind(num(0), chatId).run();
        toast = "已刪除";
        return await render(ctx, chatId, s, favView(m, await loadFavs(env, chatId)));
      }
      case "tp":
        return await pickCandidate(ctx, chatId, s, m, num(0));
      case "tc": {
        if (st.v !== "tx" || !st.tx) { toast = "已過期"; return; }
        const r = resolve(m, st.tx);
        if (r.t !== "ok") { toast = "已過期"; return; }
        return await saveMeal(ctx, chatId, s, m, "text", r.lines, st.tx.portion);
      }
      case "tn":
        return await asPlainEat(ctx, chatId, s);
      default:
        toast = "已過期";
    }
  } finally {
    await ctx.tg("answerCallbackQuery", { callback_query_id: cq.id, ...(toast ? { text: toast } : {}) });
  }
}

const menuLines = (st: State): Line[] => [
  ...(st.dish != null ? [{ code: st.dish, qty: 1 }] : []),
  ...(st.addons ?? []).map((code) => ({ code, qty: 1 })),
];

async function chooseDish(ctx: Ctx, chatId: string, s: Session, m: Menu, d: Row): Promise<void> {
  const cat = s.state.cat;
  if (combosOf(d).length) {
    s.state = { v: "addons", cat, dish: d.code, addons: [] };
    return render(ctx, chatId, s, addonsView(m, d, []));
  }
  s.state = { v: "portion", cat, dish: d.code, addons: [] };
  return render(ctx, chatId, s, portionView(compute(m, menuLines(s.state), 100)));
}

async function saveFavourite(ctx: Ctx, chatId: string, s: Session): Promise<void> {
  const sv = s.state.saved!;
  const n = await ctx.env.DB.prepare("SELECT COUNT(*) AS n FROM favourites WHERE chat_id = ?").bind(chatId).first<{ n: number }>();
  const name = `常吃 ${(n?.n ?? 0) + 1}`;
  const res = await ctx.env.DB.prepare("INSERT INTO favourites (chat_id, name, items, created_at) VALUES (?, ?, ?, ?)")
    .bind(chatId, name, JSON.stringify({ mode: sv.mode === "favourite" ? "menu" : sv.mode, lines: sv.lines, portion: sv.portion }), nowS()).run();
  const favId = Number(res.meta.last_row_id);
  const prompt = await ctx.tg("sendMessage", {
    chat_id: chatId, text: `⭐ 已存成「${name}」。想改名嗎？10 分鐘內直接回覆這則訊息的名字；不回覆就沿用「${name}」。`,
    reply_markup: { force_reply: true, input_field_placeholder: "常吃名稱" },
  });
  s.state = { ...s.state, saved: { ...sv, fav: true }, naming: { fav_id: favId, prompt_id: prompt?.result?.message_id ?? null, at: nowS() } };
  await saveSession(ctx.env, chatId, s);
  await ctx.tg("editMessageReplyMarkup", { chat_id: chatId, message_id: s.message_id, reply_markup: NONE });
}

/** A reply to the naming prompt within 10 minutes renames the favourite. True when the message was consumed. */
export async function eatNaming(ctx: Ctx, chatId: string, msg: any, text: string): Promise<boolean> {
  const s = await loadSession(ctx.env, chatId);
  const nm = s?.state.naming;
  if (!s || !nm) return false;
  if (nowS() - nm.at > NAMING_TTL_S) {
    delete s.state.naming;
    await saveSession(ctx.env, chatId, s);
    return false;
  }
  if (nm.prompt_id != null && msg.reply_to_message?.message_id !== nm.prompt_id) return false;
  const name = text.trim().slice(0, 30);
  if (!name) return false;
  await ctx.env.DB.prepare("UPDATE favourites SET name = ? WHERE id = ? AND chat_id = ?").bind(name, nm.fav_id, chatId).run();
  delete s.state.naming;
  await saveSession(ctx.env, chatId, s);
  await ctx.tg("sendMessage", { chat_id: chatId, text: `⭐ 已存成「${name}」` });
  return true;
}

// ---------------------------------------------------------------- text shortcuts

const PORTION_WORDS: [RegExp, number][] = [
  [/^(全部|全|全份|1份|一份)$/, 100],
  [/^(¾|3\/4|四分之三)$/, 75],
  [/^(½|1\/2|半|半份|一半)$/, 50],
  [/^(¼|1\/4|四分之一)$/, 25],
];
const BOWL_PREFIX = /^[廚厨]房[\s:：]*/;

export interface Parsed { bowl: boolean; toks: Tok[]; portion: number }

export function parseText(text: string): Parsed {
  let t = text.trim();
  const bowl = BOWL_PREFIX.test(t);
  if (bowl) t = t.replace(BOWL_PREFIX, "");
  const toks: Tok[] = [];
  let portion = 100;
  for (const w of t.split(/[\s,，、+＋;；]+/).filter(Boolean)) {
    const pw = bowl ? undefined : PORTION_WORDS.find(([re]) => re.test(w));
    if (pw) { portion = pw[1]; continue; }
    const mm = /^(.*?)[x×*]?(\d+(?:\.\d+)?)$/i.exec(w);
    if (mm && mm[1]) toks.push({ name: mm[1], qty: Number(mm[2]) });
    else toks.push({ name: w, qty: 1 });
  }
  return { bowl, toks, portion };
}

const norm = (x: string | null | undefined) => (x ?? "").toLowerCase().replace(/\s+/g, "");

/** Rows whose name contains the token; an exact name match wins over substrings. */
function matchRows(rows: Row[], name: string): Row[] {
  const q = norm(name);
  if (q.length < (/[^\x00-\x7f]/.test(q) ? 1 : 3)) return [];
  const exact = rows.filter((r) => norm(r.name_zh) === q || norm(r.name_en) === q);
  if (exact.length) return exact;
  return rows.filter((r) => norm(r.name_zh).includes(q) || norm(r.name_en).includes(q));
}

type Res = { t: "ok"; lines: Line[] } | { t: "amb"; idx: number; cands: Row[] } | { t: "fail" };

export function resolve(m: Menu, tx: Tx): Res {
  let amb: { idx: number; cands: Row[] } | null = null;
  const lines: Line[] = [];
  let fail = false;

  if (tx.bowl) {
    for (const [idx, t] of tx.toks.entries()) {
      if (!(t.qty > 0 && t.qty <= 10)) { fail = true; continue; }
      const forced = t.forced != null ? m.byCode.get(t.forced) : undefined;
      const c = forced ? [forced] : matchRows(m.comps, t.name);
      if (!c.length) fail = true;
      else if (c.length > 1) amb ??= { idx, cands: c };
      else lines.push({ code: c[0].code, qty: t.qty });
    }
  } else {
    const t0 = tx.toks[0];
    if (!t0 || t0.qty !== 1) return { t: "fail" };
    const forced = t0.forced != null ? m.byCode.get(t0.forced) : undefined;
    let cands = forced ? [forced] : matchRows(m.dishes, t0.name);
    if (!cands.length) return { t: "fail" };
    const rest: [Tok, number][] = tx.toks.slice(1).map((t, i) => [t, i + 1]);
    const addonToks: [Tok, number][] = [];
    for (const [t, idx] of rest) {
      // a token naming one variant (大, 半片, …) narrows an ambiguous dish
      const narrowed = cands.length > 1 ? cands.filter((r) => r.variant && norm(r.variant).includes(norm(t.name))) : [];
      if (narrowed.length && narrowed.length < cands.length) cands = narrowed;
      else addonToks.push([t, idx]);
    }
    if (cands.length > 1) amb = { idx: 0, cands };
    const allowed = new Set(cands.flatMap((d) => combosOf(d).flatMap((c) => c.items)));
    const pool = m.addons.filter((a) => allowed.has(a.code));
    const addonLines: Line[] = [];
    for (const [t, idx] of addonToks) {
      if (t.qty !== 1) { fail = true; continue; }
      const forcedA = t.forced != null ? m.byCode.get(t.forced) : undefined;
      const c = forcedA ? [forcedA] : matchRows(pool, t.name);
      if (!c.length) fail = true;
      else if (c.length > 1) amb ??= { idx, cands: c };
      else addonLines.push({ code: c[0].code, qty: 1 });
    }
    if (cands.length === 1) lines.push({ code: cands[0].code, qty: 1 });
    lines.push(...addonLines);
  }
  if (fail) return { t: "fail" };
  if (amb) return { t: "amb", ...amb };
  return { t: "ok", lines };
}

const candLabel = (m: Menu, r: Row) => (r.kind === "dish" ? dishName(m, r) : r.name_zh).slice(0, 40);

function pickView(m: Menu, idx: number, cands: Row[], tok: Tok): View {
  const rows = cands.slice(0, 8).map((r) => [b(candLabel(m, r), `e:tp:${r.code}`)]);
  rows.push([b("✏️ 當成一般外食", "e:tn")]);
  return { text: `「${tok.name}」有多個符合，選一個：`, markup: kb(rows) };
}

/**
 * `/eat <text>` (or a transcribed voice note): match it to the menu. Returns true when it replied
 * (confirmation or candidate buttons); false means "not a menu entry", so the caller stores it as free text.
 */
export async function eatShortcut(ctx: Ctx, chatId: string, text: string, orig: Orig): Promise<boolean> {
  const p = parseText(text);
  if (p.bowl && !p.toks.length) {
    await startEat(ctx, chatId, { v: "bowl", page: 0, bowl: {} });
    return true;
  }
  if (!p.toks.length) return false;
  const m = await loadMenu(ctx.env);
  const tx: Tx = { bowl: p.bowl, toks: p.toks, portion: p.portion };
  const r = resolve(m, tx);
  if (r.t === "fail") return false;
  const old = await loadSession(ctx.env, chatId);
  if (old) await settleEat(ctx, chatId, old);
  const v = r.t === "ok" ? txConfirmView(m, r.lines, tx.portion, tx.bowl) : pickView(m, r.idx, r.cands, tx.toks[r.idx]);
  const res = await ctx.tg("sendMessage", { chat_id: chatId, text: v.text, reply_markup: v.markup });
  const id = res?.result?.message_id;
  if (id) {
    await saveSession(ctx.env, chatId, {
      message_id: id, started_at: nowS(),
      state: { v: r.t === "ok" ? "tx" : "txpick", tx: r.t === "amb" ? { ...tx, amb: r.idx } : tx, orig },
    });
  }
  return true;
}

async function pickCandidate(ctx: Ctx, chatId: string, s: Session, m: Menu, code: number): Promise<void> {
  const tx = s.state.tx;
  if (s.state.v !== "txpick" || !tx || tx.amb == null) return;
  const toks = tx.toks.map((t, i) => (i === tx.amb ? { ...t, forced: code } : t));
  const next: Tx = { ...tx, toks, amb: undefined };
  const r = resolve(m, next);
  if (r.t === "ok") {
    s.state = { ...s.state, v: "tx", tx: next };
    return render(ctx, chatId, s, txConfirmView(m, r.lines, next.portion, next.bowl));
  }
  if (r.t === "amb") {
    s.state = { ...s.state, tx: { ...next, amb: r.idx } };
    return render(ctx, chatId, s, pickView(m, r.idx, r.cands, next.toks[r.idx]));
  }
  return asPlainEat(ctx, chatId, s);
}

/** Store the original text as an ordinary eat entry (the /log flow estimates it). */
async function asPlainEat(ctx: Ctx, chatId: string, s: Session): Promise<void> {
  const o = s.state.orig;
  await dropSession(ctx.env, chatId);
  if (o) {
    await insertEntry(ctx, o.message_id, o.text, { message_id: o.message_id, date: o.date, text: `/eat ${o.text}` });
  }
  await edit(ctx, chatId, s.message_id, "✅ 已記錄（外食）", NONE);
}
