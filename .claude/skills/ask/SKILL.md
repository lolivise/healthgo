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
- **Your only decision** is which claims to check (step 2). Every other decision (verdicts, impact, worth it) belongs
  to `ask-judge`, which runs on Opus.
- Don't relay results to the chat beyond one line per question.

| Step | Agent | Model | Returns |
|---|---|---|---|
| 1. Fetch source, look up prior checks, list claims | `ask-intake` | Sonnet | ≤ 15 lines |
| 2. Pick ≤ 4 claims to check | **you** | Opus | — |
| 3. Check each claim (origin paper, PubMed, fit to him) | `ask-check` × n, parallel | Sonnet | 1 line each |
| 4. Verdicts, impact, worth it, write the 繁中 record, evidence edits | `ask-judge` | Opus | 1 line |
| 5. Index + track record, send to Telegram, commit, clean up | `ask-file` | Sonnet | 1 line |

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

**The monitor expires after 30 min: re-arm it immediately, every time, with the same call**, until Darren says stop. A
re-armed watcher re-prints still-pending questions: skip any id already in progress. Say once at the start:
"監看中，每 10 秒檢查一次 /ask". One question at a time, oldest first; new events wait.

## Per question

1. **Intake**: `Agent(subagent_type: "ask-intake", description: "/ask <id> intake", prompt: "id=<id> has_file=<…>
   text=<the text verbatim>")`.
   - Returns `URGENT: …` → go straight to step 4 with `URGENT`.
   - `PRIOR:` covers the claim (a check < ~2 years old) and nothing new needs checking → step 4 with
     `prior=<file>`.
2. **Pick** (you): up to 4 CHECKABLE claims that could change what he does, skipping ones a PRIOR already settles.
   Opinions and minor claims become "unchecked".
3. **Check**: all in **one message**, one per picked claim:
   `Agent(subagent_type: "ask-check", description: "/ask <id> check <n>", prompt: "id=<id> n=<n> claim=<claim>
   source=<SOURCE line> known=<prior evidence files or none>")`.
4. **Judge**: `Agent(subagent_type: "ask-judge", description: "/ask <id> judge", prompt: "id=<id>
   checks=data/asks/pulls/<id>-check-1.md,… | prior=<file> | URGENT unchecked=<claim; claim; …>")`.
5. **File**: `Agent(subagent_type: "ask-file", description: "/ask <id> file", prompt: "id=<id>")`.
6. One line here: `/ask <id>: <verdicts> · <filed line>`. Back to waiting.

**Failure**: an agent that returns an error or nonsense gets **one** retry with the same brief. A second failure:
one line to Darren here, and leave the question pending (it stays in R2; the next re-arm re-prints it). Never send a
half-finished answer.

If this session isn't Opus, step 2 is still yours: the stakes are low, and `ask-judge` is pinned to Opus regardless.
