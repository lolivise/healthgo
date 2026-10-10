# healthgo

My health brain: Garmin Connect → this repo every evening, red-flag alerts on Telegram, and a weekly
review with Claude that tells me whether to keep cutting.

## How it works

- **20:00 every day** (and at login, to catch up after the Mac was off): pull every missing day from
  Garmin, run recovery checks, alert on Telegram only if something is off, commit and push.
- **Sunday 20:30:** prepare the week's numbers → Telegram: "run /review".
- **`/review` in Claude Code** (in this folder): asks for eating-out days, gives the verdict,
  writes `reports/YYYY-Www.md` in 繁體中文.
- **`/log`:** eating out, blood test, notes. **`/sync`:** fix things.

## Setup (done 2026-10-09)

1. 1Password vault `HealthGo`, item `secrets` with `GARMIN/USERNAME`, `GARMIN/PASSWORD`,
   `TELEGRAM/BOT_TOKEN`, `TELEGRAM/CHAT_ID`. Service-account token exported as
   `HEALTHGO_OP_SERVICE_ACCOUNT_TOKEN` in `~/.zshrc`.
2. `uv sync`
3. `uv run healthgo login`: first Garmin login; the token goes to `~/.garminconnect/`.
4. `uv run healthgo sync`: backfill from 2026-07-01.
5. `uv run healthgo notify-test`
6. `uv run healthgo install-launchd`

## Everyday commands

```bash
uv run healthgo status        # what's synced, last login, last review
uv run healthgo sync          # catch up now
uv run healthgo check         # today's recovery flags
sqlite3 -header -column data/healthgo.db "SELECT * FROM daily ORDER BY date DESC LIMIT 7"
```

The project instructions for Claude are in `CLAUDE.md`, and its memory is in `.claude/memory/`.
