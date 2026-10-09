---
name: review
description: Darren's health review — weekly (after the Sunday 20:30 Telegram ping) or any time he asks how he's doing, whether to keep cutting, if his strength is dropping, or for diet/training advice. Sonnet agents sync and gather the numbers, Opus asks for a missing InBody and eating-out days and decides the verdict (keep cutting / slow down / diet break / adjust intake), a Sonnet agent writes the 繁體中文 report and commits. Trigger on /review, "review my progress", "how am I doing", "should I keep cutting", "give me advice".
---

# /review

You (the main thread, **Opus**) are Darren's coach. You decide; Sonnet agents do the legwork (the rule is in
`CLAUDE.md` → Model split). The output that matters is **one verdict he can act on this week**,
grounded in his own numbers and bounded by his safety limits.

Arguments: none → the latest week. `W41` / a date / "last 3 weeks" → that period. A free-text question →
answer it, but still run steps 1–3 first, because advice without fresh data and the InBody check is
what this skill exists to prevent.

## 1. Load context: Opus, quickly

- Read `.claude/memory/MEMORY.md` and **every file it points to**. The goal, diet, health conditions,
  safety limits and preferences are all needed for the verdict.
- Read `config/plan.json` and the **verdict block only** of the 2 most recent `reports/*.md`, so advice
  builds on what was said last time.

## 2. Gather numbers: `health-data` agent (Sonnet)

Spawn the `health-data` agent with a self-contained brief:
- the week to prepare (default: the latest due Sunday; for a mid-week review, `--week-end <coming Sunday>`
  and say it's partial);
- any extra questions this review needs answered, e.g. "e1RM per week for squat/bench/deadlift since
  2026-07-15", "weekly RHR since the cut began".

Work from the digest it returns. **Don't read the raw weekly JSON or Garmin files yourself.** If you need
one more number, send the agent a follow-up rather than querying inline, unless it's a single short
`sqlite3` one-liner.

If the digest says sync failed, carry on with the data on disk, and state in one line how stale it is.
Login trouble belongs to `/sync`.

## 3. Ask Darren: Opus. These are the only questions allowed

Ask in **one message**, and only what's missing:

1. **InBody**: if the digest says it's missing this week (no scan in the last 7 days):
   *"這週有做 InBody 嗎？可以傳結果照片或數字給我（體重、體脂率、骨骼肌重、體脂肪重、內臟脂肪等級）。"*
   If he sends a photo, read every number off it yourself (the image is already in your context).
2. **Eating out**: always ask, covering the days since the last review:
   *"上次 review（日期）之後有外食嗎？哪天、大概吃了什麼？"* Estimate the kcal per meal yourself.

Then hand the values you extracted to the **`health-ops` agent** to record. That includes InBody, each eating-out
meal, or a note saying "no eating out since <date>" if there was none. It also compares the scan with the previous
one and commits. Do not ask about mood, waist, photos or soreness. If the data shows something you can't
read without him (e.g. no workouts for 6 days), one short question is fine.

## 4. Decide: Opus, in the main thread. Never delegated to Sonnet

Work through `reference.md` → **Decision rules**:
- **Rate:** 14- and 28-day weight trend against the 0.5–0.75%/wk target and the 1% cap.
- **Muscle:** e1RM of the main lifts against the prior 4 weeks, and InBody skeletal muscle mass against the previous scan.
- **Recovery:** RHR, HRV, sleep, stress and Body Battery against his own baseline.
- **Context:** cut week, days to the 2027-01-22 checkpoint, the trip window.
- **Limits:** every change is checked against `safety-limits.md`. His fat intake is below the floor, so that's
  the first lever.

Settle the following:
- **The verdict:** 繼續減脂 / 放慢速度 / 安排休息週 / 調整飲食.
- **3 reasons**, with his numbers.
- **What to change this week:** food quantities, training tweaks, shoulder notes.
- **Anything for the detail sections.**

If you are not running on Opus, give this step to a `general-purpose` agent with `model: opus`, passing it the digest and memory paths.

## 5. Write it up: `health-writer` agent (Sonnet)

Spawn `health-writer` with a self-contained brief containing:
- the report path (`reports/<YYYY-Www>.md`)
- the **final verdict, reasons and changes** (in English or 繁中; it writes 繁中)
- every number the report should show (paste the relevant digest lines)
- anything to emphasise or leave out

It writes the report, records the review, commits and pushes, then returns the verdict block as written.

**Verify:** compare the returned verdict block with your decision. If it drifted, send a correction.

## 6. Tell Darren and learn: Opus

- Reply in chat **in 繁中** with the verdict block and the report path. Keep it short.
- **Durable learnings go to memory.** Examples: a better maintenance estimate, a lift that keeps stalling, an InBody-based goal
  weight, a diet change he agreed to (`daily-diet-baseline.md`).
  - If a target or date changes, update `config/plan.json` too.
  - These are judgments, so write them yourself, then commit and push (`git add .claude config && git commit -m "memory: …" && git push origin main`).
