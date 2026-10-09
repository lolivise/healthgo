---
name: git-policy
description: healthgo has a standing exemption — commit and push straight to main without asking; never force-push or rewrite history
metadata:
  type: feedback
---

**In this repo, `git add` / `commit` / `push` to `main` need no permission and no question.**
Darren, 2026-10-09: "for this repo, straight commit and push to the repo. as this repo is my health
track and for myself only."

- Remote: `git@github.com:lolivise/healthgo.git` (private). **Only `main`, no branches.**
- **All data is committed and pushed** (raw Garmin JSON, FIT files, manual records, reports, memory).
  The only exception is the derived `data/healthgo.db`, which is git-ignored and rebuilt from the JSON.
- Still forbidden without an explicit ask: force-push, `reset --hard`, `rebase`, `--amend`, `tag`, `stash drop`.
- The exemption removes the question, not the report: say what was committed and whether it was pushed.

**Why:** the daily launchd sync must commit unattended, and memory or report edits happen constantly.
Nothing deploys from this repo.
