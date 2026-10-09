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

**Why:** token cost. The main thread is the expensive, long-lived context, so raw Garmin JSON and table
dumps must stay out of it.

**How to apply:** the rule is in `CLAUDE.md` (Model split) and wired into `/review`, `/log` and `/sync`. When
adding a new skill, follow the same split. Never let a worker make or alter a decision.

Related: [[review-preferences]]
