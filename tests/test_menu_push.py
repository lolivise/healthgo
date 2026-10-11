from __future__ import annotations

import json
import subprocess

import pytest

from healthgo import config, menu, store


def _w(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False))


def _nut(kcal, grams=100.0):
    return {"kcal": kcal, "protein": 10.0, "fat": 5.0, "carb": 20.0, "grams": grams}


def _comp(cid, label, used, serve=100.0, kcal=100.0):
    return {"component_id": cid, "label": label, "used_in_products": used, "serve_g": serve,
            "per_serve": None if serve is None else {"kcal": kcal, "protein": 5.0, "fat": 2.0, "carb": 10.0}}


@pytest.fixture
def shop(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "RESTAURANTS", tmp_path)
    monkeypatch.setattr(config, "STATE_FILE", tmp_path / "state.json")
    d = tmp_path / "t"
    dish = lambda vid, mid, name, cat, nutrition, variant=None, retail=False: {
        "variant_id": vid, "menu_item_id": mid, "name_zh": name, "name_en": name + " (I)", "category": cat,
        "variant_label": variant, "variant_label_zh": variant, "nutrition": nutrition, "retail": retail}
    _w(d / "dishes.json", {"shop": "t", "dishes": [
        dish("v1", "m1", "雞排飯", "Bento", _nut(800, 500)),
        dish("v2", "m2", "香腸", "Bento", None),
        dish("v3", "m3", "豆漿", "Drinks", _nut(180), "大"),
        dish("v4", "m3", "豆漿", "Drinks", _nut(80), "小"),
        dish("v5", "m4", "黑龍醬油", "Retail", _nut(10)),
        dish("v6", "m5", "0.5", "Bento", None),
    ], "addons": [
        {"addon_id": "a1", "combo_id": "c1", "name_zh": "泡菜", "name_en": "Kim'chi", "nutrition": _nut(35)},
        {"addon_id": "a2", "combo_id": "c1", "name_zh": "辣粉", "name_en": "mala", "nutrition": None},
    ], "components": [
        _comp("k1", "飯", 15), _comp("k2", "紅燒肉", 3), _comp("k3", "麵糊", 6), _comp("k4", "乾炸粉", 5),
        _comp("k5", "三杯醬", 2), _comp("k6", "炸醬麵基底", 1), _comp("k7", "滷牛腱2", 2), _comp("k8", "沒用到", 0),
        _comp("k9", "大骨高湯", 2), _comp("k10", "無份量", 3, serve=None), _comp("k11", "牛奶鍋基底", 1),
        _comp("k12", "醃漬排骨", 4), _comp("k13", "煮好的珍珠", 3),
    ], "summary": {"unmapped_ingredients": []}})
    _w(d / "pos" / "menu_categories.json", [
        {"id": "x1", "name_en": "Bento", "name_zh": "便當", "order": 1, "is_pos_only": False},
        {"id": "x2", "name_en": "Drinks", "name_zh": "飲料", "order": 2, "is_pos_only": False},
        {"id": "x3", "name_en": "Retail", "name_zh": "零售", "order": 3, "is_pos_only": True}])
    _w(d / "pos" / "menu_item_add_on_categories.json", [{"id": "ac1", "name_en": "Sides", "name_zh": "小菜"}])
    _w(d / "pos" / "menu_item_add_on_combos.json", [
        {"id": "c1", "menu_item_add_on_category_id": "ac1", "min": 0, "max": 2, "order": 1}])
    _w(d / "pos" / "menu_items_menu_items_add_on_combos.json", [
        {"id": "j1", "menu_item_add_on_combo_id": "c1", "menu_item_id": "m1"}])
    return "t"


def test_rows_filter_dishes_and_bowl(shop):
    rows = menu.menu_rows(shop)
    by = lambda kind: [r for r in rows if r["kind"] == kind]
    assert [r["name_zh"] for r in by("dish")] == ["雞排飯", "香腸", "豆漿", "豆漿"]  # retail + junk row dropped
    comps = [r["name_zh"] for r in by("component")]
    assert comps[:2] == ["飯", "紅燒肉"]  # used_in_products descending
    for bad in ("麵糊", "乾炸粉", "三杯醬", "沒用到", "大骨高湯", "無份量", "牛奶鍋基底", "醃漬排骨", "煮好的珍珠"):
        assert bad not in comps
    assert "炸醬麵基底" in comps and "滷牛腱" in comps  # 炸醬麵 is not a sauce; the trailing 2 is dropped
    sausage = next(r for r in by("dish") if r["name_zh"] == "香腸")
    assert sausage["est"] == 1 and sausage["kcal"] is None
    assert {r["category"] for r in by("dish")} == {"便當", "飲料"}


