from __future__ import annotations

import sqlite3
from datetime import date, timedelta

import pytest

from healthgo import db, whatif

TODAY = date(2026, 10, 30)
PLAN = {
    "baseline_intake_kcal": 2500,
    "intake_kcal_schedule": [{"from": "2026-09-01", "kcal": 2500}],
    "cut": {"target_body_fat_pct": [15, 18]},
    "checkpoint": {"date": "2027-01-22", "maintenance_from": "2026-12-14"},
    "events": [{"date": "2026-12-04", "label": "party"}, {"date": "2026-10-01", "label": "past"}],
    "body": {"lean_mass_kg_est": 68.0},
    "safety": {"max_loss_pct_per_week": 1.0, "min_kcal": 1700, "min_protein_g_per_kg": 1.6,
               "min_protein_g_per_kg_ffm": 2.3, "min_fat_g_per_kg": 0.7,
               "min_energy_availability_kcal": 1700, "energy_availability_red_kcal": 1500,
               "rate_cap_pct_per_week": [{"above_kg": 84, "pct": 0.7}, {"above_kg": 0, "pct": 0.5}]},
    "strength": {"baseline_from": "2026-10-05", "exclude": []},
    "final_goal": {"phase_switch_weight_band": {"stop_cut_kg": 81}},
}


@pytest.fixture
def con():
    """28 days losing a steady 0.1 kg/day from 92 kg, 500 kcal/day of logged activity."""
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    c.executescript(db.SCHEMA)
    for i in range(28):
        d = (TODAY - timedelta(days=27 - i)).isoformat()
        c.execute("INSERT INTO weights (date, kg) VALUES (?, ?)", (d, 92 - 0.1 * i))
        c.execute("INSERT INTO activities (date, calories) VALUES (?, ?)", (d, 500))
    return c


def run(con, **kw):
    return whatif.run(p=PLAN, con=con, today=TODAY, **kw)


def test_plan_line_matches_the_measured_loss(con):
    r = run(con)
    # 0.1 kg/day × 6,850 = 685 kcal deficit → TDEE ≈ 3,185 at 2,500 kcal (the slope is a % of the 28-day mean weight,
    # converted back at the 7-day average, as /review does: a few kcal off)
    assert r["now"]["tdee_est_kcal"] == pytest.approx(3185, abs=15)
    assert r["safety"]["rate"]["plan_pct_per_week"] == pytest.approx(-0.7 / 89.6 * 100, abs=0.02)
    assert [d["label"] for d in r["dates"]] == ["party", "maintenance starts", "checkpoint"]
    # flat after maintenance starts
    assert r["dates"][1]["plan_kg"] == r["dates"][2]["plan_kg"]


def test_eating_more_slows_the_loss_and_moves_reach_later(con):
    plan, more = run(con), run(con, delta=300)
    assert more["safety"]["rate"]["scenario_pct_per_week"] > plan["safety"]["rate"]["scenario_pct_per_week"]
    assert more["dates"][0]["scenario_kg"] > more["dates"][0]["plan_kg"]
    assert more["reach"]["scenario"] > more["reach"]["plan"]


def test_extra_burn_is_partly_compensated_and_cuts_energy_availability(con):
    burn = run(con, burn=400)
    drop = burn["safety"]["rate"]["plan_pct_per_week"] - burn["safety"]["rate"]["scenario_pct_per_week"]
    assert drop == pytest.approx(400 * (1 - whatif.COMPENSATION) * 7 / 6850 / 89.6 * 100, abs=0.02)
    assert burn["safety"]["energy_availability_kcal"]["scenario"] == 2500 - 500 - 400
    assert burn["safety"]["energy_availability_kcal"]["ok"] is False


def test_safety_bands_and_floors(con):
    r = run(con, kcal=1600, protein=120, fat=50)
    assert r["safety"]["rate"]["band"] == "red"
    assert r["safety"]["intake_kcal"]["ok"] is False
    assert r["safety"]["protein"]["ok"] is False and r["safety"]["fat"]["ok"] is False


def test_hypothetical_weight_starts_the_scenario_later(con):
    r = run(con, weight=85, at=date(2026, 12, 1), loss_rate=0.5, lean=70)
    assert r["dates"][0]["scenario_kg"] == pytest.approx(85 * 0.995 ** (3 / 7), abs=0.1)
    assert r["dates"][0]["scenario_bf_pct"] == pytest.approx((1 - 70 / r["dates"][0]["scenario_kg"]) * 100, abs=0.1)
    assert r["goal_weight_kg"] == [82.4, 85.4]


def test_no_recent_weigh_ins_is_an_error():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    c.executescript(db.SCHEMA)
    assert "error" in whatif.run(p=PLAN, con=c, today=TODAY)
