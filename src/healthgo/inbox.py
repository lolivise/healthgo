"""Telegram inbox: pull messages the Cloudflare Worker (worker/) stored in D1 into data/inbox/.

Photos stay on Telegram until now: each entry carries a file_id and we download it via getFile.
Transcribed voice notes are not downloaded; a failed transcription (empty text) is, as .oga.
Neither the bot token nor the pull token may reach a log line, so errors log the type only.
"""

from __future__ import annotations

import json
import logging
import shutil
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

from . import config, store, vault

log = logging.getLogger(__name__)

INBOX = config.DATA / "inbox"
DONE = INBOX / "done"
PLACEHOLDER = "REPLACE_AFTER_DEPLOY"
KINDS = {"eat", "feel", "inbody", "weight", "note", "blood"}


class InboxError(RuntimeError):
    pass


def inbox_url() -> str:
    url = (config.plan().get("inbox_url") or "").strip().rstrip("/")
    if not url or PLACEHOLDER in url:
        raise InboxError("inbox_url is not set in config/plan.json (deploy worker/ first, see worker/README.md)")
    return url


def _get(url: str, headers: dict | None = None) -> bytes:
    # Cloudflare rejects the default Python-urllib User-Agent (error 1010)
    req = urllib.request.Request(url, headers={"User-Agent": "healthgo/1.0", **(headers or {})})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def fetch_entries(since_id: int) -> list[dict]:
    url = f"{inbox_url()}/pull?since_id={int(since_id)}"
    body = _get(url, {"Authorization": f"Bearer {vault.read('INBOX/PULL_TOKEN')}"})
    return json.loads(body)["entries"]


def download_file(file_id: str) -> tuple[bytes, str]:
    """Return (content, extension) for a Telegram file_id."""
    token = vault.read("TELEGRAM/BOT_TOKEN")
    q = urllib.parse.urlencode({"file_id": file_id})
    info = json.loads(_get(f"https://api.telegram.org/bot{token}/getFile?{q}"))
    path = info["result"]["file_path"]
    ext = Path(path).suffix or ".jpg"
    return _get(f"https://api.telegram.org/file/bot{token}/{path}"), ext


def stem(entry: dict) -> str:
    # received_at is UTC; file under the local (Mac) date so morning messages land on the right day
    try:
        ts = datetime.fromisoformat((entry.get("received_at") or "").replace("Z", "+00:00"))
        day = ts.astimezone().date().isoformat()
    except ValueError:
        day = "unknown"
    kind = entry.get("kind") if entry.get("kind") in KINDS else "note"
    return f"{day}_{entry['id']}_{kind}"


def is_voice(entry: dict) -> bool:
    """True for a Telegram voice/audio message (raw is the message JSON; feel entries hold answers instead)."""
    try:
        raw = json.loads(entry.get("raw") or "null")
    except ValueError:
        return False
    return isinstance(raw, dict) and bool(raw.get("voice") or raw.get("audio"))


def write_entry(entry: dict) -> Path:
    """Write one entry (and its photo). Raises before the json exists if the download fails,
    so a retry starts clean."""
    name = stem(entry)
    record = {k: v for k, v in entry.items() if k != "raw"}
    if entry.get("kind") == "feel":  # raw holds the structured check-in answers (not a Telegram message)
        try:
            record["answers"] = json.loads(entry.get("raw") or "null")
        except ValueError:
            pass
    voice = is_voice(entry)
    record["voice"] = voice
    # a transcribed voice note needs no audio file; keep it only when transcription failed (empty text)
    if entry.get("file_id") and not (voice and (entry.get("text") or "").strip()):
        content, ext = download_file(entry["file_id"])
        if voice:
            ext = ".oga"
        INBOX.mkdir(parents=True, exist_ok=True)
        (INBOX / f"{name}{ext}").write_bytes(content)
        record["file"] = f"{name}{ext}"
    path = INBOX / f"{name}.json"
    store.write_json(path, record)
    return path


def pull() -> int:
    """Fetch and write new entries; returns how many. last id advances only past written entries."""
    state = store.load_state()
    last = int(state.get("inbox_last_id", 0))
    entries = sorted(fetch_entries(last), key=lambda e: e["id"])
    written = 0
    try:
        for e in entries:
            write_entry(e)
            last = e["id"]
            written += 1
    finally:
        if last != state.get("inbox_last_id", 0):
            state["inbox_last_id"] = last
            store.save_state(state)
    return written


def pending() -> list[dict]:
    rows = []
    for p in sorted(INBOX.glob("*.json")) if INBOX.exists() else []:
        rec = store.read_json(p, {})
        rows.append({
            "date": p.name[:10], "id": rec.get("id"), "kind": rec.get("kind"),
            "text": (rec.get("text") or "").replace("\n", " "), "file": "voice" if rec.get("voice") else "photo" if rec.get("file_id") else "-",
        })
    return rows


def format_table(rows: list[dict]) -> str:
    if not rows:
        return "inbox empty"
    lines = [f"{'date':<10}  {'id':>4}  {'kind':<6}  {'file':<5}  text"]
    for r in rows:
        text = r["text"] if len(r["text"]) <= 60 else r["text"][:59] + "…"
        lines.append(f"{r['date']:<10}  {r['id']!s:>4}  {r['kind'] or '':<6}  {r['file']:<5}  {text}")
    return "\n".join(lines)


def mark_done(ids: list[int]) -> list[str]:
    """Move every file of the given entry ids to data/inbox/done/. Returns moved file names."""
    moved = []
    for i in ids:
        for p in sorted(INBOX.glob(f"*_{int(i)}_*")) if INBOX.exists() else []:
            DONE.mkdir(parents=True, exist_ok=True)
            shutil.move(str(p), DONE / p.name)
            moved.append(p.name)
    return moved
