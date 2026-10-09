"""Internal-consistency checks for an InBody scan (the numbers may have been read off a photo).

`check(record)` returns one Result per check: ok=True (passed), ok=False (failed) or
ok=None (skipped, inputs missing). Tolerances allow for InBody's own rounding.
"""

from __future__ import annotations

from typing import NamedTuple


class Result(NamedTuple):
    name: str
    ok: bool | None
    detail: str


def _num(v) -> float | None:
    return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def _find(other: dict, include: tuple[str, ...], exclude: tuple[str, ...] = ()) -> float | None:
    """First numeric value in `other` whose key contains any `include` word and no `exclude` word."""
    skip = ("pct", "percent", "ratio", "score", "%") + exclude
    for key, val in other.items():
        k = key.lower()
        if any(w in k for w in include) and not any(w in k for w in skip) and _num(val) is not None:
            return float(val)
    return None


def check(record: dict) -> list[Result]:
    weight, bf = _num(record.get("weight_kg")), _num(record.get("body_fat_pct"))
    fat, smm = _num(record.get("fat_mass_kg")), _num(record.get("skeletal_muscle_kg"))
    vfl = _num(record.get("visceral_fat_level"))
    other = record.get("other") if isinstance(record.get("other"), dict) else {}
    ffm = _find(other, ("free", "ffm", "lean"))
    water = _find(other, ("water", "tbw"), ("ecw", "icw", "intra", "extra"))
    protein = _find(other, ("protein",))
    minerals = _find(other, ("mineral",))
    bmr = _find(other, ("bmr", "basal"))

    out: list[Result] = []

    def add(name, ok, detail):
        out.append(Result(name, ok, detail))

    def skip(name, why):
        add(name, None, f"skipped, no {why}")

    # 1. body fat % vs fat mass / weight
    if None not in (bf, fat, weight):
        calc = fat / weight * 100
        add("bf_vs_fat_mass", abs(calc - bf) <= 0.6,
            f"body_fat_pct {bf} vs fat_mass_kg {fat} / weight_kg {weight} = {calc:.1f}% (tolerance 0.6)")
    else:
        skip("bf_vs_fat_mass", "fat_mass_kg")

    # 2. fat mass + FFM = weight
    if None not in (fat, ffm, weight):
        add("fat_plus_ffm_vs_weight", abs(fat + ffm - weight) <= 0.3,
            f"fat_mass {fat} + fat-free mass {ffm} = {fat + ffm:.1f} vs weight {weight} (tolerance 0.3 kg)")
    else:
        skip("fat_plus_ffm_vs_weight", "fat mass or fat-free mass")

    # lean mass: stated FFM, else weight - fat mass
    lean = ffm if ffm is not None else (weight - fat if None not in (weight, fat) else None)
    lean_src = "fat-free mass" if ffm is not None else "weight - fat mass"

    # 3. water + protein + minerals = lean mass
    if None not in (water, protein, minerals, lean):
        s = water + protein + minerals
        add("water_protein_minerals_vs_ffm", abs(s - lean) <= 0.4,
            f"water {water} + protein {protein} + minerals {minerals} = {s:.1f} vs {lean_src} {lean:.1f} (tolerance 0.4 kg)")
    else:
        skip("water_protein_minerals_vs_ffm", "water/protein/minerals or fat-free mass")

    # 4. skeletal muscle plausibility
    if smm is not None and weight is not None:
        pct = smm / weight * 100
        add("smm_share_of_weight", 25 <= pct <= 60,
            f"skeletal_muscle_kg {smm} is {pct:.1f}% of weight {weight} (expected 25-60%)")
    else:
        skip("smm_share_of_weight", "skeletal_muscle_kg")
    if smm is not None and lean is not None:
        add("smm_below_ffm", smm < lean, f"skeletal_muscle_kg {smm} must be < {lean_src} {lean:.1f}")
    else:
        skip("smm_below_ffm", "skeletal_muscle_kg or fat-free mass")

    # 5. ranges
    for name, val, lo, hi in (("weight_kg", weight, 50, 150), ("body_fat_pct", bf, 5, 50),
                              ("visceral_fat_level", vfl, 1, 20)):
        if val is None:
            skip(f"range_{name}", name)
        else:
            add(f"range_{name}", lo <= val <= hi, f"{name} {val} (expected {lo}-{hi})")

    # 6. BMR vs Katch-McArdle
    if bmr is not None and ffm is not None:
        calc = 370 + 21.6 * ffm
        add("bmr_vs_ffm", abs(bmr - calc) <= 40,
            f"BMR {bmr:g} vs 370 + 21.6 x FFM {ffm} = {calc:.0f} (tolerance 40 kcal)")
    else:
        skip("bmr_vs_ffm", "BMR or fat-free mass")

    return out


def failures(results: list[Result]) -> list[Result]:
    return [r for r in results if r.ok is False]


def report(results: list[Result]) -> str:
    mark = {True: "pass", False: "FAIL", None: "skip"}
    return "\n".join(f"  [{mark[r.ok]}] {r.name}: {r.detail}" for r in results)
