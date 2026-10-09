"""Telegram alerts (bot creds in 1Password HealthGo/secrets), macOS notification as fallback."""

from __future__ import annotations

import json
import logging
import subprocess
import urllib.request
from datetime import date

from . import config, store, vault

log = logging.getLogger(__name__)


def _macos(text: str) -> None:
    script = f"display notification {json.dumps(text)} with title \"healthgo\""
    subprocess.run(["osascript", "-e", script], capture_output=True, timeout=10)


def send(text: str) -> bool:
    """Send to Telegram; fall back to a macOS notification. Returns True if Telegram worked."""
    try:
        token = vault.read("TELEGRAM/BOT_TOKEN")
        chat_id = vault.read("TELEGRAM/CHAT_ID")
        body = json.dumps({"chat_id": chat_id, "text": text}).encode()
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{token}/sendMessage",
            data=body, headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=20) as resp:
            if json.load(resp).get("ok"):
                return True
    except Exception as e:  # never let a notification failure break the sync
        # the bot token is part of the URL, so log the type only
        log.warning("Telegram send failed (%s); using macOS notification", type(e).__name__)
    _macos(text)
    return False


def alert_once(state: dict, key: str, text: str, today: date | None = None) -> bool:
    """Send an alert unless the same key was sent within `resend_after_days`."""
    today = today or config.today()
    sent = state.setdefault("alerts_sent", {})
    last = sent.get(key)
    if last and (today - date.fromisoformat(last)).days < config.plan()["alerts"]["resend_after_days"]:
        return False
    send(text)
    sent[key] = today.isoformat()
    store.save_state(state)
    return True
