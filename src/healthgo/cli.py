"""healthgo CLI. Run via `uv run healthgo <command>` from the repo root."""

from __future__ import annotations

import argparse
import fcntl
import json
import logging
import sys
from contextlib import contextmanager
from datetime import date

from . import config, store

log = logging.getLogger("healthgo")


@contextmanager
def sync_lock():
    """One sync at a time (launchd job vs a manual /sync or /review)."""
    config.LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)
    with config.LOCK_FILE.open("w") as fh:
        try:
            fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            sys.exit("another healthgo sync is running; try again in a few minutes")
        yield


def _do_sync(state: dict, *, start: date | None = None, force_login: bool = False) -> dict | None:
    """Connect + sync. On Garmin trouble, alert once and return None (the caller carries on
    with the data already on disk)."""
    from . import garmin, notify, sync, vault

    try:
        client = garmin.connect(state, force_login=force_login)
        return sync.run(client, state, start)
    except garmin.LoginBlocked as e:
        log.warning("%s", e)
        notify.alert_once(state, "garmin_login",
                          "healthgo：Garmin 登入失敗，今天已嘗試過一次，24 小時後會自動再試。\n"
                          "若持續失敗，請在 healthgo 執行 /sync 排查。")
    except (garmin.GarminConnectTooManyRequestsError, sync.SyncAborted) as e:
        log.warning("rate limited: %s", e)
        notify.alert_once(state, "garmin_429",
                          "healthgo：Garmin 暫時限制了請求次數 (429)。明天 20:00 會自動補抓缺少的日期。")
    except garmin.GarminConnectAuthenticationError as e:
        log.error("authentication failed: %s", e)
        notify.alert_once(state, "garmin_auth",
                          "healthgo：Garmin 帳號登入被拒。請確認 1Password HealthGo/secrets 的密碼，"
                          "然後在 healthgo 執行 /sync。")
    except vault.VaultError as e:
        log.error("%s", e)
        notify.alert_once(state, "vault", "healthgo：讀不到 1Password 憑證，請在 healthgo 執行 /sync 排查。")
    except Exception as e:  # network down, Garmin 5xx, …: tomorrow's catch-up covers it
        log.exception("sync failed: %s", e)
    return None


def cmd_login(args) -> int:
    from . import garmin

    state = store.load_state()
    garmin.connect(state, force_login=True)
    print(f"logged in; token saved under {config.TOKENSTORE}")
    return 0


def cmd_sync(args) -> int:
    from . import db, gitops

    with sync_lock():
        state = store.load_state()
        start = date.fromisoformat(args.start) if args.start else None
        result = _do_sync(state, start=start, force_login=args.force_login)
        db.build()
        print(json.dumps({"sync": result, "complete_through": state.get("complete_through")}, indent=2))
        if not args.no_commit:
            print("git:", gitops.commit_and_push(f"data: sync {config.today()}"))
    return 0 if result is not None else 1


def cmd_build_db(args) -> int:
    from . import db

    counts = db.build()
    print(json.dumps(counts, indent=2))
    return 0


def cmd_check(args) -> int:
    from . import checks, db, notify

    db.build()
    flags = checks.run(config.today())
    for f in flags:
        print(f"[{f.key}] {f.message}")
    if not flags:
        print("no flags")
    if args.notify and not config.in_trip(config.today()):
        state = store.load_state()
        for f in flags:
            notify.alert_once(state, f.key, f"⚠️ healthgo 恢復警示\n{f.message}")
    return 0


def cmd_prepare_week(args) -> int:
    from . import db, weekly

    db.build()
    sunday = date.fromisoformat(args.week_end) if args.week_end else weekly.latest_due_sunday(config.now())
    path = weekly.prepare(sunday)
    print(path.relative_to(config.ROOT))
    return 0


