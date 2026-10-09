---
name: garmin-data-access
description: How Garmin data is pulled — python-garminconnect 0.3.17, 1Password HealthGo/secrets, token in ~/.garminconnect, ≤1 login/24h, 429 risk, what his watch does/doesn't record
metadata:
  type: reference
---

- **Library:** `python-garminconnect` (cyberjunky), **pinned 0.3.17** in `pyproject.toml`. `garth` is
  deprecated: Garmin's March 2026 sign-in change broke it. The Garmin Health API is business-only.
  Expect to bump the pin when Garmin breaks login again. The procedure is in `.claude/skills/sync/SKILL.md`.
- **Credentials:** 1Password vault **HealthGo**, item **`secrets`**: `GARMIN/USERNAME`,
  `GARMIN/PASSWORD`, `TELEGRAM/BOT_TOKEN`, `TELEGRAM/CHAT_ID`. Access uses a service account whose token is
  `HEALTHGO_OP_SERVICE_ACCOUNT_TOKEN` in `~/.zshrc`. `healthgo/vault.py` greps that line because
  launchd never sources zshrc. **Never print secret values.**
- **MFA is off** on his Garmin account, which is why unattended re-login works.
- **Token:** `~/.garminconnect/garmin_tokens.json` (0600), outside the repo. It auto-refreshes.
- **Login guard:** at most **one credential login per 24h** (`state.json → last_login_attempt_at`).
  On the first login (2026-10-09) the mobile strategies got **429**, but the web strategy succeeded. Login
  is the fragile point; daily data calls have been fine.
- **Run from home internet, never a VPN.** Cloudflare blocks datacenter and VPN IPs.
- **What his watch records:** steps, kcal, RHR, stress, Body Battery, sleep stages and score, HRV
  status. Strength sets come with exercise, reps and weight. **Not available** (empty responses):
  training readiness, training status, VO2max. Don't build advice on those.
- **Units:** set weights and weigh-ins come in **grams** (`6000.0` = 6 kg). Weigh-ins are
  `sourceType: MANUAL`, typed into the app, not from an Index scale.
- A raw daily file is ~350 KB (sleep and stress time series). This is accepted: "all data lives in the
  repo".

Related: [[git-policy]]
