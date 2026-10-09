"""Plain-text storage: stable JSON so git diffs show only real changes."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from . import config


def dumps(obj: Any) -> str:
    return json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def write_json(path: Path, obj: Any) -> bool:
    """Write only when content differs. Returns True if the file changed."""
    text = dumps(obj)
    if path.exists() and path.read_text() == text:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text)
    tmp.replace(path)
    return True


def read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text())


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def append_jsonl(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as f:
        f.write(json.dumps(record, sort_keys=True, ensure_ascii=False) + "\n")


def load_state() -> dict:
    return read_json(config.STATE_FILE, {})


def save_state(state: dict) -> None:
    write_json(config.STATE_FILE, state)
