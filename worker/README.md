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

Send `/eat ...`, `/weight`, `/blood`, `/note` (or plain text) to the bot; `/help` lists them.
`uv run healthgo inbox --list` shows pending items; `--done <id>...` moves them to `data/inbox/done/`.

### Voice messages

Send a Telegram voice note (any kind: caption `/eat`, a pending command, or plain = note). The Worker downloads it
via getFile and transcribes it with Workers AI Whisper (`@cf/openai/whisper-large-v3-turbo`, binding `AI`, with a
繁中 `initial_prompt`), stores the transcript as `text` and echoes it back. At /feel's last question it becomes the
free-text answer. Over 5 min or 20 MB, or on a Whisper error, the entry is stored with empty `text` and
`transcribe_error` in `raw`; `inbox` then downloads the audio as `.oga`. Transcribed voices are not downloaded.
Needs no deploy.sh change (the `[ai]` binding is in wrangler.toml; Workers AI has a free daily allowance).

### /feel

`/feel` starts a tap-to-answer symptom check-in: one bot message edited in place (multi-select toggles with
"完成 ➡️", single-select advances; branches for 頭暈, 餓, 疲勞, 肌肉/關節痛 and the B 肝 check). The last question
accepts a free-text reply within 2 h or "跳過". Any other command, or 2 h of silence, saves a started check-in
as `partial`. It lands as one `feel` entry (negative `tg_message_id`): `text` is a 繁中 summary, `raw` the
structured answers, pulled into `data/inbox/<date>_<id>_feel.json` as `answers`. State lives in the D1
`checkins` table (`schema.sql`); the webhook must allow `callback_query` (`deploy.sh` sets it).

### /eat (Cargill Cafe menu)

`/eat` with no text shows one message, edited in place: 🍱 Cargill 菜單 (category, dish, variant, add-ons, portion) |
🥣 廚房自己配 (components with ½ · 1 · 1½ · 2 · 3 servings) | ⭐ 常吃 (saved favourites, 🗑 to delete) | ✏️ 其他外食
(the old free-text/photo prompt). After a save the receipt has ⭐ 存成常吃, which asks for a name by force-reply
(10 min, else "常吃 N"). Text shortcuts: `/eat 雞排飯`, `/eat 廚房 白飯1 紅燒肉1.5 蛋1` (a trailing number is the
multiplier; add-ons and `½` / `¾` / `¼` tokens work after a dish); voice notes go through the same matcher. If every token
matches uniquely the bot asks to confirm; an ambiguous token shows candidate buttons; a token that matches nothing stores
the text as an ordinary `eat` entry.

The menu lives in the D1 `menu` table, filled by `uv run healthgo menu-push` (also run by `healthgo daily` when the menu
changed; `--force` re-pushes). Flow state is in `eat_sessions` (2 h), favourites in `favourites`. A saved entry is `kind eat`
with a negative `tg_message_id` and `raw` = `{source:"cargill-cafe", mode, items, portion, total, meal, date}`; the Mac pull
records those straight into `data/manual/eating_out.jsonl` (`kcal_basis: "recipe"`). A dish without a recipe saves with no
kcal and stays pending for `/log` to estimate.

Local test: `.dev.vars` (git-ignored) with dummy `BOT_TOKEN`, `CHAT_ID`, `WEBHOOK_SECRET`, `PULL_TOKEN` and `TG_API_BASE`
pointing at a stub server, then `npx wrangler dev --local` and POST updates to `/telegram`.
