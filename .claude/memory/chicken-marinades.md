---
name: chicken-marinades
description: The three chicken marinades — Mustard 蜜芥, Tikka 咖哩優格, Char Siu 叉燒 — each for 1 kg raw breast, all three made together and rotated daily; recipes, Coles labels, per-350 g numbers (avg +162 kcal, +10 g fat, +940 mg Na/day)
metadata:
  type: user
---

Darren's daily 350 g chicken breast ([[daily-diet-baseline]]) is always marinated. Given 2026-10-16.
**He makes all three at once, one per 1 kg raw breast (3 kg total), and eats a different flavour each day.**
So a cycle lasts ~8.5 days and the **average of the three is what goes into the daily baseline**.

**Names (short, so he can just say "today was 叉燒"):** **Mustard 蜜芥**, **Tikka 咖哩優格**, **Char Siu 叉燒**.

## Recipes (per 1 kg raw chicken breast)

**1. Mustard 蜜芥:** Kewpie mayonnaise 60 g, Capilano honey 60 g, Coles wholegrain mustard 60 g,
Holbrooks Worcestershire 15 g, water 60 g.

**2. Tikka 咖哩優格:** Shan Chicken Tikka mix 10 g, Shan Chicken Biryani mix 10 g, Tamar Valley Greek-style
yoghurt (plain) 200 g, water 50 g.

**3. Char Siu 叉燒:** Lee Kum Kee char siu sauce 40 g, LKK premium soy 10 g, Holbrooks Worcestershire 15 g,
Capilano honey 15 g, Laoganma chilli oil with diced chicken 25 g, MasterFoods onion powder 5 g,
MasterFoods garlic powder 5 g, Ajinomoto MSG 5 g, water 100 g.

## Numbers

| | Batch (1 kg) kcal | **Per 350 g: kcal** | P | F | Sat F | C | Sugar | **Na mg** |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Mustard 蜜芥 | 714 | **250** | 2.2 | 17.2 | 2.6 | 21.1 | 18.5 | **524** |
| Tikka 咖哩優格 | 303 | **106** | 4.3 | 7.3 | 4.3 | 5.9 | 4.3 | **1,058** |
| Char Siu 叉燒 | 370 | **130** | 1.5 | 5.8 | 0.9 | 17.1 | 13.6 | **1,244** |
| **Daily average** | | **162** | 2.7 | 10.1 | 2.6 | 14.7 | 12.1 | **942** |

- Assumes **all of the marinade is eaten** with the chicken. Some left in the container or pan would lower it a little.
- Biggest contributors: Mustard kcal is the mayo (433 kcal/batch) and honey (203). Tikka sodium is the Shan
  Tikka mix (salt is its first ingredient, 20,600 mg Na/100 g → 2,060 mg/batch). Char Siu sodium comes from
  char siu sauce (1,696/batch), soy (688), MSG (615) and Laoganma (442).
- **Linoleic acid (LA):** Kewpie mayo and Laoganma are soybean oil (~53 % LA). That gives **~9 g LA per
  Mustard portion, ~3 g per Char Siu portion and ~0 for Tikka, ~4 g/day on average.** See [[skin-dryness-itch]].

## Label sources (per 100 g, read from coles.com.au 2026-10-16)

| Product | kcal | P | F | C | Sugar | Na mg | Confidence |
|---|---:|---:|---:|---:|---:|---:|---|
| Kewpie mayo (soybean oil, egg yolk, MSG) | 722 | 1.7 | 80.5 | 0.7 | 0.6 | 710 | AU label |
| Capilano honey | 338 | 0.3 | 0 | 83.1 | 82.5 | 15 | AU label |
| Coles wholegrain mustard | 110 | 8.4 | 1.1 | 12.1 | 1.6 | 1,600 | AU label |
| Holbrooks Worcestershire (per 100 mL, taken as g) | 79 | <1 | <1 | 17.9 | 14.4 | 685 | AU label |
| Shan Chicken Tikka mix | 263 | 12.5 | 12.5 | 25 | 0 | 20,600 | AU label |
| Shan Chicken Biryani mix | 251 | 10 | 10 | 30 | 10 | 8,100 | AU label |
| Tamar Valley Greek-style (plain) | 126 | 5.0 | 9.3 | 5.7 | 5.7 | 76 | AU label |
| LKK char siu sauce | 249 | 1.2 | <1 | 58.8 | 55.9 | 4,240 | AU label |
| LKK premium soy (per 100 mL, taken as g) | 95 | 7.7 | <1 | 13.8 | 10.2 | 6,880 | AU label |
| Laoganma diced chicken (soybean oil 48 %) | 660 | 6.5 | 64.8 | 4.7 | 1.7 | 1,770 | Coles snippet; Woolworths label is close |
| MasterFoods onion powder | ~341 | ~10 | ~1 | ~79 | | ~73 | generic (no AU label online) |
| MasterFoods garlic powder | ~331 | ~17 | ~1 | ~73 | | ~60 | generic (no AU label online) |
| Ajinomoto MSG | ~0 | | | | | 12,300 | sodium only; kcal negligible at 5 g |

The <1 g values were counted as 0.5 g. The generic rows add under 40 kcal per batch, so their uncertainty doesn't matter.

**Why it matters:** the marinades were **missing from the baseline** until 2026-10-16. They add ~162 kcal and
~940 mg sodium a day, so earlier intake and TDEE figures were ~160 kcal too low, and "no added salt, ~1,000 mg Na" was wrong.

**How to apply:**
- Count **+162 kcal / +10 g fat / +940 mg Na per day** on top of the plain food. `config/plan.json` adds it to every intake entry back to 2026-07-15 (1,974 → 2,136, 2,030 → 2,192,
  2,115 → 2,277). This assumes he has used them since the cut began, which he hasn't confirmed.
- If he changes a recipe or drops a flavour, recompute that row and the average (the script is simple: grams × label ÷ 100).
- On a day-level question (e.g. a salty day or a scale jump), the flavour matters: Mustard is the kcal-heavy one,
  Char Siu and Tikka are the salty ones.
- To cut kcal later without changing the routine, Mustard's mayo + honey is the lever (60 g mayo ≈ 145 kcal per 350 g).
