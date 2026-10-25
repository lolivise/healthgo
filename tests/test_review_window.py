from __future__ import annotations

import json
from datetime import date, datetime
from zoneinfo import ZoneInfo

import pytest

from healthgo import config, sync, weekly

TZ = ZoneInfo("Australia/Perth")


@pytest.fixture
def home(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "MANUAL", tmp_path / "manual")
    (tmp_path / "manual").mkdir()
    return tmp_path


def reviews(home, *records):
    (home / "manual" / "reviews.jsonl").write_text("".join(json.dumps(r) + "\n" for r in records))


def at(s: str) -> datetime:
    return datetime.fromisoformat(s).replace(tzinfo=TZ)


def test_last_complete_day_counts_today_from_18(monkeypatch):
    monkeypatch.setattr(config, "now", lambda: at("2026-10-28T17:59"))
    assert config.last_complete_day() == date(2026, 10, 27)
    monkeypatch.setattr(config, "now", lambda: at("2026-10-28T18:00"))
    assert config.last_complete_day() == date(2026, 10, 28)


def test_sunday_evening_is_full_week(home):
    reviews(home, {"date": "2026-10-18", "week": "2026-W42", "recorded_at": "2026-10-18T20:52:23+08:00"},
            {"date": "2026-10-24", "week": "2026-W43", "recorded_at": "2026-10-24T17:12:48+08:00"})
    plan = weekly.review_plan(at("2026-10-25T19:00"))
    assert plan["target"]["kind"] == "full"
    assert plan["target"]["week"] == "2026-W43"
    assert plan["target"]["all_day_metrics_through"] == "2026-10-25"
    assert plan["catch_up"] is None  # W42 was reviewed Sunday evening


def test_saturday_review_is_not_full(home):
    reviews(home, {"date": "2026-10-24", "week": "2026-W43", "recorded_at": "2026-10-24T17:12:48+08:00"})
    plan = weekly.review_plan(at("2026-10-28T13:00"))
    assert plan["target"]["kind"] == "midweek"
    assert plan["target"]["week"] == "2026-W44"
    assert plan["target"]["report"] == "reports/2026-W44-midweek-10-28.md"
    assert plan["target"]["through"] == "2026-10-28"
    assert plan["target"]["all_day_metrics_through"] == "2026-10-27"
    assert plan["catch_up"]["week"] == "2026-W43"
    assert plan["catch_up"]["week_end"] == "2026-10-25"


def test_midweek_review_after_full_needs_no_catch_up(home):
    reviews(home, {"date": "2026-10-25", "week": "2026-W43", "kind": "full", "through": "2026-10-25"},
            {"date": "2026-10-28", "week": "2026-W44", "kind": "midweek", "through": "2026-10-28"})
    plan = weekly.review_plan(at("2026-10-29T18:30"))
    assert plan["catch_up"] is None
    assert plan["target"]["all_day_metrics_through"] == "2026-10-29"


def test_sunday_before_18_is_midweek(home):
    reviews(home, {"date": "2026-10-18", "week": "2026-W42", "kind": "full", "through": "2026-10-18"})
    plan = weekly.review_plan(at("2026-10-25T17:00"))
    assert plan["target"]["kind"] == "midweek"
    assert plan["target"]["week"] == "2026-W43"
    assert plan["catch_up"] is None


def test_older_missed_weeks_listed(home):
    reviews(home, {"date": "2026-10-18", "week": "2026-W42", "kind": "full", "through": "2026-10-18"})
    plan = weekly.review_plan(at("2026-11-11T09:00"))  # Wed of W46; W43–W45 never fully reviewed
    assert plan["catch_up"]["week"] == "2026-W45"
    assert plan["older_weeks_without_full_review"] == ["2026-W43", "2026-W44"]


def test_sync_window_covers_the_last_pull_day(monkeypatch):
    monkeypatch.setattr(config, "now", lambda: at("2026-10-27T18:30"))
    state = {"complete_through": "2026-10-26", "last_sync_at": "2026-10-26T13:00:00+08:00"}
    window = sync.sync_window(state)
    assert window[0] <= date(2026, 10, 26) and window[-1] == date(2026, 10, 27)
    # a stale complete_through (a failed day) can't push the start past the last pull either
    state = {"complete_through": "2026-10-30", "last_sync_at": "2026-10-20T13:00:00+08:00"}
    monkeypatch.setattr(config, "now", lambda: at("2026-10-31T10:00"))
    assert sync.sync_window(state)[0] == date(2026, 10, 20)
