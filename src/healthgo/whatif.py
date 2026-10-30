"""What-if projections for /ask plan questions: the plan as written vs one changed variable. No model involved.

Rates are energy-derived, not read off the weight trend: TDEE comes from the 28-day trend at the planned intake (the
same estimate /review uses), so a diet change that started a few days ago is already in the plan line. Each day loses
`(intake − TDEE + net extra burn) × 7 / KCAL_PER_KG` as a % of the starting weight, held as a constant %/wk the way
`facts.projections` does, so the kg lost per week shrinks as weight falls. The cut stops at
`checkpoint.maintenance_from`; after that the plan holds weight flat.
"""

from __future__ import annotations

from datetime import date, timedelta

from . import checks, config, db, facts
from .weekly import KCAL_PER_KG, _weight_avg

# Extra activity is partly offset by lower basal expenditure: ~28 % (n=1,754 doubly labelled water,
# evidence-muscle-and-metabolism.md). Applied to --burn only; the TDEE estimate already reflects his current activity.
COMPENSATION = 0.28
REACH_HORIZON_WEEKS = 104


def _rate(p: dict, d: date, tdee: float, w0: float, delta: float = 0, burn: float = 0) -> float:
    """%/wk on day `d` (negative = losing) at the planned intake plus `delta`, with `burn` extra kcal/day of activity."""
    net = facts.intake_on(p, d) + delta - tdee - burn * (1 - COMPENSATION)
    return net * 7 / KCAL_PER_KG / w0 * 100


def project(w0: float, start: date, end: date, rate_on, stop: date | None = None) -> float:
    """Weight on `end`, stepping one day at a time from `start` at `rate_on(day)` %/wk; flat from `stop` on."""
    w = w0
    d = start
    while d < end:
        if stop is None or d < stop:
            w *= (1 + rate_on(d) / 100) ** (1 / 7)
        d += timedelta(days=1)
    return round(w, 1)


def reach(w0: float, start: date, target: float, rate_on) -> str | None:
    """First day the weight is at or below `target` if the cut never stopped, within REACH_HORIZON_WEEKS."""
    w = w0
    for i in range(REACH_HORIZON_WEEKS * 7):
        if w <= target:
            return (start + timedelta(days=i)).isoformat()
        w *= (1 + rate_on(start + timedelta(days=i)) / 100) ** (1 / 7)
    return None


def _band(loss_pct: float, cap: float | None, hard: float) -> str:
    if loss_pct > hard:
        return "red"
    if cap is not None and loss_pct > cap:
        return "yellow"
    return "green"


def _cap(p: dict, kg: float) -> float | None:
    for step in sorted(p["safety"].get("rate_cap_pct_per_week", []), key=lambda s: -s["above_kg"]):
        if kg > step["above_kg"]:
            return step["pct"]
    return None


