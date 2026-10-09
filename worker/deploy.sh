#!/usr/bin/env bash
# Deploy the inbox worker: push secrets, deploy, apply schema, register the Telegram webhook.
# Usage: ./deploy.sh https://healthgo-inbox.<subdomain>.workers.dev   (or WORKER_URL=...)
# Never prints secret values.
set -euo pipefail
cd "$(dirname "$0")"

WORKER_URL="${1:-${WORKER_URL:-}}"
WORKER_URL="${WORKER_URL%/}"
[[ -n "$WORKER_URL" ]] || { echo "usage: ./deploy.sh <worker url>" >&2; exit 2; }

# Same source as src/healthgo/vault.py: env var, else the export line in ~/.zshrc.
TOKEN="${HEALTHGO_OP_SERVICE_ACCOUNT_TOKEN:-}"
if [[ -z "$TOKEN" && -f "$HOME/.zshrc" ]]; then
  TOKEN="$(sed -nE "s/^[[:space:]]*export[[:space:]]+HEALTHGO_OP_SERVICE_ACCOUNT_TOKEN=[\"']?([^\"'[:space:]]+)[\"']?[[:space:]]*$/\1/p" "$HOME/.zshrc" | tail -1)"
fi
[[ -n "$TOKEN" ]] || { echo "HEALTHGO_OP_SERVICE_ACCOUNT_TOKEN not set and not in ~/.zshrc" >&2; exit 1; }
export OP_SERVICE_ACCOUNT_TOKEN="$TOKEN"
unset TOKEN

op_read() { op read --no-newline "op://HealthGo/secrets/$1"; }

put_secret() { # NAME SECTION/FIELD
  op_read "$2" | npx wrangler secret put "$1" >/dev/null
  echo "secret $1 set"
}

put_secret BOT_TOKEN TELEGRAM/BOT_TOKEN
put_secret CHAT_ID TELEGRAM/CHAT_ID
put_secret WEBHOOK_SECRET INBOX/WEBHOOK_SECRET
put_secret PULL_TOKEN INBOX/PULL_TOKEN

npx wrangler deploy
npx wrangler d1 execute healthgo-inbox --remote --file schema.sql

# curl reads its config from stdin, so the token and secret never show in `ps`.
# Both values are used only inside this subshell.
BOT_TOKEN="$(op_read TELEGRAM/BOT_TOKEN)"
WEBHOOK_SECRET="$(op_read INBOX/WEBHOOK_SECRET)"
printf 'url = "https://api.telegram.org/bot%s/setWebhook"\ndata-urlencode = "url=%s/telegram"\ndata-urlencode = "secret_token=%s"\ndata-urlencode = "allowed_updates=[\\"message\\"]"\n' \
  "$BOT_TOKEN" "$WORKER_URL" "$WEBHOOK_SECRET" | curl -sS -K - | python3 -c 'import json,sys; d=json.load(sys.stdin); print("setWebhook ok:", d.get("ok"), d.get("description", ""))'

printf 'url = "https://api.telegram.org/bot%s/getWebhookInfo"\n' "$BOT_TOKEN" | curl -sS -K - \
  | python3 -c 'import json,sys; r=json.load(sys.stdin).get("result", {}); [print(k+":", r.get(k)) for k in ("url","pending_update_count","last_error_date","last_error_message","allowed_updates")]'

# The command menu (the "/" button in the chat).
CMDS='[{"command":"eat","description":"外食紀錄（文字或照片）"},{"command":"inbody","description":"InBody 結果照片"},{"command":"weight","description":"手動體重"},{"command":"blood","description":"驗血結果"},{"command":"note","description":"其他備註"},{"command":"cancel","description":"取消"},{"command":"help","description":"指令說明"}]'
printf 'url = "https://api.telegram.org/bot%s/setMyCommands"\ndata-urlencode = "commands=%s"\n' \
  "$BOT_TOKEN" "${CMDS//\"/\\\"}" | curl -sS -K - | python3 -c 'import json,sys; d=json.load(sys.stdin); print("setMyCommands ok:", d.get("ok"), d.get("description", ""))'
