---
name: review
description: Darren's health review, whenever he wants one (there is no scheduled pull any more — this skill pulls Garmin data itself), or any time he asks how he's doing, whether to keep cutting, if his strength is dropping, or for diet/training advice. A Haiku agent pulls fresh Garmin + inbox data and gathers the numbers, Opus asks for eating-out days and decides the verdict (keep cutting / slow down / diet break / adjust intake), a Sonnet agent writes the 繁體中文 report, commits and sends it to Telegram. Trigger on /review, "review my progress", "how am I doing", "should I keep cutting", "give me advice".
---

# /review

You (the main thread, **Opus**) are Darren's coach. You decide; Sonnet agents do the legwork (the rule is in
`CLAUDE.md` → Model split). The output that matters is **one verdict he can act on this week**,
grounded in his own numbers and bounded by his safety limits.

Arguments: none → the plan below. `W41` / a date / "last 3 weeks" → that period. A free-text question →
answer it, but still run steps 1–3 first, because advice without fresh data is
what this skill exists to prevent.

**There is no scheduled job** (removed 2026-10-12 at Darren's request): nothing pulls Garmin data, sends
recovery alerts or prepares weekly numbers on its own. **Every `/review` starts with a fresh pull** (step 2),
so he can review any day. Start step 2 **at once, in parallel with step 1**: the pull takes a few minutes.

## What gets reviewed (Darren, 2026-10-25; replaces the 10-16 "never today" rule)

Run `uv run healthgo review-plan` first (instant). It decides, and you follow it rather than working out dates:

- **Sunday from 18:00 → full review** (`target.kind = full`) of the whole Mon–Sun week including Sunday, with the
  4 weeks before it as the baseline. The report is `reports/<YYYY-Www>.md`, the complete template.
- **Any other time → mid-week review** (`target.kind = midweek`) of the current week **through today**. Report
  `reports/<YYYY-Www>-midweek-<MM-DD>.md`, same template, headed 週中檢查. He trains in the morning, so today
  already has:
  - **always in:** this morning's weigh-in, today's workout and sets, last night's sleep, HRV and RHR, the wake-up
    Body Battery peak, and meals he reports.
  - **before 18:00, left out for today:** steps, stress and Body Battery low (the day isn't over). They count
    through yesterday.
  - **from 18:00, all in:** he's home and winding down, so today's steps and stress count too.
  `target.all_day_metrics_through` is that cut-off; `prepare-week` and the checks already apply it. State both
  dates in every brief: "everything through `target.through`, steps/stress/BB-low through `all_day_metrics_through`".
- **A missed Sunday comes first** (`catch_up` not null): the week before the target's week has no full review
  (e.g. on the trip he forgot Sunday evening). Run a **complete full review of that week first**, exactly as if it
  were that Sunday 18:00 (through its Sunday, nothing from this week), **send it to Telegram**, then do the target
  review. One pull and one eating-out question serve both.
- **Older weeks also missed** (`older_weeks_without_full_review`): no separate reports. The catch-up full report's
  近 5 週 table covers them; say in one line which weeks went unreviewed.
- **Mid-week verdicts:** a mid-week review gives a verdict and analysis like any review, but diet and target changes
  normally wait for the Sunday full review (one partial week is noisy). Change something mid-week only if a safety
  limit or a health-guard red is hit.

Every pull is stamped (`state.last_pull`). `pull` prints `previous_pull_at` and `this_pull_at`, and always re-pulls
from the day of the previous pull, so nothing logged after it (a later weigh-in, sets edited in the app) is missed.
Mention in the report which pull it rests on only if the Garmin sync failed.

## 1. Load context: Opus, quickly

- Read `.claude/memory/MEMORY.md` and **every file it points to except the `evidence-*` ones**. The goal, diet,
  health conditions, safety limits and preferences are all needed for the verdict.
- **Evidence files are on demand** (token budget, Darren 2026-10-26): their `MEMORY.md` lines carry the headline.
  Open one only when a decision or a question in this review turns on it (e.g. `evidence-metabolic-adaptation` when
  the trend stalls).
- Read `config/plan.json` and the **verdict block only** of the 2 most recent `reports/*.md`, so advice
  builds on what was said last time.

## 2. Pull and gather numbers: `health-data` agent (Haiku)

Spawn the `health-data` agent with a self-contained brief:
- **pull first:** `uv run healthgo pull` (Garmin catch-up sync from the day of the previous pull, Telegram inbox,
  Cargill menu refresh, rebuild the db, recovery flags, commit & push). If it has been a long gap, the
  catch-up covers every missing day; a 429 midway is fine, the data on disk is used and the next pull resumes;
- the week(s) to prepare: the `prepare` command of `catch_up` (if any) **and** of `target` from `review-plan`, one
  digest per week, catch-up first. Give each week's `through` and `all_day_metrics_through` as the last days to
  include in any extra query;
- **return the flags `pull` printed** and its `previous_pull_at` / `this_pull_at`, since no daily Telegram alerts exist any more;
- any extra questions this review needs answered, e.g. "e1RM per week for squat/bench/deadlift since
  2026-07-15", "weekly RHR since the cut began".

Work from the digest it returns. **Don't read the raw weekly JSON or Garmin files yourself.** If you need
one more number, send the agent a follow-up rather than querying inline, unless it's a single short
`sqlite3` one-liner.

If the digest says sync failed, carry on with the data on disk, and state in one line how stale it is.
Login trouble belongs to `/sync`.

## 3. Read the Telegram inbox, then ask Darren: Opus. These are the only questions allowed

**Inbox first.** Darren logs from his phone through the Telegram bot (`/eat`, `/feel`, `/weight`, `/note`,
`/blood`, photos). `pull` already fetched new entries, so wait for the step 2 agent, then run
`uv run healthgo inbox --list` (a short table). For each pending entry, read `data/inbox/<stem>.json` (text only). Extract text values
as in `/log` step 1. **Never open the photos in the main thread**: pass their paths to `health-ops`, which reads them
with Sonnet (meal photos: spawn it with `model: "haiku"`; bloodwork photos on Sonnet), records them, and returns the extracted values. The brief also tells it to run
`uv run healthgo inbox --done <id> …` for every entry it recorded. An entry dated before the review window still
counts if it was never recorded. Don't ask about anything the inbox already answers.

Then ask in **one message**, and only what's still missing:

**Eating out** is the only question: always ask, covering the days since the last review:
   *"上次 review（日期）之後有外食嗎？哪天、大概吃了什麼？"* Estimate the kcal per meal yourself.

Then hand the values you extracted to the **`health-ops` agent** to record. That includes each eating-out
meal, or a note saying "no eating out since <date>" if there was none. It also commits. Do not ask about mood, waist, photos or soreness. If the data shows something you can't
read without him (e.g. no workouts for 6 days), one short question is fine.

## 4. Decide: Opus, in the main thread. Never delegated to Sonnet

Work through `reference.md` → **Decision rules**:
- **Rate:** 14- and 28-day weight trend against the 0.5–0.75%/wk target and the 1% cap.
- **Muscle:** e1RM of the main lifts against the prior 4 weeks, plus rate of loss staying within target and protein adequacy (no InBody anymore; see `reference.md`).
- **Recovery:** RHR, HRV, sleep, stress and Body Battery against his own baseline.
- **Context:** cut week, phase (gentle cut → maintenance from 2026-12-14, see `cutting-goal-2026.md`), days to the trip; ground advice in the `evidence-*.md` memories (open the one you need).
- **Health guard:** run `reference.md` → **Health-guard checklist**. The digest's HEALTH GUARD line already bands
  rate, energy availability, deficit weeks, sleep and strength; you add RHR/HRV, /feel and supplements. Any yellow/red
  goes into the reasons or changes.
- **Live facts come from the digest, not memory:** strength baselines since W41 (SINCE BASELINE), projections to the
  Christmas party / maintenance / checkpoint, the training pattern and bloodwork status are recomputed every review.
  Memory holds only the rules behind them (baseline date and excluded sessions live in `config/plan.json` →
  `strength`). Don't copy these numbers back into memory; record decisions only.
- **Limits:** every change is checked against `safety-limits.md`. His fat intake is below the floor, so that's
  the first lever.

With a catch-up, decide that week first, on its own numbers only, then decide the target review building on it
(its changes are what he's following now).

Settle the following (per review):
- **The verdict:** 繼續減脂 / 放慢速度 / 安排休息週 / 調整飲食.
- **3 reasons**, with his numbers.
- **What to change this week:** food quantities, training tweaks, shoulder notes.
- **Anything for the detail sections.**

If you are not running on Opus, give this step to a `general-purpose` agent with `model: opus`, passing it the digest and memory paths.

## 5. Write it up: `health-writer` agent (Sonnet)

Spawn `health-writer` with a self-contained brief containing:
- the report path, `kind` (full / midweek) and `through` date from `review-plan`. With a catch-up, one brief holds
  both reports in order: **catch-up first, written, committed and sent to Telegram, then the target report**
- the **final verdict, reasons and changes** (in English or 繁中; it writes 繁中)
- every number the report should show (paste the relevant digest lines)
- anything to emphasise or leave out

It writes the report, records the review, commits and pushes, **sends the full report to Telegram**
(`uv run healthgo send-report <path>`, so Darren can read it on his phone), then returns the verdict block as written.

**Verify:** compare the returned verdict block with your decision. If it drifted, send a correction, and
re-send the corrected report with `send-report`. If the agent reports `TELEGRAM: failed`, run `send-report`
yourself. **Every review ends with the report on Telegram** (Darren, 2026-10-11).

## 6. Tell Darren and learn: Opus

- Reply in chat **in 繁中** with the verdict block and the report path. Keep it short.
- **Durable learnings go to memory.** Examples: a better maintenance estimate, a lift that keeps stalling, a goal
  weight estimate, a diet change he agreed to (`daily-diet-baseline.md`).
  - If a target or date changes, update `config/plan.json` too.
  - These are judgments, so write them yourself, then commit and push (`git add .claude config && git commit -m "memory: …" && git push origin main`).
