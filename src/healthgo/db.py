"""Rebuild data/healthgo.db (git-ignored) from the committed JSON. Always safe to rerun.

Field names were checked against real responses on 2026-10-09. Garmin returns
weights in grams; everything here is converted to kg.
"""

from __future__ import annotations

import json
import sqlite3
from typing import Any

from . import config, store

SCHEMA = """
CREATE TABLE daily (
  date TEXT PRIMARY KEY, steps INT, total_kcal REAL, active_kcal REAL, bmr_kcal REAL,
  rhr INT, avg_stress INT, max_stress INT,
  bb_high INT, bb_low INT, bb_charged INT, bb_drained INT,
  sleep_h REAL, deep_h REAL, light_h REAL, rem_h REAL, awake_h REAL, sleep_score INT,
  hrv_last_night INT, hrv_weekly INT, hrv_status TEXT, hrv_balanced_low INT, hrv_balanced_high INT,
  readiness_score INT, readiness_level TEXT, training_status TEXT, vo2max REAL,
  weight_kg REAL, body_fat_pct REAL
);
CREATE TABLE weights (date TEXT, kg REAL, body_fat_pct REAL, source TEXT);
CREATE TABLE activities (
  id INT PRIMARY KEY, date TEXT, start_local TEXT, type TEXT, name TEXT,
  duration_min REAL, distance_km REAL, avg_hr REAL, max_hr REAL, calories REAL,
  training_load REAL, aerobic_te REAL, anaerobic_te REAL
);
CREATE TABLE sets (
  activity_id INT, date TEXT, workout TEXT, set_no INT, category TEXT, exercise TEXT,
  reps INT, weight_kg REAL, duration_s REAL, e1rm_kg REAL
);
CREATE TABLE inbody (
  date TEXT, weight_kg REAL, body_fat_pct REAL, skeletal_muscle_kg REAL, fat_mass_kg REAL,
  visceral_fat_level REAL, raw TEXT
);
CREATE TABLE eating_out (date TEXT, meal TEXT, description TEXT, est_kcal REAL);
CREATE TABLE bloodwork (date TEXT, raw TEXT);
CREATE TABLE reviews (date TEXT, week TEXT, verdict TEXT, report TEXT);
CREATE TABLE notes (date TEXT, text TEXT);
CREATE VIEW strength_top AS
  SELECT date, exercise, MAX(weight_kg) AS top_kg, MAX(e1rm_kg) AS best_e1rm_kg, COUNT(*) AS sets
  FROM sets WHERE reps > 0 GROUP BY date, exercise;
"""


def dig(obj: Any, *path: Any) -> Any:
    for key in path:
        if obj is None:
            return None
        if isinstance(key, int):
            obj = obj[key] if isinstance(obj, list) and len(obj) > key else None
        else:
            obj = obj.get(key) if isinstance(obj, dict) else None
    return obj


def _h(seconds: Any) -> float | None:
    return round(seconds / 3600, 2) if isinstance(seconds, (int, float)) else None


def _kg(grams: Any) -> float | None:
    return round(grams / 1000, 2) if isinstance(grams, (int, float)) and grams > 0 else None


def e1rm(weight_kg: float | None, reps: int | None) -> float | None:
    """Epley. Only meaningful for 1–12 reps with real load."""
    if not weight_kg or not reps or reps < 1 or reps > 12:
        return None
    return round(weight_kg * (1 + reps / 30), 1) if reps > 1 else weight_kg


def _daily_row(rec: dict) -> tuple[dict, list[tuple]]:
    e = rec["endpoints"]
    s, sleep, hrv = e.get("summary") or {}, e.get("sleep") or {}, e.get("hrv") or {}
    dto = sleep.get("dailySleepDTO") or {}
    hs = hrv.get("hrvSummary") or {}
    readiness = e.get("training_readiness") or []
    ts_data = dig(e.get("training_status"), "mostRecentTrainingStatus", "latestTrainingStatusData") or {}
    ts_first = next(iter(ts_data.values()), {}) if isinstance(ts_data, dict) else {}
    weights = [w for w in (dig(e.get("weigh_ins"), "dateWeightList") or []) if _kg(w.get("weight"))]
    last_w = max(weights, key=lambda w: w.get("date") or 0) if weights else {}
    row = {
        "date": rec["date"],
        "steps": s.get("totalSteps"),
        "total_kcal": s.get("totalKilocalories"),
        "active_kcal": s.get("activeKilocalories"),
        "bmr_kcal": s.get("bmrKilocalories"),
        "rhr": s.get("restingHeartRate") or dig(e.get("rhr"), "allMetrics", "metricsMap",
                                                "WELLNESS_RESTING_HEART_RATE", 0, "value"),
        "avg_stress": _nonneg(s.get("averageStressLevel")),
        "max_stress": _nonneg(s.get("maxStressLevel")),
        "bb_high": s.get("bodyBatteryHighestValue"),
        "bb_low": s.get("bodyBatteryLowestValue"),
        "bb_charged": s.get("bodyBatteryChargedValue"),
        "bb_drained": s.get("bodyBatteryDrainedValue"),
        "sleep_h": _h(dto.get("sleepTimeSeconds")),
        "deep_h": _h(dto.get("deepSleepSeconds")),
        "light_h": _h(dto.get("lightSleepSeconds")),
        "rem_h": _h(dto.get("remSleepSeconds")),
        "awake_h": _h(dto.get("awakeSleepSeconds")),
        "sleep_score": dig(dto, "sleepScores", "overall", "value"),
        "hrv_last_night": hs.get("lastNightAvg"),
        "hrv_weekly": hs.get("weeklyAvg"),
        "hrv_status": hs.get("status"),
        "hrv_balanced_low": dig(hs, "baseline", "balancedLow"),
        "hrv_balanced_high": dig(hs, "baseline", "balancedUpper"),
        "readiness_score": dig(readiness, 0, "score"),
        "readiness_level": dig(readiness, 0, "level"),
        "training_status": ts_first.get("trainingStatusFeedbackPhrase") or ts_first.get("trainingStatus"),
        "vo2max": dig(e.get("max_metrics"), 0, "generic", "vo2MaxPreciseValue")
                  or dig(e.get("max_metrics"), 0, "generic", "vo2MaxValue"),
        "weight_kg": _kg(last_w.get("weight")),
        "body_fat_pct": last_w.get("bodyFat"),
    }
    weigh_rows = [(rec["date"], _kg(w["weight"]), w.get("bodyFat"), f"garmin:{w.get('sourceType')}")
                  for w in weights]
    return row, weigh_rows


