"""Numbers that used to be copied into memory by hand, computed fresh for every /review.

Memory keeps the rules and decisions (what counts as a baseline, which sessions are excluded, the limits); this module
turns them into today's figures, so a memory file never has to carry a lift log or a projection that goes stale.
Thresholds come from config/plan.json; the bands match `.claude/skills/review/reference.md` → Health-guard checklist.
"""

from __future__ import annotations

from datetime import date, timedelta

from . import checks


def iso_week(d: date) -> str:
    y, w, _ = d.isocalendar()
    return f"{y}-W{w:02d}"


def intake_on(p: dict, d: date) -> float:
    """Planned daily intake on `d` from `intake_kcal_schedule` (falls back to the baseline)."""
    k = p["baseline_intake_kcal"]
    for e in sorted(p.get("intake_kcal_schedule", []), key=lambda e: e["from"]):
        if date.fromisoformat(e["from"]) <= d:
            k = e["kcal"]
    return k


def mean_intake(p: dict, start: date, end: date) -> float:
    days = [start + timedelta(days=i) for i in range((end - start).days + 1)]
    return sum(intake_on(p, d) for d in days) / len(days)


def _excluded(row, rules: list[dict]) -> bool:
    for r in rules:
        if "date" in r and row["date"] == r["date"]:
            return True
        if r.get("exercise") == row["exercise"] and row["date"] < r.get("before", "9999"):
            return True
    return False


def strength_since_baseline(con, p: dict, end: date) -> list[dict]:
    """Best set per exercise per ISO week from `strength.baseline_from` (W41: every load since then is real), minus
    `strength.exclude` (another gym's session, a form reset). The score is Epley e1RM; `db.e1rm` stops at 12 reps,
    but his accessories run 15–20, so here it is uncapped and above 12 reps only means "heavier or more reps".
    Guard: red ≥5 % below the best since baseline, yellow when down two weeks running."""
    s = p.get("strength", {})
    rows = con.execute(
        "SELECT date, exercise, weight_kg, reps FROM sets WHERE date BETWEEN ? AND ? AND weight_kg > 0 AND reps > 0",
        (s.get("baseline_from", "2026-10-05"), end.isoformat())).fetchall()
    weekly: dict[str, dict[str, float]] = {}
    for r in rows:
        if _excluded(r, s.get("exclude", [])):
            continue
        score = r["weight_kg"] * (1 + r["reps"] / 30) if r["reps"] > 1 else r["weight_kg"]
        wk = iso_week(date.fromisoformat(r["date"]))
        ex = weekly.setdefault(r["exercise"], {})
        ex[wk] = max(ex.get(wk, 0), score)

    out = []
    for name, weeks in weekly.items():
        series = [round(weeks[w], 1) for w in sorted(weeks)]
        best = max(series)
        down = 0
        for prev, cur in zip(reversed(series[:-1]), reversed(series)):
            if cur >= prev:
                break
            down += 1
        vs_best = round((series[-1] / best - 1) * 100, 1)
        guard = "red" if vs_best <= -5 else "yellow" if down >= 2 else "green"
        out.append({"exercise": name, "weekly_best": dict(zip(sorted(weeks), series)), "best": best,
                    "latest": series[-1], "vs_best_pct": vs_best, "down_weeks_running": down, "guard": guard})
    return sorted(out, key=lambda e: -e["best"])


def training_pattern(con, end: date, days: int = 28) -> dict:
    """What his weeks actually look like over the last `days`: which workout on which weekday, sets and cardio."""
    start = end - timedelta(days=days - 1)
    span = (start.isoformat(), end.isoformat())
    by_weekday: dict[str, dict[str, int]] = {}
    for d, name in con.execute("SELECT date, name FROM activities WHERE type = 'strength_training' "
                               "AND date BETWEEN ? AND ? ORDER BY date", span):
        day = date.fromisoformat(d).strftime("%a")
        by_weekday.setdefault(day, {})
        by_weekday[day][name] = by_weekday[day].get(name, 0) + 1
    weeks = days / 7
    sessions = sum(sum(v.values()) for v in by_weekday.values())
    sets = con.execute("SELECT COUNT(*) FROM sets WHERE reps > 0 AND date BETWEEN ? AND ?", span).fetchone()[0]
    cardio = {t: round(m / weeks) for t, m in con.execute(
        "SELECT type, SUM(duration_min) FROM activities WHERE type != 'strength_training' AND type != 'meditation' "
        "AND date BETWEEN ? AND ? GROUP BY type", span)}
    order = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    return {"window": list(span), "strength_sessions_per_week": round(sessions / weeks, 1),
            "logged_sets_per_week": round(sets / weeks), "cardio_min_per_week": cardio,
            "by_weekday": {d: by_weekday[d] for d in order if d in by_weekday}}


def energy_availability(con, p: dict, start: date, end: date) -> dict:
    """EA = planned intake − Garmin activity kcal (sum of `activities.calories`, which includes BMR during the session,
    so EA comes out conservative), daily average over [start, end]. Eat-out meals replace planned food, so they are
    not added."""
    n = (end - start).days + 1
    act = con.execute("SELECT COALESCE(SUM(calories), 0) FROM activities WHERE date BETWEEN ? AND ?",
                      (start.isoformat(), end.isoformat())).fetchone()[0] / n
    intake = mean_intake(p, start, end)
    ea = intake - act
    s = p["safety"]
    band = ("green" if ea >= s["min_energy_availability_kcal"]
            else "yellow" if ea >= s.get("energy_availability_red_kcal", 1500) else "red")
    return {"intake_kcal": round(intake), "activity_kcal_per_day": round(act), "ea_kcal": round(ea),
            "ea_per_kg_ffm": round(ea / p["body"]["lean_mass_kg_est"], 1), "band": band}


