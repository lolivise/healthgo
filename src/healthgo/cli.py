"""healthgo CLI. Run via `uv run healthgo <command>` from the repo root."""

from __future__ import annotations

import argparse
import fcntl
import json
import logging
import sys
from contextlib import contextmanager
from datetime import date
from pathlib import Path

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
                          "healthgo：Garmin 暫時限制了請求次數 (429)。下次執行 /review 時會自動補抓缺少的日期。")
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


def _pull_inbox() -> None:
    """Pull Telegram inbox entries; never fails the caller. Log the type only (URLs carry tokens)."""
    from . import inbox

    try:
        n = inbox.pull()
        if n:
            log.info("inbox: %d new entries", n)
    except inbox.InboxError as e:
        log.warning("inbox skipped: %s", e)
    except Exception as e:
        log.warning("inbox pull failed (%s)", type(e).__name__)


def _refresh_menu(state_shop: str = "cargill-cafe") -> None:
    """Daily: re-export the Cargill Cafe recipes, recompute, push to the worker when the menu changed.
    Never fails the caller: any error is a warning (the Mac or tunnel being offline must not break the sync)."""
    from . import menu, notify

    try:
        out = menu.sync(state_shop, do_export=True, close=True)
        out.pop("_export_counts", None)
        new = menu.new_unmapped(state_shop, out)
        if new:
            notify.alert_once(store.load_state(), "menu_unmapped:" + ",".join(new)[:80],
                              "healthgo：Cargill 菜單出現沒有營養資料的新食材：" + "、".join(new[:10])
                              + "\n請在 nutrition-map.json 補上。")
    except BaseException as e:  # SystemExit from the exporter included
        log.warning("menu-sync skipped (%s)", type(e).__name__)
        return
    try:
        r = menu.push(state_shop)
        log.info("menu-push: %s", r)
    except BaseException as e:
        log.warning("menu-push failed (%s)", type(e).__name__)


def cmd_inbox(args) -> int:
    from . import inbox

    if args.list:
        print(inbox.format_table(inbox.pending()))
        return 0
    if args.done:
        moved = inbox.mark_done(args.done)
        print(f"moved {len(moved)} files to data/inbox/done/")
        return 0 if moved else 1
    try:
        print(f"pulled {inbox.pull()} new entries")
    except inbox.InboxError as e:
        print(e, file=sys.stderr)
        return 1
    except Exception as e:
        print(f"inbox pull failed ({type(e).__name__})", file=sys.stderr)
        return 1
    return 0


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


def cmd_pubmed(args) -> int:
    from . import pubmed

    sectors = args.sector or [s for s, v in pubmed.research()["sectors"].items() if v["cadence"] == "quarterly"]
    since = date.fromisoformat(args.since) if args.since else None
    until = date.fromisoformat(args.until) if args.until else None
    for s in sectors:
        print(json.dumps(pubmed.pull(s, since, until), ensure_ascii=False))
    return 0


def cmd_prepare_week(args) -> int:
    from . import db, weekly

    db.build()
    sunday = date.fromisoformat(args.week_end) if args.week_end else weekly.latest_due_sunday(config.now())
    path = weekly.prepare(sunday)
    print(path.relative_to(config.ROOT))
    return 0


def cmd_review_plan(args) -> int:
    from . import weekly

    print(json.dumps(weekly.review_plan(config.now()), ensure_ascii=False, indent=2))
    return 0


def cmd_pull(args) -> int:
    """What /review runs first: everything the old scheduled job did, minus the Telegram pings.

    Garmin catch-up sync → Telegram inbox → Cargill menu refresh → rebuild db → print recovery flags →
    commit & push. A Garmin failure is reported, not fatal: the review carries on with the data on disk.
    """
    from . import checks, db, gitops

    with sync_lock():
        state = store.load_state()
        previous = state.get("last_pull")
        started = config.now().isoformat(timespec="seconds")
        result = _do_sync(state)
        _pull_inbox()
        _refresh_menu()
        db.build()
        state = store.load_state()
        # Every pull is stamped, so the next review can say what it covers since this one.
        state["last_pull"] = {"at": started, "garmin": "ok" if result is not None else "failed",
                              "garmin_window": state.get("last_sync_window") if result is not None else None,
                              "inbox_last_id": state.get("inbox_last_id")}
        store.save_state(state)
        flags = checks.run(config.today())
        print(json.dumps({"sync": "ok" if result is not None else "failed",
                          "previous_pull_at": (previous or {}).get("at") or state.get("last_sync_at"),
                          "this_pull_at": started,
                          "garmin_window": state["last_pull"]["garmin_window"],
                          "complete_through": state.get("complete_through"),
                          "all_day_metrics_through": config.last_complete_day().isoformat(),
                          "flags": [f"{f.key}: {f.message}" for f in flags]}, ensure_ascii=False, indent=2))
        print("git:", gitops.commit_and_push(f"data: pull {config.today()}"))
    return 0 if result is not None else 1


def cmd_daily(args) -> int:
    """The launchd entry point: sync → checks → weekly prep if due → commit & push."""
    from . import checks, db, gitops, notify, weekly

    with sync_lock():
        state = store.load_state()
        _do_sync(state)
        _pull_inbox()
        _refresh_menu()
        state = store.load_state()  # the inbox pull and menu refresh saved their own keys; don't clobber them
        db.build()
        today = config.today()
        if not config.in_trip(today):
            for f in checks.run(config.today()):
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

    record = json.loads(args.json)
    record = manual.add(args.kind, record)
    db.build()
    print(json.dumps(record, ensure_ascii=False))
    return 0