def cmd_daily(args) -> int:
    """The launchd entry point: sync → checks → weekly prep if due → commit & push."""
    from . import checks, db, gitops, notify, weekly

    with sync_lock():
        state = store.load_state()
        _do_sync(state)
        db.build()
        today = config.today()
        if not config.in_trip(today):
            for f in checks.run(today):
                notify.alert_once(state, f.key, f"⚠️ healthgo 恢復警示\n{f.message}")
        sunday = weekly.latest_due_sunday(config.now())
        if sunday and not weekly.week_file(sunday).exists():
            weekly.prepare(sunday)
            if not config.in_trip(sunday):
                notify.send(weekly.ready_message(sunday))
        log.info("git: %s", gitops.commit_and_push(f"data: daily sync {today}"))
    return 0


def cmd_add(args) -> int:
    from . import db, manual

    record = manual.add(args.kind, json.loads(args.json))
    db.build()
    print(json.dumps(record, ensure_ascii=False))
    return 0


def cmd_status(args) -> int:
    from . import launchd, weekly

    state = store.load_state()
    token = config.TOKENSTORE / "garmin_tokens.json"
    reviews = store.read_jsonl(config.MANUAL / "reviews.jsonl")
    inbody = store.read_jsonl(config.MANUAL / "inbody.jsonl")
    out = {
        "today": config.today().isoformat(),
        "complete_through": state.get("complete_through"),
        "last_sync_at": state.get("last_sync_at"),
        "last_login_attempt_at": state.get("last_login_attempt_at"),
        "last_login_result": state.get("last_login_result"),
        "token_present": token.exists(),
        "launchd_loaded": launchd.is_loaded(),
        "latest_weekly": weekly.latest_week_file(),
        "last_review": reviews[-1]["date"] if reviews else None,
        "last_inbody": inbody[-1]["date"] if inbody else None,
        "in_trip": config.in_trip(config.today()),
    }
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


def cmd_notify_test(args) -> int:
    from . import notify

    ok = notify.send(args.text or "healthgo：Telegram 通知測試成功 ✅")
    print("telegram" if ok else "macOS fallback")
    return 0 if ok else 1


def cmd_install_launchd(args) -> int:
    from . import launchd

    print(launchd.install())
    return 0


def cmd_uninstall_launchd(args) -> int:
    from . import launchd

    print(launchd.uninstall())
    return 0


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    p = argparse.ArgumentParser(prog="healthgo")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("login", help="force a credential login (ignores the 24h guard)").set_defaults(fn=cmd_login)

    s = sub.add_parser("sync", help="catch-up sync, rebuild db, commit & push")
    s.add_argument("--from", dest="start", help="re-pull from this date (YYYY-MM-DD)")
    s.add_argument("--force-login", action="store_true")
    s.add_argument("--no-commit", action="store_true")
    s.set_defaults(fn=cmd_sync)

    sub.add_parser("build-db", help="rebuild data/healthgo.db from the JSON").set_defaults(fn=cmd_build_db)

    c = sub.add_parser("check", help="run the rule-based recovery checks")
    c.add_argument("--notify", action="store_true")
    c.set_defaults(fn=cmd_check)

    w = sub.add_parser("prepare-week", help="write data/weekly/<ISO week>.json")
    w.add_argument("--week-end", help="the Sunday ending the week (YYYY-MM-DD)")
    w.set_defaults(fn=cmd_prepare_week)

    sub.add_parser("daily", help="launchd entry point").set_defaults(fn=cmd_daily)

    a = sub.add_parser("add", help="append a manual record")
    a.add_argument("kind", choices=["inbody", "eating_out", "bloodwork", "weight", "review", "note"])
    a.add_argument("json", help="the record as a JSON object")
    a.set_defaults(fn=cmd_add)

    sub.add_parser("status").set_defaults(fn=cmd_status)

    n = sub.add_parser("notify-test")
    n.add_argument("text", nargs="?")
    n.set_defaults(fn=cmd_notify_test)

    sub.add_parser("install-launchd").set_defaults(fn=cmd_install_launchd)
    sub.add_parser("uninstall-launchd").set_defaults(fn=cmd_uninstall_launchd)

    args = p.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
