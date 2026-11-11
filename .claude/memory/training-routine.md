---
name: training-routine
description: Darren's training rules and current load decisions — 5-day split from 2026-10-10 (Tue legs, Wed back, Thu shoulders, Sat back, Sun chest; Wed walk optional in the cut; bulk adds Fri legs, drops Wed+Fri walks) + daily treadmill, no squat/deadlift, every load from W41 is real; the numbers themselves (baselines, sets/wk, cardio min) come from prepare-week
metadata:
  type: project
---

⭐ **Numbers live in the review digest, not here (2026-10-26).** `prepare-week` recomputes every review:
`strength_since_baseline` (best set per exercise per ISO week from W41), `training_pattern_4w` (which workout on which
weekday, sessions, logged sets and cardio minutes per week) and the strength rows of `health_guard`. This file keeps
only the rules behind those numbers and the decisions made about them. Don't paste lift logs back in.

- **Split:** early-morning sessions, Back ×2, Chest, Shoulders, Legs, plus short "Functional Workout" sessions, and
  treadmill ~30 min most days.
- ⭐ **Weekday lifting ≤ 50 min (Darren, 2026-11-05):** he goes to work after training, so Tue/Wed/Thu (and any
  weekday) sessions must fit in 50 min; only weekend sessions may run over an hour. Any exercise added to a weekday
  session must be paid for by removing or supersetting something. He also wants sessions efficient, not long.
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

⭐ **Schedule change from W46 (Darren, 2026-11-11): Mon / Wed / Fri mornings = treadmill walk ONLY.** Rushing to
lift before the office was too hard. This drops **Wednesday back** (pulldown 4 + indoor row 3 + row 3 + DB curl 3 +
Y-raise 2) and the Mon/Fri 10-min "Functional" sessions (wall slide, push-up plus, Y-raise). Back is now Saturday only
(~10 sets/wk, see the 10-26 halving note in [[evidence-hypertrophy-training]]). **Thursday = shoulders + arms**
(full delt + biceps + triceps), still ≤ 50 min. ⭐ **Side delt is his priority (Darren, 11-11).** Dropping the DB
shoulder press was proposed (front delt grows from bench: Lanza 2024 JBMT, PMID 39593465, RCT n=24, MRI), but
⭐ **he chose to keep it, done FIRST** (11-11). Order costs the later lift strength, not growth (Nunes 2021, PMID
32077380). **Agreed Thursday (from 11-12):** warm-up **incline Y raise 2 × 15 @ 8 kg** (Darren 11-11: replaces wall
slide + push-up plus on Thursday; Y raise = lower trap, Kolber 2017; push-up plus has EMG-only evidence) → **DB shoulder press 35 kg
3 × 8–12** (hold, shoulder rule) → DB lateral raise 14 kg 3 × 12–16 near failure (≤ 90°) → superset DB curl 14 kg
3 × 10–15 + cable kickback 15 kg 3 × 15 → rope face pull 2 × 15 → **weighted crunch 2 × 20 @ 20 kg last** (Darren,
11-11: Thursday cable lateral raise removed, crunch kept at the end). Side delt/wk: Thu 3 + Sun 3 + **Sat 2
single-arm cable lateral (new, weekend; load so failure lands in 12–16, Larsen 2025 Front Physiol 16:1611468: cable
= DB)** = 8. Proposed, his call: a 4th DB lateral set on Thursday (→ 9/wk; Pelland: most gain ≤ ~12). ⚠️ Thursday lateral raise follows the press, so compare
its reps only with other Thursdays, never with Sunday's. Rest: press 2 min, lateral raise 90 s, curl↔kickback
superset 0 s within / 90 s between rounds, face pull + crunch 60 s, Y raise 30 s (Singer 2024 PMID 39205815: no
hypertrophy gain beyond 90 s); estimated ~35 min, not yet measured. "Funny" right shoulder → neutral-grip DB or landmine press. The bulk plan below
(Wed back, Fri legs) needs re-deciding when the bulk starts.

**Schedule trial from 2026-10-10 (agreed 2026-10-09; Mon/Wed/Fri superseded 2026-11-11 above):**

| Mon | Tue | Wed | Thu | Fri | Sat | Sun |
|---|---|---|---|---|---|---|
| rest | **Legs** | Back | **Shoulders** | rest | **Back** | **Chest** |

- **Why:** a recurring Friday slump (6 weeks before the trial: Friday HRV 40.7 vs a 42.9 mean, all-day stress 38.9 vs
  34.3), read as accumulated fatigue from the Tue–Thu streak with legs last plus short Wednesday sleep. Not overtraining.
- Legs moved to the first day of the streak. Darren's own change: chest and back swap on the weekend, so the shoulder
  gets 72 h between shoulder day (Thu) and chest (Sun).
- Extras: Friday energy bar at 3–4 pm, Friday treadmill easy or skipped, earlier bedtime on Wednesday.
- Judge on Friday HRV and stress against those means, Friday `/feel` entries, and shoulder or chest pressing loads.
- **Wednesday (Darren, 2026-10-26): back day stays for the cut; the walk is optional.** It is an office day and
  rushed, so when time is short he walks less or skips the walk, never the back session. A skipped Wednesday walk is
  his rule, not a lapse: don't flag it. (He briefly considered dropping Wednesday back the same day; the evidence said
  back would still grow, slower, but he chose to keep it.)
