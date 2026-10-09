---
name: sync
description: Operate and troubleshoot the healthgo Garmin pipeline — manual catch-up sync or re-pull from a date, check status, fix Garmin login failures / 429 rate limits, test Telegram, (re)install the launchd job, bump the pinned garminconnect version. Trigger on /sync, "sync my Garmin", "the sync failed", "Garmin login failed", Telegram alerts saying run /sync.
---

# /sync

The split follows `CLAUDE.md` → Model split:
- **The `health-ops` agent (Sonnet) runs everything below** and returns facts: status, log excerpts,
  errors, what it ran.
- **The main thread (Opus) decides:** whether to force a login, whether to bump the library, and what to tell
  Darren.

Brief the agent with what Darren reported, and tell it to start with:

```bash
uv run healthgo status
tail -50 ~/Library/Logs/healthgo/daily.log
```

The agent must **not** force a login (`healthgo login`, `--force-login`) unless your brief says
you approved it.

## Normal operations

| Want | Command |
|---|---|
| Catch up now | `uv run healthgo sync` (it commits and pushes `data/` itself) |
| Re-pull a range | `uv run healthgo sync --from 2026-09-01` |
| Rebuild the database only | `uv run healthgo build-db` |
| See today's flags | `uv run healthgo check` |
| Test Telegram | `uv run healthgo notify-test` |
| (Re)install the scheduled job | `uv run healthgo install-launchd` |
| Run the scheduled job now | `launchctl kickstart -k gui/$(id -u)/com.healthgo.daily` |

## Login trouble: read before touching anything

Garmin punishes repeated logins. **One credential attempt per 24h is enforced in code** (`state.json →
last_login_attempt_at`). Don't work around it casually.

1. **`LoginBlocked`**: the guard is working. Wait unless Darren explicitly wants to force it. If he does, run
   `uv run healthgo login` **once**.
2. **429 on login:** don't retry. Garmin may block by client fingerprint for 24h or more. Wait a day. If
   it persists for several days, check the upstream issues
   (github.com/cyberjunky/python-garminconnect/issues) for a fix release and bump the pin (below).
3. **403 or Cloudflare errors on data calls:** usually a VPN or unusual network. The Mac must be on home internet.
4. **Authentication rejected:** the password may have changed. Darren updates `HealthGo/secrets → GARMIN/PASSWORD` in
   1Password, then runs `uv run healthgo login`.
5. **`VaultError`:** `HEALTHGO_OP_SERVICE_ACCOUNT_TOKEN` is missing from `~/.zshrc` or has expired. Test it with
   `uv run python -c "from healthgo import vault; vault.read('GARMIN/USERNAME'); print('ok')"`.
   **Never print the value.**
6. **MFA:** off at setup. If Darren turns it on, unattended re-login stops working, and `healthgo login`
   will prompt for the code in a terminal (`! uv run healthgo login`).

## Bumping garminconnect (when Garmin breaks login)

1. Check the PyPI release notes and upstream issues for the fix.
2. Edit the pin in `pyproject.toml`, then run `uv lock && uv sync`.
3. Tokens from older formats may need one fresh login: `uv run healthgo login`.
4. Run `uv run healthgo sync --no-commit`, inspect a fresh `data/garmin/daily/...json`, then run `build-db`. If field
   names changed, fix `src/healthgo/db.py` (`_daily_row`).
5. Commit and push. Update `.claude/memory/garmin-data-access.md` with the new version and what broke.

## Data-shape changes

If `build-db` produces NULLs where there used to be values, compare a new daily JSON with an older one
and adjust `db.py`. The raw JSON is untouched, so a fixed builder recovers history.
