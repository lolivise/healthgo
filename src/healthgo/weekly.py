"""Sunday prep: crunch the week's numbers into data/weekly/<ISO week>.json for /review.

The AI review itself happens interactively (it must ask about eating out),
so this step only prepares numbers and pings Darren that the review is ready.
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta
from pathlib import Path

from . import checks, config, db, facts, store

KCAL_PER_KG = 7700
PREP_TIME = time(18, 0)


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


# Recorded overnight or in the morning, so today's value is already final before Darren reviews: last night's sleep,
# HRV and RHR, the wake-up Body Battery peak, Garmin's morning readiness. Everything else in `daily` (steps, stress,
# Body Battery low) fills in all day and only counts through `config.last_complete_day()`.
MORNING_COLS = ("rhr", "hrv_last_night", "sleep_h", "sleep_score", "bb_high", "readiness_score")
ALL_DAY_COLS = ("avg_stress", "bb_low", "steps")


def _weekly_rows(con, p: dict, sunday: date, end: date, day_end: date, weeks: int = 5) -> list[dict]:
    """This week and the `weeks - 1` before it, one row each, so a report can show the trajectory."""
    rows = []
    for i in range(weeks - 1, -1, -1):
        s_end = sunday - timedelta(days=7 * i)
        s_start = s_end - timedelta(days=6)
        kg, n = _weight_avg(con, s_start, min(s_end, end))
        row = {"week": week_id(s_end), "avg_kg": kg, "weigh_ins": n}
        for col in MORNING_COLS[:3]:
            row[col] = _avg(con, col, s_start, min(s_end, end))
        for col in ("avg_stress", "steps"):
            row[col] = _avg(con, col, s_start, min(s_end, day_end))
        row["eat_out_kcal"] = con.execute(
            "SELECT ROUND(SUM(est_kcal)) FROM eating_out WHERE date BETWEEN ? AND ?",
            (s_start.isoformat(), min(s_end, end).isoformat())).fetchone()[0]
        row["ea_kcal"] = facts.energy_availability(con, p, s_start, min(s_end, end))["ea_kcal"]
        rows.append(row)
    for prev, row in zip(rows, rows[1:]):
        if prev["avg_kg"] and row["avg_kg"]:
            row["change_kg"] = round(row["avg_kg"] - prev["avg_kg"], 2)
    return rows


def prepare(sunday: date) -> Path:
    """Numbers for the Mon–Sun week ending `sunday`.

    A week in progress runs through today for overnight/morning data, weigh-ins, workouts and meals (`MORNING_COLS`),
    and through `config.last_complete_day()` for all-day metrics (`ALL_DAY_COLS`): before 18:00 today's steps and
    stress are left out, from 18:00 they count (Darren, 2026-10-25). A past week is complete either way."""
    start = sunday - timedelta(days=6)
    end = min(sunday, config.today())
    day_end = min(sunday, config.last_complete_day())
    base_start, base_end = start - timedelta(days=28), start - timedelta(days=1)
    p = config.plan()
    con = db.connect()

    w_now, n_now = _weight_avg(con, start, end)
    w_prev, n_prev = _weight_avg(con, start - timedelta(days=7), start - timedelta(days=1))
    slope14 = checks.weight_slope_pct_per_week(con, end, 14)
    slope28 = checks.weight_slope_pct_per_week(con, end, 28)
    tdee = None
    if slope28 and w_now:
        kg_per_day = slope28[0] / 100 * w_now / 7
        tdee = round(facts.mean_intake(p, end - timedelta(days=27), end) - kg_per_day * KCAL_PER_KG)

    recovery = {}
    for col in MORNING_COLS + ALL_DAY_COLS:
        through = end if col in MORNING_COLS else day_end
        recovery[col] = {"week": _avg(con, col, start, through),
                         "baseline_4w": _avg(con, col, base_start, base_end)}
    hrv_statuses = [r[0] for r in con.execute(
        "SELECT hrv_status FROM daily WHERE date BETWEEN ? AND ? ORDER BY date",
        (start.isoformat(), end.isoformat()))]

    training = [dict(r) for r in con.execute(
        "SELECT type, COUNT(*) AS sessions, ROUND(SUM(duration_min)) AS minutes, ROUND(AVG(avg_hr)) AS avg_hr "
        "FROM activities WHERE date BETWEEN ? AND ? GROUP BY type ORDER BY sessions DESC",
        (start.isoformat(), end.isoformat()))]
    workouts = [dict(r) for r in con.execute(
        "SELECT date, name, duration_min FROM activities WHERE type = 'strength_training' "
        "AND date BETWEEN ? AND ? ORDER BY date", (start.isoformat(), end.isoformat()))]

    eating_out = [dict(r) for r in con.execute(
        "SELECT * FROM eating_out WHERE date BETWEEN ? AND ? ORDER BY date", (start.isoformat(), end.isoformat()))]
    last_review = con.execute("SELECT MAX(date) FROM reviews").fetchone()[0]
    strength = _strength(con, start, end)
    weeks = _weekly_rows(con, p, sunday, end, day_end)
    cut_start = date.fromisoformat(p["cut"]["start_date"])
    since_baseline = facts.strength_since_baseline(con, p, end)
    ea = facts.energy_availability(con, p, start, end)
    guard = facts.health_guard(con, p, end, start, (end - cut_start).days // 7, recovery["sleep_h"]["week"],
                               ea, since_baseline)
    pattern = facts.training_pattern(con, end)
    bloodwork = facts.bloodwork_status(con, p, config.today())
    con.close()
    summary = {
        "week": week_id(sunday),
        "range": [start.isoformat(), end.isoformat()],
        "all_day_metrics_through": day_end.isoformat(),
        "partial": day_end < sunday,
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
        "health_guard": guard,
        "projections": facts.projections(p, end, w_now, slope14[0] if slope14 else None,
                                         slope28[0] if slope28 else None),
        "strength_since_baseline": since_baseline,
        "training_pattern_4w": pattern,
        "bloodwork": bloodwork,
        "recovery": recovery,
        "hrv_status_days": hrv_statuses,
        "training": training,
        "strength_workouts": workouts,
        "strength": strength,
        "eating_out_recorded": eating_out,
        "last_review": last_review,
        "days_since_review": (config.today() - date.fromisoformat(last_review)).days if last_review else None,
        "flags": [f.__dict__ for f in checks.run(end, day_end)],
        "last_5_weeks": weeks,
        "in_trip": config.in_trip(sunday),
    }
    path = week_file(sunday)
    store.write_json(path, summary)
    return path


def _week_sunday(week: str | None) -> date | None:
    """`2026-W43` → its Sunday; None for anything else (e.g. the old `2026-W43-midweek` labels)."""
    try:
        y, w = (week or "").split("-W")
        return date.fromisocalendar(int(y), int(w), 7)
    except ValueError:
        return None


def is_full_review(r: dict, sunday: date) -> bool:
    """Whether review record `r` covered the whole Mon–Sun week ending `sunday`. New records say so with `kind` and
    `through`; older ones count if they were written on or after that Sunday 18:00."""
    if r.get("week") != week_id(sunday) or r.get("kind") == "midweek":
        return False
    if r.get("through"):
        return r["through"] >= sunday.isoformat()
    at = datetime.fromisoformat(r.get("recorded_at") or r["date"]).replace(tzinfo=None)
    return at >= datetime.combine(sunday, time(config.EVENING_HOUR))


def review_plan(now: datetime) -> dict:
    """What /review runs at `now` (Darren, 2026-10-25).

    Target: Sunday from 18:00 → the full week; any other time → a mid-week review of the current week. Before that,
    if the week ending the Sunday before the target's week has no full review, it gets one first (`catch_up`), as if
    it had been run that Sunday evening. Older unreviewed weeks get no report of their own; they're listed so the
    full report's week-by-week table can call them out."""
    today = now.date()
    evening = now.hour >= config.EVENING_HOUR
    if today.weekday() == 6 and evening:
        sunday, kind, report = today, "full", f"reports/{week_id(today)}.md"
    else:
        sunday = today + timedelta(days=6 - today.weekday())
        kind, report = "midweek", f"reports/{week_id(sunday)}-midweek-{today:%m-%d}.md"
    target = {"kind": kind, "week": week_id(sunday), "week_end": sunday.isoformat(), "report": report,
              "through": today.isoformat(),
              "all_day_metrics_through": (today if evening else today - timedelta(days=1)).isoformat(),
              "prepare": f"uv run healthgo prepare-week --week-end {sunday.isoformat()}"}

    reviews = store.read_jsonl(config.MANUAL / "reviews.jsonl")
    full = sorted(s for r in reviews if (s := _week_sunday(r.get("week"))) and is_full_review(r, s))
    prev = sunday - timedelta(days=7)
    catch_up = None
    if prev not in full:
        catch_up = {"kind": "full", "week": week_id(prev), "week_end": prev.isoformat(),
                    "report": f"reports/{week_id(prev)}.md", "through": prev.isoformat(),
                    "all_day_metrics_through": prev.isoformat(),
                    "prepare": f"uv run healthgo prepare-week --week-end {prev.isoformat()}"}
    last_full = max((s for s in full if s < sunday), default=None)
    older = []
    if last_full:
        s = last_full + timedelta(days=7)
        while s < prev:
            older.append(week_id(s))
            s += timedelta(days=7)
    return {"now": now.isoformat(timespec="minutes"), "evening": evening, "catch_up": catch_up, "target": target,
            "last_full_review_week": week_id(last_full) if last_full else None,
            "older_weeks_without_full_review": older}


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
