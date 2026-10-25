---
name: review-preferences
description: How reviews must run — no InBody (gone 2026-10-10), ask eating-out since last review, 繁中 report with verdict on top, training tweaks only, no waist/photos
metadata:
  type: feedback
---

Decided with Darren 2026-10-09:

- **InBody: no longer exists** (gym removed it, 2026-10-10). Never ask for it ([[data-sources]]).
- **Eating out:** about once every 1–2 weeks (team lunch, friends). **At every review ask "did you eat
  out since the last review? when, roughly what?" and record the answer**, including "none".
- **Dropped on purpose:** waist measurements and progress photos ("too much, it will turn me off").
  Do not bring them back.
- **How he feels** = Garmin **stress** and **Body Battery**, plus sleep/HRV/RHR. Do not ask for
  subjective ratings.
- **Report language: Traditional Chinese (繁體中文)**, with English technical terms in brackets so he can
  look them up. Food names in both languages.
- **Report shape:** a short verdict block first (keep cutting / slow down / diet break / adjust
  intake, plus 3 reasons and what to change this week), then detail underneath. Tone: direct, like a
  coach who knows his numbers, no sugar-coating.
- **Training advice level:** targeted adjustments to his existing routine (lighter weeks, stalled
  lifts, shoulder protection). **Not** a full new program.
- **Diet changes:** adjust quantities of his existing foods, not a new diet ([[daily-diet-baseline]]).
- **Every review is sent to Telegram in full** (Darren, 2026-10-11: "every review need to push to telegram bot,
  so I can read it on my mobile"). `uv run healthgo send-report reports/<file>.md`, run by `health-writer`
  after the commit. It is plain text, split under the 4,096-char limit. A corrected report is re-sent.
  **Phone layout (Darren, 2026-10-11):** the first send was "squished together" paragraphs, hard to read at a
  ~350 px chat width. Reports are now one fact per line, bold titles with indented sub-bullets, each change on its
  own line (rules in `.claude/skills/review/reference.md` → Report template). The sender renders them as Telegram HTML.
- **Cadence: on demand (Darren, 2026-10-12).** He removed the scheduled pull: "merge the feature into `/review`
  … so I can do review whenever I want". `/review` pulls fresh data itself (`healthgo pull`). There are no
  daily red-flag alerts or Sunday pings any more. The recovery flags surface inside the review, so **always
  mention any flags in the verdict**, since that is now the only place he sees them. Don't reinstall the job
  without asking.

- **Review window (Darren, 2026-10-25, replaces the 10-16 "never analyse today" rule):**
  - **Sunday from 18:00 = full review** of the whole Mon–Sun week incl. Sunday, against the last 4 weeks (10-18 rule, kept).
  - **Any other time = mid-week review through today.** He trains in the morning, so today's weigh-in, workout and
    last night's sleep/HRV/RHR count. Before 18:00 today's steps and stress are left out (day not over); from 18:00
    they count ("I'll probably be at home already … get ready to bed, so there is no much activities after that").
  - **A missed Sunday is caught up first:** if last week has no full review (likely on the trip), run that full
    review first, send it to Telegram, then the mid-week one.
  - Built into `healthgo review-plan`, `prepare-week` and the checks (`config.last_complete_day()` = today from 18:00).
- **Every pull is stamped** (`state.last_pull`) and the next pull re-fetches from that day, so nothing logged after
  the previous pull is missed (Darren, 2026-10-25: "make sure all the data is complete and there's nothing missing").

**Why:** he wants the system to carry the tracking burden. Questions are acceptable only inside a
review he chose to start.

Related: [[user-profile]], [[safety-limits]]
