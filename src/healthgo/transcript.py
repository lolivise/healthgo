"""YouTube transcript for /ask: the video's own captions as plain text with [mm:ss] marks, no model in the loop.

yt-dlp runs through `uvx` (always the latest release: YouTube breaks old ones), and only for the video's metadata.
The one caption track we want is then fetched directly: asking yt-dlp for a wildcard of languages also pulls
machine-translated tracks and trips YouTube's 429.
"""

from __future__ import annotations

import json
import re
import subprocess
import urllib.request
from pathlib import Path

PREFERRED = ["zh-TW", "zh-Hant", "zh-HK", "zh", "zh-Hans", "zh-CN", "en", "en-US", "en-GB"]


class TranscriptError(RuntimeError):
    pass


def info(url: str) -> dict:
    res = subprocess.run(["uvx", "yt-dlp", "-J", "--skip-download", "--no-warnings", url],
                         capture_output=True, text=True, timeout=180)
    if res.returncode != 0:
        raise TranscriptError(f"yt-dlp failed: {res.stderr.strip()[-300:]}")
    meta = json.loads(res.stdout)
    if meta.get("_type") == "playlist":  # a search or playlist URL: take its first video
        if not meta.get("entries"):
            raise TranscriptError("no video found at that URL")
        meta = meta["entries"][0]
    return meta


def pick_track(meta: dict) -> tuple[str, str, str] | None:
    """(kind, language, vtt url): uploaded captions first, then the auto captions in the spoken language.
    Auto-caption keys like `en-de` are machine translations, so only the original (`<lang>-orig` / `<lang>`) counts."""
    def vtt(formats: list[dict]) -> str | None:
        return next((f["url"] for f in formats if f.get("ext") == "vtt"), None)

    subs = {k: v for k, v in (meta.get("subtitles") or {}).items() if k != "live_chat"}
    for lang in PREFERRED + sorted(subs):
        if lang in subs and (u := vtt(subs[lang])):
            return "uploaded", lang, u
    auto = meta.get("automatic_captions") or {}
    spoken = meta.get("language") or ""
    for lang in [f"{spoken}-orig", spoken, *(k for k in auto if k.endswith("-orig")), "en"]:
        if lang and lang in auto and (u := vtt(auto[lang])):
            return "auto", lang, u
    return None


_TS = re.compile(r"^(\d+):(\d\d):(\d\d)\.\d+ --> ")


def vtt_to_text(vtt: str, every_s: int = 30) -> str:
    """Caption text with a [mm:ss] mark every ~30 s. Auto captions repeat each line as it scrolls: keep it once."""
    out, last_line, next_mark, now = [], None, 0, 0
    for raw in vtt.splitlines():
        if m := _TS.match(raw):
            now = int(m[1]) * 3600 + int(m[2]) * 60 + int(m[3])
            continue
        line = re.sub(r"<[^>]+>", "", raw).strip()
        if not line or line == last_line or line.startswith(("WEBVTT", "Kind:", "Language:", "NOTE")) or "-->" in line:
            continue
        if now >= next_mark:
            out.append(f"\n[{now // 60:02d}:{now % 60:02d}] ")
            next_mark = now + every_s
        out.append(line + " ")
        last_line = line
    return "".join(out).strip()


def fetch(url: str, out: Path) -> dict:
    meta = info(url)
    track = pick_track(meta)
    head = [f"# {meta.get('title', '')}", "",
            f"- Channel: {meta.get('channel') or meta.get('uploader', '')} ({meta.get('channel_url', '')})",
            f"- Uploaded: {meta.get('upload_date', '')} · duration {int(meta.get('duration') or 0) // 60} min · "
            f"views {meta.get('view_count', '')}",
            f"- URL: {meta.get('webpage_url', url)}",
            f"- Captions: {f'{track[0]} ({track[1]})' if track else 'none'}", "",
            "## Description", "", (meta.get("description") or "").strip(), "", "## Transcript", ""]
    body = "_No captions on this video._"
    if track:
        req = urllib.request.Request(track[2], headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=60) as r:
            body = vtt_to_text(r.read().decode("utf-8", "replace"))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(head) + body + "\n")
    return {"title": meta.get("title"), "channel": meta.get("channel") or meta.get("uploader"),
            "captions": f"{track[0]}:{track[1]}" if track else None, "chars": len(body), "file": str(out)}
