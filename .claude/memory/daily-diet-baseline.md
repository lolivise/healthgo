---
name: daily-diet-baseline
description: Darren's fixed daily cutting diet (1,846 kcal / 167 g protein), eaten identically every day; eating out ~once every 1–2 weeks
metadata:
  type: user
---

Darren eats **the same food every day** during the cut and is strict about it. Treat this as
the default daily intake for every day unless a day is logged as different.
Source: `daily_diet_intake(1).csv`, given 2026-10-09.

| Food | Daily amount | kcal | Protein g | Fat g | Carbs g |
|---|---|---:|---:|---:|---:|
| Potato (馬鈴薯) | 400 g | 308 | 8.2 | 0.4 | 70.0 |
| Olive oil (橄欖油) | 8 g | 72 | 0.0 | 8.0 | 0.0 |
| Chicken breast (雞胸肉) | 350 g raw weight | 420 | 78.8 | 9.1 | 0.0 |
| Yogurt (優格) | 300 g | 274 | 13.2 | 5.2 | 42.6 |
| Oats (燕麥) | 35 g | 136 | 5.9 | 2.4 | 23.2 |
| Vegetables (蔬菜) | 400 g | 120 | 5.2 | 0.8 | 22.0 |
| Eggs (雞蛋) | 2 eggs | 144 | 12.6 | 9.6 | 0.7 |
| Protein powder (蛋白粉) | 50 g | 201 | 39.5 | 2.5 | 4.9 |
| Chia seeds (奇亞籽) | 10 g | 49 | 1.7 | 3.1 | 4.2 |
| Energy bar (能量棒) | 1 bar (31.3 g) | 122 | 2.2 | 3.6 | 18.7 |
| Creatine (肌酸) | 5 g | 0 | 0 | 0 | 0 |
| **Daily total** | | **1,846** | **167.3** | **44.7** | **186.3** |

**Water:** about **3.5–4 L/day** in total, including the water in coffee and protein shakes (Darren, 2026-10-09).
That is adequate for ~91 kg with daily training and creatine. It is a steady habit, so it shouldn't move the scale
trend. Coffee: **black, 2 × 300 ml cups/day** (≈5–10 kcal total, so it is not counted in intake). That is
≈250–400 mg caffeine, within the ~400 mg/day guideline. Sleep is his weakest metric, so the advice given was to have
the last cup before ~1 pm.

**Fish oil:** 2 capsules/day (2 g fish oil each → 4 g fat, ~36 kcal; 600 mg omega-3 per capsule, i.e. 360 EPA + 240 DHA).
It was not in the CSV, so the real baseline was **≈1,893 kcal / 48.8 g fat (0.54 g/kg)**, not 1,846 / 44.7.

**Meal timing (Darren, 2026-10-09):** energy bar → *workout* → protein shake + 2 eggs + 200 g potato +
200 g veg → lunch: 350 g chicken + 200 g potato + 200 g veg → dinner: yogurt (actually **310 g**) + 35 g oats.
Chicken, potato and oats are weighed **raw**. Olive oil, chia and creatine were not in this list; they are
assumed unchanged (oil for cooking, chia with the yogurt). Confirm at the next review.

**Labels checked from photos 2026-10-09:**
- Yogurt is Coles Simply strawberry, sweetened, per 100 g: 92 kcal, 4.4 P, 1.7 F, 14.2 C, 12 g sugar.
- Whey (chocolate) per 100 g: 401 kcal, 79 P, 5 F, 10 C. A label scoop is 30.4 g; he uses 50 g ≈ 1.6 scoops.
- The energy bar is Nestlé chewy choc chip, 31.3 g: 122 kcal, 2.2 P, 3.6 F, 18.7 C.

These match the table above.

**Changes agreed at the 2026-W41 review (2026-10-09):**
- **Fat up to the 0.6 g/kg floor:** olive oil 8 g → **14 g**, permanently. Fish oil supplies the other 4 g. The first
  proposal (18 g) was made before the fish oil was known.
- **2,000 kcal experiment, 3 weeks: 2026-10-12 → 2026-11-01 (W42–W44)**, with rice replacing potato.
  - Darren wanted 2,000 kcal: the 1,850 number "looks low" (not hunger or energy). He also has a long-term wish of a 2,500 TDEE.
  - Daily: **SunRice 100 g raw (50 g per meal)** + olive oil 14 g + fish oil 4 g → ≈1,995 kcal / 166 P / 54.5 F / 197 C.
    SunRice white medium grain, raw per 100 g: 356 kcal, 6.8 P, 0.1 F, 79.1 C (label confirmed 2026-10-09).
  - Expected at TDEE ≈2,330: ≈ −0.33 %/wk, putting him at ~87 kg on 1/16 (vs ~85 at 1,850). He accepted the slower pace.
  - **Purpose: measure his real TDEE** from the daily weigh-ins at a known, constant intake.
  - **Rule:** if the 14-day trend is slower than −0.25 %/wk for 2 consecutive weekly reviews, go back to ~1,900
    (≈75 g rice). Ignore the first rice week's scale noise, so judge from W43 on.
  - **The 2027-01-22 checkpoint (83–85 kg) is NOT changed yet.** Re-plan at the W44 review (~2026-11-01) from the measured
    rate and TDEE, and update `config/plan.json` too if it moves.
- Fallback numbers: 1,852 kcal = 60 g rice. Potato version of 2,000 kcal ≈ 470 g potato + 14 g oil.
- **Food gaps from the rice swap (estimated 2026-10-09):**
  - fiber ~29 → ~20 g/day (AU guideline 30 g);
  - potassium ~5,100 → ~3,600 mg (AU adequate intake 3,800).
  Advice given: fix with food (more vegetables, leafy greens), not supplements. If he adds veg, update the intake
  schedule in `config/plan.json`.
- Calorie-equivalent swap: 400 g potato ≈ 86 g raw rice. Rice is far less filling per kcal. If he is hungry, add vegetables
  (~30 kcal/100 g).

**Eating out:** a team lunch at work or a meal with friends, about **once every 1–2 weeks**. Those days are
the exception and should be logged as such, not assumed.

**Why it matters:** the intake is constant and known, so the weight trend can be turned
directly into a maintenance-calorie (TDEE) estimate. Weekly weight change × ~7,700 kcal/kg ÷ 7 = the daily
deficit, and maintenance ≈ 1,846 + that deficit. The early weeks of the cut (from 2026-07-15) include
water and glycogen loss, so they overstate the deficit.

**How to apply:**
- Protein is about 1.85 g/kg bodyweight (at 90.6 kg), which is adequate for keeping muscle on a cut.
- Fat is about 0.5 g/kg, the low end of what's sensible. Raise it before cutting calories further.
- Creatine at 5 g/day adds water weight. Keep it constant so the scale trend stays comparable.
- When recommending changes, adjust **quantities of these same foods** rather than proposing a new diet. He
  prefers a fixed routine.

Related: [[cutting-goal-2026]]
