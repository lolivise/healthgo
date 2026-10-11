from __future__ import annotations

import json

import pytest

from healthgo import config, db, inbox, store


@pytest.fixture
def home(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA", tmp_path)
    monkeypatch.setattr(config, "MANUAL", tmp_path / "manual")
    monkeypatch.setattr(config, "STATE_FILE", tmp_path / "state.json")
    monkeypatch.setattr(inbox, "INBOX", tmp_path / "inbox")
    monkeypatch.setattr(inbox, "DONE", tmp_path / "inbox" / "done")
    return tmp_path


RAW = {"source": "cargill-cafe", "mode": "menu", "date": "2026-10-11", "meal": "lunch", "portion": 0.5,
       "items": [{"code": 1, "name": "雞排飯", "qty": 1, "kcal": 1590.3}],
       "total": {"kcal": 795.2, "protein": 27.5, "fat": 37.0, "carb": 88.2}}


def entry(id_=7, raw=RAW, kind="eat", text="雞排飯（吃 ½）"):
    return {"id": id_, "tg_message_id": -1000, "received_at": "2026-10-11T04:30:00.000Z", "kind": kind,
            "text": text, "file_id": None, "media_group_id": None, "raw": json.dumps(raw)}


def test_recipe_record_fields():
    r = inbox.recipe_record(entry())
    assert r == {"date": "2026-10-11", "meal": "lunch", "description": "雞排飯（吃 ½）", "est_kcal": 795,
                 "source": "cargill-cafe", "protein_g": 27.5, "fat_g": 37.0, "carb_g": 88.2,
                 "items": RAW["items"], "kcal_basis": "recipe", "inbox_id": 7}


@pytest.mark.parametrize("e", [
    entry(raw={**RAW, "total": {"kcal": None, "protein": None, "fat": None, "carb": None}}),  # no recipe
    entry(raw={**RAW, "source": "other"}),
    entry(kind="note"),
    {**entry(), "raw": "not json"},
    {**entry(), "raw": json.dumps({"message_id": 5, "text": "/eat pizza"})},  # a plain free-text eat
])
def test_not_recipe_based(e):
    assert inbox.recipe_record(e) is None


def test_pull_auto_records_and_files_done(home, monkeypatch):
    plain = {"message_id": 9, "text": "/eat 朋友聚餐"}
    monkeypatch.setattr(inbox, "fetch_entries", lambda since: [
        entry(8, raw={**RAW, "total": {"kcal": None, "protein": None, "fat": None, "carb": None}}, text="香腸便當 (無食譜，需估算)"),
        entry(7), entry(9, raw=plain, text="朋友聚餐")])
    assert inbox.pull() == 3
    rows = store.read_jsonl(home / "manual" / "eating_out.jsonl")
    assert len(rows) == 1 and rows[0]["est_kcal"] == 795 and rows[0]["kcal_basis"] == "recipe"
    assert (home / "inbox" / "done" / "2026-10-11_7_eat.json").exists()
    assert not (home / "inbox" / "2026-10-11_7_eat.json").exists()
    left = sorted(p.name for p in (home / "inbox").glob("*.json"))
    assert left == ["2026-10-11_8_eat.json", "2026-10-11_9_eat.json"]  # no-recipe + free text wait for /log
    assert store.load_state()["inbox_last_id"] == 9


def test_auto_record_is_idempotent(home):
    inbox.write_entry(entry())
    assert inbox.auto_record(entry())
    inbox.write_entry(entry())
    assert inbox.auto_record(entry())  # the same inbox id pulled again does not duplicate
    assert len(store.read_jsonl(home / "manual" / "eating_out.jsonl")) == 1


def test_db_eating_out_new_columns(home, monkeypatch):
    monkeypatch.setattr(config, "DB_FILE", home / "healthgo.db")
    monkeypatch.setattr(config, "DAILY_DIR", home / "daily")
    monkeypatch.setattr(config, "ACTIVITY_DIR", home / "act")
    store.append_jsonl(home / "manual" / "eating_out.jsonl", {"date": "2026-10-01", "meal": "dinner", "description": "old", "est_kcal": 900})
    inbox.write_entry(entry())
    inbox.auto_record(entry())
    db.build()
    con = db.connect()
    rows = [dict(r) for r in con.execute("SELECT * FROM eating_out ORDER BY date")]
    assert rows[0]["protein_g"] is None and rows[0]["source"] is None and rows[0]["est_kcal"] == 900
    assert rows[1]["protein_g"] == 27.5 and rows[1]["fat_g"] == 37.0 and rows[1]["carb_g"] == 88.2
    assert rows[1]["source"] == "cargill-cafe" and rows[1]["kcal_basis"] == "recipe"
