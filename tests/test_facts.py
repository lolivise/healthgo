from __future__ import annotations

import sqlite3
from datetime import date

import pytest

from healthgo import db, facts

PLAN = {
    "baseline_intake_kcal": 2000,
    "intake_kcal_schedule": [{"from": "2026-10-01", "kcal": 2000}, {"from": "2026-10-26", "kcal": 2500}],
    "cut": {"target_body_fat_pct": [15, 18]},
    "checkpoint": {"date": "2027-01-22", "maintenance_from": "2026-12-14"},
    "events": [{"date": "2026-12-04", "label": "party"}],
    "body": {"lean_mass_kg_est": 68.0},
    "safety": {"min_energy_availability_kcal": 1700, "energy_availability_red_kcal": 1500,
               "rate_cap_pct_per_week": [{"above_kg": 84, "pct": 0.7}, {"above_kg": 0, "pct": 0.5}]},
    "strength": {"baseline_from": "2026-10-05",
                 "exclude": [{"date": "2026-10-10"}, {"exercise": "KICKBACK", "before": "2026-10-22"}]},
    "bloodwork_every_months": 6,
}


@pytest.fixture
def con():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    c.executescript(db.SCHEMA)
    return c


def sets(con, *rows):
    con.executemany("INSERT INTO sets (date, exercise, weight_kg, reps) VALUES (?,?,?,?)", rows)


def by_name(result, name):
    return next(e for e in result if e["exercise"] == name)


def test_intake_follows_the_schedule():
    assert facts.intake_on(PLAN, date(2026, 10, 25)) == 2000
    assert facts.intake_on(PLAN, date(2026, 10, 26)) == 2500
    assert facts.mean_intake(PLAN, date(2026, 10, 25), date(2026, 10, 26)) == 2250


def test_strength_drops_excluded_sessions_and_pre_baseline(con):
    sets(con, ("2026-09-30", "PULLDOWN", 80, 10),   # before baseline: technique phase
         ("2026-10-07", "PULLDOWN", 50, 12),
         ("2026-10-10", "PULLDOWN", 60, 9),         # other gym
         ("2026-10-14", "PULLDOWN", 55, 12),
         ("2026-10-15", "KICKBACK", 22.5, 10),       # before the form reset
         ("2026-10-22", "KICKBACK", 15, 15))
    r = facts.strength_since_baseline(con, PLAN, date(2026, 10, 25))
    pull = by_name(r, "PULLDOWN")
    assert pull["weekly_best"] == {"2026-W41": 70.0, "2026-W42": 77.0}
    assert pull["guard"] == "green"
    assert by_name(r, "KICKBACK")["weekly_best"] == {"2026-W43": 22.5}  # 15 × 15, uncapped Epley


def test_strength_guard_bands(con):
    sets(con, ("2026-10-06", "BENCH", 60, 10), ("2026-10-13", "BENCH", 59.5, 10), ("2026-10-20", "BENCH", 59, 10),
         ("2026-10-06", "ROW", 40, 10), ("2026-10-13", "ROW", 37, 10))
    r = facts.strength_since_baseline(con, PLAN, date(2026, 10, 25))
    bench = by_name(r, "BENCH")
    assert bench["down_weeks_running"] == 2 and bench["guard"] == "yellow"
    assert by_name(r, "ROW")["guard"] == "red"  # −7.5 % from best


def test_energy_availability_bands(con):
    con.executemany("INSERT INTO activities (id, date, type, calories) VALUES (?,?,?,?)",
                    [(1, "2026-10-20", "treadmill_running", 2100), (2, "2026-10-21", "treadmill_running", 1400)])
    ea = facts.energy_availability(con, PLAN, date(2026, 10, 19), date(2026, 10, 25))
    assert ea["activity_kcal_per_day"] == 500 and ea["ea_kcal"] == 1500
    assert ea["band"] == "yellow"
    assert ea["ea_per_kg_ffm"] == 22.1


def test_projection_stops_at_maintenance():
    pr = facts.projections(PLAN, date(2026, 10, 25), 89.0, -1.0, -0.5)
    party, maint, checkpoint = pr["dates"]
    assert party["label"] == "party" and party["at_trend28_kg"] > maint["at_trend28_kg"]
    assert maint["at_trend28_kg"] == checkpoint["at_trend28_kg"]
    assert maint["at_cap_kg"] < 89.0 and maint["at_cap_kg"] >= maint["at_trend14_kg"]
    assert pr["goal_weight_kg"] == [80.0, 82.9]


def test_bloodwork_due(con):
    assert facts.bloodwork_status(con, PLAN, date(2026, 10, 25))["last_recorded"] is None
    con.execute("INSERT INTO bloodwork VALUES ('2026-03-01', '{}')")
    b = facts.bloodwork_status(con, PLAN, date(2026, 10, 25))
    assert b["due"] is True and b["months_since"] > 6
