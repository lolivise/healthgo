---
name: ask
description: Darren's long-running answer desk for Telegram /ask, two desks behind one command. Myth-buster: a YouTube link, web page or claim he heard is traced to its source paper, graded, answered in 繁中 and filed in research/claims/. Plan desk: a question about his own plan ("what if I swap X for Y", "more cardio?", "if I weigh Z by Christmas, when do I reach 81 kg?") is turned into `healthgo whatif` projections plus evidence, answered in 繁中 and filed in research/plan-questions/. Watches the Worker every 10 s with a Monitor; the main thread only routes and dispatches, sub-agents do all the work. Trigger on /ask, "watch my asks", "start the ask monitor", "answer my Telegram questions".
---

# /ask: answer desk (dispatcher)

**Why it exists**: two kinds of questions reach him on his phone, away from the Mac.
- **Claims** ([[ask-myth-buster]]): YouTube and web health claims often quote part of a paper or build a statement
  around a study that says something else. Each is traced to its source, graded, checked against Darren's own
  situation, answered, and **filed in `research/claims/`** so the knowledge base keeps growing.
- **His own plan** ([[ask-plan-questions]]): "what happens if I change X in my diet", "swap exercise A for B", "how
  does the prediction look if my weight or lifts change". Answered from the `healthgo whatif` projections (a script)
  and the evidence memories, **filed in `research/plan-questions/`**. Proposes only; adopting it happens at `/review`.

## Route each question (your one judgement call)

