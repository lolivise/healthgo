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


def rate_cap_pct_per_week(con, end: date) -> float | None:
    """The weight-dependent loss cap from `safety.rate_cap_pct_per_week` (the leaner, the slower), at the last weigh-in."""
    row = con.execute("SELECT kg FROM weights WHERE date <= ? ORDER BY date DESC LIMIT 1", (end.isoformat(),)).fetchone()
    if not row:
        return None
    for step in sorted(config.plan()["safety"].get("rate_cap_pct_per_week", []), key=lambda s: -s["above_kg"]):
        if row[0] > step["above_kg"]:
            return step["pct"]
    return None


def run(through: date, day_through: date | None = None) -> list[Flag]:
    """Checks over days up to and including `through` (today counts: sleep, HRV, RHR and the morning weigh-in are in).
    All-day metrics (stress) stop at `day_through`, default `config.last_complete_day()`."""
    day_through = min(day_through or config.last_complete_day(), through)
    a = config.plan()["alerts"]
    flags: list[Flag] = []
    con = db.connect()

    recent = _series(con, "rhr", through - timedelta(days=6), through)
    base = _baseline(con, "rhr", through)
    if len(recent) >= 5 and len(base) >= 14 and mean(recent) - median(base) >= a["rhr_rise_bpm"]:
        flags.append(Flag("rhr_up", f"靜息心率 (RHR) 近 7 天平均 {mean(recent):.0f}，比你的基準 {median(base):.0f} "
                                    f"高 {mean(recent) - median(base):.0f} bpm。可能是恢復不足、壓力或快生病了。"))

    statuses = _series(con, "hrv_status", through - timedelta(days=3), through)
    if len([s for s in statuses if s in ("LOW", "POOR", "UNBALANCED")]) >= 3:
        flags.append(Flag("hrv_low", f"心率變異度 (HRV) 最近 4 天有 3 天以上不在平衡範圍（{', '.join(statuses)}）。"
                                     "考慮今天輕量訓練、早點睡。"))

    sleep = _series(con, "sleep_h", through - timedelta(days=4), through)
    short = [h for h in sleep if h < a["sleep_short_hours"]]
    if len(sleep) >= 4 and len(short) >= 3:
        flags.append(Flag("sleep_short", f"最近 5 晚有 {len(short)} 晚睡不到 {a['sleep_short_hours']:.0f} 小時。"
                                         "熱量赤字期睡眠不足最容易掉肌肉。"))

    bb = _series(con, "bb_high", through - timedelta(days=3), through)
    if len(bb) >= 3 and len([v for v in bb if v < a["body_battery_high_below"]]) >= 3:
        flags.append(Flag("bb_low", f"身體能量 (Body Battery) 最近幾天最高只到 {max(bb)}，"
                                    f"連續低於 {a['body_battery_high_below']}。身體沒有充好電。"))

    recent = _series(con, "avg_stress", day_through - timedelta(days=6), day_through)
    base = _baseline(con, "avg_stress", day_through)
    if len(recent) >= 5 and len(base) >= 14 and mean(recent) - median(base) >= a["stress_rise"]:
        flags.append(Flag("stress_up", f"壓力指數近 7 天平均 {mean(recent):.0f}，比你平常的 {median(base):.0f} "
                                       f"高 {mean(recent) - median(base):.0f}。"))

    slope = weight_slope_pct_per_week(con, through)
    limit = config.plan()["safety"]["max_loss_pct_per_week"]
    if slope and -slope[0] > limit:
        flags.append(Flag("loss_fast", f"近 14 天體重下降速度約每週 {-slope[0]:.2f}%（{slope[1]} 次量測），"
                                       f"超過安全上限 {limit}%。掉太快容易流失肌肉，也增加膽結石風險。"))
    elif slope and (cap := rate_cap_pct_per_week(con, through)) and -slope[0] > cap:
        flags.append(Flag("loss_above_cap", f"近 14 天體重下降速度約每週 {-slope[0]:.2f}%，超過目前體重的建議上限 "
                                            f"{cap}%。越瘦，每減一公斤裡肌肉的比例越高，建議放慢。"))

    s = config.plan()["safety"]
    act = con.execute("SELECT COUNT(DISTINCT date), COALESCE(SUM(calories), 0) FROM activities WHERE date BETWEEN ? AND ?",
                      ((through - timedelta(days=6)).isoformat(), through.isoformat())).fetchone()
    if act[0] >= 3:
        from .facts import mean_intake
        ea = mean_intake(config.plan(), through - timedelta(days=6), through) - act[1] / 7
        if ea < s["min_energy_availability_kcal"]:
            flags.append(Flag("ea_low", f"近 7 天能量可用性 (EA) 約 {ea:.0f} kcal/天（攝取 − 運動消耗），"
                                        f"低於下限 {s['min_energy_availability_kcal']}。運動多的日子要吃夠。"))

    ohp = con.execute(
        "SELECT date, MAX(weight_kg) FROM sets WHERE weight_kg > 0 AND (category = 'SHOULDER_PRESS' "
        "OR exercise LIKE '%SHOULDER_PRESS%' OR exercise LIKE '%OVERHEAD_PRESS%') "
        "AND date BETWEEN ? AND ? GROUP BY date ORDER BY date",
        ((through - timedelta(days=30)).isoformat(), through.isoformat())).fetchall()
    recent_ohp = [kg for d, kg in ohp if d >= (through - timedelta(days=1)).isoformat()]
    prior_ohp = [kg for d, kg in ohp if d < (through - timedelta(days=1)).isoformat()]
    if recent_ohp and prior_ohp and max(recent_ohp) >= max(prior_ohp) * a["ohp_jump_ratio"]:
        flags.append(Flag("ohp_jump", f"肩推 (OHP) 重量 {max(recent_ohp):g} kg，比前 30 天最高 {max(prior_ohp):g} kg "
                                      f"跳了 {max(recent_ohp) / max(prior_ohp) * 100 - 100:.0f}%。注意右肩。"))
    con.close()
    return flags
