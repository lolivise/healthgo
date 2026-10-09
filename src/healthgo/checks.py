"""Rule-based daily recovery checks. No AI: plain thresholds from config/plan.json.

Each check compares the recent window with Darren's own baseline (the 4 weeks
before it), never with population norms. A flag is only raised when there is
enough data to be confident; missing data never raises a flag.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from statistics import mean, median

from . import config, db


@dataclass
class Flag:
    key: str
    message: str


def _series(con, col: str, start: date, end: date) -> list:
    rows = con.execute(f"SELECT {col} FROM daily WHERE date BETWEEN ? AND ? AND {col} IS NOT NULL ORDER BY date",
                       (start.isoformat(), end.isoformat())).fetchall()
    return [r[0] for r in rows]


def _baseline(con, col: str, today: date) -> list:
    return _series(con, col, today - timedelta(days=35), today - timedelta(days=8))


def weight_slope_pct_per_week(con, end: date, days: int = 14) -> tuple[float, int] | None:
    """Least-squares slope of daily-average weight over `days`, as % of mean weight per week."""
    rows = con.execute(
        "SELECT date, AVG(kg) FROM weights WHERE date BETWEEN ? AND ? GROUP BY date ORDER BY date",
        ((end - timedelta(days=days - 1)).isoformat(), end.isoformat())).fetchall()
    if len(rows) < 5:
        return None
    xs = [(date.fromisoformat(d) - end).days for d, _ in rows]
    ys = [kg for _, kg in rows]
    mx, my = mean(xs), mean(ys)
    denom = sum((x - mx) ** 2 for x in xs)
    if denom == 0:
        return None
    slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / denom  # kg/day
    return round(slope * 7 / my * 100, 2), len(rows)


def run(today: date) -> list[Flag]:
    a = config.plan()["alerts"]
    flags: list[Flag] = []
    con = db.connect()
    yesterday = today - timedelta(days=1)  # today is partial at 20:00

    recent = _series(con, "rhr", today - timedelta(days=6), today)
    base = _baseline(con, "rhr", today)
    if len(recent) >= 5 and len(base) >= 14 and mean(recent) - median(base) >= a["rhr_rise_bpm"]:
        flags.append(Flag("rhr_up", f"靜息心率 (RHR) 近 7 天平均 {mean(recent):.0f}，比你的基準 {median(base):.0f} "
                                    f"高 {mean(recent) - median(base):.0f} bpm。可能是恢復不足、壓力或快生病了。"))

    statuses = _series(con, "hrv_status", today - timedelta(days=3), today)
    if len([s for s in statuses if s in ("LOW", "POOR", "UNBALANCED")]) >= 3:
        flags.append(Flag("hrv_low", f"心率變異度 (HRV) 最近 4 天有 3 天以上不在平衡範圍（{', '.join(statuses)}）。"
                                     "考慮今天輕量訓練、早點睡。"))

    sleep = _series(con, "sleep_h", yesterday - timedelta(days=4), today)[-5:]
    short = [h for h in sleep if h < a["sleep_short_hours"]]
    if len(sleep) >= 4 and len(short) >= 3:
        flags.append(Flag("sleep_short", f"最近 5 晚有 {len(short)} 晚睡不到 {a['sleep_short_hours']:.0f} 小時。"
                                         "熱量赤字期睡眠不足最容易掉肌肉。"))

    bb = _series(con, "bb_high", today - timedelta(days=3), today)
    if len(bb) >= 3 and len([v for v in bb if v < a["body_battery_high_below"]]) >= 3:
        flags.append(Flag("bb_low", f"身體能量 (Body Battery) 最近幾天最高只到 {max(bb)}，"
                                    f"連續低於 {a['body_battery_high_below']}。身體沒有充好電。"))

    recent = _series(con, "avg_stress", today - timedelta(days=6), yesterday)
    base = _baseline(con, "avg_stress", today)
    if len(recent) >= 5 and len(base) >= 14 and mean(recent) - median(base) >= a["stress_rise"]:
        flags.append(Flag("stress_up", f"壓力指數近 7 天平均 {mean(recent):.0f}，比你平常的 {median(base):.0f} "
                                       f"高 {mean(recent) - median(base):.0f}。"))

    slope = weight_slope_pct_per_week(con, today)
    limit = config.plan()["safety"]["max_loss_pct_per_week"]
    if slope and -slope[0] > limit:
        flags.append(Flag("loss_fast", f"近 14 天體重下降速度約每週 {-slope[0]:.2f}%（{slope[1]} 次量測），"
                                       f"超過安全上限 {limit}%。掉太快容易流失肌肉，也增加膽結石風險。"))

    ohp = con.execute(
        "SELECT date, MAX(weight_kg) FROM sets WHERE weight_kg > 0 AND (category = 'SHOULDER_PRESS' "
        "OR exercise LIKE '%SHOULDER_PRESS%' OR exercise LIKE '%OVERHEAD_PRESS%') "
        "AND date >= ? GROUP BY date ORDER BY date", ((today - timedelta(days=30)).isoformat(),)).fetchall()
    recent_ohp = [kg for d, kg in ohp if d >= (today - timedelta(days=1)).isoformat()]
    prior_ohp = [kg for d, kg in ohp if d < (today - timedelta(days=1)).isoformat()]
    if recent_ohp and prior_ohp and max(recent_ohp) >= max(prior_ohp) * a["ohp_jump_ratio"]:
        flags.append(Flag("ohp_jump", f"肩推 (OHP) 重量 {max(recent_ohp):g} kg，比前 30 天最高 {max(prior_ohp):g} kg "
                                      f"跳了 {max(recent_ohp) / max(prior_ohp) * 100 - 100:.0f}%。注意右肩。"))
    con.close()
    return flags
