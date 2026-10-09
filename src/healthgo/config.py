from __future__ import annotations

import json
import os
from datetime import date, datetime
from functools import lru_cache
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
GARMIN = DATA / "garmin"
DAILY_DIR = GARMIN / "daily"
ACTIVITY_DIR = GARMIN / "activities"
PROFILE_FILE = GARMIN / "profile.json"
MANUAL = DATA / "manual"
WEEKLY = DATA / "weekly"
STATE_FILE = DATA / "state.json"
DB_FILE = DATA / "healthgo.db"
LOCK_FILE = DATA / ".sync.lock"
PLAN_FILE = ROOT / "config" / "plan.json"
REPORTS = ROOT / "reports"

# Garmin tokens are credentials, not health data: they live outside the repo.
TOKENSTORE = Path(os.environ.get("HEALTHGO_TOKENSTORE", "~/.garminconnect")).expanduser()


@lru_cache
def plan() -> dict:
    return json.loads(PLAN_FILE.read_text())


def tz() -> ZoneInfo:
    return ZoneInfo(plan()["timezone"])


def now() -> datetime:
    return datetime.now(tz())


def today() -> date:
    return now().date()


def in_trip(d: date) -> bool:
    trip = plan()["trip"]
    return date.fromisoformat(trip["start"]) <= d <= date.fromisoformat(trip["end"])