def run(*, kcal: float | None = None, delta: float = 0, change_from: date | None = None, burn: float = 0,
        loss_rate: float | None = None, weight: float | None = None, at: date | None = None,
        lean: float | None = None, protein: float | None = None, fat: float | None = None,
        target: float | None = None, p: dict | None = None, con=None, today: date | None = None) -> dict:
    """Plan vs scenario. `kcal` (absolute) or `delta` changes intake from `change_from`; `burn` adds daily activity kcal
    (negative = less); `loss_rate` replaces the energy model with a fixed % lost per week; `weight` + `at` start the
    scenario from a hypothetical weight on a date; `lean` replaces the lean-mass estimate."""
    p = p or config.plan()
    today = today or config.today()
    own = con is None
    con = con or db.connect()
    try:
        last = con.execute("SELECT MAX(date) FROM weights").fetchone()[0]
        w_now, _ = _weight_avg(con, today - timedelta(days=6), today)
        if w_now is None:
            return {"error": "no weigh-ins in the last 7 days", "data_through": last}
        slope14 = checks.weight_slope_pct_per_week(con, today, 14)
        slope28 = checks.weight_slope_pct_per_week(con, today, 28)
        ea = facts.energy_availability(con, p, today - timedelta(days=27), today)
        strength = facts.strength_since_baseline(con, p, today)
    finally:
        if own:
            con.close()
    if not slope28:
        return {"error": "fewer than 5 weigh-in days in the last 28", "data_through": last}
    tdee = facts.tdee_estimate(p, today, w_now, slope28[0], KCAL_PER_KG)

    start = at or today
    w0 = weight or w_now
    change_from = change_from or start
    lean_kg = lean or p["body"]["lean_mass_kg_est"]
    stop = date.fromisoformat(p["checkpoint"]["maintenance_from"])
    target = target or p.get("final_goal", {}).get("phase_switch_weight_band", {}).get("stop_cut_kg")

    def plan_rate(d: date) -> float:
        return _rate(p, d, tdee, w_now)

    def scen_delta(d: date) -> float:
        if d < change_from:
            return 0
        return kcal - facts.intake_on(p, d) if kcal is not None else delta

    def scen_rate(d: date) -> float:
        if loss_rate is not None and d >= change_from:
            return -loss_rate
        return _rate(p, d, tdee, w0, scen_delta(d), burn if d >= change_from else 0)

    def bf(w: float, lm: float) -> float:
        return round((1 - lm / w) * 100, 1)

    dates = [(e["label"], e["date"]) for e in p.get("events", [])]
    dates += [("maintenance starts", p["checkpoint"]["maintenance_from"]), ("checkpoint", p["checkpoint"]["date"])]
    rows = []
    for label, d in sorted(dates, key=lambda x: x[1]):
        day = date.fromisoformat(d)
        if day < today:
            continue
        plan_kg = project(w_now, today, day, plan_rate, stop)
        scen_kg = project(w0, start, day, scen_rate, stop) if day >= start else None
        rows.append({"label": label, "date": d, "plan_kg": plan_kg, "scenario_kg": scen_kg,
                     "plan_bf_pct": bf(plan_kg, p["body"]["lean_mass_kg_est"]),
                     "scenario_bf_pct": bf(scen_kg, lean_kg) if scen_kg else None})

    s = p["safety"]
    first = max(change_from, start)
    plan_now, scen_now = plan_rate(first), scen_rate(first)
    intake = facts.intake_on(p, first) + scen_delta(first)
    scen_ea = intake - ea["activity_kcal_per_day"] - burn
    safety = {
        "rate": {"plan_pct_per_week": round(plan_now, 2), "scenario_pct_per_week": round(scen_now, 2),
                 "cap": _cap(p, w0), "hard_stop": s["max_loss_pct_per_week"],
                 "band": _band(-scen_now, _cap(p, w0), s["max_loss_pct_per_week"])},
        "intake_kcal": {"scenario": round(intake), "min": s["min_kcal"], "ok": intake >= s["min_kcal"]},
        "energy_availability_kcal": {"scenario": round(scen_ea), "min": s["min_energy_availability_kcal"],
                                     "red_below": s.get("energy_availability_red_kcal"),
                                     "ok": scen_ea >= s["min_energy_availability_kcal"]},
    }
    if protein is not None:
        safety["protein"] = {"g_per_kg": round(protein / w0, 2), "min_g_per_kg": s["min_protein_g_per_kg"],
                             "g_per_kg_ffm": round(protein / lean_kg, 2),
                             "min_g_per_kg_ffm": s.get("min_protein_g_per_kg_ffm"),
                             "ok": protein / w0 >= s["min_protein_g_per_kg"]
                             and protein / lean_kg >= s.get("min_protein_g_per_kg_ffm", 0)}
    if fat is not None:
        safety["fat"] = {"g_per_kg": round(fat / w0, 2), "min_g_per_kg": s["min_fat_g_per_kg"],
                         "ok": fat / w0 >= s["min_fat_g_per_kg"]}

    lo, hi = p["cut"]["target_body_fat_pct"]
    return {
        "data_through": last,
        "now": {"date": today.isoformat(), "weight_7d_kg": w_now,
                "trend14_pct_per_week": slope14[0] if slope14 else None, "trend28_pct_per_week": slope28[0],
                "tdee_est_kcal": round(tdee), "intake_kcal": facts.intake_on(p, today),
                "activity_kcal_per_day": ea["activity_kcal_per_day"],
                "est_bf_pct": bf(w_now, p["body"]["lean_mass_kg_est"]),
                "lean_mass_kg_est": p["body"]["lean_mass_kg_est"]},
        "scenario": {"start": start.isoformat(), "start_kg": w0, "change_from": change_from.isoformat(),
                     "kcal": kcal, "delta_kcal": delta if kcal is None else None, "burn_kcal": burn,
                     "loss_rate_pct_per_week": loss_rate, "lean_mass_kg": lean_kg},
        "safety": safety,
        "dates": rows,
        "reach": {"target_kg": target, "if_cutting_non_stop": True,
                  "plan": reach(w_now, today, target, plan_rate) if target else None,
                  "scenario": reach(w0, start, target, scen_rate) if target else None},
        "goal_weight_kg": [round(lean_kg / (1 - lo / 100), 1), round(lean_kg / (1 - hi / 100), 1)],
        "strength": [{k: e[k] for k in ("exercise", "best", "latest", "vs_best_pct", "guard")} for e in strength],
        "assumptions": [
            f"TDEE {round(tdee)} kcal = 28-day planned intake + weight trend × {KCAL_PER_KG} kcal/kg; ±200 kcal, "
            "ignores eating out and water swings",
            "constant %/wk from the starting weight: kg lost per week shrinks as weight falls",
            f"extra activity offset {int(COMPENSATION * 100)} % by lower basal expenditure",
            f"plan holds weight flat from {p['checkpoint']['maintenance_from']} (maintenance); "
            "`reach` ignores that and assumes the cut never stops",
        ],
    }
