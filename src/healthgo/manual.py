"""Manual records (things Garmin never sees), appended to data/manual/<kind>.jsonl."""

from __future__ import annotations

from datetime import date

from . import config, store

REQUIRED = {
    "inbody": ("date", "weight_kg", "body_fat_pct"),
    "eating_out": ("date", "description"),
    "bloodwork": ("date", "results"),
    "weight": ("date", "kg"),
    "review": ("date", "week", "verdict", "report"),
    "note": ("date", "text"),
}
FILES = {"review": "reviews", "note": "notes"}


def add(kind: str, record: dict) -> dict:
    missing = [k for k in REQUIRED[kind] if record.get(k) in (None, "")]
    if missing:
        raise SystemExit(f"{kind} record missing: {', '.join(missing)}")
    date.fromisoformat(record["date"])  # validate
    record.setdefault("recorded_at", config.now().isoformat(timespec="seconds"))
    store.append_jsonl(config.MANUAL / f"{FILES.get(kind, kind)}.jsonl", record)
    return record
