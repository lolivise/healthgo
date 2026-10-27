---
name: ask-myth-buster
description: Telegram /ask is his myth-buster — YouTube/web/heard health claims traced to the source paper, graded for quality and fit to him, every check filed in research/claims/ so the knowledge base grows
metadata:
  type: project
---

**`/ask` exists to stop him being misled.** Darren, 2026-10-27: he watches YouTube and reads the web on longevity,
health and sport, and much of it misleads: "they just reference part of the paper or grab some data from somewhere and
then make up their statement". He wants a guardian that gives him "the full picture" so he holds correct knowledge.

He sends a **YouTube link** (transcript via `healthgo transcript`), a **web page**, or **types what he heard**. Each
check answers: where the claim comes from (which paper or research), is it legit or misleading (weak experiment,
cherry-picked, animal data, a population unlike him), does it fit **him** (age 36, Hep B, his lifestyle), and is it
worth adopting.

**Why:** he can't judge study quality himself, and a myth accepted once is hard to shift ([[research-purpose]],
eggs/cholesterol as the model case).

**How to apply:**
- **Every check is kept** (his words: "once you have investigated I want you to put it into our knowledge base"):
  one record per source in `research/claims/`, an index row, the source's track record in `research/claims/sources.md`,
  and the matching `evidence-*` file when it adds real evidence. Search `research/claims/` before researching anything.
- The answer always covers fit to him, not just whether the study is right in general.
- Workflow: `.claude/skills/ask/SKILL.md`. Safety limits and the Hep B supplement rule bound every verdict
  ([[safety-limits]], [[health-conditions]]).
