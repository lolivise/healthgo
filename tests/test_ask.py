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


def test_vtt_auto_captions_dedupe_and_marks():
    from healthgo import transcript

    vtt = """WEBVTT
Kind: captions
Language: en

00:00:01.000 --> 00:00:03.000
zone two is <c>easy</c>

00:00:03.000 --> 00:00:05.000
zone two is easy

00:00:40.000 --> 00:00:42.000
lactate under two
"""
    assert transcript.vtt_to_text(vtt) == "[00:01] zone two is easy \n[00:40] lactate under two"


def test_pick_track_skips_machine_translations():
    from healthgo import transcript

    meta = {"language": "en", "subtitles": {},
            "automatic_captions": {"en-de": [{"ext": "vtt", "url": "de"}], "en-orig": [{"ext": "vtt", "url": "orig"}]}}
    assert transcript.pick_track(meta) == ("auto", "en-orig", "orig")
    meta["subtitles"] = {"zh-TW": [{"ext": "json3", "url": "x"}, {"ext": "vtt", "url": "tw"}]}
    assert transcript.pick_track(meta) == ("uploaded", "zh-TW", "tw")
