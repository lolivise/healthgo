---
name: knowledge-review
description: Quarterly review of Darren's health knowledge base — pulls the new PubMed research for each sector (fat-loss, training, medical, aging) with a script, Sonnet workers screen it against the evidence memories, Opus decides what changes and rewrites the evidence in place so it stays lean. Trigger on /knowledge-review, "review the knowledge base", "quarterly research review", "is our research still current".
---

# /knowledge-review

Every ~3 months. You (the main thread, **Opus**) decide; workers do the pulling and reading (`CLAUDE.md` → Model
split). The sectors, searches and last-review dates are in `config/research.json`; the human index is
`research/README.md`.

Arguments: none → every quarterly sector that is due (`last_reviewed` ≥ ~3 months ago; ask once if none is due).
A sector name → only that sector.

## The lean rule (Darren, 2026-10-26)

Research accumulates and science corrects itself, so the knowledge base holds **the current best answer, not a
history**:
- An evidence file is rewritten in place. A contradicted row is **replaced**, never kept next to its correction.
  A refined row gets the new number. Confirming papers change nothing except, sometimes, the strength grade.
- What changed and why goes in **one line** in `research/<sector>/CHANGELOG.md`
  (`YYYY-MM-DD · evidence-file · row: old → new (PMID)`). Git keeps the rest.
- **Budget: each evidence file ≤ ~50 lines.** If an edit pushes it past that, merge or drop the weakest rows.
- Raw pulls (`research/<sector>/reviews/*-pulled.md`) are git-ignored and deleted at the end.
- Full reports in `research/<sector>/` are frozen snapshots. When a review overturns something a report says, add one
  line under its title: `> ⚠️ 已更新 YYYY-MM-DD：<what changed>，見 <evidence file>`. Don't rewrite reports.

## 1. Plan: Opus, quickly

Read `config/research.json` and `research/README.md` (no evidence files yet). Decide which sectors run.

## 2. Pull and screen: one `health-research` agent per sector (Sonnet), in parallel

Spawn them in one message. Each brief: the sector name, "run `uv run healthgo pubmed --sector <sector>`, screen it
against the sector's evidence files, re-check up to 5 [M] citations, return the delta in your format". The pull is a
script (no tokens); the agent reads only the index and the abstracts it picks. Don't run the pull yourself, and don't
open the pull files.

## 3. Decide: Opus. Never delegated

For each returned change, open only the evidence file it touches and decide:
- **Adopt**: rewrite the row in place (the agent's proposed row is a draft; keep the file's style and [V]/[M] tags).
- **Contested**: one row, both sides in a few words, strength "contested". Not two rows.
- **Reject**: say why in one line to Darren; nothing is written.
- **[M] checks**: replace [M] with [V] and correct the number.

Changes that would move a **safety limit, a plan target or his diet/training** are **proposals for Darren**, not edits:
list them, and change `safety-limits.md` / `config/plan.json` only after he approves (as in /review).

Then write each sector's `CHANGELOG.md` lines, check the budgets (`wc -l .claude/memory/evidence-*.md`), update the
`MEMORY.md` pointer line of any evidence file whose headline changed, and set `last_reviewed` in
`config/research.json` to the pull's `until` date for each finished sector.

## 4. Close

- `rm research/*/reviews/*-pulled.md`.
- Commit and push (`git add .claude config research && git commit -m "knowledge: <quarter> review (<sectors>)" && git push origin main`).
- Reply to Darren in **繁中**, short: per sector, what changed (one line each), proposals waiting for his OK, PDFs worth
  getting (paywalled papers the agents flagged). If nothing changed in a sector, say so in one line.
