// /feel check-in: pure flow logic (question table, next step, rendering, summary). No I/O here.

export type Answers = Record<string, any>;

interface Opt {
  code: string;
  label: string;
  short?: string; // used in the saved summary when the button label is long
  act?: boolean; // immediate action button (own row, never a toggle)
}

interface Step {
  id: string;
  title: string;
  multi?: boolean;
  options: Opt[];
  cols: number;
  when?: (a: Answers) => boolean; // branch condition; absent = always asked
  summary?: (a: Answers) => string | null;
}

const has = (a: Answers, code: string) => Array.isArray(a.q1) && a.q1.includes(code);
const lab = (stepId: string, code: string): string => {
  const o = STEPS.find((s) => s.id === stepId)?.options.find((x) => x.code === code);
  return o ? (o.short ?? o.label) : String(code);
};
const labs = (stepId: string, codes: string[]) => codes.map((c) => lab(stepId, c)).join("、");

export const STEPS: Step[] = [
  {
    id: "q1", title: "哪裡不對勁？（可多選）", multi: true, cols: 2,
    options: [
      { code: "hungry", label: "餓" }, { code: "dizzy", label: "頭暈" },
      { code: "headache", label: "頭痛" }, { code: "fatigue", label: "疲勞沒力" },
      { code: "sleep", label: "睡不好" }, { code: "mood", label: "情緒低落/煩躁" },
      { code: "pain", label: "肌肉或關節痛" }, { code: "gi", label: "腸胃不適" },
      { code: "sick", label: "生病（喉嚨痛、發燒）", short: "生病" }, { code: "other", label: "其他" },
      { code: "urgent", label: "🚨 緊急", act: true },
    ],
    summary: (a) => labs("q1", a.q1 ?? []),
  },
  {
    id: "q2", title: "多嚴重？", cols: 5,
    options: [
      { code: "1", label: "1 輕微" }, { code: "2", label: "2" }, { code: "3", label: "3" },
      { code: "4", label: "4" }, { code: "5", label: "5 很嚴重" },
    ],
    summary: (a) => (a.q2 != null ? `嚴重度 ${a.q2}` : null),
  },
  {
    id: "q3", title: "多久了？", cols: 2,
    options: [
      { code: "now", label: "剛剛" }, { code: "today", label: "今天" },
      { code: "d2_3", label: "2–3 天" }, { code: "week", label: "一週以上" },
    ],
    summary: (a) => (a.q3 ? lab("q3", a.q3) : null),
  },
  {
    id: "q4", title: "可能的原因？（可多選）", multi: true, cols: 2,
    options: [
      { code: "workout", label: "剛練完" }, { code: "underate", label: "吃太少/太久沒吃", short: "太久沒吃" },
      { code: "sleep", label: "沒睡好" }, { code: "stress", label: "壓力" },
      { code: "caffeine", label: "咖啡因有變" }, { code: "eatout", label: "外食" },
      { code: "unknown", label: "不知道" },
    ],
    summary: (a) => (a.q4?.length ? `原因：${labs("q4", a.q4)}` : null),
  },
  {
    id: "b1", title: "什麼時候暈？", cols: 1, when: (a) => has(a, "dizzy"),
    options: [
      { code: "standing", label: "站起來時才暈" }, { code: "constant", label: "一直暈" },
      { code: "palpitation", label: "有心悸/冷汗/發抖" },
    ],
    summary: (a) => (a.b1 ? `頭暈：${lab("b1", a.b1)}` : null),
  },
  {
    id: "b2", title: "餓：跟平常比？", cols: 1, when: (a) => has(a, "hungry"),
    options: [
      { code: "same", label: "差不多" }, { code: "more", label: "比較餓" },
      { code: "obsessed", label: "一直想著食物" },
    ],
    summary: (a) => (a.b2 ? `餓：${lab("b2", a.b2)}` : null),
  },
  {
    id: "b3", title: "這週訓練表現？", cols: 1, when: (a) => has(a, "fatigue"),
    options: [
      { code: "normal", label: "正常" }, { code: "slight", label: "有點掉" },
      { code: "marked", label: "明顯掉（做不完原本的次數或重量）", short: "明顯掉" },
    ],
    summary: (a) => (a.b3 ? `訓練表現：${lab("b3", a.b3)}` : null),
  },
  {
    id: "b4", title: "痛在哪裡？", cols: 3, when: (a) => has(a, "pain"),
    options: [
      { code: "shoulder", label: "肩" }, { code: "elbow", label: "手肘" }, { code: "back", label: "背" },
      { code: "hip", label: "髖" }, { code: "knee", label: "膝" }, { code: "other", label: "其他" },
    ],
    summary: (a) =>
      a.b4 ? `痛處：${lab("b4", a.b4)}${a.b4i ? `（${a.b4i === "yes" ? "會" : "不會"}影響訓練）` : ""}` : null,
  },
  {
    id: "b4i", title: "會影響訓練嗎？", cols: 2, when: (a) => has(a, "pain"),
    options: [{ code: "yes", label: "會" }, { code: "no", label: "不會" }],
  },
  {
    id: "b6", title: "B 肝檢查：有沒有以下任何一項？（可多選）", multi: true, cols: 1,
    when: (a) => has(a, "fatigue") || has(a, "gi") || has(a, "sick"),
    options: [
      { code: "jaundice", label: "皮膚或眼白發黃", short: "發黃" }, { code: "darkurine", label: "尿色變深" },
      { code: "palestool", label: "大便顏色變淡" }, { code: "ruq", label: "右上腹痛" },
      { code: "itch", label: "新出現的發癢" }, { code: "bruise", label: "容易瘀青" },
      { code: "none", label: "都沒有", act: true },
    ],
    summary: (a) => (a.b6 ? `B肝檢查：${a.b6.length ? labs("b6", a.b6) : "都沒有"}` : null),
  },
  {
    id: "q5", title: "還想補充什麼？直接傳文字給我，或按「跳過」。", cols: 1,
    options: [{ code: "skip", label: "跳過", act: true }],
    summary: (a) => (a.note ? `補充：${a.note}` : null),
  },
];

