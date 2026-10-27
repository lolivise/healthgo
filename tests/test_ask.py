from __future__ import annotations

import json

import pytest

from healthgo import ask


def test_watch_prints_each_question_once_and_one_line_per_failure_streak(monkeypatch, capsys):
    replies = iter([
        [{"id": 5, "asked_at": "t", "text": "空腹咖啡傷肝？", "file_id": None}],
        RuntimeError("down"), RuntimeError("down"),
        [{"id": 5, "asked_at": "t", "text": "空腹咖啡傷肝？", "file_id": None},
         {"id": 9, "asked_at": "t", "text": "q2", "file_id": "f"}],
    ])

    def fake_pending():
        r = next(replies)
        if isinstance(r, Exception):
            raise r
        return r

    calls = {"n": 0}

    def fake_sleep(_):
        calls["n"] += 1
        if calls["n"] == 4:
            raise KeyboardInterrupt

    monkeypatch.setattr(ask, "pending", fake_pending)
    monkeypatch.setattr(ask.time, "sleep", fake_sleep)
    with pytest.raises(KeyboardInterrupt):
        ask.watch(0)
    lines = [json.loads(l) for l in capsys.readouterr().out.splitlines()]
    assert [l["event"] for l in lines] == ["ask", "error", "recovered", "ask"]
    assert lines[0]["text"] == "空腹咖啡傷肝？" and lines[3] == {"event": "ask", "id": 9, "asked_at": "t",
                                                                "text": "q2", "has_file": True}


def test_answer_keeps_question_pending_when_telegram_fails(monkeypatch, tmp_path):
    f = tmp_path / "a.md"
    f.write_text("# x")
    monkeypatch.setattr(ask.notify, "send_report", lambda *a, **k: False)
    monkeypatch.setattr(ask, "_request", lambda *a, **k: pytest.fail("must not mark done"))
    assert ask.answer(5, f) == {"id": 5, "telegram": False, "done": False}
