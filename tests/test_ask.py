from __future__ import annotations

import json

import pytest

from healthgo import ask


def test_watch_prints_each_question_once_and_one_line_per_failure_streak(monkeypatch, capsys, tmp_path):
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

    cards = []
    monkeypatch.setattr(ask, "status", lambda i, t, done=False: cards.append((i, t)))
    monkeypatch.setattr(ask, "PULLS", tmp_path)
    monkeypatch.setattr(ask, "pending", fake_pending)
    monkeypatch.setattr(ask.time, "sleep", fake_sleep)
    with pytest.raises(KeyboardInterrupt):
        ask.watch(0)
    lines = [json.loads(l) for l in capsys.readouterr().out.splitlines()]
    assert [l["event"] for l in lines] == ["ask", "error", "recovered", "ask"]
    assert lines[0]["text"] == "空腹咖啡傷肝？" and lines[3] == {"event": "ask", "id": 9, "asked_at": "t",
                                                                "text": "q2", "has_file": True}
    assert cards == [(5, "收到，開始處理"), (9, "收到，排隊中（前面還有 1 題）")]


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


def test_card_marks_only_the_last_line_in_progress():
    lines = [["09:41", "收到"], ["09:42", "查 PubMed"]]
    assert ask.render_card(lines, False) == "🔎 /ask 進度\n✅ 09:41 收到\n⏳ 09:42 查 PubMed"
    assert ask.render_card(lines, True).endswith("✅ 09:42 查 PubMed")


def test_status_sends_once_then_edits(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(ask, "PULLS", tmp_path)
    monkeypatch.setattr(ask.notify, "api", lambda m, p: calls.append((m, p)) or {"message_id": 77})
    assert ask.status(5, "收到") and ask.status(5, "查知識庫")
    assert calls[0][0] == "sendMessage" and calls[0][1]["reply_parameters"]["message_id"] == 5
    assert calls[1][0] == "editMessageText" and calls[1][1]["message_id"] == 77
    assert calls[1][1]["text"].endswith("⏳ " + calls[1][1]["text"].split("⏳ ")[1]) and "✅" in calls[1][1]["text"]


SOURCES_HEAD = """# Source track record

| Source | Type | Checked | ✅ | 🟡 | ❌ | ❓ | Pattern | Files |
|---|---|---|---|---|---|---|---|---|
"""


def test_update_sources_adds_then_accumulates(tmp_path):
    f = tmp_path / "sources.md"
    f.write_text(SOURCES_HEAD)
    src = {"name": "早安健康", "type": "YouTube", "url": "https://youtube.com/@x",
           "verdicts": {"✅": 0, "🟡": 1, "❌": 1, "❓": 0}, "pattern": "名醫背書、只講好處"}
    ask.update_sources(f, src, "a.md")
    ask.update_sources(f, {**src, "verdicts": {"✅": 1}, "pattern": ""}, "b.md")
    row = f.read_text().splitlines()[-1]
    assert row == ("| [早安健康](https://youtube.com/@x) | YouTube | 3 | 1 | 1 | 1 | 0 | 名醫背書、只講好處 | "
                   "[a.md](a.md) · [b.md](b.md) |")
    ask.update_sources(f, {"name": "自己聽到的", "verdicts": {"✅": 1}}, "c.md")
    assert f.read_text().splitlines()[-1] == row