export const URGENT_TEXT =
  "🚨 如果有胸痛、昏倒、呼吸困難、吐血、眼白或皮膚變黃 → 立刻看醫生或打 000。不要等 review。";

export const firstStep = "q1";

/** The step after `current` whose branch condition holds; null when the check-in is complete. */
export function nextStep(current: string, a: Answers): string | null {
  const i = STEPS.findIndex((s) => s.id === current);
  for (const s of STEPS.slice(i + 1)) if (!s.when || s.when(a)) return s.id;
  return null;
}

export interface Press {
  answers: Answers;
  advance: boolean;
  urgent?: boolean;
  toast?: string;
}

/** Apply one button press to the answers. Pure: returns a new answers object. */
export function applyPress(stepId: string, code: string, prev: Answers): Press {
  const step = STEPS.find((s) => s.id === stepId);
  const a: Answers = { ...prev };
  if (!step) return { answers: a, advance: false, toast: "已過期" };

  if (stepId === "q1" && code === "urgent") return { answers: a, advance: false, urgent: true };
  if (stepId === "q5") return { answers: a, advance: code === "skip" };

  if (step.multi) {
    const cur: string[] = [...(a[stepId] ?? [])];
    if (code === "none") return { answers: { ...a, [stepId]: [] }, advance: true };
    if (code === "done") {
      if (!cur.length) {
        return { answers: a, advance: false, toast: stepId === "b6" ? "請選項目，或按「都沒有」" : "請至少選一項" };
      }
      return { answers: a, advance: true };
    }
    const opt = step.options.find((o) => o.code === code && !o.act);
    if (!opt) return { answers: a, advance: false };
    a[stepId] = cur.includes(code) ? cur.filter((c) => c !== code) : [...cur, code];
    return { answers: a, advance: false };
  }

  if (!step.options.some((o) => o.code === code)) return { answers: a, advance: false };
  a[stepId] = stepId === "q2" ? Number(code) : code;
  return { answers: a, advance: true };
}

/** Text and inline keyboard for a step, given the answers so far. */
export function render(stepId: string, a: Answers) {
  const step = STEPS.find((s) => s.id === stepId)!;
  const picked: string[] = step.multi ? (a[stepId] ?? []) : [];
  const btn = (o: Opt) => ({
    text: picked.includes(o.code) ? `✅ ${o.label}` : o.label,
    callback_data: `f:${stepId}:${o.code}`,
  });
  const rows: { text: string; callback_data: string }[][] = [];
  const toggles = step.options.filter((o) => !o.act);
  for (let i = 0; i < toggles.length; i += step.cols) rows.push(toggles.slice(i, i + step.cols).map(btn));
  for (const o of step.options.filter((x) => x.act)) rows.push([btn(o)]);
  if (step.multi) rows.push([{ text: "完成 ➡️", callback_data: `f:${stepId}:done` }]);
  return { text: `🩺 ${step.title}`, reply_markup: { inline_keyboard: rows } };
}

export function summarize(a: Answers): string {
  if (a.urgent) return "🚨 緊急";
  const parts = STEPS.map((s) => s.summary?.(a)).filter((x): x is string => !!x);
  if (a.partial) parts.push("未完成");
  return parts.join("｜");
}

export function warnings(a: Answers): string[] {
  const w: string[] = [];
  if (a.b1 === "palpitation") w.push("⚠️ 頭暈加上心悸、冷汗或發抖，如果再發生請看醫生。");
  if (a.b6?.length) w.push("⚠️ 有 B 肝相關症狀，請盡快聯絡醫生安排抽血。");
  return w;
}

/** Structured answers as stored in entries.raw. */
export function rawAnswers(a: Answers): Answers {
  return { urgent: false, partial: false, ...a };
}

export function finalText(a: Answers): string {
  const body = a.urgent ? `${summarize(a)}\n${URGENT_TEXT}` : [summarize(a), ...warnings(a)].join("\n");
  return `✅ 已記錄（身體狀況）\n${body}`;
}
