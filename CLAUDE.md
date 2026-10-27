# healthgo

Darren's personal health brain: it pulls his Garmin Connect data whenever he runs `/review`, watches for recovery
red flags, and runs a weekly review that decides whether to **keep cutting, slow down, take a diet
break, or adjust intake**. It is for him only, lives in a private repo, and has a single branch.

## Memory lives in this repo, not in `~/.claude`

**Agent memory for this project is `.claude/memory/`, committed here.** Read `.claude/memory/MEMORY.md`
at the start of any health conversation. It holds his goal, diet, health conditions, safety limits and
review preferences. Write new durable facts there (one fact per file, frontmatter as in the existing
files, plus a pointer line in `MEMORY.md`), not in the global auto-memory directory. Update a file
rather than duplicating it, and delete memories that turn out to be wrong.

`config/plan.json` is the machine-readable twin of the plan in memory (dates, targets, safety
thresholds). **Change both together.**

## Non-negotiables

- **Safety limits** (`.claude/memory/safety-limits.md`) bound every recommendation. Hep B means no new
  supplements and a doctor referral for anything liver-related.
- **Reports and advice are in Traditional Chinese (繁體中文)**, with English technical terms in brackets.
- **Don't add tracking chores.** He rejected waist and photo tracking. Read Garmin data, and only ask
  questions inside a review he started (eating out since the last review).
- **Never print secret values.** Credentials live in 1Password `HealthGo/secrets`; the Garmin token
  lives in `~/.garminconnect/`.

## Model split: Sonnet executes, Opus decides

Darren's standing rule (2026-10-09), for token efficiency:

| Work | Who | How |
|---|---|---|
| **Pulling Garmin data**: routine sync, re-pull a range, status, build-db | **Haiku** | `health-ops` spawned with `model: "haiku"` (Darren, 2026-10-10) |
| Execution: recording entries, commits, troubleshooting (login failures, 429s, launchd, library bump) | **Sonnet** | `health-ops` agent |
| **Reading blood-report images**: extracting the values | **Sonnet** | `health-ops` agent, given the file path. Opus never opens images |
| **Reading meal photos** (eating-out kcal estimate) | **Haiku** | `health-ops` spawned with `model: "haiku"` |
| Voice notes | Workers AI Whisper | transcribed in the Worker; the text is handled like any note |
| Information gathering: Garmin sync, running prep, querying the DB, building the numeric digest | **Haiku** | `health-data` agent (pinned `model: haiku`) |
| Report writing: the 繁中 report from a decided verdict | **Sonnet** | `health-writer` agent |
| **Research pulls** (quarterly `/knowledge-review`) | **no model** | `healthgo pubmed`, a script (Darren, 2026-10-26: data pulling never on Opus) |
| **Screening research** against the evidence memories | **Sonnet** | `health-research` agent, one per sector, reads the title index and only the abstracts it picks |
| **`/ask` myth-buster**: transcript, PubMed pulls, Telegram progress card, filing + sending + commit | **no model** | `healthgo transcript` (yt-dlp via uvx), `healthgo pubmed --query`, `healthgo ask status`, `healthgo ask file` |
| **`/ask`**: intake + claim list, per-claim source check | **Sonnet** | `ask-intake`, `ask-check` (parallel) |
| **`/ask`**: verdicts, impact on his plan, worth it, the 繁中 record, evidence edits | **Opus** | `ask-judge` sub-agent (pinned `model: opus`). The long-running main thread only dispatches: one-line briefs, one-line returns, never opens files |
| **Analysis and decisions**: the verdict, diet or training changes, whether to force a login, plan or target changes, memory updates | **Opus** | the main conversation |

- The agents are defined in `.claude/agents/`, pinned with `model: sonnet` (except `health-data` on Haiku and `ask-judge` on Opus). Every brief to them must be
  self-contained, because they don't see this conversation.
- **The main thread does not read raw Garmin JSON or dump query tables into its own context.** It reads the
  digest an agent returns. It may run a quick one-line command whose short output it needs to see.
- **Decisions never move to Sonnet.** If the main session is not running Opus, hand the decision step
  to a `general-purpose` agent with `model: opus`, passing it the digest and memory paths.
- Agents never delegate further: delegation is one level deep.

## Git: commit and push straight to `main`, no asking

A standing exemption for this repo (see `.claude/memory/git-policy.md`). Commit and push as part of
finishing any change, then report what landed. **Never** force-push, `reset --hard`, `rebase`, `--amend`,
`tag` or `stash drop` without an explicit ask. Everything is committed except the derived
`data/healthgo.db`.

## No InBody anymore

His gym removed its InBody machine (2026-10-10), so no new scans will ever exist. The one scan (2026-09-27: 91.4 kg,
25.5 %) stays in `data/manual/inbody.jsonl` and the `inbody` table as history only. Body-fat % is no longer measured:
progress toward the 15-18 % goal is estimated from the weight trend, assuming lean mass of about 68 kg
(15-18 % is roughly 80-83 kg), a rough estimate. Data sources now: Garmin (incl. strength sets, sleep, HRV), weight,
eating out, and `/feel` + notes via Telegram.

