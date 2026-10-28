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
| Adaptive thermogenesis | **Corrected 10-28.** Trexler 2014 JISSN, PMID 24571926 [V, full text] (narrative review) says the opposite of the old row: the EE drop "often exceeds" what mass loss predicts, can persist >1 y, and NEAT "may remain suppressed for some time" after intake returns. The "small for him" conclusion rests instead on [[evidence-long-cut-duration]] (moderate CR: ~80–135 kcal/d, recovers by ~12 wk: Redman 2018, Heilbronn 2006, Buechel 2026). Practical: the measured maintenance may run a little low at first, which the week-3 trim rule already covers | moderate |
| Post-diet overeating | Keys' Minnesota experiment, re-analysed by Dulloo 1997 AJCN, PMID 9062520 [V] (n=12 semi-starved lean men, refeeding): hyperphagia continued until fat and FFM recovered (r −0.6 / −0.5); fat overshoot is modelled, not a measured binge. Far deeper deficit than his. His risk is **behavioural** (fatigue + rigid rules), not physiological | weak fit |
| Rigid vs flexible restraint | Westenhoefer 1999 Int J Eat Disord, PMID 10349584 [V] (questionnaire, 3 samples: n=54,517 programme, 1,838 population): rigid control ↔ more disinhibition, higher BMI, more/worse binges; flexible ↔ lower BMI, fewer binges, more 1-yr success; `observational only` | moderate |
| Scale jump on raising kcal | Mechanism verified: ≥3 g water stored per g muscle glycogen (Fernández-Elías 2015 Eur J Appl Physiol, PMID 25911631, n=9 cyclists, biopsies); glycogen stored with 3–4 parts water, carb refeeding → "exaggerated regain" (Kreitzman 1992 AJCN, PMID 1615908). **The ~400–600 g store and the +0.5–2 kg size are arithmetic, not measured** (no refeeding weigh-in data found 10-28) | mechanism moderate, size inference |
| Holiday gain | Helander 2016 NEJM letter (Wansink co-author): numbers **not verifiable** (no abstract, paywalled). Use instead: Yanovski 2000 NEJM, PMID 10727591 [V] (n=195 US adults, weighed): holidays +0.37 kg, net +0.48 kg by Feb–Mar, kept. Cooper & Tokar 2016 Physiol Behav, PMID 26768234 [V] (n=122, 1–3 wk vacations, scale): +0.32 kg, +0.41 kg still at 6 wk. Nothing longer than 3 wk, no fat/water split. **No Lunar New Year study on PubMed**; the "2011 Taiwan DoH ~1.7 kg" estimate is unverified. Obesity Reviews 2024 [V]: daily self-weighing + advice helped a little | weak |
| Maintenance phases | Coaching heuristic, small trials only: 1–2 wk maintenance per 6–12 wk of dieting. NWCR: Wing & Phelan 2005 AJCN, PMID 16002825 [V] (review, members lost ~33 kg, kept >5 y, self-report): ~1 h/day activity, breakfast, self-weighing, same eating pattern weekdays/weekends. Gorin 2004 Int J Obes, PMID 14647183 [V] (n=1,429, 12 mo): consistent eaters (incl. holidays/vacations) 1.58× (1.2–2.2) likelier to stay within 2.3 kg; `observational only`, formerly obese | weak |
| TDEE from trend | **Hall 2008** IJO, PMID 17848938 [V 10-28, full text] (modified-Forbes model + published loss data; earlier note wrongly said Hall 2011): the 3,500 kcal/lb = 7,700 kcal/kg (32.2 MJ/kg) rule fits only with **>~25–30 kg initial body fat**; below that the deficit per kg lost is **lower**, because a bigger share of the loss is lean tissue (~7.6 MJ/kg vs fat 39.5). Worked example in the paper: 20 kg fat → **28 MJ/kg ≈ 6,700 kcal/kg**. Glycogen effects sit in the first week. Model parameterised on women (n=166), so a man who lifts probably loses less lean → somewhat higher, ~6,700–7,000 for him (≈20 kg fat). Hall 2011 Lancet, PMID 21872751 [V], is the dynamic model: weight response half-time ~1 yr, the deficit shrinks as weight falls. TDEE ≈ mean intake + (kg lost × ~6,700–7,000) ÷ days, using ≥2–3 weeks of 7-day-average weights at a constant intake, **excluding the first weeks of a cut**. `prepare-week` (`weekly.py` `KCAL_PER_KG`) switched 7,700 → **6,850** on 2026-10-28 (Darren); TDEE estimates before that date were ~60–140 kcal/day too high | moderate (model + data) |

**How to apply:**
- To end a cut, step **straight to measured maintenance** (or two steps one week apart). Don't use a +50 kcal/week ramp.
- Pre-warn him about the +0.5–2 kg jump and judge only the trend after week 2. If weight still rises >0.25 kg/wk
  after week 3, trim 100–150 kcal.
- Prefer flexible rules ("protein each meal, daily walk") over a list of forbidden foods, especially for the trip.
- The plan built on this lives in [[cutting-goal-2026]] and [[trip-taiwan-2027]]. Related: [[evidence-cutting]].