def cmd_status(args) -> int:
    from . import launchd, weekly

    state = store.load_state()
    token = config.TOKENSTORE / "garmin_tokens.json"
    reviews = store.read_jsonl(config.MANUAL / "reviews.jsonl")
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
        "in_trip": config.in_trip(config.today()),
    }
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


def cmd_notify_test(args) -> int:
    from . import notify

    ok = notify.send(args.text or "healthgo：Telegram 通知測試成功 ✅")
    print("telegram" if ok else "macOS fallback")
    return 0 if ok else 1


def cmd_send_report(args) -> int:
    from . import notify

    path = Path(args.path)
    if not path.is_absolute():
        path = config.ROOT / path
    ok = notify.send_report(path)
    print("telegram" if ok else "failed (macOS notification shown)")
    return 0 if ok else 1


def cmd_install_launchd(args) -> int:
    from . import launchd

    print(launchd.install())
    return 0


def cmd_uninstall_launchd(args) -> int:
    from . import launchd

    print(launchd.uninstall())
    return 0


def cmd_menu_sync(args) -> int:
    from . import menu

    out = menu.sync(args.shop, do_export=not args.no_export, close=args.close)
    if out.pop("_export_counts"):
        print("exported to", menu.shop_dir(args.shop) / "pos")
    print(menu.format_summary(out))
    return 0


def cmd_menu_push(args) -> int:
    from . import menu

    try:
        r = menu.push(args.shop, force=args.force)
    except Exception as e:
        print(f"menu-push failed: {e}", file=sys.stderr)
        return 1
    print(json.dumps(r, ensure_ascii=False))
    return 0


def cmd_menu_show(args) -> int:
    from . import menu

    print(menu.format_show(args.shop, args.text, args.tree, args.retail, args.hidden))
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

    pm = sub.add_parser("pubmed", help="pull new PubMed papers per research sector (config/research.json)")
    pm.add_argument("--sector", action="append", help="one sector (repeatable); default: every quarterly sector")
    pm.add_argument("--since", help="YYYY-MM-DD; default: the sector's last_reviewed")
    pm.add_argument("--until", help="YYYY-MM-DD; default: today")
    pm.set_defaults(fn=cmd_pubmed)

    sub.add_parser("review-plan", help="which reviews /review runs now: a missed full week first, then today's"
                   ).set_defaults(fn=cmd_review_plan)

    sub.add_parser("pull", help="/review's first step: sync, inbox, menu, db, flags, commit & push (no pings)"
                   ).set_defaults(fn=cmd_pull)

    sub.add_parser("daily", help="old launchd entry point (job removed 2026-10-12; kept for reinstall)"
                   ).set_defaults(fn=cmd_daily)

    a = sub.add_parser("add", help="append a manual record")
    a.add_argument("kind", choices=["eating_out", "bloodwork", "weight", "review", "note"])
    a.add_argument("json", help="the record as a JSON object")
    a.set_defaults(fn=cmd_add)

    i = sub.add_parser("inbox", help="pull Telegram inbox entries into data/inbox/")
    i.add_argument("--list", action="store_true", help="show pending entries")
    i.add_argument("--done", nargs="+", type=int, metavar="ID", help="move these entries to data/inbox/done/")
    i.set_defaults(fn=cmd_inbox)

    m = sub.add_parser("menu-sync", help="export a restaurant's recipes from the POS DB and compute nutrition")
    m.add_argument("--shop", default="cargill-cafe")
    m.add_argument("--no-export", action="store_true", help="recompute from the existing pos/*.json")
    m.add_argument("--close", action="store_true", help="close the query.py tunnel after exporting")
    m.set_defaults(fn=cmd_menu_sync)

    m = sub.add_parser("menu-push", help="push the menu (dishes, kitchen components, add-ons) to the worker's D1")
    m.add_argument("--shop", default="cargill-cafe")
    m.add_argument("--force", action="store_true", help="push even if the menu hash is unchanged")
    m.set_defaults(fn=cmd_menu_push)

    m = sub.add_parser("menu-show", help="search dishes/components (en or zh) and show nutrition")
    m.add_argument("text")
    m.add_argument("--shop", default="cargill-cafe")
    m.add_argument("--tree", action="store_true", help="ingredient breakdown in grams")
    m.add_argument("--retail", action="store_true", help="include take-home retail items (hidden by default)")
    m.add_argument("--hidden", action="store_true", help="include dishes hidden by overrides.json")
    m.set_defaults(fn=cmd_menu_show)

    sub.add_parser("status").set_defaults(fn=cmd_status)

    n = sub.add_parser("notify-test")
    n.add_argument("text", nargs="?")
    n.set_defaults(fn=cmd_notify_test)

    r = sub.add_parser("send-report", help="send a review report (reports/*.md) to Telegram in full")
    r.add_argument("path")
    r.set_defaults(fn=cmd_send_report)

    sub.add_parser("install-launchd").set_defaults(fn=cmd_install_launchd)
    sub.add_parser("uninstall-launchd").set_defaults(fn=cmd_uninstall_launchd)

    args = p.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
