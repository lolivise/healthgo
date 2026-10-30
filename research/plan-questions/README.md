# Plan questions (/ask about his own plan)

Questions Darren sends through Telegram `/ask` about **his own plan** rather than a claim someone made: "what happens
if I swap X for Y in my diet", "can I replace this exercise with that one", "if my weight is Z by Christmas, when do I
reach 81 kg". Each answer is filed here; the claims someone else made live in `../claims/`.

- **One file per question**: `YYYY-MM-DD-<slug>.md`, 繁中, the exact text sent to Telegram.
- **Numbers come from `healthgo whatif`** (a script: plan vs scenario at each plan date, when the stop-cut weight is
  reached, safety floors), never from a model's arithmetic. Each answer states the data date and the model's limits.
- **Research comes from the `evidence-*` memories**, plus a fresh PubMed check for any point they don't cover.
- **These answers propose, never change the plan.** Adopting one happens at the next `/review`, which updates
  `config/plan.json` and the memory files together. A question asked again after the plan changed is answered fresh.

| Date | Question | Answer | File |
|---|---|---|---|
