# /review reference

## Decision rules

Judge on **trends, not single days**. Weight noise from salt, carbs, creatine and eating out can be ±1 kg.

| Signal | Keep cutting | Slow down | Diet break | Adjust intake |
|---|---|---|---|---|
| 14d weight trend | −0.5 to −0.75 %/wk | below −1.0 %/wk, or −0.75 to −1.0 % with any recovery flag | — | above −0.25 %/wk for 2+ weeks (a plateau) with good recovery |
| Strength (e1RM, main lifts) | stable within ±3 % | −3 to −5 % on 1–2 lifts | −5 % or worse on several lifts for 2+ weeks | — |
| InBody muscle | SMM stable | SMM −0.5 kg or more between scans | SMM falling on 2 scans in a row | — |
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
- **Deliberate load drops:** since late Sep 2026 he trains lighter and slower on purpose (form, mind-muscle;
  see memory `training-routine.md`). An e1RM drop on a lift he deliberately de-loaded is **not** strength loss.
  Judge muscle by InBody SMM, plus e1RM on lifts whose load he kept.
- **Creatine** (5 g/day) holds water. Keep it constant, and don't read a creatine change as fat.
- **Shoulder:** any OHP or shoulder-press load jump, or pain he mentions → keep the load moderate, use 8–12 reps, and suggest a
  landmine press or neutral-grip dumbbell press as a swap.
- **Doctor referral:** RHR up 8+ bpm for 2 weeks, HRV low for 2+ weeks despite rest, or anything
  liver-related. Say so plainly.

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

```markdown
# 週報 2026-W41（10/05 – 10/11）· 減脂第 13 週

## 結論：繼續減脂 ✅
- 體重趨勢每週 −0.6%（目標 0.5–0.75%），速度剛好
- 主要動作力量持平：深蹲 (squat) e1RM 112 kg（前 4 週 113 kg）
- 恢復正常：靜息心率 (RHR) 51、心率變異度 (HRV) 平衡

**本週要改的：** 橄欖油 8 g → 18 g（脂肪拉到 0.6 g/kg 安全下限）

---

## 體重與身體組成
| | 本週 | 上週 | 變化 |
…（平均體重、14/28 天趨勢、InBody 體脂率與骨骼肌重 vs 上次）

## 力量 (Strength)
…（主要動作 e1RM 表格、停滯或下降的動作、肩推 (OHP) 狀況）

## 恢復 (Recovery)
…（RHR、HRV、睡眠、壓力、身體能量 (Body Battery) vs 你的 4 週基準）

## 飲食
…（基準 1,846 kcal；外食紀錄；估算維持熱量 (TDEE)；建議調整用現有食物的份量表示）

## 訓練建議
…（只做針對性調整，不換整套課表）

## 距離目標
…（離 2027-01-22 檢查點還有幾週、預估屆時體重、離 15–18% 體脂還差多少）
```