- **Bulk plan (agreed in principle 10-26, set when the bulk starts):** Wednesday = back, no walk. Friday = a second
  leg day (40–45 min) in place of the walk, 1-for-1. Lifting Tue–Sun, Mon rest; walking Mon, Tue, Thu, Sat, Sun
  (~150–190 min/wk, keeps the cardio floor in [[evidence-exercise-and-aging]]). Make Friday legs a different emphasis
  (hamstrings/glutes: leg curl, hip thrust, RDL-free) from Tuesday (leg press, quads). Watch Friday HRV/stress, since
  Friday was the slump day; the surplus should help. Not Monday: Mon + Tue legs back-to-back.

**Shoulder split change (Darren's proposal 2026-11-05, tuned by evidence; start Sun 11-08 / Thu 11-12):**
- Trigger: Thu 11-05 the right shoulder "felt funny" on the 3rd delt exercise (cable lateral raise) after DB lateral
  raise 14→**16 kg** and OHP 35 × 12/12/12, the heaviest shoulder session so far. Side delts were 5 sets/wk, all Thursday.
- **Thursday:** cable lateral raise (2 sets) → **rope face pull, 2–3 × 15, light, finish thumbs back (external
  rotation)**: rear delt + external rotators (Kolber 2014/2017: lifters with impingement have weak ERs; ER training
  inversely associated). 3 sets only as a superset with cable kickback, to stay ≤ 50 min (11-05 was 50.3 min).
  DB lateral raise back to **14 kg**, raise to shoulder height (≤ 90°, Kolber 2014).
- **Sunday chest:** + **DB lateral raise 3 × 15 at 12–14 kg**, to shoulder height (weekend, no time cap). Placement
  (Darren's order, 11-05): **chest fly → DB lateral raise (3 straight sets) → cable kickback + weighted crunch as a
  superset**. Not first: heavy incline/flat bench must not start on a fatigued cuff, and multi-joint first favours bench
  strength (Nunes 2021, PMID 32077380); hypertrophy is order-independent. Sunday drifted 63 → 82.5 min (10-18 → 11-01).
- ⭐ **Sunday triceps: lying DB triceps extension → cable kickback (Darren, from W45; first Sunday 11-08).** Kickback is
  now Thu + Sun, 3 sets each; lying extension is no longer done. Trade-off: kickback trains the long head with the
  shoulder extended (short length), losing the stretched position (Maeo 2023, PMID 35819335, `tiny n`: overhead >
  neutral); the overhead variant would put the right shoulder in full flexion, so kickback is a reasonable choice for him.
- Result: side delt 5 → 6 sets/wk over 2 days (Schoenfeld 2019: frequency neutral when volume equal), rear delt
  3 → 5–6 (Thu + Sat), external rotation 0 → 2–3. Recurring "funny" feeling, pain, swelling or night pain → physio.
- ⚠️ Tuesday legs runs 53 min (10-27, 11-03), over the weekday cap: trim a leg-press ramp set or superset
  adduction/abduction. Flagged 11-05, his call.

**Current load decisions (as of the W44 full review, 2026-11-01).** Rule of thumb: add load once every working set
reaches 12 clean reps.
- DB shoulder press (OVERHEAD_DUMBBELL_PRESS): **hold 35 kg for 8–12 reps, no further increase** (right shoulder);
  swap to neutral-grip DB or landmine press on any pain.
- Lat pulldown: stepped up to 60 kg on 11-04 (W45 midweek review; e1RM 80). Hold 60 until all three sets reach 12.
- Indoor row: 40 kg is the baseline.
- Flat barbell bench: stay at 50 kg until all three sets reach 12, then 55. Incline bench stays at 50.
- Chest fly: hold 40 kg; back to 33 on any front-shoulder discomfort.
- Lying DB triceps extension (**dropped from W45**, replaced by Sunday cable kickback; history only): 15 kg back-off sets recovering (10-18 10/7 → 10-25 9/9 → 11-01 12/10); hold 15 kg until all sets reach 12. The digest's "−25 % vs best 30" is an e1RM artefact of the 20 kg × 15 first set, not a loss. Weighted crunch "−28.7 %" likewise (same 20 kg, 20–40-rep sets): ignore e1RM on high-rep accessories.
  Accessory only.
- Cable kickback: 15 kg from 10-22; 15 × 15 on all three sets 10-29 → 17.5 kg next shoulder day.
- DB shoulder press 10-29: 35 × 12/12/11 (10-22: 12/11/10). Still hold 35 kg (shoulder rule above).
- Seated row (ROW): 30 kg × 12/12/12 (10-21, 10-28) and × 15/15/15 (10-24), so no drop; 3 × 15 reached again 10-31 → next load step up at the next back day.
  ⚠️ The digest's W43 "best 45" came from the 15-rep sets; a 12-rep session at the same load reads as −6.7 %. Before calling
  any e1RM "drop" a loss, check the sets: same load with fewer reps on a fixed rep target is not a decrease (mistake made 10-29).

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
