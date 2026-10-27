"""Telegram /ask: questions the Worker parks in R2 (`pending/<id>.json`), answered by a Claude session here.

`watch` is the event source for that session's Monitor: it polls the Worker and prints one JSON line per question it
has not printed before, so every stdout line is one thing to answer. `answer` sends the written answer to Telegram,
threaded under the question, moves it to `done/` in R2 and commits the markdown under data/asks/.
The pull token and bot token never reach a log line or stdout: errors print the exception type only.
"""

from __future__ import annotations

import json
import sys
import time
import urllib.request
from pathlib import Path

from . import config, gitops, inbox, notify, vault

ASKS = config.DATA / "asks"


def _request(path: str, body: dict | None = None) -> dict:
    req = urllib.request.Request(
        f"{inbox.inbox_url()}{path}",
        data=json.dumps(body).encode() if body is not None else None,
        # Cloudflare rejects the default Python-urllib User-Agent (error 1010)
        headers={"User-Agent": "healthgo/1.0", "Content-Type": "application/json",
                 "Authorization": f"Bearer {vault.read('INBOX/PULL_TOKEN')}"},
        method="POST" if body is not None else "GET",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def pending() -> list[dict]:
    return _request("/asks")["asks"]


def _emit(obj: dict) -> None:
    print(json.dumps(obj, ensure_ascii=False), flush=True)


def watch(interval: float = 10) -> None:
    """Poll forever. A question is printed once per process; a failure streak prints one line, and so does recovery,
    so a dead network can't flood the monitor."""
    seen: set[int] = set()
    failing = False
    while True:
        try:
            asks = pending()
            if failing:
                _emit({"event": "recovered"})
                failing = False
            for a in asks:
                if a["id"] not in seen:
                    seen.add(a["id"])
                    _emit({"event": "ask", "id": a["id"], "asked_at": a["asked_at"], "text": a["text"],
                           "has_file": bool(a.get("file_id"))})
        except KeyboardInterrupt:
            raise
        except Exception as e:
            if not failing:
                _emit({"event": "error", "type": type(e).__name__})
                failing = True
        sys.stdout.flush()
        time.sleep(interval)


def answer(ask_id: int, path: Path) -> dict:
    """Send the answer under the question, then mark it done in R2 and commit data/asks/.
    If Telegram fails nothing is marked, so the question stays pending."""
    path = path if path.is_absolute() else config.ROOT / path
    if not notify.send_report(path, reply_to=ask_id, icon="❓"):
        return {"id": ask_id, "telegram": False, "done": False}
    try:
        _request(f"/asks/{int(ask_id)}/done", {"answer": path.read_text()})
        done = True
    except Exception as e:
        print(f"marking done failed ({type(e).__name__}); the answer was sent", file=sys.stderr)
        done = False
    git = gitops.commit_and_push(f"ask: answer {ask_id}", ("data/asks",))
    return {"id": ask_id, "telegram": True, "done": done, "git": git}