def _project(w: float, pct_per_week: float, weeks: float) -> float:
    return round(w * (1 + pct_per_week / 100) ** weeks, 1)


def _project_at_cap(w: float, p: dict, weeks: float) -> float:
    """Losing at the weight-dependent cap the whole way (the fastest allowed), one week at a time."""
    steps = sorted(p["safety"]["rate_cap_pct_per_week"], key=lambda s: -s["above_kg"])
    while weeks > 0:
        pct = next(s["pct"] for s in steps if w > s["above_kg"])
        w *= 1 - pct / 100 * min(weeks, 1)
        weeks -= 1
    return round(w, 1)


def projections(p: dict, today: date, w_now: float | None, trend14: float | None, trend28: float | None) -> dict:
    """Weight and estimated body fat now and at each event / checkpoint. The cut stops at `checkpoint.maintenance_from`,
    so later dates are projected only to then. Body fat assumes lean mass holds at `body.lean_mass_kg_est`."""
    if not w_now:
        return {}
    lean = p["body"]["lean_mass_kg_est"]
    def bf(w: float) -> float:
        return round((1 - lean / w) * 100, 1)

    stop = date.fromisoformat(p["checkpoint"]["maintenance_from"])
    dates = [(e["label"], e["date"]) for e in p.get("events", [])]
    dates += [("maintenance starts", p["checkpoint"]["maintenance_from"]), ("checkpoint", p["checkpoint"]["date"])]
    out = []
    for label, d in sorted(dates, key=lambda x: x[1]):
        weeks = max((min(date.fromisoformat(d), stop) - today).days, 0) / 7
        row = {"label": label, "date": d}
        for key, trend in (("at_trend14_kg", trend14), ("at_trend28_kg", trend28)):
            row[key] = _project(w_now, trend, weeks) if trend is not None else None
        row["at_cap_kg"] = _project_at_cap(w_now, p, weeks)
        row["bf_pct_at_trend28"] = bf(row["at_trend28_kg"]) if row["at_trend28_kg"] else None
        out.append(row)
    lo, hi = p["cut"]["target_body_fat_pct"]
    return {"weight_kg": w_now, "est_bf_pct": bf(w_now), "lean_mass_kg_est": lean,
            "goal_weight_kg": [round(lean / (1 - lo / 100), 1), round(lean / (1 - hi / 100), 1)], "dates": out}


def bloodwork_status(con, p: dict, today: date) -> dict:
    last = con.execute("SELECT MAX(date) FROM bloodwork").fetchone()[0]
    every = p.get("bloodwork_every_months", 6)
    if not last:
        return {"last_recorded": None, "every_months": every, "due": None,
                "note": "no bloodwork recorded in healthgo yet; ask for the date of the last test"}
    months = round((today - date.fromisoformat(last)).days / 30.44, 1)
    return {"last_recorded": last, "months_since": months, "every_months": every, "due": months >= every}


def health_guard(con, p: dict, end: date, start: date, cut_weeks: int, sleep_week: float | None,
                 ea: dict, strength: list[dict]) -> dict:
    """The automatic rows of the Health-guard checklist, each with its band. /feel, notes and supplements stay manual."""
    slope = checks.weight_slope_pct_per_week(con, end, 14)
    cap = checks.rate_cap_pct_per_week(con, end)
    rate = None
    if slope:
        loss = -slope[0]
        kg = con.execute("SELECT kg FROM weights WHERE date <= ? ORDER BY date DESC LIMIT 1",
                         (end.isoformat(),)).fetchone()[0]
        red = loss > p["safety"]["max_loss_pct_per_week"] or loss / 100 * kg > 1.5
        rate = {"trend14_pct_per_week": slope[0], "cap": cap,
                "band": "red" if red else "yellow" if cap and loss > cap else "green"}
    lo, hi = p["safety"]["diet_break_after_weeks"]
    short_nights = con.execute("SELECT COUNT(*) FROM daily WHERE sleep_h < 6 AND date BETWEEN ? AND ?",
                               (start.isoformat(), end.isoformat())).fetchone()[0]
    sleep = None
    if sleep_week is not None:
        sleep = {"avg_h": sleep_week, "nights_under_6h": short_nights,
                 "band": "red" if sleep_week < 6 or short_nights >= 3
                 else "yellow" if sleep_week < p["safety"]["sleep_target_hours"] else "green"}
    return {
        "rate": rate,
        "energy_availability": ea,
        "deficit_weeks": {"weeks": cut_weeks, "band": "green" if cut_weeks < lo else "yellow" if cut_weeks <= hi else "red"},
        "sleep": sleep,
        "strength": [{"exercise": e["exercise"], "vs_best_pct": e["vs_best_pct"],
                      "down_weeks_running": e["down_weeks_running"], "band": e["guard"]}
                     for e in strength if e["guard"] != "green"],
    }

