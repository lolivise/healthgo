# /review reference

## Decision rules

Judge on **trends, not single days**. Weight noise from salt, carbs, creatine and eating out can be ±1 kg.

| Signal | Keep cutting | Slow down | Diet break | Adjust intake |
|---|---|---|---|---|
| 14d weight trend | −0.3 to −0.7 %/wk (>84 kg), −0.3 to −0.5 %/wk (≤84 kg) | faster than the weight-based cap (0.7 / 0.5 %, adopted 2026-10-25); faster than 1 % = hard stop | — | above −0.25 %/wk for 2+ weeks (a plateau) with good recovery |
| Strength (e1RM, main lifts) | stable within ±3 % | −3 to −5 % on 1–2 lifts | −5 % or worse on several lifts for 2+ weeks | — |
| Recovery | baseline | 1–2 flags (RHR +5, HRV unbalanced, sleep <6 h, BB high <50) | flags persisting 10+ days | — |
| Cut length | — | — | 10–12+ weeks of continuous deficit with fatigue signs | — |

- **A plateau with good recovery** → "adjust intake". First raise fat to the 0.6 g/kg floor if it is below it
  (his baseline is 0.5 g/kg), then trim carbs, e.g. potato 400 g → 350 g ≈ −40 kcal. Never cut protein, and never go below
  1,700 kcal.
- **A plateau with poor recovery** → not "eat less" but "diet break" or "slow down". Under-recovery
  stalls loss too.
- **Diet break** = 1–2 weeks at the estimated maintenance (`maintenance_kcal_estimate`, ±200), mostly
  from extra carbs (potato, oats) and fat. Protein stays the same.
- **Near the trip:** from about 2027-01-16, plan maintenance regardless of the other signals ([[trip-taiwan-2027]]).
- **The first 4–6 weeks of the cut** overstate fat loss (water and glycogen). Don't use them to calibrate the maintenance estimate.
- **No deliberate load drops any more (Darren, 2026-10-18):** the late-Sep technique phase (lighter, slower) finished by
  W41. From W41 (2026-10-05) on every load is real, so **any drop in e1RM or reps at the same load against W41-or-later
  numbers is real strength loss**. Never explain it away as "deliberately lighter" or "technique phase". Don't compare
  against pre-W41 loads (that drop was the phase, already done). See memory `training-routine.md`.
- **Muscle signal (no InBody anymore, gym removed it 2026-10-10):** strength on those lifts, plus the rate of loss staying
  within target (at most about 0.5-0.75 %/wk) and protein adequacy. Body-fat % is no longer measured: progress toward the
  15-18 % goal is estimated from the weight trend, assuming lean mass of about 68 kg from the one 2026-09-27 scan
  (91.4 kg, 25.5 %), so 15-18 % is roughly 80-83 kg. Treat it as a rough estimate.
- **Creatine** (5 g/day) holds water. Keep it constant, and don't read a creatine change as fat.
- **Shoulder:** any OHP or shoulder-press load jump, or pain he mentions → keep the load moderate, use 8–12 reps, and suggest a
  landmine press or neutral-grip dumbbell press as a swap.
- **Doctor referral:** RHR up 8+ bpm for 2 weeks, HRV low for 2+ weeks despite rest, or anything
  liver-related. Say so plainly.

## Health-guard checklist (inflammation, too-fast loss, immunity, face)

Added 2026-10-25 from `research/reports/慢性發炎 減重過快 臉部老化.md`; evidence in memory `evidence-rapid-loss-harms.md`,
`evidence-inflammation-immunity-hepb.md`, `evidence-facial-aging.md`. Run it every review with data already on hand
(no new tracking). Yellow bands and the EA 1,500 red line are working numbers, not study cut-offs. Where a row is
stricter than `safety-limits.md`, the hard limits there still decide; a yellow here argues for "slow down".

| Check | Green | Yellow → slow down / eat more | Red |
|---|---|---|---|
| 14d weight trend | >84 kg: ≤0.7 %/wk; ≤84 kg: ≤0.5 %/wk | above that | >1 %/wk, or >1.5 kg/wk |
| Energy availability: fixed-diet kcal (+ eat-out) − Garmin activity kcal (sum of `activities.calories`), weekly avg | ≥1,700 | 1,500–1,700 | <1,500 |
| Weeks of continuous deficit | <10 | 10–12: raise a diet break | >12 with no break |
| Main-lift e1RM | flat or up | down 2 weeks running | ≥5 % below the cut's best |
| Sleep (Garmin weekly avg) | ≥7 h | 6–7 h | <6 h, or ≥3 nights <6 h |
| RHR / HRV | stable | RHR falling **with** cold/tired on /feel (deep-deficit sign, not fitness) | RHR +5 bpm for a week, or HRV unbalanced most days |
| /feel, notes | nothing | hunger, irritability, more hair shedding (window ≈ mid-Sep → mid-Nov 2026), skin worse | RUQ pain after fatty food, yellow eyes/skin, dark urine → doctor within days |
| New supplements / herbal | none | — | any (esp. fat burners, "liver" or Chinese herbal) → ask the doctor first |

