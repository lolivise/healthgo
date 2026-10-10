# healthgo

Darren's personal health brain: it pulls his Garmin Connect data every evening, watches for recovery
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
| Execution: sync, backfill, recording entries, commits, troubleshooting commands | **Sonnet** | `health-ops` agent |
| **Reading blood-report images**: extracting the values | **Sonnet** | `health-ops` agent, given the file path. Opus never opens images |
| **Reading meal photos** (eating-out kcal estimate) | **Haiku** | `health-ops` spawned with `model: "haiku"` |
| Voice notes | Workers AI Whisper | transcribed in the Worker; the text is handled like any note |
| Information gathering: running prep, querying the DB, building the numeric digest | **Sonnet** | `health-data` agent |
| Report writing: the 繁中 report from a decided verdict | **Sonnet** | `health-writer` agent |
| **Analysis and decisions**: the verdict, diet or training changes, whether to force a login, plan or target changes, memory updates | **Opus** | the main conversation |

- The agents are defined in `.claude/agents/`, pinned with `model: sonnet`. Every brief to them must be
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
| `src/healthgo/` | Python CLI (`uv run healthgo …`): `sync`, `daily`, `check`, `prepare-week`, `add`, `status`, `build-db`, `inbox`, `login`, `notify-test`, `install-launchd` |
| `data/garmin/daily/YYYY/DATE.json` | Raw Garmin responses for one day: summary, sleep, HRV, stress, Body Battery, RHR, weigh-ins, … |
| `data/garmin/activities/YYYY-MM/DATE_ID/` | `summary.json`, `sets.json` (strength), `activity.fit` |
| `data/manual/*.jsonl` | Things Garmin never sees (`inbody` is history only, see below): `eating_out`, `bloodwork`, `weight` (seed), `reviews`, `notes` |
| `data/inbox/` | Telegram bot entries pulled from the Cloudflare Worker (`worker/`), pending until recorded; recorded ones move to `data/inbox/done/` |
| `data/weekly/YYYY-Www.json` | Numbers prepared on Sunday 20:30 for `/review` |
| `data/state.json` | Sync bookkeeping: `complete_through`, login guard, alert de-duplication |
| `data/healthgo.db` | SQLite built from the JSON (git-ignored). Query with `sqlite3 -header -column data/healthgo.db` |
| `reports/YYYY-Www.md` | Weekly reviews (繁中) |
| `config/plan.json` | Targets, trip dates, safety and alert thresholds |
| `bin/healthgo-job` | launchd entry point → `healthgo daily` |
| `.claude/agents/` | Sonnet workers: `health-data`, `health-ops`, `health-writer` (see Model split) |

**Database tables:** `daily`, `weights`, `activities`, `sets` (with `e1rm_kg`), `inbody` (history: one scan, 2026-09-27), `eating_out`,
`bloodwork`, `reviews`, `notes`; view `strength_top`.

## Automation

One launchd agent, `com.healthgo.daily`, runs daily at 20:00, Sundays at 20:30, and at login. Each run:
1. Catch-up sync of every date since `complete_through`, minus a 3-day overlap.
2. Pull the Telegram inbox (`healthgo inbox`); a failure is only a warning.
3. Rebuild the database.
4. Rule-based checks, with a Telegram alert, de-duplicated over 3 days and silenced during the trip.
5. If a Sunday 20:30 has passed without a weekly file: prepare it and send a Telegram ping to run `/review`.
6. Commit and push `data/`.

Logs go to `~/Library/Logs/healthgo/daily.log`. Garmin login is capped at one credential attempt per 24h.

## Skills

- `/review`: the weekly (or any-time) review. Sync, ask about eating out, verdict, 繁中 report, commit.
- `/log`: record eating out (text or meal photo), bloodwork, a manual weight, or a note.
- `/sync`: manual sync or backfill, status, and troubleshooting Garmin login, 429s, launchd and the library pin.