From the event's `text` alone, no file reads:
- **Claims desk**: any link, a photo, or a claim someone else made ("YouTube 說…", "聽說…", "is it true that…"), even if
  he also asks whether it applies to him (the myth-buster's 對你的影響 covers that).
- **Plan desk**: plain text about changing or projecting **his own** plan: food or kcal swaps, exercise swaps, more or
  less cardio, "if my weight / lifts are Z, then…", "when will I reach…", "should I…".
- **Unsure** → claims desk. Either intake can bounce it: `ROUTE: plan` / `ROUTE: claims` → start over at the other
  desk's step 1 (one bounce only; a second goes to the plan desk).

## This thread is a dispatcher. Keep it tiny

This session runs for hours and its context only grows; sub-agents clean themselves up when they finish
(Darren, 2026-10-27: "make sure the main thread agent does not consume a lot of token"). So:

- **Never open a file, transcript, web page, abstract or memory file here.** Not the record, not the checks. Workers
  read; you only see their one-line returns.
- **Briefs are one line of parameters.** Each agent's full instructions live in its definition in `.claude/agents/`.
  Don't repeat them.
- **You decide nothing but the route.** Every claim the intake lists gets checked (step 2). Every decision
  (verdicts, impact, worth it, what a plan change would do) belongs to `ask-judge` / `plan-judge`, which run on Opus.
- Don't relay results to the chat beyond one line per question.

| Step | Claims desk | Plan desk | Returns |
|---|---|---|---|
| 1. Intake | `ask-intake` (Sonnet): fetch source, prior checks, list every claim | `plan-intake` (Sonnet): food/exercise → numbers, `healthgo whatif` scenarios, research points | ≤ 15 lines |
| 2–3. Check | `ask-check` × every claim, ≤ 5 at a time | `ask-check` × each research point with `known: none` only, ≤ 5 at a time | 1 line each |
| 4. Decide + write the 繁中 answer | `ask-judge` (Opus) | `plan-judge` (Opus) | 1 line |
| 5. Index, send to Telegram, commit, clean up | `healthgo ask file` (**no model**, script) | same | 1 JSON line |
| Progress card in Telegram, all along | `healthgo ask status` (**no model**, script) | same | — |

## Progress card: he watches it live

Darren hates sending a question and wondering for 20 minutes whether anything is happening (2026-10-27). So every
question gets a **status card** in Telegram under it, one message edited in place, line by line:
- The **watcher script** opens it the moment it sees the question ("收到，開始處理" or "排隊中（前面還有 N 題）"),
  before any agent runs.
- Each agent adds its own milestones (`uv run healthgo ask status <id> "<text>"`): source read, knowledge base hit or
  miss, PubMed per claim, each verdict, Opus judging. The instructions are in their definitions.
- `healthgo ask file` closes it ("完成，答案在下面 👇"), and the answer arrives as its own reply.
Sending is a script, not a model: cheaper than even Haiku. You only post to the card on a failure.

## Start: arm the monitor

```
Monitor  command: cd /Users/darrenhung/Projects/storium/healthgo && uv run healthgo ask watch --interval 10
         description: Telegram /ask questions     timeout_ms: 1800000
```

Each stdout line is one JSON event:
- `{"event":"ask","id":…,"asked_at":…,"text":…,"has_file":…}`: a question. Already-pending ones print on start.
- `{"event":"error","type":…}`: polling failed (one line per streak). Wait for `recovered`; if none comes within a few
  minutes, run `uv run healthgo ask list` once and say in one line what failed.
- `{"event":"recovered"}`: nothing to do.

**Backlog first.** Questions he sent while the Mac was off (or while no session was watching) wait in R2 and are
never lost. The watcher's first poll prints every one of them right away, oldest first, and opens their progress
cards ("收到你 21:30 傳的問題（當時 Mac 沒開），開始處理"). **Start the pipeline on the first one immediately**: no
greeting, no confirmation question. Say once: "監看中，每 10 秒檢查一次 /ask · 待處理 <n> 題" (n = the ask events
printed on start). `"resumed": true` means a previous run was cut off mid-question (Mac shut down): **start that
question over from step 1** (the work files may be half-written; agents overwrite them).

**The monitor expires after 30 min: re-arm it immediately, every time, with the same call**, until Darren says stop. A
re-armed watcher re-prints still-pending questions: skip any id already in progress. One question at a time, oldest
first; new events wait.

## Per question: claims desk

1. **Intake**: `Agent(subagent_type: "ask-intake", description: "/ask <id> intake", prompt: "id=<id> has_file=<…>
   text=<the text verbatim>")`.
   - Returns `URGENT: …` → go straight to step 4 with `URGENT`.
   - `PRIOR:` covers **every** listed claim (a check < ~2 years old) → step 4 with `prior=<file>`.
2. **Check every CHECKABLE claim. Never pick, never skip** (Darren, 2026-10-27: "how do I know what I can believe"
   if some points go unchecked). A claim the knowledge base already covers is still checked, with `known=<file>`, so
   the worker only looks for newer evidence. OPINION claims (pure value judgments, nothing research can test) are not
   checked; they go to the judge as `opinions=`.
3. **Check**: one per CHECKABLE claim, `n` = its intake number, **in waves of at most 5** (repo rule: ≤ 5 sub-agents
   at once): up to 5 in one message, wait for all of them, then the next wave:
   `Agent(subagent_type: "ask-check", description: "/ask <id> check <n>", prompt: "id=<id> n=<n> claim=<claim>
   source=<SOURCE line> known=<prior evidence/claims files or none>")`.
4. **Judge**: `Agent(subagent_type: "ask-judge", description: "/ask <id> judge", prompt: "id=<id>
   checks=data/asks/pulls/<id>-check-1.md,… | prior=<file> | URGENT opinions=<claim; claim; …>")`.
5. **File**: `uv run healthgo ask file <id>` (a script, no agent): index row, source track record, sends the record under
   his question, marks it done in R2, commits + pushes, closes the progress card, deletes the work files. It prints
   JSON: `telegram: false` → retry once (filing is idempotent); `done: false` → sent but still pending in R2, run
   `uv run healthgo ask list` and never send twice; `git` other than `pushed` → `git push origin main` once.
6. One line here: `/ask <id>: <verdicts> · <git result>`. Back to waiting.

## Per question: plan desk

1. **Intake**: `Agent(subagent_type: "plan-intake", description: "/ask <id> plan intake", prompt: "id=<id>
   has_file=<…> text=<the text verbatim>")`. `URGENT: …` → step 3 with `URGENT`. `ROUTE: claims` → claims desk.
2. **Check** each `RESEARCH` line with `known: none`, in waves of at most 5:
   `Agent(subagent_type: "ask-check", description: "/ask <id> check <n>", prompt: "id=<id> n=<n> claim=<research
   question> source=plan question known=none")`. Lines with a `known:` file are not re-checked: the judge cites the
   evidence file (`/knowledge-review` keeps those current). No research lines → straight to step 3.
3. **Judge**: `Agent(subagent_type: "plan-judge", description: "/ask <id> plan judge", prompt: "id=<id>
   checks=data/asks/pulls/<id>-check-1.md,…|none known=<evidence files from the RESEARCH lines>|none | URGENT")`.
4. **File**: `uv run healthgo ask file <id>`, exactly as the claims desk's step 5 (it reads `kind: plan` from the
   filing JSON and indexes into `research/plan-questions/`).
5. One line here: `/ask <id> (plan): <answer word> · <git result>`. Back to waiting.

**Failure**: an agent that returns an error or nonsense gets **one** retry with the same brief. A second failure:
`uv run healthgo ask status <id> "⚠️ 卡住了：<step>，稍後再試"`, one line to Darren here, and leave the question pending (it stays in R2; the next re-arm re-prints it). Never send a
half-finished answer.

