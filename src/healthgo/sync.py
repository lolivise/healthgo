"""Catch-up sync: every date not yet fully pulled, plus a 3-day overlap.

`state["complete_through"]` is the last date for which every endpoint succeeded
AND which is before today (today is always partial at 20:00). Each run fetches
from OVERLAP_DAYS before the day after it through today, so a Mac that was off
for a week backfills the whole week, and late-settling sleep/HRV/readiness
values get overwritten with their final versions.
"""

from __future__ import annotations

import io
import logging
import time
import zipfile
from datetime import date, timedelta
from typing import Any, Callable

from garminconnect import (
    Garmin,
    GarminConnectConnectionError,
    GarminConnectNotFoundError,
    GarminConnectTooManyRequestsError,
)

from . import config, store

log = logging.getLogger(__name__)

OVERLAP_DAYS = 3
CALL_DELAY_S = 0.7  # be a polite, low-volume client

DAILY_ENDPOINTS: dict[str, Callable[[Garmin, str], Any]] = {
    "summary": lambda g, d: g.get_user_summary(d),
    "sleep": lambda g, d: g.get_sleep_data(d),
    "hrv": lambda g, d: g.get_hrv_data(d),
    "stress": lambda g, d: g.get_stress_data(d),
    "body_battery": lambda g, d: g.get_body_battery(d),
    "rhr": lambda g, d: g.get_rhr_day(d),
    "training_readiness": lambda g, d: g.get_training_readiness(d),
    "training_status": lambda g, d: g.get_training_status(d),
    "max_metrics": lambda g, d: g.get_max_metrics(d),
    "weigh_ins": lambda g, d: g.get_daily_weigh_ins(d),
}

STRENGTH_TYPES = {"strength_training"}


class SyncAborted(RuntimeError):
    """Rate-limited mid-sync; stop immediately and leave the rest for tomorrow."""


def _call(fn: Callable[[], Any]) -> Any:
    time.sleep(CALL_DELAY_S)
    try:
        return fn()
    except GarminConnectNotFoundError:
        return None
    except GarminConnectTooManyRequestsError as e:
        raise SyncAborted(f"rate limited by Garmin: {e}") from e


def daily_path(d: date):
    return config.DAILY_DIR / f"{d:%Y}" / f"{d.isoformat()}.json"


def sync_window(state: dict, start_override: date | None = None) -> list[date]:
    end = config.today()
    if start_override:
        start = start_override
    elif state.get("complete_through"):
        start = date.fromisoformat(state["complete_through"]) + timedelta(days=1 - OVERLAP_DAYS)
    else:
        start = date.fromisoformat(config.plan()["backfill_start"])
    start = min(start, end)
    return [start + timedelta(days=i) for i in range((end - start).days + 1)]


def fetch_day(client: Garmin, d: date) -> bool:
    """Fetch and store one day. Returns True if every endpoint succeeded."""
    ds = d.isoformat()
    record: dict[str, Any] = {"date": ds, "endpoints": {}, "errors": {}}
    for name, fn in DAILY_ENDPOINTS.items():
        try:
            record["endpoints"][name] = _call(lambda: fn(client, ds))
        except GarminConnectConnectionError as e:
            log.warning("%s %s failed: %s", ds, name, e)
            record["errors"][name] = str(e)[:300]
    if not record["errors"]:
        del record["errors"]
    previous = store.read_json(daily_path(d))
    if "errors" in record and previous and "errors" not in previous:
        # Never replace a good day with a partly failed one.
        return False
    store.write_json(daily_path(d), record)
    return "errors" not in record


def _activity_dir(activity: dict):
    start = activity.get("startTimeLocal") or ""
    aid = activity["activityId"]
    existing = list(config.ACTIVITY_DIR.glob(f"*/*_{aid}"))
    if existing:
        return existing[0]
    return config.ACTIVITY_DIR / start[:7] / f"{start[:10]}_{aid}"


def sync_activities(client: Garmin, start: date, end: date, refresh_from: date) -> int:
    activities = _call(lambda: client.get_activities_by_date(start.isoformat(), end.isoformat())) or []
    for act in activities:
        aid = act["activityId"]
        folder = _activity_dir(act)
        store.write_json(folder / "summary.json", act)
        act_date = date.fromisoformat((act.get("startTimeLocal") or "")[:10] or end.isoformat())
        type_key = (act.get("activityType") or {}).get("typeKey")
        sets_file = folder / "sets.json"
        if type_key in STRENGTH_TYPES and (not sets_file.exists() or act_date >= refresh_from):
            # sets get edited in the app after the workout, so refresh recent ones
            sets = _call(lambda: client.get_activity_exercise_sets(aid))
            if sets is not None:
                store.write_json(sets_file, sets)
        fit_file = folder / "activity.fit"
        if not fit_file.exists():
            try:
                raw = _call(lambda: client.download_activity(aid, Garmin.ActivityDownloadFormat.ORIGINAL))
            except GarminConnectConnectionError as e:
                log.warning("FIT download for %s failed: %s", aid, e)
                raw = None
            if raw:
                with zipfile.ZipFile(io.BytesIO(raw)) as z:
                    fits = [n for n in z.namelist() if n.lower().endswith(".fit")]
                    if fits:
                        fit_file.write_bytes(z.read(fits[0]))
    return len(activities)


def run(client: Garmin, state: dict, start_override: date | None = None) -> dict:
    window = sync_window(state, start_override)
    today = config.today()
    log.info("syncing %s → %s (%d days)", window[0], window[-1], len(window))

    profile = _call(client.get_userprofile_settings)
    if profile:
        store.write_json(config.PROFILE_FILE, profile)

    complete = date.fromisoformat(state["complete_through"]) if state.get("complete_through") else None
    contiguous = True
    failed: list[str] = []
    for d in window:
        ok = fetch_day(client, d)
        if not ok:
            failed.append(d.isoformat())
            contiguous = False
        elif contiguous and d < today and (complete is None or d > complete):
            complete = d
        if complete:
            state["complete_through"] = complete.isoformat()
            store.save_state(state)

    refresh_from = today - timedelta(days=OVERLAP_DAYS)
    n_acts = sync_activities(client, window[0], window[-1], refresh_from)

    state["last_sync_at"] = config.now().isoformat(timespec="seconds")
    state["last_sync_window"] = [window[0].isoformat(), window[-1].isoformat()]
    store.save_state(state)
    return {"days": len(window), "failed_days": failed, "activities": n_acts}
