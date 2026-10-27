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


INDENT = "  "  # em spaces: Telegram keeps them, so nested bullets stay indented on a phone


def _inline(s: str) -> str:
    """Escape for Telegram HTML, then **bold** → <b>, `code` → plain."""
    s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    return s.replace("**", "").replace("`", "")


def _cells(row: str) -> list[str]:
    return [c.strip() for c in row.strip().strip("|").split("|")]


def _table(rows: list[str]) -> list[str]:
    """A Markdown table is unreadable at ~350 px, so each row becomes a bullet.

    ≤3 columns: one line, `• label：value（header3 value3）`.
    More columns: the label line, then one indented line per cell, `◦ header：value`.
    """
    head, body = _cells(rows[0]), [_cells(r) for r in rows[1:]]
    out = []
    for cells in body:
        label, rest = cells[0], cells[1:]
        if len(cells) <= 3:
            line = f"• <b>{_inline(label)}</b>：{_inline(rest[0])}" if label else f"• {_inline(rest[0])}"
            if len(rest) > 1 and rest[1]:
                line += f"（{_inline(head[2])} {_inline(rest[1])}）"
            out.append(line)
            continue
        out.append(f"• <b>{_inline(label)}</b>")
        for h, c in zip(head[1:], rest):
            if c:
                out.append(f"{INDENT}◦ {_inline(h)}：{_inline(c)}" if h else f"{INDENT}◦ {_inline(c)}")
    return out


def _telegram_html(md: str, icon: str = "📊") -> str:
    """Markdown report → Telegram HTML laid out for a phone: bold headings, bullets, indented sub-points."""
    out: list[str] = []
    lines = md.splitlines()
    i = 0
    while i < len(lines):
        s = lines[i].rstrip()
        if s.lstrip().startswith("|"):
            rows = []
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                if not re.fullmatch(r"\s*\|?[\s:|-]+\|?\s*", lines[i]):  # skip the separator row
                    rows.append(lines[i])
                i += 1
            out.extend(_table(rows) if len(rows) > 1 else [_inline(" · ".join(_cells(rows[0])))])
            continue
        i += 1
        indent = len(s) - len(s.lstrip())
        t = s.strip()
        if t.startswith("# "):
            out.append(f"<b>{icon} {_inline(t[2:])}</b>")
        elif t.startswith("## "):
            out += ["", f"<b>▍{_inline(t[3:])}</b>"]
        elif t.startswith("### "):
            out += ["", f"<b>▸ {_inline(t[4:])}</b>"]
        elif t == "---":
            out.append("────────────")
        elif re.match(r"[-*] ", t):
            out.append(f"{INDENT * (indent // 2)}{'◦' if indent else '•'} {_inline(t[2:])}")
        elif indent and re.match(r"\d+\. ", t):
            out.append(f"{INDENT * (indent // 2)}{_inline(t)}")
        elif re.match(r"\d+\. ", t):
            out += ["", _inline(t)]  # numbered reasons get breathing room
        else:
            out.append(_inline(t))
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


def send_report(path: Path, reply_to: int | None = None, icon: str = "📊") -> bool:
    """Send a review report (or an /ask answer, threaded under the question) to Telegram in full,
    split into messages under the API limit."""
    parts = _chunks(_telegram_html(path.read_text(), icon))
    for i, part in enumerate(parts, 1):
        text = part if len(parts) == 1 else f"{part}\n\n（{i}/{len(parts)}）"
        to = reply_to if i == 1 else None
        # if Telegram rejects the HTML, the same text without tags still beats nothing
        if not (_telegram(text, html=True, reply_to=to) or _telegram(re.sub(r"</?b>", "", text)
                                                                     .replace("&lt;", "<").replace("&gt;", ">")
                                                                     .replace("&amp;", "&"), reply_to=to)):
            _macos(f"{path.name} 傳到 Telegram 失敗（{i}/{len(parts)}）")
            return False
    return True


def _telegram(text: str, html: bool = False, reply_to: int | None = None) -> bool:
    try:
        token = vault.read("TELEGRAM/BOT_TOKEN")
        chat_id = vault.read("TELEGRAM/CHAT_ID")
        msg = {"chat_id": chat_id, "text": text}
        if html:
            msg["parse_mode"] = "HTML"
        if reply_to:
            msg["reply_parameters"] = {"message_id": reply_to, "allow_sending_without_reply": True}
        body = json.dumps(msg).encode()
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
