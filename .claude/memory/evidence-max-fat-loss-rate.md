---
name: evidence-max-fat-loss-rate
description: "Daily fat-burn ceiling" = Alpert 2005 model, 290±25 kJ ≈ 69 kcal per kg fat per day; theoretical (Minnesota starvation data), never tested; his rate caps already sit at about half of it, so no plan or check change (2026-10-25)
metadata:
  type: reference
  sector: fat-loss
---

Darren asked 2026-10-25 (from a YouTube video) whether there is a scientific daily ceiling on fat loss.

**The source:** Alpert SS, *J Theor Biol* 2005 (PMID 15615615): the fat store can release at most
**290 ± 25 kJ ≈ 69 kcal per kg of fat mass per day** (≈31 kcal/lb). A deficit beyond that is covered
by fat-free mass. Popular "max fat loss calculators" (fatcalc etc.) use it.

**Strength of evidence: weak-moderate.** It is a mathematical model fitted to one old dataset (Minnesota
Starvation Experiment, lean men, semistarvation), never tested prospectively, no head-to-head with Hall's
model. The all-or-nothing "beyond the line it's all muscle" is a simplification: Forbes/Hall (2007) show the
lean share of loss rises gradually as fat mass falls.
Likely higher with adequate protein and lifting.

**Applied to him (lean ≈ 68 kg assumed, all-fat 7,700 kcal/kg):**
- Cap deficit at 0.7 %/wk ≈ 7.7 × W kcal/day; at 0.5 %/wk ≈ 5.5 × W; 1 % stop ≈ 11 × W.
- Alpert ceiling ≈ 69 × (W − 68). The caps stay below it for every W above ~76 kg (0.7 %) / ~74 kg (0.5 %);
  the 1 % stop line stays below it above ~81 kg.
- 88.7 kg (10-24): ceiling ≈ 1,430/day; his cap ≈ 680; actual plan (2,520 vs TDEE 2,800–3,000) ≈ 300–500.
- At goal ~82 kg: ceiling ≈ 970; 0.5 % cap ≈ 450.

**Decision:** no change to plan, `config/plan.json` or the health-guard checks — the existing rate caps
([[safety-limits]]) are always the binding limit across his whole range. Do not add an Alpert metric.
It only matters if he ever goes below ~76 kg or wants a crash cut. Related: [[evidence-rapid-loss-harms]],
[[evidence-muscle-turnover]], [[data-sources]].
