"""Telegram /ask: questions the Worker parks in R2 (`pending/<id>.json`), answered by a Claude session here.

`watch` is the event source for that session's Monitor: it polls the Worker and prints one JSON line per question it
has not printed before, so every stdout line is one thing to answer. It also opens the question's progress card in
Telegram the moment it sees it, so Darren knows it was picked up before any agent starts.
`status` adds a line to that card (one message, edited in place); the agents call it at each milestone.
`file` is the last step, no model involved: index row + source track record from the judge's filing JSON, then
`answer` sends the record under the question, marks it done in R2 and commits the knowledge base.
The pull token and bot token never reach a log line or stdout: errors print the exception type only.
"""

from __future__ import annotations

import fcntl
import json
import sys
import time
import urllib.request
from pathlib import Path

from . import config, gitops, inbox, notify, store, vault

PULLS = config.DATA / "asks" / "pulls"  # work files, git-ignored
CLAIMS = config.ROOT / "research" / "claims"
# Everything an answer may touch: the claim record + index, evidence memories, leftovers under data/asks/.
COMMIT_PATHS = ("research", ".claude/memory", "data/asks")
CARD_LINES = 25  # keep the card well under Telegram's 4096 chars


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


# ---- progress card ----

def _status_file(ask_id: int) -> Path:
    return PULLS / f"{int(ask_id)}-status.json"


def render_card(lines: list[list[str]], done: bool) -> str:
    out = ["🔎 /ask 進度"]
    for i, (hhmm, text) in enumerate(lines[-CARD_LINES:]):
        last = i == len(lines[-CARD_LINES:]) - 1
        out.append(f"{'⏳' if last and not done else '✅'} {hhmm} {text}")
    return "\n".join(out)


def status(ask_id: int, text: str, done: bool = False) -> bool:
    """Append a line to the question's progress card: the first call sends it under the question, later calls edit it.
    Parallel agents call this at once, so the read-modify-write is locked. Never raises."""
    try:
        PULLS.mkdir(parents=True, exist_ok=True)
        path = _status_file(ask_id)
        with open(path.with_suffix(".lock"), "w") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            card = store.read_json(path, {"message_id": None, "lines": []})
            card["lines"].append([config.now().strftime("%H:%M"), text.strip()])
            body = render_card(card["lines"], done)
            if card["message_id"]:
                ok = notify.api("editMessageText", {"message_id": card["message_id"], "text": body}) is not None
            else:
                sent = notify.api("sendMessage", {"text": body, "reply_parameters": {
                    "message_id": int(ask_id), "allow_sending_without_reply": True}})
                card["message_id"] = (sent or {}).get("message_id")
                ok = sent is not None
            store.write_json(path, card)
            return ok
    except Exception as e:
        print(f"status failed ({type(e).__name__})", file=sys.stderr)
        return False


# ---- watcher ----

def _emit(obj: dict) -> None:
    print(json.dumps(obj, ensure_ascii=False), flush=True)


def watch(interval: float = 10) -> None:
    """Poll forever. A question is printed once per process; a failure streak prints one line, and so does recovery,
    so a dead network can't flood the monitor. A question without a progress card gets one straight away (a re-armed
    watcher finds the card already there and stays quiet)."""
    seen: set[int] = set()
    failing = False
    while True:
        try:
            asks = pending()
            if failing:
                _emit({"event": "recovered"})
                failing = False
            for pos, a in enumerate(asks):
                if a["id"] in seen:
                    continue
                seen.add(a["id"])
                if not _status_file(a["id"]).exists():
                    status(a["id"], "收到，開始處理" if pos == 0 else f"收到，排隊中（前面還有 {pos} 題）")
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


# ---- filing + answer ----

def _cells(row: str) -> list[str]:
    return [c.strip() for c in row.strip().strip("|").split("|")]


def _row(cells: list) -> str:
    return "| " + " | ".join(str(c) for c in cells) + " |"


def _append_line(path: Path, line: str) -> None:
    text = path.read_text()
    path.write_text(text + ("" if text.endswith("\n") else "\n") + line + "\n")


def update_sources(path: Path, src: dict, record: str) -> None:
    """Add the verdicts to the source's row in sources.md (matched by name or URL), or add a row.
    Columns: Source | Type | Checked | ✅ | 🟡 | ❌ | ❓ | Pattern | Files."""
    name, url = (src.get("name") or "").strip(), (src.get("url") or "").strip()
    if not name or name == "自己聽到的":
        return
    v = src.get("verdicts") or {}
    adds = [int(v.get(k, 0)) for k in ("✅", "🟡", "❌", "❓")]
    link = f"[{record}]({record})"
    lines = path.read_text().splitlines()
    for i, line in enumerate(lines):
        if not line.startswith("| ") or line.startswith("| Source") or set(line) <= set("|- "):
            continue
        c = _cells(line)
        if name.lower() in c[0].lower() or (url and url in c[0]):
            counts = [int(x or 0) + a for x, a in zip(c[3:7], adds)]
            files = c[8] if link in c[8] else f"{c[8]} · {link}".strip(" ·")
            lines[i] = _row([c[0], c[1], sum(counts), *counts, src.get("pattern") or c[7], files])
            path.write_text("\n".join(lines) + "\n")
            return
    first = f"[{name}]({url})" if url else name
    _append_line(path, _row([first, src.get("type", ""), sum(adds), *adds, src.get("pattern", ""), link]))


def answer(ask_id: int, path: Path) -> dict:
    """Send the answer under the question, then mark it done in R2 and commit the knowledge base.
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
    paths = tuple(p for p in COMMIT_PATHS if (config.ROOT / p).exists())
    git = gitops.commit_and_push(f"ask: {path.stem} (/ask {ask_id})", paths)
    return {"id": ask_id, "telegram": True, "done": done, "git": git}


def file(ask_id: int) -> dict:
    """The last step, from data/asks/pulls/<id>-filing.json (written by ask-judge): index rows, source track record,
    send + done + commit, close the card, delete the work files. Work files stay if Telegram failed, for a retry."""
    filing = json.loads((PULLS / f"{int(ask_id)}-filing.json").read_text())
    record = filing["record"]
    name = Path(record).name
    if f"]({name})" not in (CLAIMS / "README.md").read_text():  # a retry after a failed send files nothing twice
        for r in filing.get("index_rows", []):
            _append_line(CLAIMS / "README.md", _row([r["date"], r["claim"], r["verdict"], r["source"], f"[{name}]({name})"]))
        if filing.get("source"):
            update_sources(CLAIMS / "sources.md", filing["source"], name)
    status(ask_id, "寄出答案")
    res = answer(ask_id, Path(record))
    if res["telegram"]:
        status(ask_id, "完成，答案在下面 👇", done=True)
        for p in PULLS.glob(f"{int(ask_id)}-*"):
            p.unlink()
    else:
        status(ask_id, "⚠️ 答案寄送失敗，會再試")
    return res
