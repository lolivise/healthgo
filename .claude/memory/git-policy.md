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
- **Every finished task ends committed and pushed, unasked** (Darren, 2026-10-27: "if that task is done you just
  commit and push to me without asking me"). Covers answering a question, an `/ask` the monitor picked up, a research
  run, a memory/rule edit, anything. Never leave it in the working tree with commands for him to run.
- **Command shape so the allow-list matches** (`.claude/settings.json`): run from the repo root, one git command per
  Bash call, no `cd … &&` chains: `git add <files>`, `git commit -m "…"`, `git push origin main`. A compound command
  falls through to the auto-mode classifier, which blocked a push on 2026-10-27.
- Still forbidden without an explicit ask: force-push, `reset --hard`, `rebase`, `--amend`, `tag`, `stash drop`.
- The exemption removes the question, not the report: say what was committed and whether it was pushed.

**Why:** `healthgo pull` (run by `/review`) commits data itself, and memory or report edits happen constantly.
Nothing deploys from this repo.
