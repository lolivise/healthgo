---
name: ask
description: Darren's myth-buster: a long-running answer desk for Telegram /ask. Watches the Worker every 10 s with a Monitor; each question (a YouTube link, a web page, or a claim he heard) is traced to its source paper, graded for study quality and fit to him, answered in 繁中 (where it comes from, the science, impact on him, worth adopting?), sent back under the question, and filed in the claims knowledge base. Trigger on /ask, "watch my asks", "start the ask monitor", "answer my Telegram questions".
---

# /ask: myth-buster desk

**Why this exists** (Darren, 2026-10-27): he watches YouTube and reads the web on longevity, health and sport, and a
lot of it misleads: a paper quoted in part, a number lifted out of context, a statement made up around a study. `/ask`
is his guardian: find where a claim really comes from, whether the research is any good, whether it even applies to
him (age, Hep B, lifestyle), and **keep every check in the knowledge base** so his picture keeps getting more complete.
See [[ask-myth-buster]].

Darren sends `/ask <text or link>` (or voice) to the bot. The Worker parks it in R2 (`healthgo-asks`,
`pending/<message id>.json`) and replies "收到". This session answers. It runs for hours: keep its context lean, never
re-read a file already in context, and let workers read transcripts, pages and abstracts.

Split (`CLAUDE.md` → Model split): **Opus (this thread) judges and writes.** Sections 3–4 are decisions about his
plan. **Scripts fetch** (`healthgo transcript`, `healthgo pubmed`, no tokens). **`health-research` (Sonnet) reads.**
If this session isn't Opus, hand steps 3–6 to a `general-purpose` agent with `model: opus`.

## Start: arm the monitor

```
Monitor  command: cd /Users/darrenhung/Projects/storium/healthgo && uv run healthgo ask watch --interval 10
         description: Telegram /ask questions     timeout_ms: 1800000
```

Each stdout line is one JSON event:
- `{"event":"ask","id":…,"asked_at":…,"text":…,"has_file":…}`: a question. Already-pending ones print on start.
- `{"event":"error","type":…}`: polling failed (one line per streak). Wait for `recovered`; if none comes within a few
  minutes, run `uv run healthgo ask list` once and say what failed. Never print tokens.
- `{"event":"recovered"}`: nothing to do.

**The monitor expires after 30 min. Re-arm it immediately, every time, with the same call**, until Darren says stop.
A re-armed watcher re-prints still-pending questions: skip any id you are already answering. Say once at the start:
"監看中，每 10 秒檢查一次 /ask". One question at a time, oldest first.

## For each question

### 1. What kind of input (Opus)

- **YouTube link** (`youtube.com`, `youtu.be`, shorts): `uv run healthgo transcript '<url>' --out
  data/asks/pulls/<id>-source.md`. It writes title, channel, upload date, description (where creators list their
  "references") and the caption transcript with [mm:ss] marks, and prints a JSON line (`captions: null` means no
  captions: say so, and work from the title and description only). **Don't open the file yourself**; step 3's
  extractor reads it.
- **Other link**: the extractor WebFetches it.
- **Plain text**: the claim is the text. Restate it in one line; if ambiguous, take the likeliest reading and say so
  in the answer (he can `/ask` again).
- **Urgent symptoms** (chest pain, fainting, yellow eyes/skin, black stool, vomiting blood, severe right-side
  abdominal pain): skip all of this and answer at once: GP / ED now (Australia 000). Hep B makes liver signs urgent.
- `has_file: true`: a photo came with it. Opus never opens images; if the text can't stand alone, `health-ops`
  downloads it (`inbox.download_file(file_id)`, file_id from `uv run healthgo ask list`) and describes it.

### 2. Already checked? (Opus, cheap)

`grep -i` 2–3 keywords (中文 and English) in `research/claims/README.md` and `research/claims/sources.md`, and look at
the `MEMORY.md` index (already in context) for matching `evidence-*` files. A source already in `sources.md` tells you
its usual flaw. A claim checked < ~2 years ago: answer from that file (open it), add only what is new, and skip the
research. Evidence files that settle a claim with [V] citations also need no new pull.

### 3. Research: `health-research` agents (Sonnet)

**3a. Extract** (only for a video or web page). One agent, brief:

> CLAIM EXTRACTION, ad-hoc /ask, not a sector review. Source: `data/asks/pulls/<id>-source.md` (YouTube transcript;
> read it whole) | <url> (WebFetch it). Darren: 36-y-old Taiwanese man in Perth, 177 cm ~89 kg, cutting toward
> 15–18 % body fat, lifts 5×/wk + treadmill, Hep B on entecavir, no new supplements without his doctor.
> Return ≤ 30 lines: SOURCE (who, credentials, what they sell or promote, upload date) · REFERENCES they cite (papers,
> books, studies, with timestamps) · CLAIMS: up to 8 factual health claims, each one line with its [mm:ss], ranked by
> how much it could change what Darren does, marked CHECKABLE or OPINION. Skip motivational filler. Don't research yet.

Opus picks **≤ 4** claims that matter and are checkable (the rest get one line in the answer: "未查：…").

