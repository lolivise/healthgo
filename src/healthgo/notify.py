"""Telegram alerts (bot creds in 1Password HealthGo/secrets), macOS notification as fallback."""

from __future__ import annotations

import json
import logging
import re
import subprocess
import urllib.request
from datetime import date
from pathlib import Path

from . import config, store, vault

log = logging.getLogger(__name__)


def _macos(text: str) -> None:
    script = f"display notification {json.dumps(text)} with title \"healthgo\""
    subprocess.run(["osascript", "-e", script], capture_output=True, timeout=10)


def send(text: str) -> bool:
    """Send to Telegram; fall back to a macOS notification. Returns True if Telegram worked."""
    if _telegram(text):
        return True
    _macos(text)
    return False


TELEGRAM_LIMIT = 4000  # the API caps a message at 4096 chars


def _plain(md: str) -> str:
    """Markdown report → plain text that reads well in Telegram (no parse_mode, so nothing can fail to parse)."""
    out = []
    for line in md.splitlines():
        s = line.rstrip()
        if re.fullmatch(r"\|?[\s:|-]+\|?", s) and "-" in s:  # table separator row
            continue
        if s.startswith("|"):
            s = " · ".join(c.strip() for c in s.strip("|").split("|"))
        elif s.startswith("# "):
            s = "📊 " + s[2:]
        elif s.startswith("## "):
            s = "\n▍" + s[3:]
        elif s.startswith("### "):
            s = "▸ " + s[4:]
        elif s.strip() == "---":
            s = "────────"
        s = s.replace("**", "").replace("`", "")
        out.append(s)
    return re.sub(r"\n{3,}", "\n\n", "\n".join(out)).strip()


def _chunks(text: str, limit: int = TELEGRAM_LIMIT) -> list[str]:
    parts, cur = [], ""
    for line in text.split("\n"):
        while len(line) > limit:  # a single overlong line: hard-split it
            if cur:
                parts.append(cur)
                cur = ""
            parts.append(line[:limit])
            line = line[limit:]
        if len(cur) + len(line) + 1 > limit:
            parts.append(cur)
            cur = line
        else:
            cur = f"{cur}\n{line}" if cur else line
    if cur:
        parts.append(cur)
    return parts


def send_report(path: Path) -> bool:
    """Send a review report to Telegram in full, split into messages under the API limit."""
    parts = _chunks(_plain(path.read_text()))
    for i, part in enumerate(parts, 1):
        if not _telegram(part if len(parts) == 1 else f"{part}\n\n（{i}/{len(parts)}）"):
            _macos(f"週報 {path.name} 傳到 Telegram 失敗（{i}/{len(parts)}）")
            return False
    return True


def _telegram(text: str) -> bool:
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
                log.info("Telegram sent: %s", text.splitlines()[0][:60])
                return True
            log.warning("Telegram replied ok=false")
    except Exception as e:  # never let a notification failure break the sync
        # the bot token is part of the URL, so log the type only
        log.warning("Telegram send failed (%s)", type(e).__name__)
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
