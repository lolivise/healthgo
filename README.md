# healthgo

My health brain: Garmin Connect → this repo whenever I review, and a review with Claude that tells me
whether to keep cutting.

## How it works

- **No schedule.** Nothing runs on its own (the evening launchd job was removed 2026-10-12).
- **`/review` in Claude Code** (in this folder), any day: pulls every missing day from Garmin plus the
  Telegram inbox (`healthgo pull`), runs the recovery checks, asks for eating-out days, gives the verdict,
  writes `reports/YYYY-Www.md` in 繁體中文 and sends it to Telegram.
- **`/log`:** eating out, blood test, notes. **`/sync`:** fix things.

## Setup (done 2026-10-09)

1. 1Password vault `HealthGo`, item `secrets` with `GARMIN/USERNAME`, `GARMIN/PASSWORD`,
   `TELEGRAM/BOT_TOKEN`, `TELEGRAM/CHAT_ID`. Service-account token exported as
   `HEALTHGO_OP_SERVICE_ACCOUNT_TOKEN` in `~/.zshrc`.
2. `uv sync`
3. `uv run healthgo login`: first Garmin login; the token goes to `~/.garminconnect/`.
4. `uv run healthgo sync`: backfill from 2026-07-01.
5. `uv run healthgo notify-test`
6. ~~`uv run healthgo install-launchd`~~ removed 2026-10-12; run it again to bring the evening job back.

## Everyday commands

```bash
uv run healthgo status        # what's synced, last login, last review
uv run healthgo pull          # catch up now: Garmin + inbox + menu, flags, commit & push
uv run healthgo check         # today's recovery flags
sqlite3 -header -column data/healthgo.db "SELECT * FROM daily ORDER BY date DESC LIMIT 7"
```

The project instructions for Claude are in `CLAUDE.md`, and its memory is in `.claude/memory/`.