**3b. Check** one agent **per claim, in parallel** (one message), brief:

> CLAIM CHECK, ad-hoc /ask, not a sector review. Claim: "<one line>" — made by <source>, who cites: <references or
> "nothing">. Darren: <same one-liner as above>. Already in his knowledge base: <evidence files, or none>; don't
> re-derive those.
> 1. ORIGIN: find the paper(s) the claim really comes from (their cited one first; else the likeliest), with WebSearch,
>    WebFetch and PubMed. What did it actually test: humans or animals/cells, who (age, sex, health, trained?), n,
>    duration, outcome (hard outcome or a marker), effect size with CI, relative vs absolute risk, funding.
> 2. DISTORTION: what the claim says that the paper doesn't: cherry-picked, animal→human, marker→outcome, relative
>    risk sold as absolute, dose way off, a different population, correlation as cause, retracted, outdated.
> 3. WIDER EVIDENCE: `uv run healthgo pubmed --query '<q>' [--query …] --since <10 years ago> --out
>    data/asks/pulls/<id>-<n>.md` (2–4 queries). Read only the index, open ≤ 8 abstracts. Meta-analyses of RCTs first.
> 4. FIT TO DARREN: does the evidence cover someone like him (age 36, Asian, male, lifting, in a calorie deficit,
>    Hep B on entecavir)? Any reason it would differ for him or be unsafe (liver!)?
> Return ≤ 35 lines: ORIGIN · WHAT THE PAPER REALLY SHOWED · DISTORTION · WIDER EVIDENCE (PMID, type, n, effect + CI,
> year, flags) · VERDICT (✅ supported / 🟡 partly or exaggerated / ❌ misleading or wrong / ❓ unknown) + strength ·
> FIT TO DARREN · PMIDs and links. Never edit memory, config or reports.

A plain-text claim skips 3a and goes straight to one 3b agent.

### 4. Write the record (Opus)

File: `research/claims/<YYYY-MM-DD>-<slug>.md` (Perth date, short English slug). It is both the Telegram answer and
the permanent record, so write it once, in **繁體中文** with English terms in brackets, phone-sized, no tables.
About **800–1,200 characters per claim**; it may span several Telegram messages for a video.

```markdown
# <claim, or the video title>

來源：<channel / site / person> · <link> · <date>
**總評：** <✅/🟡/❌/❓> <one sentence: what is true, what is hype, what to do>

## <✅/🟡/❌/❓> 主張：<claim in one line>（<mm:ss>）
**1. 出處：** <the paper it really comes from: who, year, journal, PMID; or "找不到出處">
**2. 科學證據：** <what that paper actually tested (人/動物, who, n, how long, which outcome) and what the wider
evidence says, graded 統合分析 / RCT / 觀察性 / 動物>
- **被扭曲的地方：** <the distortion, plainly>
**3. 對你的影響：** <against his real plan and situation: 2,520 kcal cut, 5-day split + treadmill, Hep B on entecavir,
age 36. Does the evidence even cover someone like him? Or "不影響你現在的計畫" and why>
**4. 值不值得做：** **<值得試 / 不必 / 先問醫生 / 你已經在做>**，因為 <why>。<if worth it: the smallest concrete step
that fits his routine>

（repeat the block per claim）

未查：<other claims from the source, one line each, or omit>
**記住這句：** <one line he can say next time someone repeats it>
參考：PMID … · <links>
```

Non-negotiable:
- **Safety limits** (`safety-limits.md`) bound every suggestion.
- **A new supplement, a fast, or anything liver-related is only "先問醫生"** (Hep B, entecavir). Never "try it".
- **No new tracking chores.**
- **Propose, never change the plan**: don't edit `config/plan.json`, `safety-limits.md` or the diet/training memories
  from here. If adopting it would change his plan: "要採用的話，下次 /review 跟我說".
- Grade honestly: weak or missing evidence is said plainly, and so is a claim that turns out true.

### 5. File it in the knowledge base (Opus) — every time

1. **Index row** at the end of `research/claims/README.md`: `| date | claim (short) | verdict | source | file |`, one
   row per claim checked.
2. **`research/claims/sources.md`**: add the source or update its counts and its Pattern (the habitual flaw).
3. **Evidence files**, only when the check adds real evidence on a topic his plan or the knowledge base already covers
   (or is likely to come back to): rewrite the matching `evidence-*.md` row in place, or create a new evidence file
   (≤ ~50 lines, `sector:` tag, [V]/[M] tags, a `MEMORY.md` pointer line, a row in `research/README.md`), following
   `/knowledge-review`'s lean rule. One `research/<sector>/CHANGELOG.md` line per change.

### 6. Send and commit

`uv run healthgo ask answer <id> research/claims/<file>.md` sends it threaded under his question, marks it done in R2,
and commits + pushes `research/`, `.claude/memory/` and `data/asks/`. JSON out: `telegram: false` means nothing was
marked: retry once, then tell Darren here. `done: false` means sent but still pending: check `uv run healthgo ask
list` and never send twice.

Then `rm data/asks/pulls/<id>*`, one line here (id, verdicts, sent), and back to waiting.
