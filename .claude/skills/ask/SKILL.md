---
name: ask
description: Long-running answer desk for Darren's Telegram /ask questions. Watches the Worker every 10 s with a Monitor; for each new question it checks the knowledge base, has a Sonnet worker pull PubMed when the evidence is missing, Opus writes a 繁中 answer (where the claim comes from, the science, impact on his plan, worth adopting?) and sends it to Telegram under the question. Trigger on /ask, "watch my asks", "start the ask monitor", "answer my Telegram questions".
---

# /ask: answer desk

Darren sends `/ask <question>` (text or voice) to the bot. The Worker parks it in R2 (`healthgo-asks`,
`pending/<message id>.json`) and replies "收到". This session answers it. It runs for hours, so keep its context
lean: never re-read a file already in context, and let workers do the reading.

Split (`CLAUDE.md` → Model split): **Opus (this thread) decides and writes the answer.** Sections 3–4 are judgement
about his plan, which never moves off Opus. **`health-research` (Sonnet) does the PubMed pull and the reading.** If
this session isn't Opus, hand steps 2–4 to a `general-purpose` agent with `model: opus`.

## Start: arm the monitor

```
Monitor  command: cd /Users/darrenhung/Projects/storium/healthgo && uv run healthgo ask watch --interval 10
         description: Telegram /ask questions     timeout_ms: 1800000
```

Every stdout line is one JSON event:
- `{"event":"ask","id":…,"asked_at":…,"text":…,"has_file":…}`: a question to answer. Questions already pending
  print right away on start.
- `{"event":"error","type":…}`: polling failed (one line per failure streak). Wait for `recovered`; if none comes
  within a few minutes, run `uv run healthgo ask list` once and say what failed. Never print tokens.
- `{"event":"recovered"}`: back to normal, nothing to do.

**The monitor expires after 30 min. Re-arm it immediately, every time, with the same call**, and keep doing so
until Darren says stop. A re-armed watcher prints still-pending questions again: skip any id you are already
answering. Tell Darren once at the start: "監看中，每 10 秒檢查一次 /ask".

Questions are answered one at a time, oldest first. New events wait in the queue meanwhile.

## For each question

### 1. Read the question (Opus)

- What exactly is the claim? Restate it in one line. If ambiguous, take the most likely reading and say so in the
  answer (he can't reply here; he can `/ask` again).
- **Urgent symptoms** (chest pain, fainting, yellow eyes/skin, black stool, vomiting blood, severe right-side
  abdominal pain): skip research and answer at once: go to a GP / ED now (Australia: 000). Hep B makes liver signs
  urgent.
- `has_file: true`: the question came with a photo. Opus never opens images: if the text can't be answered without
  it, have `health-ops` download it (`inbox.download_file(file_id)`, file_id from `uv run healthgo ask list`) and
  describe it.

### 2. Check the knowledge base (Opus, cheap)

`MEMORY.md` is already in context. From its index pick the `evidence-*` files that cover the claim (≤ 3) plus the
plan files that section 3 needs (usually `daily-diet-baseline`, `training-routine`, `safety-limits`,
`health-conditions`, `supplements`). Current numbers: the latest `reports/*.md` (read its top section only). Don't
query the DB yourself; if a number is truly needed, ask `health-data` (Haiku) for that one figure.

**Pull PubMed only when needed**: the claim isn't covered, or the evidence files cover it only with [M] (unverified)
citations or with research older than ~3 years on a fast-moving topic. A claim the evidence files already settle
with [V] citations needs no pull: say "已有研究，見知識庫" and answer.

### 3. Research when needed: one `health-research` agent (Sonnet)

Brief it self-contained (it doesn't see this conversation):

> AD-HOC QUESTION, not a sector review. Question: "<text>". Claim to check: "<your one-line claim>".
> 1. Origin: find where this claim comes from (book, doctor, influencer, a specific study, a misread one) with
>    WebSearch/WebFetch. One or two lines, with a link.
> 2. Evidence: run `uv run healthgo pubmed --query '<q1>' --query '<q2>' --since <10 years ago> --out
>    data/asks/pulls/<id>.md` (2–4 PubMed queries; you may rewrite mine: <suggested queries>). Read only the index,
>    then open ≤ 10 abstracts. Already in the knowledge base: <evidence file names, or none>; don't re-derive those.
> 3. Return ≤ 40 lines: ORIGIN · VERDICT (supported / partly / myth / unknown, strength strong|moderate|weak) ·
>    KEY EVIDENCE (PMID, type, n, effect + CI, year, weakness flags) · WHAT IS HYPE (the part of the claim the data
>    doesn't support) · RELEVANCE to a 36-y-old male lifter in a calorie deficit with Hep B on entecavir · PMIDs.
> Never edit memory, config or reports.

### 4. Write the answer (Opus)

File: `data/asks/<YYYY-MM-DD>_<id>.md` (Perth date). **繁體中文**, English terms in brackets, phone-sized:
**≤ ~2,500 characters**, no tables (they render as bullets anyway). Shape:

```markdown
# <the question, short>

**結論：** <one sentence: true / partly / myth, and what to do>

## 1. 這個說法從哪來
<origin, 1–3 lines>

## 2. 科學證據
- <strongest evidence first, grade it: 統合分析 / RCT / 觀察性 / 動物>（PMID 12345678）
- **被誇大的部分：** <what the claim adds beyond the data>

## 3. 對你的影響
<against his actual plan: 2,520 kcal, 5-day split + treadmill, cut pace, Hep B, sleep, supplements.
 Say what it would change, or "不影響現在的計畫" and why>

## 4. 值不值得做
**<值得試 / 不必 / 先問醫生 / 已經在做>**，因為 <why>。
- 怎麼做：<concrete, smallest step that fits his routine>（if worth it）

來源：PMID … · <origin link>
```

Rules, all non-negotiable:
- **Safety limits** (`safety-limits.md`) bound every suggestion. Nothing past them, ever.
- **A new supplement or anything liver-related is only "先問醫生"** (Hep B, entecavir). Never "try it".
- **No new tracking chores** (no waist, no photos, no extra logging).
- An answer **proposes**, it never changes his plan: don't edit `config/plan.json`, `safety-limits.md` or the diet /
  training memories from here. If adopting it would change the plan, say "要採用的話，下次 /review 跟我說".
- Say plainly when evidence is weak or missing; flag hype (`research-purpose.md`).

### 5. Send

`uv run healthgo ask answer <id> data/asks/<file>.md` sends it threaded under his question, marks it done in R2,
and commits + pushes `data/asks/`. It prints JSON: `telegram: false` means nothing was marked, so retry once, then
tell Darren here. `done: false` means it was sent but is still pending: run `uv run healthgo ask list` and don't
send it twice.

### 6. Keep what's durable (only when it earns it)

A new topic he is likely to come back to, with real evidence behind it, becomes knowledge the same way
`/knowledge-review` adds a new question: a new or updated `evidence-*.md` (≤ ~50 lines, `sector:` tag, [V]/[M]
tags), a `MEMORY.md` pointer line, a row in `research/README.md`. Then
`git add .claude/memory research && git commit -m "knowledge: <topic> (from /ask <id>)" && git push origin main`.
One-off curiosities stay in `data/asks/` only.

Then one line here (id, verdict, sent) and back to waiting. `rm data/asks/pulls/<id>.md` when done.
