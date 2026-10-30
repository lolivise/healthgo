---
name: ask-plan-questions
description: Telegram /ask also answers questions about his OWN plan (2026-10-30) — what-if diet/exercise swaps and projections under changed weight or performance; numbers from `healthgo whatif`, filed in research/plan-questions/, propose-only
metadata:
  type: project
---

**`/ask` has a second desk for his own plan.** Darren, 2026-10-30, away from his PC: "what will happen if I change
xyz on my diet or swap xyz exercise with abc exercise", and "how would the prediction look if my weight and exercise
performance has some changes". He said this is **not** the myth-buster; it's a general question about the plan,
asked through Telegram and picked up by the same `/ask` monitor.

**Why:** questions come up during the day (at the gym, at the shops) and waiting for a `/review` at the Mac loses
them. One command (`/ask`) for both kinds, so he has nothing new to remember.

**How to apply:**
- The `/ask` dispatcher routes: links and other people's claims → myth-buster ([[ask-myth-buster]]); plain questions
  about changing or projecting his own plan → plan desk (`plan-intake` → `ask-check` for uncovered research points →
  `plan-judge` on Opus → `healthgo ask file`). Workflow: `.claude/skills/ask/SKILL.md`.
- **Projections come from `uv run healthgo whatif`** (script: TDEE from the 28-day trend, constant %/wk, plan vs
  scenario at each plan date, when 81 kg is reached, safety floors), never from model arithmetic.
- **Propose, never change the plan** from Telegram: adopting an answer happens at the next `/review`, which edits
  `config/plan.json` and the memories together. Every answer still follows [[evidence-only-answers]] and
  [[safety-limits]], and respects his standing decisions ([[cutting-goal-2026]], [[performance-first]]).
- Answers are filed in `research/plan-questions/` (search it before answering a repeat question; re-answer if the plan
  changed since).
