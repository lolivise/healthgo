---
name: ask
description: Darren's myth-buster: a long-running answer desk for Telegram /ask. Watches the Worker every 10 s with a Monitor; each question (a YouTube link, a web page, or a claim he heard) is traced to its source paper, graded for study quality and fit to him, answered in 繁中 (where it comes from, the science, impact on him, worth adopting?), sent back under the question, and filed in the claims knowledge base. The main thread only dispatches; sub-agents do all the work. Trigger on /ask, "watch my asks", "start the ask monitor", "answer my Telegram questions".
---

# /ask: myth-buster desk (dispatcher)

**Why it exists** ([[ask-myth-buster]]): YouTube and web health claims often quote part of a paper or build a
statement around a study that says something else. Each `/ask` is traced to its source, graded, checked against
Darren's own situation, answered, and **filed in `research/claims/`** so the knowledge base keeps growing.

## This thread is a dispatcher. Keep it tiny

This session runs for hours and its context only grows; sub-agents clean themselves up when they finish
(Darren, 2026-10-27: "make sure the main thread agent does not consume a lot of token"). So:

- **Never open a file, transcript, web page, abstract or memory file here.** Not the record, not the checks. Workers
  read; you only see their one-line returns.
- **Briefs are one line of parameters.** Each agent's full instructions live in its definition in `.claude/agents/`.
  Don't repeat them.
- **You decide nothing about the claims.** Every claim the intake lists gets checked (step 2). Every decision
  (verdicts, impact, worth it) belongs to `ask-judge`, which runs on Opus.
- Don't relay results to the chat beyond one line per question.

| Step | Agent | Model | Returns |
|---|---|---|---|
| 1. Fetch source, look up prior checks, list every claim | `ask-intake` | Sonnet | 1 line per claim |
| 2–3. Check **every** claim (origin paper, PubMed, fit to him) | `ask-check` × n, ≤ 5 at a time | Sonnet | 1 line each |
| 4. Verdicts, impact, worth it, write the 繁中 record, evidence edits | `ask-judge` | Opus | 1 line |
| 5. Index + track record, send to Telegram, commit, clean up | `healthgo ask file` | **no model** (script) | 1 JSON line |
| Progress card in Telegram, all along | `healthgo ask status` | **no model** (script) | — |

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

## Per question

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

**Failure**: an agent that returns an error or nonsense gets **one** retry with the same brief. A second failure:
`uv run healthgo ask status <id> "⚠️ 卡住了：<step>，稍後再試"`, one line to Darren here, and leave the question pending (it stays in R2; the next re-arm re-prints it). Never send a
half-finished answer.

