---
name: training-routine
description: Darren's training rules and current load decisions — 4-day split from W44 (Tue legs, Thu shoulders, Sat back, Sun chest; Wed back dropped 2026-10-26, walk only; 5-day trial from 2026-10-10) + daily treadmill, no squat/deadlift, every load from W41 is real; the numbers themselves (baselines, sets/wk, cardio min) come from prepare-week
metadata:
  type: project
---

⭐ **Numbers live in the review digest, not here (2026-10-26).** `prepare-week` recomputes every review:
`strength_since_baseline` (best set per exercise per ISO week from W41), `training_pattern_4w` (which workout on which
weekday, sessions, logged sets and cardio minutes per week) and the strength rows of `health_guard`. This file keeps
only the rules behind those numbers and the decisions made about them. Don't paste lift logs back in.

- **Split:** early-morning sessions, Back ×2, Chest, Shoulders, Legs, plus short "Functional Workout" sessions, and
  treadmill ~30 min most days.
- **No squat or deadlift**, ever ([[health-conditions]]). Legs = leg press and machines. Garmin labels are inconsistent:
  bench shows as BARBELL_BENCH_PRESS, BENCH_PRESS or UNKNOWN.
- **Technique phase (late Sep → early Oct 2026) is OVER.** He lowered loads for posture and slower tempo, and the
  reduction was finished by **W41 (week of 2026-10-05)**. ⛔ **Darren, 2026-10-18:** "I am not deliberately reducing the
  weight now… if there is a decrease, it is a real decrease." **From W41 on, every load is real.** A drop against
  W41-or-later numbers is a real strength decrease: report it as one, and never write 刻意放輕 / "deliberately
  lighter" / "technique phase" / "非流失" about it in a review. Never compare against pre-W41 loads.
- **Excluded from every comparison** (kept in `config/plan.json` → `strength.exclude`, which prepare-week applies):
  - Sat 2026-10-10, a different gym short of equipment (Darren, 2026-10-18).
  - Cable kickback before 2026-10-22: the 22.5 kg sets had bad form; he reset to 15 kg to do it properly. This one reset is
    a form correction, not strength loss; the "every drop is real" rule holds for everything else, and for kickback after it.
  - **If he trains at another gym again, ask him to flag it (a `/note`)** and add the date to `strength.exclude`.
- **Garmin set corrections:** chest fly on 2026-10-25 was logged as 33 kg for the first two sets; Darren corrected it to 40 kg
  locally and in Garmin Connect, so re-pulls keep 40 kg.

**Schedule trial from 2026-10-10 (agreed 2026-10-09):**

| Mon | Tue | Wed | Thu | Fri | Sat | Sun |
|---|---|---|---|---|---|---|
| rest | **Legs** | Back | **Shoulders** | rest | **Back** | **Chest** |

- **Why:** a recurring Friday slump (6 weeks before the trial: Friday HRV 40.7 vs a 42.9 mean, all-day stress 38.9 vs
  34.3), read as accumulated fatigue from the Tue–Thu streak with legs last plus short Wednesday sleep. Not overtraining.
- Legs moved to the first day of the streak. Darren's own change: chest and back swap on the weekend, so the shoulder
  gets 72 h between shoulder day (Thu) and chest (Sun).
- Extras: Friday energy bar at 3–4 pm, Friday treadmill easy or skipped, earlier bedtime on Wednesday.
- Judge on Friday HRV and stress against those means, Friday `/feel` entries, and shoulder or chest pressing loads.
- **Change from W44 (2026-10-26): Wednesday back day dropped, Wednesday = walk only.** Darren's office day, too
  rushed, the one session he dreads; the reason he trains is to eat out without worry, so a routine without pressure
  comes first. Back goes from ~20 to ~10 direct sets/wk (Sat: pull-up/pulldown 4 + row 6), nothing moved elsewhere,
  on his request. Evidence check in [[evidence-hypertrophy-training]]: still grows, somewhat slower; well above the
  maintenance dose. Option if back lags in the bulk: 3–4 row sets on another lifting day. Lifting = Tue, Thu, Sat, Sun.

**Current load decisions (as of the W43 review, 2026-10-25).** Rule of thumb: add load once every working set
reaches 12 clean reps.
- DB shoulder press (OVERHEAD_DUMBBELL_PRESS): **hold 35 kg for 8–12 reps, no further increase** (right shoulder);
  swap to neutral-grip DB or landmine press on any pain.
- Lat pulldown: 57.5 kg next (55 × 12 on all three sets 10-24).
- Indoor row: 40 kg is the baseline.
- Flat barbell bench: stay at 50 kg until all three sets reach 12, then 55. Incline bench stays at 50.
- Chest fly: hold 40 kg; back to 33 on any front-shoulder discomfort.
- Lying DB triceps extension: back-off sets at 15 kg slipped (15/15 → 10/7 → 9/9); hold 15 kg, target 12+, re-check W44.
  Accessory only.
- Cable kickback: 15 kg from 10-22, add load at 12 clean reps.

**Training history (told 2026-10-12):** lifting 3–4 years but on/off: blocks of 3–4 months at 6 days/wk, then 1–2
months off or only 1–2 days/wk. The 2026-07 cut is his first long consistent block. Treat him as **late novice /
early intermediate** (effective training age ~1.5–2 yr; bench e1RM ~0.75× bodyweight). He still has fast-gain
potential, and his lifts rising during the cut fit that. **Consistency is his biggest lever.**

**Why he used to stop (told 2026-10-12):** overtraining, **36 sets/day × 6 days (~216/wk)**, no clear goal and no
plan, chronic tiredness, and **all-or-nothing breaks**: once he rests, the break runs 1–2 months. Current volume is
about half that (see `training_pattern_4w`); the guard is against creeping back up.
**He keeps the current split as is (2026-10-12: "the training plan I have is doable")**: don't propose a rewrite;
add shoulder-width work (side delts, shrugs) only as small tweaks inside a review. Deload every 6th week and a "never
zero" 2-session/wk floor were proposed and **declined for now** (2026-10-12: "no, not now"). Don't re-push them; raise
again only if the data shows fatigue building or he starts skipping weeks.

**How to apply:** there is no InBody any more ([[data-sources]]), so the muscle signal is strength from
`strength_since_baseline`; any decrease is real and counts. Training advice stays as targeted tweaks to this split
([[review-preferences]]); watch shoulder loads ([[health-conditions]]). Update "Current load decisions" at each review.
