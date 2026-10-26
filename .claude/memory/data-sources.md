---
name: data-sources
description: What data exists for Darren — Garmin + daily weigh-ins + his fixed diet + Telegram (eating out, notes, /feel, voice, meal/blood photos). NO InBody since 2026-10-10 (gym removed the machine); one historical scan only
metadata:
  type: project
---

**No more InBody (Darren, 2026-10-10):** his gym cancelled the InBody machine, so there will be no further scans. The bot's
`/inbody` command was removed. **Never ask him for an InBody and never plan around one.**

What exists from now on:
- **Garmin:** daily weigh-ins (scale), sleep, HRV, RHR, stress, Body Battery, steps, activities and strength sets.
- **Diet:** the fixed daily diet ([[daily-diet-baseline]]), so intake is known.
- **Telegram bot:** `/eat` (eating out, text or meal photo), `/note`, `/feel` (when something is wrong), voice notes, `/weight`, `/blood`.
- **Bloodwork** twice a year.

**History:** one scan, 2026-09-27: 91.4 kg, 25.5 % BF → lean mass ≈ 68 kg (BIA error ±~3 points, [[evidence-asian-hepb]]).
It stays in `data/manual/inbody.jsonl` as the only body-composition anchor.

**How to apply:**
- **Muscle signal = strength:** e1RM or reps at the same load against his W41-onward numbers; no load drop is
  deliberate any more, so a decrease is real ([[training-routine]]), plus a loss rate within target and protein ≥1.6 g/kg.
- **Body fat is estimated, not measured:** BF ≈ (weight − 68) ÷ weight, assuming lean mass held. 15–18 % ≈ 80–83 kg. Say it is
  a rough estimate; strength holding is what makes the 68 kg assumption believable.
- If he ever gets a DEXA or another BIA, record it as a one-off; don't recreate a weekly ask.

**Body-fat scale / DEXA: researched and declined (2026-10-23).** After the comparison in
`research/measurement/Home body fat scales comparison.md` (pick would have been Garmin Index S2; DEXA in Perth ≈ A$120–185),
he chose to keep the current plan: "not training for bodybuilding but to be healthy", and no method is proven
enough to justify it. **Don't re-suggest a scale or DEXA**; point to the report only if he raises it again.