- Garmin activity kcal include BMR during the session, so EA comes out conservative (≈590/day W37–W42 → EA ≈30 at 2,520).
- Garmin HRV is **not** an inflammation marker; don't write "發炎升高" from HRV. Inflammation is judged from hs-CRP at the GP.
- Report language: a changed face during a cut is expected deflation, not collagen damage; the skin lever is daily
  SPF50+, not slower eating ([[evidence-facial-aging]]).
- Before the Taiwan trip, and whenever alcohol comes up: no safe dose with Hep B; never stop antivirals; protect sleep
  around flights ([[evidence-inflammation-immunity-hepb]]).

## Useful queries

```sql
-- weekly weight averages over the whole cut
SELECT strftime('%Y-W%W', date) wk, ROUND(AVG(kg),2) avg_kg, COUNT(*) n FROM weights GROUP BY wk ORDER BY wk;

-- best e1RM per exercise per week (main-lift trend)
SELECT strftime('%Y-W%W', date) wk, exercise, MAX(e1rm_kg) e1rm, MAX(weight_kg) top
FROM sets WHERE weight_kg > 0 GROUP BY wk, exercise ORDER BY exercise, wk;

-- recovery by week
SELECT strftime('%Y-W%W', date) wk, ROUND(AVG(rhr),1) rhr, ROUND(AVG(hrv_last_night),1) hrv,
       ROUND(AVG(sleep_h),2) sleep, ROUND(AVG(avg_stress),1) stress, ROUND(AVG(bb_high),1) bb_hi
FROM daily GROUP BY wk ORDER BY wk;

-- what his weeks look like
SELECT date, type, name, duration_min, avg_hr FROM activities ORDER BY date DESC LIMIT 30;

-- volume per exercise category, last 4 weeks
SELECT category, COUNT(*) sets, SUM(reps) reps FROM sets WHERE date >= date('now','-28 day') GROUP BY category ORDER BY sets DESC;
```

Exercise names are Garmin keys (`BARBELL_BENCH_PRESS`, `WEIGHTED_INCLINE_Y_RAISE`, …). Translate them to
normal 繁中/English names in the report. Sets logged with 0 or null weight are bodyweight or machine sets
with no load recorded, so don't count them as strength loss.

## Report template (繁體中文)

**Darren reads it on his phone in Telegram** (`healthgo send-report`, chat bubble ≈350 px ≈ 18–20 Chinese
characters per line). Write for that screen:
- **One fact per line.** Every number, change or lift gets its own bullet. Never chain facts with `、` / `；` /
  `。` into a paragraph.
- **A bullet is at most ~40 characters** (about 2 lines on the phone). If it's longer, split it into sub-bullets.
- **Reasons and changes = bold title line + indented sub-bullets** (2-space `-`). The sender renders headings
  bold, `-` as `•`, an indented `-` as an indented `◦`.
- **Tables:** short ones only. Each row becomes a bullet on the phone (≤3 columns → one line, 4 → a label line
  plus one sub-line per cell), so keep cells short.
- **No long runs of numbers** like a 14-day weight string. Show 3–5 key points, or a short table.
- **Paragraph text is for one-line notes only.**

```markdown
# 週報 2026-W41（10/05 – 10/11）
減脂第 13 週

## 結論：繼續減脂 ✅

1. **速度剛好**
  - 14 天趨勢 −0.6 %/週
  - 目標 0.5–0.75 %，上限 1 %
2. **力量持平**
  - 腿推 (leg press) e1RM 252 kg（前 4 週 240）
  - 滑輪下拉 (lat pulldown) e1RM 78 kg，本輪最佳
3. **恢復正常**
  - 靜息心率 (RHR) 50（基準 49.6）
  - 心率變異度 (HRV) 7/7 平衡

## 本週要改的
- **脂肪拉到安全下限**
  - 橄欖油 (olive oil) 8 g → 14 g
- **訓練**
  - 腿伸屈 (leg extension) 維持 50 kg，觀察次數

---

## 體重
| | 本週 | 上週 |
|---|---|---|
| 平均體重 | 91.0 kg | 91.7 kg |
- 14 天趨勢：−0.81 %/週
- 估計體脂：約 25 %（粗估）

## 力量 (Strength)
…（每個動作一行：重量 × 次數、e1RM、對照；對照 W41 起的數字，下降就寫下降（不寫「刻意放輕」）；肩推 (OHP) 狀況）

## 恢復 (Recovery)
…（每項一行：本週 vs 4 週基準，用短表格）

## 飲食
…（每餐外食一行：日期、kcal、內容；TDEE 一行；調整一項一行）

## 訓練建議
…（只做針對性調整，不換整套課表；一項一行）

## 距離目標
…（檢查點倒數、預估體重、距 15–18 % 體脂；一項一行）
```
