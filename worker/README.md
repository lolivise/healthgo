# healthgo-inbox

Cloudflare Worker + D1. Telegram webhook -> D1 `entries`; the Mac pulls with `uv run healthgo inbox`
(also part of `healthgo daily`). Photos stay on Telegram (file_id only); no R2.

## Setup

1. `cd worker && npm install && npx wrangler login`
2. `npx wrangler d1 create healthgo-inbox`, then paste the printed `database_id` into `wrangler.toml`.
3. In 1Password `HealthGo/secrets` add section `INBOX` with fields `WEBHOOK_SECRET` and `PULL_TOKEN`
   (long random strings; letters and digits only, since Telegram limits the secret to `A-Za-z0-9_-`).
   `TELEGRAM/BOT_TOKEN` and `TELEGRAM/CHAT_ID` already exist.
4. `./deploy.sh https://healthgo-inbox.<your-subdomain>.workers.dev` (the URL wrangler prints on first deploy;
   run it once to learn the URL, then again). It sets the secrets, deploys, applies `schema.sql`, sets the webhook.
5. Put that URL in `config/plan.json` as `inbox_url`.

## Use

Send `/eat ...`, `/inbody` + photo, `/weight`, `/blood`, `/note` (or plain text) to the bot; `/help` lists them.
`uv run healthgo inbox --list` shows pending items; `--done <id>...` moves them to `data/inbox/done/`.