## Layout

| Path | What |
|---|---|
| `src/healthgo/` | Python CLI (`uv run healthgo …`): `pull`, `sync`, `daily` (old job), `check`, `review-plan`, `prepare-week`, `add`, `status`, `build-db`, `inbox`, `login`, `notify-test`, `send-report`, `install-launchd`, `pubmed`, `ask`, `transcript` |
| `data/garmin/daily/YYYY/DATE.json` | Raw Garmin responses for one day: summary, sleep, HRV, stress, Body Battery, RHR, weigh-ins, … |
| `data/garmin/activities/YYYY-MM/DATE_ID/` | `summary.json`, `sets.json` (strength), `activity.fit` |
| `data/manual/*.jsonl` | Things Garmin never sees (`inbody` is history only, see below): `eating_out`, `bloodwork`, `weight` (seed), `reviews`, `notes` |
| `research/claims/` | `/ask` myth-buster records (繁中), one per source, = the Telegram answer; `README.md` index, `sources.md` track record per channel/site |
| `data/asks/pulls/` | `/ask` working files (transcripts, PubMed pulls), git-ignored |
| `data/inbox/` | Telegram bot entries pulled from the Cloudflare Worker (`worker/`), pending until recorded; recorded ones move to `data/inbox/done/` |
| `data/weekly/YYYY-Www.json` | Numbers prepared by `/review` (`prepare-week`) |
| `data/state.json` | Sync bookkeeping: `complete_through`, login guard, alert de-duplication |
| `data/healthgo.db` | SQLite built from the JSON (git-ignored). Query with `sqlite3 -header -column data/healthgo.db` |
| `reports/YYYY-Www.md` | Weekly reviews (繁中) |
| `config/plan.json` | Targets, trip dates, events, safety and alert thresholds, strength baseline + excluded sessions, lean-mass estimate |
| `config/research.json` | Research sectors: PubMed searches, cadence, `last_reviewed` |
| `research/<sector>/` | Full research reports (繁中) + `notes/`, filed by sector (`fat-loss`, `training`, `medical`, `aging`, `measurement`, `food`, `nutrition`). Index and quarterly-review scope: `research/README.md`. Distilled findings are the `evidence-*` memories, tagged `sector:` |
| `bin/healthgo-job` | old launchd entry point → `healthgo daily` (job removed 2026-10-12) |
| `.claude/agents/` | Workers (`health-data` on Haiku, the rest Sonnet): `health-data`, `health-ops`, `health-writer`, `health-research` (see Model split) |
| `friends/tom/` | Training notes for Darren's friend Tom (T2 diabetes on GLP-1, hunched posture, beginner): profile and safety, 2-day plan, session log. Not part of the pipeline; Darren's own memory and safety limits don't apply to him |

**Database tables:** `daily`, `weights`, `activities`, `sets` (with `e1rm_kg`), `inbody` (history: one scan, 2026-09-27), `eating_out`,
`bloodwork`, `reviews`, `notes`; view `strength_top`.

## Automation

**None scheduled, on purpose.** Darren removed the launchd job on 2026-10-12: data is pulled **on demand when
he runs `/review`**, so he can review any day. `uv run healthgo pull` is that first step:
1. Catch-up sync of every date since `complete_through`, minus a 3-day overlap, and never starting after the day of
   the previous pull (stamped in `state.last_pull`, printed as `previous_pull_at`).
2. Pull the Telegram inbox; a failure is only a warning.
3. Refresh the Cargill menu from the POS and push it to the Worker; a failure is only a warning.
4. Rebuild the database.
5. Rule-based recovery checks, printed (no Telegram alert).
6. Commit and push `data/`.

What the removal gave up: daily red-flag alerts on Telegram, the Sunday "run /review" ping, and the daily menu
refresh. `healthgo daily` and `install-launchd` still exist, so it's one command to bring the job back. Garmin login is
capped at one credential attempt per 24h.

## Skills

- `/review`: the review, any day. Sunday from 18:00 a full week; otherwise mid-week through today; a missed Sunday
  is caught up first. Pull fresh data, ask about eating out, verdict, 繁中 report, commit, send to Telegram.
- `/log`: record eating out (text or meal photo), bloodwork, a manual weight, or a note.
- `/sync`: manual sync or backfill, status, and troubleshooting Garmin login, 429s, launchd and the library pin.
- `/ask`: the myth-buster, a long-running answer desk. A Monitor runs `healthgo ask watch` (polls the Worker every
  10 s). Each Telegram `/ask` (YouTube link → transcript, web page, or a claim he heard) is traced to its source paper,
  graded for study quality and fit to him, answered in 繁中 (出處 · 科學證據 · 對你的影響 · 值不值得做) under the question,
  and filed in `research/claims/` (+ evidence files when it adds real evidence). Questions wait in R2 `healthgo-asks`.
- `/knowledge-review`: every ~3 months, per research sector: script pulls new PubMed papers, Sonnet screens them,
  Opus rewrites the evidence memories in place (lean: current best answer only, changes logged in one line).