def test_dish_addon_combos_and_variants(shop):
    rows = {r["ref_id"]: r for r in menu.menu_rows(shop)}
    chicken = rows["v1"]
    combos = json.loads(chicken["addon_combos"])
    assert combos == [{"name": "小菜", "min": 0, "max": 2, "items": [rows["a1"]["code"], rows["a2"]["code"]]}]
    assert rows["v3"]["item_ref"] == rows["v4"]["item_ref"] == "m3" and rows["v3"]["variant"] == "大"
    assert rows["a2"]["est"] == 1 and rows["a1"]["est"] == 0
    assert chicken["name_en"] == "雞排飯"  # the "(I)" suffix is dropped


def test_codes_are_stable(shop, tmp_path):
    first = {r["ref_id"]: r["code"] for r in menu.menu_rows(shop)}
    assert sorted(first.values()) == list(range(1, len(first) + 1))
    # a new dish appears first in the list: existing codes must not move
    data = store.read_json(tmp_path / "t" / "dishes.json")
    data["dishes"].insert(0, {**data["dishes"][0], "variant_id": "vNEW", "menu_item_id": "mNEW", "name_zh": "新菜"})
    store.write_json(tmp_path / "t" / "dishes.json", data)
    again = {r["ref_id"]: r["code"] for r in menu.menu_rows(shop)}
    assert all(again[k] == v for k, v in first.items())
    assert again["vNEW"] == max(first.values()) + 1
    # and a removed dish never frees its code
    data["dishes"] = [d for d in data["dishes"] if d["variant_id"] != "v2"]
    store.write_json(tmp_path / "t" / "dishes.json", data)
    assert {r["ref_id"]: r["code"] for r in menu.menu_rows(shop)}["v1"] == first["v1"]
    assert json.loads((tmp_path / "t" / "codes.json").read_text())["v2"] == first["v2"]


def test_sql_replaces_and_escapes(shop):
    sql = menu.menu_sql(shop, menu.menu_rows(shop))
    lines = sql.splitlines()
    assert lines[0] == "DELETE FROM menu WHERE shop = 't';"
    assert all(ln.startswith("INSERT INTO menu (code,shop,kind,item_ref,ref_id,") for ln in lines[1:])
    assert len(lines) == 1 + len(menu.menu_rows(shop))
    assert "'Kim''chi'" in sql  # apostrophes doubled
    assert "NULL" in sql  # no-recipe rows carry NULL nutrition
    assert sql.count("INSERT INTO menu") == len(lines) - 1


def test_push_skips_when_unchanged(shop, monkeypatch):
    calls = []

    def fake_run(cmd, **kw):
        calls.append((cmd, kw["cwd"], open(cmd[-1]).read()))
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(menu, "_npx_env", lambda: ("/bin/npx", {}))
    r = menu.push(shop)
    assert r["pushed"] and r["rows"] == {"dish": 4, "component": 4, "addon": 2}
    cmd, cwd, sql = calls[0]
    assert cmd[:6] == ["/bin/npx", "wrangler", "d1", "execute", "healthgo-inbox", "--remote"] and cmd[6] == "--file"
    assert cwd == config.ROOT / "worker" and sql.startswith("DELETE FROM menu")
    assert menu.push(shop) == {"pushed": False, "reason": "unchanged", "rows": r["rows"]}
    assert len(calls) == 1
    assert menu.push(shop, force=True)["pushed"] and len(calls) == 2
    # a change to the menu pushes again
    data = store.read_json(config.RESTAURANTS / "t" / "dishes.json")
    data["dishes"][0]["nutrition"]["kcal"] = 900
    store.write_json(config.RESTAURANTS / "t" / "dishes.json", data)
    assert menu.push(shop)["pushed"] and len(calls) == 3


def test_failed_push_keeps_hash_unset(shop, monkeypatch):
    monkeypatch.setattr(subprocess, "run", lambda cmd, **kw: subprocess.CompletedProcess(cmd, 1, "", "boom"))
    monkeypatch.setattr(menu.time, "sleep", lambda s: None)
    monkeypatch.setattr(menu, "_npx_env", lambda: ("/bin/npx", {}))
    with pytest.raises(RuntimeError):
        menu.push(shop)
    assert "menu_hash" not in store.load_state()