def _nonneg(v: Any) -> Any:
    # Garmin uses -1/-2 for "not enough data"
    return v if isinstance(v, (int, float)) and v >= 0 else None


def build() -> dict:
    tmp = config.DB_FILE.with_suffix(".db.tmp")
    tmp.unlink(missing_ok=True)
    con = sqlite3.connect(tmp)
    con.executescript(SCHEMA)
    counts = {"daily": 0, "activities": 0, "sets": 0}

    for path in sorted(config.DAILY_DIR.glob("*/*.json")):
        row, weigh_rows = _daily_row(json.loads(path.read_text()))
        con.execute(f"INSERT INTO daily ({','.join(row)}) VALUES ({','.join('?' * len(row))})",
                    list(row.values()))
        con.executemany("INSERT INTO weights VALUES (?,?,?,?)", weigh_rows)
        counts["daily"] += 1

    for path in sorted(config.ACTIVITY_DIR.glob("*/*/summary.json")):
        a = json.loads(path.read_text())
        start = a.get("startTimeLocal") or ""
        con.execute("INSERT OR REPLACE INTO activities VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", (
            a["activityId"], start[:10], start, dig(a, "activityType", "typeKey"), a.get("activityName"),
            round((a.get("duration") or 0) / 60, 1), round((a.get("distance") or 0) / 1000, 2),
            a.get("averageHR"), a.get("maxHR"), a.get("calories"), a.get("activityTrainingLoad"),
            a.get("aerobicTrainingEffect"), a.get("anaerobicTrainingEffect"),
        ))
        counts["activities"] += 1
        sets_file = path.parent / "sets.json"
        if sets_file.exists():
            n = 0
            for st in (json.loads(sets_file.read_text()).get("exerciseSets") or []):
                if st.get("setType") != "ACTIVE":
                    continue
                n += 1
                ex = dig(st, "exercises", 0) or {}
                kg, reps = _kg(st.get("weight")), st.get("repetitionCount")
                con.execute("INSERT INTO sets VALUES (?,?,?,?,?,?,?,?,?,?)", (
                    a["activityId"], start[:10], a.get("activityName"), n, ex.get("category"),
                    ex.get("name") or ex.get("category"), reps, kg, st.get("duration"), e1rm(kg, reps),
                ))
                counts["sets"] += 1

    for r in store.read_jsonl(config.MANUAL / "weight.jsonl"):
        con.execute("INSERT INTO weights VALUES (?,?,?,?)", (r["date"], r["kg"], r.get("body_fat_pct"),
                                                             r.get("source", "manual")))
    for r in store.read_jsonl(config.MANUAL / "inbody.jsonl"):
        con.execute("INSERT INTO inbody VALUES (?,?,?,?,?,?,?)", (
            r["date"], r.get("weight_kg"), r.get("body_fat_pct"), r.get("skeletal_muscle_kg"),
            r.get("fat_mass_kg"), r.get("visceral_fat_level"), json.dumps(r, ensure_ascii=False)))
    for r in store.read_jsonl(config.MANUAL / "eating_out.jsonl"):
        con.execute("INSERT INTO eating_out VALUES (?,?,?,?)",
                    (r["date"], r.get("meal"), r.get("description"), r.get("est_kcal")))
    for r in store.read_jsonl(config.MANUAL / "bloodwork.jsonl"):
        con.execute("INSERT INTO bloodwork VALUES (?,?)", (r["date"], json.dumps(r, ensure_ascii=False)))
    for r in store.read_jsonl(config.MANUAL / "reviews.jsonl"):
        con.execute("INSERT INTO reviews VALUES (?,?,?,?)", (r["date"], r.get("week"), r.get("verdict"),
                                                             r.get("report")))
    for r in store.read_jsonl(config.MANUAL / "notes.jsonl"):
        con.execute("INSERT INTO notes VALUES (?,?)", (r["date"], r.get("text")))

    con.commit()
    con.close()
    tmp.replace(config.DB_FILE)
    return counts


def connect() -> sqlite3.Connection:
    con = sqlite3.connect(config.DB_FILE)
    con.row_factory = sqlite3.Row
    return con
