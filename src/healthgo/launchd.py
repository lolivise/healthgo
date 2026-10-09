"""Install the single launchd job: daily 20:00, Sunday 20:30, and at login.

One job covers both schedules: `healthgo daily` always syncs, checks, and prepares
the weekly file if a Sunday 20:30 has passed without one. RunAtLoad catches the
case where the Mac was powered off (launchd only replays missed runs after sleep).
"""

from __future__ import annotations

import os
import plistlib
import subprocess
from pathlib import Path

from . import config

LABEL = "com.healthgo.daily"
PLIST = Path.home() / "Library" / "LaunchAgents" / f"{LABEL}.plist"
LOG_DIR = Path.home() / "Library" / "Logs" / "healthgo"


def _domain() -> str:
    return f"gui/{os.getuid()}"


def install() -> str:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    job = {
        "Label": LABEL,
        "ProgramArguments": [str(config.ROOT / "bin" / "healthgo-job")],
        "WorkingDirectory": str(config.ROOT),
        "StartCalendarInterval": [{"Hour": 20, "Minute": 0}, {"Weekday": 0, "Hour": 20, "Minute": 30}],
        "RunAtLoad": True,
        "StandardOutPath": str(LOG_DIR / "daily.log"),
        "StandardErrorPath": str(LOG_DIR / "daily.log"),
        "ProcessType": "Background",
    }
    PLIST.parent.mkdir(parents=True, exist_ok=True)
    if is_loaded():
        subprocess.run(["launchctl", "bootout", f"{_domain()}/{LABEL}"], capture_output=True)
    PLIST.write_bytes(plistlib.dumps(job))
    res = subprocess.run(["launchctl", "bootstrap", _domain(), str(PLIST)], capture_output=True, text=True)
    if res.returncode != 0:
        raise SystemExit(f"launchctl bootstrap failed: {res.stderr.strip()}")
    return f"installed {PLIST} (logs: {LOG_DIR / 'daily.log'})"


def uninstall() -> str:
    subprocess.run(["launchctl", "bootout", f"{_domain()}/{LABEL}"], capture_output=True)
    PLIST.unlink(missing_ok=True)
    return f"removed {LABEL}"


def is_loaded() -> bool:
    return subprocess.run(["launchctl", "print", f"{_domain()}/{LABEL}"], capture_output=True).returncode == 0
