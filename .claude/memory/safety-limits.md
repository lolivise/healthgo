---
name: safety-limits
description: Hard limits advice must never cross — loss ≤0.7 %/wk >84 kg, ≤0.5 % ≤84 kg (1 % absolute stop), ≥1700 kcal total AND ≥1700 after exercise (EA), protein ≥1.6 g/kg & ≥2.3 g/kg FFM, fat ≥0.7 g/kg, diet break after 10–12 wk, sleep target ≥7 h, red flags
metadata:
  type: feedback
---

Agreed with Darren 2026-10-09; **tightened 2026-10-25** after the inflammation / too-fast-loss research
([[evidence-rapid-loss-harms]]), all four proposals adopted by him. No recommendation may cross these, whatever the data says:

| Limit | Value |
|---|---|
| Loss rate cap (14-day trend) | **>84 kg: ≤0.7 %/wk; ≤84 kg: ≤0.5 %/wk** (2026-10-25). The leaner he gets, the bigger the lean share of each kg lost |
| Absolute stop line | 1 % bodyweight/week on the 14-day trend (the 2026-10-09 limit, kept) |
| Calorie floor | ~1,700 kcal/day total, unless he explicitly asks to go lower |
| Energy-availability floor | **intake − Garmin activity kcal ≥ 1,700/day** (25 kcal/kg × ~68 kg FFM), weekly average (2026-10-25). His first 13 weeks at 2,023 were ≈23 kcal/kg, below it |
| Protein floor | 1.6 g/kg bodyweight **and ≥2.3 g/kg FFM (~156 g)**; he eats ~167 g |
| Fat floor | **0.7 g/kg bodyweight** (was 0.6; raised 2026-10-25 for gallstone protection, testosterone, olive-oil anti-inflammatory evidence). Olive oil 4 → 13 g from 2026-11-09 |
| Diet break | Recommend after 10–12 weeks of continuous deficit. ⛔ **Overridden for this cut (Darren, 2026-10-29): cut to 12-13 no matter what; don't raise a break before then** ([[cutting-goal-2026]]) |
| Sleep target | **≥7 h weekly average** (2026-10-25: top immune lever; <6 h = 4.2× cold risk). <6 h stays the red flag |
| Red flags | RHR up 5+ bpm for a week, HRV out of balance most days, sleep falling apart → "slow down / stop", and if it persists, "see a doctor" |

**Why:** he is 36 with Hep B ([[health-conditions]]) and said not to "break my metabolism and health
during cutting". Speed is explicitly secondary.

**How to apply:** the thresholds live in `config/plan.json` (`safety`, `alerts`) and drive
`healthgo check` (`loss_fast` = 1 % stop line, `loss_above_cap` = weight-dependent cap). In a review, run the
Health-guard checklist in `.claude/skills/review/reference.md` and check every suggested change against this table
before writing it. If the data argues for crossing a limit, say so and recommend a doctor or dietitian instead.

Related: [[cutting-goal-2026]], [[daily-diet-baseline]], [[evidence-inflammation-immunity-hepb]]
