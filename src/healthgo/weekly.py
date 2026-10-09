"""Sunday prep: crunch the week's numbers into data/weekly/<ISO week>.json for /review.

The AI review itself happens interactively (it must ask about InBody and eating out),
so this step only prepares numbers and pings Darren that the review is ready.
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta
from pathlib import Path
from statistics import mean

from . import checks, config, db, store

KCAL_PER_KG = 7700
PREP_TIME = time(20, 30)


def latest_due_sunday(now: datetime) -> date:
    d = now.date()
    if d.weekday() == 6 and now.time() >= PREP_TIME:
        return d
    return d - timedelta(days=(d.weekday() + 1) % 7 or 7)


def week_id(sunday: date) -> str:
    y, w, _ = sunday.isocalendar()
    return f"{y}-W{w:02d}"


def week_file(sunday: date) -> Path:
    return config.WEEKLY / f"{week_id(sunday)}.json"


def latest_week_file() -> str | None:
    files = sorted(config.WEEKLY.glob("*.json"))
    return files[-1].stem if files else None


def _avg(con, col: str, start: date, end: date) -> float | None:
    v = con.execute(f"SELECT AVG({col}) FROM daily WHERE date BETWEEN ? AND ?",
                    (start.isoformat(), end.isoformat())).fetchone()[0]
    return round(v, 1) if v is not None else None


def _weight_avg(con, start: date, end: date) -> tuple[float | None, int]:
    row = con.execute("SELECT AVG(kg), COUNT(DISTINCT date) FROM weights WHERE date BETWEEN ? AND ?",
                      (start.isoformat(), end.isoformat())).fetchone()
    return (round(row[0], 2) if row[0] else None), row[1]


def _strength(con, start: date, end: date) -> list[dict]:
    prior_start = start - timedelta(days=28)
    rows = con.execute("""
        SELECT exercise,
          MAX(CASE WHEN date >= :s THEN e1rm_kg END)  AS e1rm_week,
          MAX(CASE WHEN date <  :s THEN e1rm_kg END)  AS e1rm_prior_4w,
          MAX(CASE WHEN date >= :s THEN weight_kg END) AS top_week,
          MAX(CASE WHEN date <  :s THEN weight_kg END) AS top_prior_4w,
          SUM(CASE WHEN date >= :s THEN 1 ELSE 0 END)  AS sets_week
        FROM sets WHERE date BETWEEN :p AND :e AND weight_kg > 0
        GROUP BY exercise HAVING sets_week > 0 ORDER BY e1rm_week DESC""",
        {"s": start.isoformat(), "p": prior_start.isoformat(), "e": end.isoformat()}).fetchall()
    out = []
    for r in rows:
        item = dict(r)
        if r["e1rm_week"] and r["e1rm_prior_4w"]:
            item["e1rm_change_pct"] = round((r["e1rm_week"] / r["e1rm_prior_4w"] - 1) * 100, 1)
        out.append(item)
    return out


def prepare(sunday: date) -> Path:
    start = sunday - timedelta(days=6)
    base_start, base_end = start - timedelta(days=28), start - timedelta(days=1)
    p = config.plan()
    con = db.connect()

    w_now, n_now = _weight_avg(con, start, sunday)
    w_prev, n_prev = _weight_avg(con, start - timedelta(days=7), start - timedelta(days=1))
    slope14 = checks.weight_slope_pct_per_week(con, sunday, 14)
    slope28 = checks.weight_slope_pct_per_week(con, sunday, 28)
    tdee = None
    if slope28 and w_now:
        kg_per_day = slope28[0] / 100 * w_now / 7
        tdee = round(p["baseline_intake_kcal"] - kg_per_day * KCAL_PER_KG)

    recovery = {}
    for col in ("rhr", "hrv_last_night", "sleep_h", "sleep_score", "avg_stress", "bb_high", "bb_low", "steps",
                "readiness_score"):
        recovery[col] = {"week": _avg(con, col, start, sunday), "baseline_4w": _avg(con, col, base_start, base_end)}
    hrv_statuses = [r[0] for r in con.execute(
        "SELECT hrv_status FROM daily WHERE date BETWEEN ? AND ? ORDER BY date",
        (start.isoformat(), sunday.isoformat()))]

    training = [dict(r) for r in con.execute(
        "SELECT type, COUNT(*) AS sessions, ROUND(SUM(duration_min)) AS minutes, ROUND(AVG(avg_hr)) AS avg_hr "
        "FROM activities WHERE date BETWEEN ? AND ? GROUP BY type ORDER BY sessions DESC",
        (start.isoformat(), sunday.isoformat()))]
    workouts = [dict(r) for r in con.execute(
        "SELECT date, name, duration_min FROM activities WHERE type = 'strength_training' "
        "AND date BETWEEN ? AND ? ORDER BY date", (start.isoformat(), sunday.isoformat()))]

    inbody = [dict(r) for r in con.execute(
        "SELECT date, weight_kg, body_fat_pct, skeletal_muscle_kg, fat_mass_kg, visceral_fat_level "
        "FROM inbody ORDER BY date DESC LIMIT 2")]
    latest_inbody = inbody[0] if inbody else None
    eating_out = [dict(r) for r in con.execute(
        "SELECT * FROM eating_out WHERE date BETWEEN ? AND ? ORDER BY date", (start.isoformat(), sunday.isoformat()))]
    last_review = con.execute("SELECT MAX(date) FROM reviews").fetchone()[0]
    strength = _strength(con, start, sunday)
    con.close()

    cut_start = date.fromisoformat(p["cut"]["start_date"])
    summary = {
        "week": week_id(sunday),
        "range": [start.isoformat(), sunday.isoformat()],
        "cut_week": (sunday - cut_start).days // 7 + 1,
        "days_to_checkpoint": (date.fromisoformat(p["checkpoint"]["date"]) - sunday).days,
        "weight": {
            "avg_week_kg": w_now, "weigh_ins_week": n_now,
            "avg_prev_week_kg": w_prev, "weigh_ins_prev_week": n_prev,
            "change_kg": round(w_now - w_prev, 2) if w_now and w_prev else None,
            "change_pct": round((w_now / w_prev - 1) * 100, 2) if w_now and w_prev else None,
            "trend_14d_pct_per_week": slope14[0] if slope14 else None,
            "trend_28d_pct_per_week": slope28[0] if slope28 else None,
            "total_lost_since_cut_kg": round(p["cut"]["start_weight_kg"] - w_now, 1) if w_now else None,
        },
        "maintenance_kcal_estimate": tdee,
        "maintenance_note": "baseline intake + 28-day weight trend × 7700 kcal/kg; ignores eating-out days "
                            "and water swings, so treat as ±200 kcal",
        "recovery": recovery,
        "hrv_status_days": hrv_statuses,
        "training": training,
        "strength_workouts": workouts,
        "strength": strength,
        "inbody_latest": latest_inbody,
        "inbody_previous": inbody[1] if len(inbody) > 1 else None,
        "inbody_missing_this_week": not latest_inbody or latest_inbody["date"] < start.isoformat(),
        "eating_out_recorded": eating_out,
        "last_review": last_review,
        "days_since_review": (sunday - date.fromisoformat(last_review)).days if last_review else None,
        "flags": [f.__dict__ for f in checks.run(sunday)],
        "in_trip": config.in_trip(sunday),
    }
    path = week_file(sunday)
    store.write_json(path, summary)
    return path


def ready_message(sunday: date) -> str:
    s = store.read_json(week_file(sunday))
    lines = [f"📊 healthgo 週報 {s['week']} 已準備好", "在 healthgo 開 Claude 執行 /review"]
    w = s["weight"]
    if w["avg_week_kg"]:
        change = f"（{w['change_kg']:+.1f} kg）" if w["change_kg"] is not None else ""
        lines.append(f"本週平均體重 {w['avg_week_kg']:.1f} kg{change}")
    if s["days_since_review"] and s["days_since_review"] > 7:
        lines.append(f"距離上次 review 已 {s['days_since_review']} 天")
    if s["flags"]:
        lines.append(f"⚠️ {len(s['flags'])} 個警示待看")
    return "\n".join(lines)
