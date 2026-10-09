"""Manual records (things Garmin never sees), appended to data/manual/<kind>.jsonl."""

from __future__ import annotations

import sys
from datetime import date

from . import config, inbody_check, store

REQUIRED = {
    "inbody": ("date", "weight_kg", "body_fat_pct"),
    "eating_out": ("date", "description"),
    "bloodwork": ("date", "results"),
    "weight": ("date", "kg"),
    "review": ("date", "week", "verdict", "report"),
    "note": ("date", "text"),
}
FILES = {"review": "reviews", "note": "notes"}


def check_inbody(record: dict) -> list[inbody_check.Result]:
    """Print the consistency report; return the results."""
    results = inbody_check.check(record)
    print(inbody_check.report(results), file=sys.stderr)
    return results


def add(kind: str, record: dict, *, force: bool = False) -> dict:
    missing = [k for k in REQUIRED[kind] if record.get(k) in (None, "")]
    if missing:
        raise SystemExit(f"{kind} record missing: {', '.join(missing)}")
    date.fromisoformat(record["date"])  # validate
    if kind == "inbody":
        bad = inbody_check.failures(check_inbody(record))
        if bad and not force:
            print(f"inbody scan is internally inconsistent ({len(bad)} failed); nothing written. "
                  "Re-read the numbers, or pass --force to record anyway.", file=sys.stderr)
            raise SystemExit(2)
        if bad:
            record["consistency_override"] = True
            record["failed_checks"] = [r.name for r in bad]
    record.setdefault("recorded_at", config.now().isoformat(timespec="seconds"))
    store.append_jsonl(config.MANUAL / f"{FILES.get(kind, kind)}.jsonl", record)
    return record
