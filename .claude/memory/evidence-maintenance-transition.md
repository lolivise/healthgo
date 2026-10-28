---
name: evidence-maintenance-transition
description: Research base (researched 2026-10-10) for ending a cut — reverse diet vs straight to maintenance, expected scale jump, binge/rigid-restraint risk, holiday weight gain, how to estimate TDEE from the trend
metadata:
  type: reference
  sector: fat-loss
---

**[V]** = checked online, **[M]** = from model memory, not re-checked.

| Topic | Evidence | Strength |
|---|---|---|
| Reverse diet vs straight to maintenance | Rodriguez Da Silva / Campbell 2025 RCT (n=49 trained adults, 15 wk after a 5 % loss) [V]: gradual reverse diet regained 3.7 %, immediate maintenance 2.7 %, ad lib 1.3 % (ns); reverse arm had **more dropouts** (45 vs 30 %). Gradual ramps have no proven advantage | moderate (one RCT) |
| Adaptive thermogenesis | After a moderate cut it is small (a few hundred kcal at most), mostly explained by lost mass; NEAT and leptin recover in days–weeks once intake rises (Trexler 2014 review) [M] | weak–moderate |
| Post-diet overeating | Minnesota experiment (Keys 1950) [M]: fat "overshoot" and binges after ~25 % loss in starvation. Darren's mild cut is far from that. His risk is **behavioural** (fatigue + rigid rules), not physiological | moderate |
| Rigid vs flexible restraint | Westenhoefer 1999 [M]: all-or-nothing rules predict binges and disinhibition; flexible rules predict lower weight and fewer binges | moderate |
| Scale jump on raising kcal | Glycogen ~400–600 g binds ~3 g water/g; more carbs + sodium + gut content → **+0.5–2 kg within 1–2 weeks, not fat** | moderate |
| Holiday gain | Helander 2016 NEJM (n=2,924) [M via summary]: holidays +0.2–0.6 %, about half retained. Obesity Reviews 2024 [V]: daily self-weighing + advice helped a little. No Taiwan Lunar New Year study found; a 2011 Taiwan DoH estimate said ~1.7 kg | weak |
| Maintenance phases | Coaching heuristic, small trials only: 1–2 wk maintenance per 6–12 wk of dieting. National Weight Control Registry [M]: maintainers keep activity, consistent eating, self-weighing | weak |
| TDEE from trend | **Hall 2008** IJO, PMID 17848938 [V 10-28, full text] (modified-Forbes model + published loss data; earlier note wrongly said Hall 2011): the 3,500 kcal/lb = 7,700 kcal/kg (32.2 MJ/kg) rule fits only with **>~25–30 kg initial body fat**; below that the deficit per kg lost is **lower**, because a bigger share of the loss is lean tissue (~7.6 MJ/kg vs fat 39.5). Worked example in the paper: 20 kg fat → **28 MJ/kg ≈ 6,700 kcal/kg**. Glycogen effects sit in the first week. Model parameterised on women (n=166), so a man who lifts probably loses less lean → somewhat higher, ~6,700–7,000 for him (≈20 kg fat). Hall 2011 Lancet, PMID 21872751 [V], is the dynamic model: weight response half-time ~1 yr, the deficit shrinks as weight falls. TDEE ≈ mean intake + (kg lost × ~6,700–7,000) ÷ days, using ≥2–3 weeks of 7-day-average weights at a constant intake, **excluding the first weeks of a cut**. `prepare-week` (`weekly.py` `KCAL_PER_KG`) switched 7,700 → **6,850** on 2026-10-28 (Darren); TDEE estimates before that date were ~60–140 kcal/day too high | moderate (model + data) |

**How to apply:**
- To end a cut, step **straight to measured maintenance** (or two steps one week apart). Don't use a +50 kcal/week ramp.
- Pre-warn him about the +0.5–2 kg jump and judge only the trend after week 2. If weight still rises >0.25 kg/wk
  after week 3, trim 100–150 kcal.
- Prefer flexible rules ("protein each meal, daily walk") over a list of forbidden foods, especially for the trip.
- The plan built on this lives in [[cutting-goal-2026]] and [[trip-taiwan-2027]]. Related: [[evidence-cutting]].
