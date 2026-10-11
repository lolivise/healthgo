"""Restaurant menu nutrition: export a shop's recipes (BOM) from the Storium POS DB and compute
kcal/protein/fat/carb per dish, add-on and kitchen component.

Files (data/restaurants/<shop>/):
  pos/<table>.json      raw rows, exported read-only from prod (stable JSON)
  nutrition-map.json    input: per-ingredient per-100g values and densities / unit weights (optional)
  adjustments.json      input: extra nutrition per product unit / component batch (optional)
  dishes.json           output of `compute`
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import statistics
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path

from . import config, store

QUERY_PY = Path("/Users/darrenhung/Projects/storium/pos-workplace/.claude/skills/investigate-db/query.py")
TABLES = [
    "menu_categories", "menu_items", "menu_item_variants", "menu_item_add_on_combos",
    "menu_items_menu_items_add_on_combos", "menu_item_add_on_combos_items",
    "ingredients", "components", "products", "item_stacks", "menu_item_add_on_categories",
]
DROP_COLS = {"created_at", "updated_at", "deleted_at", "shop_id"}
KEYS = ("kcal", "protein", "fat", "carb")
FRIED = ("炸", "酥", "fried", "crispy")  # deep-fried
PAN_FRIED = ("煎",)
SAUCE_OIL = ("醬油", "蠔油", "油膏", "香油")  # sauces and sesame-oil seasoning, not cooking oil
# Cooking-oil allowance: the kitchen does not record frying oil, so it is estimated.
# Basis: coated deep-fried foods absorb roughly 8-15% of their weight as fat.
DEEP_FRY_OIL_PCT = 0.10    # of the fried mass (dish grams minus rice/noodle base)
FRIES_OIL_PCT = 0.06       # frozen par-fried fries (薯條)
PAN_FRY_OIL_G = 5.0        # per dish, when no cooking oil is in the tree
STIR_FRY_OIL_G = 10.0      # per dish, when no cooking oil is in the tree
OIL_KCAL_PER_G = 8.84
BASE_RE = re.compile(r"便當基底|白飯|飯|麵線基底|意麵|麵基底|米苔目|基底.*麵|麵.*基底")  # carb/base components
NO_OIL_COMP = re.compile(r"粉|醬|基底|麵糊")
RETAIL = {"黑龍玻璃瓶", "黑龍醬油（大瓶）"}  # bottles of sauce sold to take home
# Dishes (by menu name_zh) whose fish is pan-fried although a crispy side (香脆筍) would flag them deep-fried.
PAN_FRIED_DISHES = {"虱目魚肚飯"}
LABEL_G = re.compile(r"(\d+(?:\.\d+)?)\s*g\b", re.I)
UNIT_ALIAS = {"cc": "ml", "gm": "g", "gram": "g", "grams": "g", "公克": "g", "克": "g", "公斤": "kg",
              "毫升": "ml", "升": "l", "litre": "l", "liter": "l"}


def shop_dir(shop: str) -> Path:
    return config.RESTAURANTS / shop


# ---------------------------------------------------------------- export

_OP_EXPORT = re.compile(r"""^\s*export\s+OP_SERVICE_ACCOUNT_TOKEN=(["']?)([^"'\s]+)\1\s*$""", re.M)


def query_env() -> dict:
    """Environment for the pos-workplace query.py. It needs the Storium service-account token
    (OP_SERVICE_ACCOUNT_TOKEN, exported in ~/.zshrc). launchd never sources ~/.zshrc, so read that one
    export line the way vault.py does for the HealthGo token. The value is never logged."""
    env = dict(os.environ)
    if not env.get("OP_SERVICE_ACCOUNT_TOKEN"):
        zshrc = Path.home() / ".zshrc"
        m = _OP_EXPORT.search(zshrc.read_text()) if zshrc.exists() else None
        if m:
            env["OP_SERVICE_ACCOUNT_TOKEN"] = m.group(2)
    return env


def close_tunnel() -> None:
    """Tear the query.py Cloudflare tunnel down (best effort)."""
    subprocess.run([str(QUERY_PY), "--close"], capture_output=True, text=True, env=query_env(), timeout=60)


def _query(sql: str) -> list[dict]:
    r = subprocess.run([str(QUERY_PY), "--format", "json", sql], capture_output=True, text=True, env=query_env())
    if r.returncode:
        raise SystemExit(f"query failed: {r.stderr.strip()[:300]}")
    m = re.search(r"^\[", r.stdout, re.M)  # skip a leading "tunnel up" line
    if not m:
        raise SystemExit(f"no JSON in query output: {r.stdout[:200]}")
    return json.JSONDecoder().raw_decode(r.stdout[m.start():])[0]


def export(shop: str, close: bool = False) -> dict[str, int]:
    try:
        return _export(shop)
    finally:
        if close:
            try:
                close_tunnel()
            except Exception:
                pass


def _export(shop: str) -> dict[str, int]:
    if not re.fullmatch(r"[a-z0-9-]+", shop):
        raise SystemExit("bad shop slug")
    shops = _query(f"select id, slug, name from shops where slug = '{shop}' and deleted_at is null")
    if not shops:
        raise SystemExit(f"no shop {shop!r}")
    sid = shops[0]["id"]
    d = shop_dir(shop) / "pos"
    store.write_json(d / "shop.json", shops[0])
    counts = {}
    for t in TABLES:
        rows = _query(f"select * from {t} where shop_id = '{sid}' and deleted_at is null")
        rows = [{k: v for k, v in r.items() if k not in DROP_COLS} for r in rows]
        rows.sort(key=lambda r: str(r["id"]))
        store.write_json(d / f"{t}.json", rows)
        counts[t] = len(rows)
    return counts


# ---------------------------------------------------------------- units

def num(v) -> float | None:
    try:
        return None if v is None else float(v)
    except (TypeError, ValueError):
        return None


def norm_unit(u) -> str:
    u = (u or "").strip().lower()
    return UNIT_ALIAS.get(u, u)


def split_unit(u: str) -> tuple[str, str, float]:
    """-> (kind, base unit, factor to base): kind is mass | vol | count."""
    if u == "g":
        return "mass", "g", 1.0
    if u == "kg":
        return "mass", "g", 1000.0
    if u == "ml":
        return "vol", "ml", 1.0
    if u == "l":
        return "vol", "ml", 1000.0
    return "count", u, 1.0


# ---------------------------------------------------------------- results

@dataclass
class Res:
    n: dict = field(default_factory=lambda: dict.fromkeys(KEYS, 0.0))
    grams: float = 0.0       # grams with a known weight
    covered: float = 0.0     # of those, grams that have nutrition values
    warn: set = field(default_factory=set)   # (code, kind, id, unit)
    labels: set = field(default_factory=set)  # product/component labels in the tree
    oil: bool = False
    used: dict = field(default_factory=dict)  # ingredient id -> grams
    base_g: float = 0.0      # grams from rice/noodle base components

    def add(self, o: Res, f: float = 1.0, grams: float | None = None) -> None:
        """Add o scaled by f; `grams` overrides the scaled grams (component yield vs sum of children)."""
        for k in KEYS:
            self.n[k] += o.n[k] * f
        g = o.grams * f if grams is None else grams
        ratio = o.covered / o.grams if o.grams else 0.0
        self.grams += g
        self.covered += g * ratio
        self.warn |= o.warn
        self.labels |= o.labels
        self.oil |= o.oil
        self.base_g += o.base_g * f
        for i, x in o.used.items():
            self.used[i] = self.used.get(i, 0.0) + x * f

    def adjust(self, a: dict | None) -> None:
        if a:
            for k in KEYS:
                self.n[k] += num(a.get(k)) or 0.0


class Calc:
    def __init__(self, shop: str):
        d = shop_dir(shop)
        rd = lambda t: store.read_json(d / "pos" / f"{t}.json", [])
        self.shop = shop
        self.cats = {r["id"]: r for r in rd("menu_categories")}
        self.items = {r["id"]: r for r in rd("menu_items")}
        self.variants = rd("menu_item_variants")
        self.combos = {r["id"]: r for r in rd("menu_item_add_on_combos")}
        self.item_combo = rd("menu_items_menu_items_add_on_combos")
        self.addon_items = rd("menu_item_add_on_combos_items")
        self.ings = {r["id"]: r for r in rd("ingredients")}
        self.comps = {r["id"]: r for r in rd("components")}
        self.prods = {r["id"]: r for r in rd("products")}
        self.stacks = rd("item_stacks")
        nm = store.read_json(d / "nutrition-map.json", {}) or {}
        self.imap = nm.get("ingredients", {})
        self.cmap = nm.get("components", {})
        self.adj = store.read_json(d / "adjustments.json", {}) or {}
        # data-driven fixes: {"hide_menu_items": {menu_item_id: reason}} (by id, so a POS rename cannot break it)
        self.overrides = store.read_json(d / "overrides.json", {}) or {}
        self.children: dict[str, list[dict]] = {}
        for s in self.stacks:
            self.children.setdefault(s["parent_id"], []).append(s)
        for v in self.children.values():
            v.sort(key=lambda s: (s["child_item_type"], str(s["child_id"])))
        self._memo: dict[str, Res] = {}
        self.oddities: dict[str, list] = {"orphan_edges": [], "dangling_edges": [], "cycles": [],
                                          "zero_yields": [], "unit_mismatches": []}
        self._mismatch: dict[tuple, int] = {}

    # --- labels
    def label(self, kind: str, id_: str) -> str:
        t = {"ingredient": self.ings, "component": self.comps, "product": self.prods}.get(kind, {})
        return (t.get(id_) or {}).get("label") or id_

    # --- unit conversion to grams (None = unknown)
    def to_grams(self, q: float, unit: str, gpml: float | None, gpu: dict, kind: str, id_: str, warn: set) -> float | None:
        k, base, f = split_unit(unit)
        if k == "mass":
            return q * f
        if k == "vol":
            if gpml is None:
                warn.add(("assumed_density", kind, id_, unit))
                gpml = 1.0
            return q * f * gpml
        w = num((gpu or {}).get(unit))
        if w is None:
            warn.add(("missing_unit_weight", kind, id_, unit))
            return None
        return q * w

    def ingredient(self, id_: str, q: float, unit: str) -> Res:
        r = Res()
        m = self.imap.get(id_) or {}
        label = self.label("ingredient", id_)
        g = self.to_grams(q, unit, num(m.get("g_per_ml")), m.get("g_per_unit") or {}, "ingredient", id_, r.warn)
        if re.search(r"油|oil", label, re.I) and not any(x in label for x in SAUCE_OIL):
            r.oil = True
        p = m.get("per100g")
        if g is None:
            if p and all(num(p.get(k)) == 0 for k in KEYS):  # manual zero-kcal item (cups, napkins): nothing to count
                r.warn = {w for w in r.warn if w[0] != "missing_unit_weight"}
            return r
        r.grams = g
        r.used[id_] = g
        if p and all(num(p.get(k)) is not None for k in KEYS):
            r.covered = g
            for k in KEYS:
                r.n[k] = g * float(p[k]) / 100
        return r

    # --- component batch (whole yield)
    def component(self, id_: str, stack: tuple = ()) -> Res:
        if id_ in self._memo:
            return self._memo[id_]
        c = self.comps[id_]
        r = Res()
        r.labels.add(c["label"])
        if id_ in stack:
            r.warn.add(("cycle", "component", id_, ""))
            self.oddities["cycles"].append(c["label"])
            return r  # not memoised: partial
        kids = self.edges(id_, "COMPONENT", stack + (id_,))
        r.add(kids)
        r.adjust(self.adj.get(id_))
        children_g = r.grams
        ratio = r.covered / r.grams if r.grams else 0.0
        w: set = set()
        yg = self.yield_grams(id_, w)
        if yg is None and not any(x[0] == "zero_yield" for x in w):
            r.warn.add(("yield_from_children", "component", id_, ""))  # count yield without a weight
        r.warn |= {x for x in w if x[0] != "missing_unit_weight"}
        if yg is not None:
            r.grams = yg
            r.covered = yg * ratio
        self._memo[id_] = r
        return r

    def yield_grams(self, id_: str, warn: set) -> float | None:
        c = self.comps[id_]
        y, u = num(c.get("volume")), norm_unit(c.get("unit_type"))
        if not y:
            warn.add(("zero_yield", "component", id_, u))
            if c["label"] not in self.oddities["zero_yields"]:
                self.oddities["zero_yields"].append(c["label"])
            return None
        cm = self.cmap.get(id_) or {}
        return self.to_grams(y, u, num(cm.get("g_per_ml")), cm.get("g_per_unit") or {}, "component", id_, warn)

    def fraction(self, cid: str, q: float, unit: str, warn: set) -> float | None:
        """Share of component cid's yield that q `unit` represents."""
        c = self.comps[cid]
        y, yu = num(c.get("volume")), norm_unit(c.get("unit_type"))
        if not y:
            warn.add(("zero_yield", "component", cid, yu))
            return None
        cm = self.cmap.get(cid) or {}
        gpml, gpu = num(cm.get("g_per_ml")), cm.get("g_per_unit") or {}
        k1, b1, f1 = split_unit(unit)
        k2, b2, f2 = split_unit(yu)
        if (k1, b1) == (k2, b2):
            return q * f1 / (y * f2)
        gq = self.to_grams(q, unit, gpml, gpu, "component", cid, warn)
        gy = self.to_grams(y, yu, gpml, gpu, "component", cid, warn)
        if gq is None or gy is None or not gy:
            return None
        return gq / gy

    # --- a parent's children summed
    def edges(self, parent: str, ptype: str, stack: tuple = ()) -> Res:
        r = Res()
        for s in self.children.get(parent, []):
            cid, ct = s["child_id"], s["child_item_type"]
            q, unit = num(s["volume"]) or 0.0, norm_unit(s["unit_type"])
            if ct == "INGREDIENT":
                if cid not in self.ings:
                    r.warn.add(("dangling_edge", "ingredient", cid, unit))
                    self.oddities["dangling_edges"].append(f"{parent}->{cid} ingredient")
                    continue
                r.add(self.ingredient(cid, q, unit))
            elif ct == "COMPONENT":
                if cid not in self.comps:
                    r.warn.add(("dangling_edge", "component", cid, unit))
                    self.oddities["dangling_edges"].append(f"{parent}->{cid} component")
                    continue
                self.note_mismatch(cid, unit)
                before_g, before_b = r.grams, r.base_g
                r.add(*self.component_edge(cid, q, unit, stack))
                if BASE_RE.search(self.comps[cid]["label"]):  # count the edge once, not its nested bases too
                    r.base_g = before_b + (r.grams - before_g)
            else:
                r.warn.add(("dangling_edge", ct.lower(), cid, unit))
        return r

    def component_edge(self, cid: str, q: float, unit: str, stack: tuple) -> tuple[Res, float, float | None]:
        batch = self.component(cid, stack)
        w: set = set()
        f = self.fraction(cid, q, unit, w)
        if f is None:
            out = Res()
            out.warn = batch.warn | w
            out.labels = set(batch.labels)
            out.oil = batch.oil
            return out, 0.0, 0.0
        return (_with_warn(batch, w) if w else batch), f, None

    def note_mismatch(self, cid: str, unit: str) -> None:
        yu = norm_unit(self.comps[cid].get("unit_type"))
        if split_unit(unit)[:2] != split_unit(yu)[:2]:
            k = (self.comps[cid]["label"], yu, unit)
            self._mismatch[k] = self._mismatch.get(k, 0) + 1

    # --- products / add-ons
    def product(self, pid: str) -> Res:
        r = Res()
        r.labels.add(self.prods[pid]["label"])
        r.add(self.edges(pid, "PRODUCT"))
        r.adjust(self.adj.get(pid))
        return r

    def addon(self, a: dict) -> Res | None:
        q, unit = num(a.get("volume")) or 0.0, norm_unit(a.get("unit_type"))
        if a.get("product_id") in self.prods:
            return self.product(a["product_id"])
        if a.get("ingredient_id") in self.ings:
            return self.ingredient(a["ingredient_id"], q, unit)
        if a.get("component_id") in self.comps:
            r = Res()
            b, f, g = self.component_edge(a["component_id"], q, unit, ())
            r.add(b, f, g)
            return r
        return None


def _with_warn(r: Res, w: set) -> Res:
    o = Res(dict(r.n), r.grams, r.covered, set(r.warn) | w, set(r.labels), r.oil, dict(r.used))
    return o


# ---------------------------------------------------------------- compute

def _r1(x: float) -> float:
    return round(x + 0.0, 1)


def nutrition(r: Res) -> dict:
    return {**{k: _r1(r.n[k]) for k in KEYS}, "grams": _r1(r.grams)}


def coverage(r: Res) -> float | None:
    return round(r.covered / r.grams, 3) if r.grams else None


def render_warnings(c: Calc, warn: set) -> list[str]:
    out = []
    for code, kind, id_, unit in sorted(warn, key=lambda w: (w[0], w[1], c.label(w[1], w[2]), w[3])):
        out.append(f"{code}: {c.label(kind, id_)}" + (f" [{unit}]" if unit else ""))
    return out


def breakdown(c: Calc, r: Res) -> list[dict]:
    rows = [{"id": i, "label": c.label("ingredient", i), "grams": _r1(g)} for i, g in r.used.items()]
    return sorted(rows, key=lambda x: (-x["grams"], x["label"]))


def _flags(r: Res, *names: str, force_pan: bool = False) -> dict:
    hay = [*r.labels, *names]
    has = lambda keys: any(k in (h or "").lower() for h in hay for k in keys)
    if force_pan:
        return {"fried_flag": False, "pan_fried_flag": True, "has_oil": r.oil}
    return {"fried_flag": has(FRIED), "pan_fried_flag": has(PAN_FRIED), "has_oil": r.oil}


def label_grams(*names: str) -> float | None:
    for n in names:
        m = LABEL_G.search(n or "")
        if m:
            return float(m.group(1))
    return None


def oil_allowance(r: Res, names: tuple, flags: dict) -> tuple[float, str | None]:
    """Estimated cooking oil (g) absorbed or used, and why. Stir > pan > deep fry."""
    nm = " ".join(n or "" for n in names)
    if r.grams <= 0:
        return 0.0, None
    if "炒" in nm or "鐵板麵" in nm:
        return (0.0, None) if r.oil else (STIR_FRY_OIL_G, "stir_fry")
    if flags["pan_fried_flag"]:
        return (0.0, None) if r.oil else (PAN_FRY_OIL_G, "pan_fry")
    if flags["fried_flag"]:
        fries = any("薯條" in x for x in [nm, *r.labels])
        pct = FRIES_OIL_PCT if fries else DEEP_FRY_OIL_PCT
        return max(r.grams - r.base_g, 0.0) * pct, f"deep_fry_{pct * 100:.0f}pct" + ("_fries" if fries else "")
    return 0.0, None


def finish(c: Calc, r: Res, names: tuple, *, product_name: str | None = None, scale: bool = True,
           force_pan: bool = False) -> tuple[Res, dict]:
    """Apply stated-weight scaling and the oil allowance. Returns (adjusted Res, extra output fields)."""
    extra: dict = {"oil_allowance_g": 0.0, "oil_reason": None}
    warn = set(r.warn)
    lg = label_grams(*names)
    if scale and lg and r.grams and abs(r.grams - lg) / lg > 0.2:
        f = lg / r.grams
        r = Res({k: v * f for k, v in r.n.items()}, lg, r.covered * f, set(r.warn), set(r.labels), r.oil,
                {i: g * f for i, g in r.used.items()}, r.base_g * f)
        extra["scaled_to_label_g"] = lg
    flags = _flags(r, *names, force_pan=force_pan)
    names_for_stir = names if product_name is None else (*names, product_name)
    g, why = oil_allowance(r, names_for_stir, flags)
    if g:
        r = Res(dict(r.n), r.grams, r.covered, set(r.warn), set(r.labels), r.oil, dict(r.used), r.base_g)
        r.n["fat"] += g
        r.n["kcal"] += g * OIL_KCAL_PER_G
        extra.update({"oil_allowance_g": _r1(g), "oil_reason": why})
    return r, extra


def _result(c: Calc, r: Res, *names: str, product_name: str | None = None, scale: bool = True,
            force_pan: bool = False) -> dict:
    flags = _flags(r, *names, force_pan=force_pan)
    r2, extra = finish(c, r, names, product_name=product_name, scale=scale, force_pan=force_pan)
    out = {"nutrition": nutrition(r2), "coverage": coverage(r2), "warnings": render_warnings(c, r2.warn),
           **flags, "breakdown": breakdown(c, r2), **extra}
    if "scaled_to_label_g" in extra:
        out["warnings"] = sorted([*out["warnings"], f"scaled_to_label_g: {extra['scaled_to_label_g']:g} g"])
    return out


def compute(shop: str) -> dict:
    c = Calc(shop)
    prod_res = {pid: c.product(pid) for pid in sorted(c.prods)}
    comp_res = {cid: c.component(cid) for cid in sorted(c.comps)}
    dishes = []
    cat_order = lambda i: (c.cats.get(i["category_id"]) or {}).get("order", 0)
    for v in sorted(c.variants, key=lambda v: (
            cat_order(c.items.get(v["menu_item_id"], {})), c.items.get(v["menu_item_id"], {}).get("order", 0),
            str(v["menu_item_id"]), v.get("name_en") or "", str(v["id"]))):
        it = c.items.get(v["menu_item_id"])
        if not it:
            continue
        d = {"menu_item_id": it["id"], "variant_id": v["id"], "product_id": v.get("product_id"),
             "category": (c.cats.get(it["category_id"]) or {}).get("name_en"),
             "name_en": it["name_en"], "name_zh": it["name_zh"], "variant_label": v.get("name_en") or None,
             "variant_label_zh": v.get("name_zh") or None,
             "price": num(v.get("price")), "status": v.get("status") or it.get("status")}
        pid = v.get("product_id")
        if pid in prod_res:
            d.update(_result(c, prod_res[pid], it["name_en"], it["name_zh"], v.get("name_en"), v.get("name_zh"),
                             product_name=c.prods[pid]["label"], force_pan=it["name_zh"] in PAN_FRIED_DISHES))
            d["retail"] = it["name_zh"] in RETAIL
            d["coverage"] = coverage(prod_res[pid])
        else:
            d.update({"nutrition": None, "coverage": None, "warnings": ["no_recipe"] if not pid else ["product_missing"],
                      "fried_flag": False, "pan_fried_flag": False, "has_oil": False, "breakdown": [],
                      "oil_allowance_g": 0.0, "oil_reason": None, "retail": it["name_zh"] in RETAIL})
        why = (c.overrides.get("hide_menu_items") or {}).get(it["id"])
        if why:
            d["hidden"], d["hidden_reason"] = True, why
        dishes.append(d)

    combo_items: dict[str, list[str]] = {}
    for j in c.item_combo:
        combo_items.setdefault(j["menu_item_add_on_combo_id"], []).append(j["menu_item_id"])
    addons = []
    for a in sorted(c.addon_items, key=lambda a: (str(a["menu_item_add_on_combo_id"]), a.get("order") or 0, str(a["id"]))):
        r = c.addon(a)
        kind = "product" if a.get("product_id") else "ingredient" if a.get("ingredient_id") else "component" if a.get("component_id") else None
        d = {"addon_id": a["id"], "combo_id": a["menu_item_add_on_combo_id"], "name_en": a["name_en"],
             "name_zh": a["name_zh"], "price": num(a.get("price")), "source": kind,
             "qty": num(a.get("volume")), "unit": norm_unit(a.get("unit_type")) or None,
             "menu_items": sorted(c.items[i]["name_en"] for i in combo_items.get(a["menu_item_add_on_combo_id"], []) if i in c.items)}
        if r is None:
            d.update({"nutrition": None, "coverage": None, "warnings": ["no_source"], "fried_flag": False, "pan_fried_flag": False, "has_oil": False,
                      "breakdown": [], "oil_allowance_g": 0.0, "oil_reason": None})
        else:
            d.update(_result(c, r, a["name_en"], a["name_zh"]))
        addons.append(d)

    # components: per 100 g and per serve (median grams used per product edge)
    used_by: dict[str, set] = {}
    edge_g: dict[str, list[float]] = {}
    for s in c.stacks:
        if s["parent_item_type"] == "PRODUCT" and s["child_item_type"] == "COMPONENT" and s["child_id"] in c.comps \
                and s["parent_id"] in c.prods:
            used_by.setdefault(s["child_id"], set()).add(s["parent_id"])
            f = c.fraction(s["child_id"], num(s["volume"]) or 0.0, norm_unit(s["unit_type"]), set())
            g = comp_res[s["child_id"]].grams
            if f is not None and g:
                edge_g.setdefault(s["child_id"], []).append(f * g)
    comps = []
    for cid in sorted(c.comps, key=lambda i: (c.comps[i]["label"], i)):
        r0, row = comp_res[cid], c.comps[cid]
        if NO_OIL_COMP.search(row["label"]):  # coating powders, batters, sauces and bases are not fried food
            r, extra = r0, {"oil_allowance_g": 0.0, "oil_reason": None}
        else:
            r, extra = finish(c, r0, (row["label"],), scale=False)
        yv, yu = num(row.get("volume")), norm_unit(row.get("unit_type"))
        serve = None
        if split_unit(yu)[0] == "count" and yv and r.grams:
            serve = r.grams / yv
        elif edge_g.get(cid):
            serve = statistics.median(edge_g[cid])
        per100 = {k: _r1(r.n[k] / r.grams * 100) for k in KEYS} if r.grams else None
        comps.append({
            "component_id": cid, "label": row["label"], "yield": yv, "yield_unit": yu or None,
            "batch_g": _r1(r.grams), "batch": {k: _r1(r.n[k]) for k in KEYS},
            "per100g": per100, "serve_g": _r1(serve) if serve else None,
            "per_serve": {k: _r1(r.n[k] / r.grams * serve) for k in KEYS} if serve and r.grams else None,
            "coverage": coverage(r), "used_in_products": len(used_by.get(cid, ())),
            "warnings": render_warnings(c, r.warn), **_flags(r0), "breakdown": breakdown(c, r), **extra})

    # summary
    unm: dict[str, float] = {}
    for r in prod_res.values():
        for i, g in r.used.items():
            p = (c.imap.get(i) or {}).get("per100g")
            if not p:
                unm[i] = unm.get(i, 0.0) + g
    miss: dict[tuple, set] = {}
    for d, pid in ((d, d["product_id"]) for d in dishes if d["product_id"] in prod_res):
        for w in prod_res[pid].warn:
            if w[0] == "missing_unit_weight":
                miss.setdefault((w[1], w[2], w[3]), set()).add(d["variant_id"])
    c.oddities["unit_mismatches"] = [
        {"component": k[0], "yield_unit": k[1], "edge_unit": k[2], "edges": n} for k, n in sorted(c._mismatch.items())]
    for s in c.stacks:
        if s["parent_item_type"] == "PRODUCT" and s["parent_id"] not in c.prods or \
                s["parent_item_type"] == "COMPONENT" and s["parent_id"] not in c.comps:
            c.oddities["orphan_edges"].append(f"{s['parent_id']}->{s['child_id']}")
    linked = [d for d in dishes if d["nutrition"]]
    summary = {
        "counts": {"dishes": len(dishes), "linked": len(linked), "unlinked": len(dishes) - len(linked),
                   "dishes_with_grams": sum(1 for d in linked if d["nutrition"]["grams"]),
                   "dishes_fully_covered": sum(1 for d in linked if d["coverage"] == 1.0),
                   "addons": len(addons), "components": len(comps), "ingredients": len(c.ings),
                   "ingredients_mapped": sum(1 for i in c.ings if (c.imap.get(i) or {}).get("per100g"))},
        "unmapped_ingredients": sorted(
            ({"id": i, "label": c.label("ingredient", i), "grams_used_total": _r1(g)} for i, g in unm.items()),
            key=lambda x: (-x["grams_used_total"], x["label"])),
        "missing_unit_weights": sorted(
            ({"kind": k, "id": i, "label": c.label(k, i), "unit": u, "dishes_affected": len(v)}
             for (k, i, u), v in miss.items()), key=lambda x: (-x["dishes_affected"], x["label"], x["unit"])),
        "oil_allowance": _oil_summary(dishes, addons, comps),
        "scaled_to_label_g": sum(1 for x in dishes + addons if "scaled_to_label_g" in x),
        "retail": sum(1 for x in dishes if x.get("retail")),
        "hidden": sum(1 for x in dishes if x.get("hidden")),
        "oddities": {k: sorted(set(v)) if k != "unit_mismatches" else v for k, v in c.oddities.items()},
    }
    return {"shop": shop, "synced_at": _synced_at(shop), "dishes": dishes, "addons": addons,
            "components": comps, "summary": summary}


def _oil_summary(*groups: list) -> dict:
    out: dict = {}
    for name, g in zip(("dishes", "addons", "components"), groups):
        rows = [x for x in g if x.get("oil_allowance_g")]
        by: dict[str, int] = {}
        for x in rows:
            by[x["oil_reason"]] = by.get(x["oil_reason"], 0) + 1
        out[name] = {"applied": len(rows), "total_oil_g": _r1(sum(x["oil_allowance_g"] for x in rows)), "by_reason": by}
    return out


def _synced_at(shop: str) -> str:
    """Deterministic: the export file's mtime date, so recomputing does not churn the output."""
    f = shop_dir(shop) / "pos" / "item_stacks.json"
    return config.datetime.fromtimestamp(f.stat().st_mtime, config.tz()).isoformat(timespec="minutes") if f.exists() else ""


def sync(shop: str, do_export: bool = True, close: bool = False) -> dict:
    counts = export(shop, close=close) if do_export else None
    out = compute(shop)
    store.write_json(shop_dir(shop) / "dishes.json", out)
    out["_export_counts"] = counts
    return out


# ---------------------------------------------------------------- show

def search(shop: str, text: str, retail: bool = False, hidden: bool = False) -> tuple[list[dict], list[dict]]:
    data = store.read_json(shop_dir(shop) / "dishes.json")
    if not data:
        raise SystemExit("no dishes.json: run `healthgo menu-sync` first")
    t = text.lower()
    hit = lambda *xs: any(t in (x or "").lower() for x in xs)
    ds = [d for d in data["dishes"] if (retail or not d.get("retail")) and (hidden or not d.get("hidden")) and hit(d["name_en"], d["name_zh"], d.get("variant_label"), d.get("variant_label_zh"))]
    ds += [a for a in data["addons"] if hit(a["name_en"], a["name_zh"])]
    return ds, [x for x in data["components"] if hit(x["label"])]


def format_show(shop: str, text: str, tree: bool = False, retail: bool = False, hidden: bool = False) -> str:
    ds, cs = search(shop, text, retail, hidden)
    lines = []

    def tr(rows):
        return [f"      {r['grams']:>7.1f} g  {r['label']}" for r in rows] if tree else []

    for d in ds:
        nm = d["name_en"] + (f" / {d['variant_label']}" if d.get("variant_label") else "") + f" ({d['name_zh']})"
        n = d["nutrition"]
        if not n:
            lines.append(f"[dish] {nm}: no recipe")
            continue
        lines.append(f"[{'addon' if 'addon_id' in d else 'dish'}] {nm}: {n['kcal']} kcal  P{n['protein']} F{n['fat']} C{n['carb']}"
                     f"  {n['grams']} g  coverage {d['coverage']}" + ("  FRIED" if d["fried_flag"] else "") + ("  PAN" if d["pan_fried_flag"] else "")
                     + ("  oil" if d["has_oil"] else "")
                     + (f"  +{d['oil_allowance_g']} g oil ({d['oil_reason']})" if d.get("oil_allowance_g") else ""))
        lines += [f"    ! {w}" for w in d["warnings"]] if tree else []
        lines += tr(d["breakdown"])
    for x in cs:
        p, s = x["per100g"], x["per_serve"]
        lines.append(f"[component] {x['label']} (yield {x['yield']} {x['yield_unit']}, {x['batch_g']} g): "
                     + (f"per100g {p['kcal']} kcal P{p['protein']} F{p['fat']} C{p['carb']}" if p else "per100g n/a")
                     + (f"  serve {x['serve_g']} g = {s['kcal']} kcal P{s['protein']} F{s['fat']} C{s['carb']}" if s else "")
                     + f"  coverage {x['coverage']}")
        lines += [f"    ! {w}" for w in x["warnings"]] if tree else []
        lines += tr(x["breakdown"])
    return "\n".join(lines) or "no match"


def format_summary(out: dict) -> str:
    s = out["summary"]
    c = s["counts"]
    lines = [f"{out['shop']}: " + ", ".join(f"{k} {v}" for k, v in c.items()),
             f"unmapped ingredients: {len(s['unmapped_ingredients'])}, missing unit weights: {len(s['missing_unit_weights'])}"]
    lines += [f"  {m['dishes_affected']:>3} dishes  {m['kind']} {m['label']} [{m['unit']}]" for m in s["missing_unit_weights"][:15]]
    return "\n".join(lines)


# ---------------------------------------------------------------- Telegram menu (worker D1)

# Which components show in the Telegram "廚房自己配" bowl list: things you would scoop into a bowl
# (rice, braised meats, fried cutlets, eggs, tofu, noodles, served soups, count-yield bases).
# Excluded by label: powders (粉), batters (麵糊), sauces (醬, but not 炸醬麵基底), stocks and pot bases
# (高湯 / 鍋底 / 牛奶鍋基底), braising liquids (滷汁), drinks and dessert toppings, raw marinated meat (醃漬),
# semi-finished goods (半成品), 肉圓 parts, thawed raw oysters, waste-loss rows (損耗).
BOWL_EXCLUDE = re.compile(
    r"粉|麵糊|(?<!炸)醬|高湯|鍋底|牛奶鍋基底|奶茶|茶基底|奶蓋|豆漿|米漿|仙草|珍珠|湯圓|粉粿|蜜紅豆|布丁"
    r"|滷汁|損耗|半成品|醃漬|肉圓|解凍")
BOWL_RENAME = {"滷牛腱2": "滷牛腱",  # a trailing digit would read as a multiplier in text shortcuts
               "便當基底": "便當配菜+飯", "滷大腸(50g)": "滷大腸"}
# Dish templates, not things you scoop: they are whole meals or the sizzling/hot-pot starting points.
BOWL_TEMPLATES = {"火鍋基底", "薑母鴨火鍋基底", "牛排基底", "意麵基底", "煎基底"}
# Standalone side/snack PRODUCTS offered as bowl items (serve = 1 product). The staples come first in the list
# (a bowl needs rice, veg and egg), the rest follow the kitchen components. Names are POS menu names (name_zh).
BOWL_STAPLES = ("白飯", "炒青菜", "煎蛋")
BOWL_PRODUCTS = ("滷百頁豆腐", "滷大腸(50g)", "滷肉燥")
BOWL_PRODUCT_RE = re.compile(r"^炸")  # the 炸* snacks in the Side Dishes category
# A kitchen component that is the same thing as a product: keep the product (it carries the oil allowance).
BOWL_SUPERSEDED = {"飯": "白飯", "雞排": "炸雞排", "鹹酥雞": "炸鹹酥雞", "煎蛋": "煎蛋", "肉燥": "滷肉燥"}
JUNK_DISH = re.compile(r"^[\d.\s]*$")  # POS test rows such as "0.5"
CODES_FILE = "codes.json"
MENU_COLUMNS = ("code", "shop", "kind", "item_ref", "ref_id", "category", "name_zh", "name_en", "variant",
                "kcal", "protein", "fat", "carb", "grams", "serve_g", "sort", "addon_combos", "est")
WRANGLER_DB = "healthgo-inbox"


def bowl_items(data: dict) -> list[dict]:
    """The kitchen-bowl list as uniform rows {key, label, serve_g, per_serve}: staple products first, then
    components (most used first), then the other side/snack products. Serve = one component serve or one product."""
    prods: dict[str, dict] = {}
    for d in data["dishes"]:
        n = d.get("nutrition")
        if not n or not n.get("grams") or d["name_zh"] in prods:
            continue
        if d["name_zh"] in BOWL_STAPLES + BOWL_PRODUCTS or (BOWL_PRODUCT_RE.match(d["name_zh"]) and d["category"] == "Side Dishes"):
            prods[d["name_zh"]] = {"key": "bowl:" + d["variant_id"], "ref": d["variant_id"], "label": d["name_zh"],
                                   "serve_g": n["grams"], "per_serve": {k: n[k] for k in KEYS}}
    comps = [{"key": c["component_id"], "ref": c["component_id"], "label": c["label"], "serve_g": c["serve_g"],
              "per_serve": c["per_serve"]}
             for c in data["components"]
             if c["used_in_products"] > 0 and c["serve_g"] and c["per_serve"] and not BOWL_EXCLUDE.search(c["label"])
             and c["label"] not in BOWL_TEMPLATES and BOWL_SUPERSEDED.get(c["label"]) not in prods]
    comps.sort(key=lambda c: (-next(x["used_in_products"] for x in data["components"] if x["component_id"] == c["key"]), c["label"]))
    staples = [prods[n] for n in BOWL_STAPLES if n in prods]
    rest = [prods[n] for n in BOWL_PRODUCTS if n in prods] + sorted(
        (p for n, p in prods.items() if n not in BOWL_STAPLES + BOWL_PRODUCTS), key=lambda p: p["label"])
    return staples + comps + rest


def assign_codes(shop: str, ref_ids: list[str]) -> dict[str, int]:
    """Stable small integer per POS id (Telegram callback_data is limited to 64 bytes). Never reused."""
    path = shop_dir(shop) / CODES_FILE
    codes: dict[str, int] = store.read_json(path, {}) or {}
    nxt = max(codes.values(), default=0) + 1
    for r in ref_ids:
        if r not in codes:
            codes[r] = nxt
            nxt += 1
    store.write_json(path, codes)
    return codes


def _strip_i(name: str | None) -> str:
    return re.sub(r"\s*\(I+\)\s*$", "", (name or "").strip()).strip()


def menu_rows(shop: str) -> list[dict]:
    data = store.read_json(shop_dir(shop) / "dishes.json")
    if not data:
        raise SystemExit("no dishes.json: run `healthgo menu-sync` first")
    pos = lambda t: store.read_json(shop_dir(shop) / "pos" / f"{t}.json", []) or []
    cat_zh = {c["name_en"]: c.get("name_zh") or c["name_en"] for c in pos("menu_categories")}
    addon_cat = {c["id"]: c.get("name_zh") or c.get("name_en") or "加購" for c in pos("menu_item_add_on_categories")}
    combos = {c["id"]: c for c in pos("menu_item_add_on_combos")}

    pos_only = {c["name_en"] for c in pos("menu_categories") if c.get("is_pos_only")}  # the Retail category
    dishes = [d for d in data["dishes"] if not d.get("retail") and not d.get("hidden") and d["category"] not in pos_only
              and not JUNK_DISH.match(d["name_zh"] or "")]
    bowl = bowl_items(data)
    addons = data["addons"]
    codes = assign_codes(shop, [d["variant_id"] for d in dishes] + [c["key"] for c in bowl]
                         + [a["addon_id"] for a in addons])

    combo_addons: dict[str, list[dict]] = {}
    for a in addons:
        combo_addons.setdefault(a["combo_id"], []).append(a)
    item_combos: dict[str, list[str]] = {}
    for j in pos("menu_items_menu_items_add_on_combos"):
        item_combos.setdefault(j["menu_item_id"], []).append(j["menu_item_add_on_combo_id"])

    def nut(x: dict | None) -> dict:
        n = (x or {}).get("nutrition") or {}
        return {k: n.get(k) for k in KEYS} | {"grams": n.get("grams")}

    rows: list[dict] = []
    for i, d in enumerate(dishes):
        mine = []
        for cid in sorted(item_combos.get(d["menu_item_id"], []), key=lambda c: (combos.get(c, {}).get("order") or 0, c)):
            cb = combos.get(cid)
            items = [codes[a["addon_id"]] for a in combo_addons.get(cid, [])]
            if cb and items:
                mine.append({"name": addon_cat.get(cb.get("menu_item_add_on_category_id"), "加購"),
                             "min": int(cb.get("min") or 0), "max": int(cb.get("max") or 1), "items": items})
        n = nut(d)
        rows.append({"code": codes[d["variant_id"]], "shop": shop, "kind": "dish", "item_ref": d["menu_item_id"],
                     "ref_id": d["variant_id"], "category": cat_zh.get(d["category"], d["category"]),
                     "name_zh": d["name_zh"].strip(), "name_en": _strip_i(d["name_en"]),
                     "variant": (d.get("variant_label_zh") or d.get("variant_label") or "").strip() or None,
                     **{k: n[k] for k in KEYS}, "grams": n["grams"], "serve_g": None, "sort": i,
                     "addon_combos": json.dumps(mine, ensure_ascii=False) if mine else None,
                     "est": 0 if d["nutrition"] else 1})
    for i, c in enumerate(bowl):
        ps = c["per_serve"]
        rows.append({"code": codes[c["key"]], "shop": shop, "kind": "component", "item_ref": c["key"],
                     "ref_id": c["ref"], "category": "廚房", "name_zh": BOWL_RENAME.get(c["label"], c["label"]),
                     "name_en": None, "variant": None, **{k: ps[k] for k in KEYS}, "grams": c["serve_g"],
                     "serve_g": c["serve_g"], "sort": i, "addon_combos": None, "est": 0})
    for i, a in enumerate(addons):
        n = nut(a)
        rows.append({"code": codes[a["addon_id"]], "shop": shop, "kind": "addon", "item_ref": a["addon_id"],
                     "ref_id": a["addon_id"], "category": addon_cat.get((combos.get(a["combo_id"]) or {}).get(
                         "menu_item_add_on_category_id"), "加購"),
                     "name_zh": a["name_zh"].strip(), "name_en": (a["name_en"] or "").strip() or None, "variant": None,
                     **{k: n[k] for k in KEYS}, "grams": n["grams"], "serve_g": None, "sort": i,
                     "addon_combos": None, "est": 0 if a["nutrition"] else 1})
    return rows


def _lit(v) -> str:
    if v is None:
        return "NULL"
    if isinstance(v, bool):
        return "1" if v else "0"
    if isinstance(v, (int, float)):
        return repr(v)
    return "'" + str(v).replace("'", "''") + "'"


def menu_sql(shop: str, rows: list[dict]) -> str:
    """Full replace of one shop's rows in the worker's D1 `menu` table."""
    cols = ",".join(MENU_COLUMNS)
    out = [f"DELETE FROM menu WHERE shop = {_lit(shop)};"]
    out += [f"INSERT INTO menu ({cols}) VALUES ({','.join(_lit(r[c]) for c in MENU_COLUMNS)});" for r in rows]
    return "\n".join(out) + "\n"


def _npx_env() -> tuple[str, dict]:
    """npx is usually under nvm, which a launchd job's PATH lacks."""
    import glob
    import shutil

    env = dict(os.environ)
    found = shutil.which("npx", path=env.get("PATH"))
    if found:
        return found, env
    cands = sorted(glob.glob(str(Path.home() / ".nvm/versions/node/*/bin/npx")))[-1:]
    cands += [p for p in ("/opt/homebrew/bin/npx", "/usr/local/bin/npx") if Path(p).exists()]
    if not cands:
        raise RuntimeError("npx not found")
    env["PATH"] = f"{Path(cands[0]).parent}:{env.get('PATH', '')}"
    return cands[0], env


def push(shop: str, force: bool = False) -> dict:
    """Generate the SQL and run it against the worker's remote D1. Skips when nothing changed.

    The hash covers the generated SQL (so a change to the bowl rule or the codes also re-pushes), and is
    stored in data/state.json only after wrangler succeeded."""
    import tempfile

    rows = menu_rows(shop)
    sql = menu_sql(shop, rows)
    digest = hashlib.sha256(sql.encode()).hexdigest()
    state = store.load_state()
    counts = {k: sum(1 for r in rows if r["kind"] == k) for k in ("dish", "component", "addon")}
    if not force and state.get("menu_hash", {}).get(shop) == digest:
        return {"pushed": False, "reason": "unchanged", "rows": counts}
    npx, env = _npx_env()
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / "menu.sql"
        f.write_text(sql)
        cmd = [npx, "wrangler", "d1", "execute", WRANGLER_DB, "--remote", "--file", str(f)]
        for attempt in (1, 2):  # the Cloudflare import API sometimes answers "Authentication error" once
            r = subprocess.run(cmd, cwd=config.ROOT / "worker", env=env, capture_output=True, text=True, timeout=300)
            if not r.returncode:
                break
            if attempt == 1:
                time.sleep(5)
    if r.returncode:
        raise RuntimeError(f"wrangler d1 execute failed: {(r.stderr or r.stdout).strip()[-300:]}")
    state = store.load_state()  # the file may have changed while wrangler ran
    state.setdefault("menu_hash", {})[shop] = digest
    store.save_state(state)
    return {"pushed": True, "rows": counts}


def unmapped_ids(out: dict) -> list[str]:
    return sorted(u["label"] for u in out["summary"]["unmapped_ingredients"])


def new_unmapped(shop: str, out: dict) -> list[str]:
    """Ingredient labels unmapped now that were not in the previous run (first run seeds the baseline)."""
    state = store.load_state()
    prev = (state.get("menu_unmapped") or {}).get(shop)
    now = unmapped_ids(out)
    state.setdefault("menu_unmapped", {})[shop] = now
    store.save_state(state)
    return [] if prev is None else [x for x in now if x not in prev]