def test_new_unmapped_alerts_only_for_new(shop):
    out = lambda *ls: {"summary": {"unmapped_ingredients": [{"label": x} for x in ls]}}
    assert menu.new_unmapped(shop, out("a", "b")) == []  # first run seeds the baseline
    assert menu.new_unmapped(shop, out("a", "b", "c")) == ["c"]
    assert menu.new_unmapped(shop, out("a")) == []
    assert menu.new_unmapped(shop, out("a", "c")) == ["c"]


def test_bowl_products_templates_and_dedupe(shop, tmp_path):
    data = store.read_json(tmp_path / "t" / "dishes.json")
    prod = lambda vid, name, cat, g, kcal: {"variant_id": vid, "menu_item_id": "m" + vid, "name_zh": name, "name_en": name,
                                            "category": cat, "variant_label": None, "variant_label_zh": None, "retail": False,
                                            "nutrition": _nut(kcal, g)}
    data["dishes"] += [prod("p1", "白飯", "Snacks", 300, 531), prod("p2", "炒青菜", "Snacks", 400, 144),
                       prod("p3", "炸雞排", "Side Dishes", 200, 690), prod("p4", "炸地瓜球", "Side Dishes", None, None),
                       prod("p5", "滷大腸(50g)", "Retail", 50, 99)]
    data["dishes"][-2]["nutrition"] = None  # no recipe: not offered
    data["components"] += [_comp("t1", "牛排基底", 5), _comp("t2", "雞排", 3), _comp("t3", "便當基底", 15)]
    store.write_json(tmp_path / "t" / "dishes.json", data)
    items = {r["name_zh"]: r for r in menu.menu_rows("t") if r["kind"] == "component"}
    names = list(items)
    assert names[:2] == ["白飯", "炒青菜"]  # staples first
    assert "牛排基底" not in items and "飯" not in items and "雞排" not in items  # template, and superseded by products
    assert "炸地瓜球" not in items and "炸雞排" in items and "滷大腸" in items
    assert "便當配菜+飯" in items and items["炸雞排"]["serve_g"] == 200 and items["炸雞排"]["kcal"] == 690


def test_hidden_dish_excluded_from_push_and_show(shop):
    d = config.RESTAURANTS / "t"
    data = json.loads((d / "dishes.json").read_text())
    data["dishes"] += [
        {"variant_id": "v7", "menu_item_id": "m7", "name_zh": "奶茶", "name_en": "Milk Tea (I)", "category": "Drinks",
         "variant_label": None, "variant_label_zh": None, "nutrition": _nut(200), "retail": False,
         "hidden": True, "hidden_reason": "duplicate"},
        {"variant_id": "v8", "menu_item_id": "m8", "name_zh": "奶茶", "name_en": "Milk Tea (I)", "category": "Drinks",
         "variant_label": "大", "variant_label_zh": "大", "nutrition": _nut(250), "retail": False}]
    _w(d / "dishes.json", data)
    rows = [r for r in menu.menu_rows("t") if r["kind"] == "dish" and r["name_zh"] == "奶茶"]
    assert [r["ref_id"] for r in rows] == ["v8"]
    assert "v7" not in {r["ref_id"] for r in menu.menu_rows("t")}
    assert [x["variant_id"] for x in menu.search("t", "奶茶")[0]] == ["v8"]
    assert {x["variant_id"] for x in menu.search("t", "奶茶", hidden=True)[0]} == {"v7", "v8"}


def test_compute_marks_hidden_by_menu_item_id(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "RESTAURANTS", tmp_path)
    d = tmp_path / "t"
    _w(d / "pos" / "menu_categories.json", [{"id": "c", "name_en": "Drinks", "order": 1}])
    _w(d / "pos" / "menu_items.json", [
        {"id": "A", "category_id": "c", "name_en": "Milk Tea", "name_zh": "奶茶", "order": 1},
        {"id": "B", "category_id": "c", "name_en": "Milk Tea", "name_zh": "奶茶", "order": 2}])
    _w(d / "pos" / "menu_item_variants.json", [
        {"id": "va", "menu_item_id": "A", "name_en": "L", "price": 5},
        {"id": "vb", "menu_item_id": "B", "name_en": None, "price": 5}])
    _w(d / "overrides.json", {"hide_menu_items": {"B": "dup"}})
    out = menu.compute("t")
    by = {x["variant_id"]: x for x in out["dishes"]}
    assert by["vb"]["hidden"] is True and by["vb"]["hidden_reason"] == "dup"
    assert not by["va"].get("hidden")
    assert out["summary"]["hidden"] == 1
