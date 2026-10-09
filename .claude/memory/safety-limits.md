---
name: safety-limits
description: Hard limits advice must never cross — max 1%/wk loss, ≥1700 kcal, protein ≥1.6 g/kg, fat ≥0.6 g/kg, diet break after 10–12 wk, red-flag rules
metadata:
  type: feedback
---

Agreed with Darren 2026-10-09. No recommendation may cross these, whatever the data says:

| Limit | Value |
|---|---|
| Max sustained loss | 1% bodyweight/week, judged on the 14-day trend |
| Calorie floor | ~1,700 kcal/day, unless he explicitly asks to go lower |
| Protein floor | 1.6 g/kg bodyweight |
| Fat floor | 0.6 g/kg bodyweight. His baseline is ~0.5 g/kg, so **raise fat (~+10 g/day) before cutting anything else** |
| Diet break | Recommend after 10–12 weeks of continuous deficit |
| Red flags | RHR up 5+ bpm for a week, HRV out of balance most days, sleep falling apart → "slow down / stop", and if it persists, "see a doctor" |

**Why:** he is 36 with Hep B ([[health-conditions]]) and said not to "break my metabolism and health
during cutting". Speed is explicitly secondary.

**How to apply:** the thresholds live in `config/plan.json` (`safety`, `alerts`) and drive
`healthgo check`. In a review, check every suggested change against this table before writing it.
If the data argues for crossing a limit, say so and recommend a doctor or dietitian instead.

Related: [[cutting-goal-2026]], [[daily-diet-baseline]]
