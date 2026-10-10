---
name: model-split
description: Standing rule — Sonnet agents (health-data / health-ops / health-writer) do execution, data gathering and report writing; Opus main thread does analysis and decisions only
metadata:
  type: feedback
---

**Sonnet does the execution, data gathering and report writing. Opus does the analysis and
decision-making.** Darren, 2026-10-09: "to be more token efficient, make sure use sonnet agents to do
execution and information gathering and report writing. the analyse and descision making can use opus
model" — and then: "write this as a rule or a skill".

- **`health-data`** (Sonnet): sync, prepare-week, DB queries. Returns a ≤60-line digest.
- **`health-ops`** (Sonnet): `/log` recording, `/sync` operations and diagnosis, commits.
- **`health-writer`** (Sonnet): writes the 繁中 report from the verdict Opus decided, records it, commits.
- **Opus (main thread):** reads memory, asks Darren the review questions, reads the digest, decides the
  verdict and changes, and updates memory.

**Images go to Sonnet too (Darren, 2026-10-09):** "when doing any images parsing, use sonnet agent. do not use
opus. it will be overkilled". `health-ops` reads bloodwork and meal photos by file path and returns the values.
Opus checks the returned numbers and makes the judgment calls. Photos come in through the Telegram
inbox (`data/inbox/`). If one is pasted into chat, ask him to resend it via the bot.

**Revised 2026-10-09, after Darren asked whether Haiku would be accurate:**
- **Meal photos → `health-ops` on Haiku** (`model: "haiku"`). The kcal is an estimate anyway.
- **Bloodwork photos stay on Sonnet.** One misread digit could matter, and they are rare.
- InBody no longer exists (2026-10-10), so its `--check` validator and the Haiku-vs-Sonnet comparison were dropped ([[data-sources]]).
- **Voice notes:** no Claude model takes audio. Workers AI Whisper transcribes them in the Worker, and the transcript is
  text like any note.

**Why:** token cost. The main thread is the expensive, long-lived context, so raw Garmin JSON and table
dumps must stay out of it.

**How to apply:** the rule is in `CLAUDE.md` (Model split) and wired into `/review`, `/log` and `/sync`. When
adding a new skill, follow the same split. Never let a worker make or alter a decision.

Related: [[review-preferences]]
