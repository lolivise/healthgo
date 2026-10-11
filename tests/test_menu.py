from __future__ import annotations

import json

import pytest

from healthgo import config, menu


def _w(d, name, rows):
    (d / f"{name}.json").write_text(json.dumps(rows))


@pytest.fixture
def shop(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "RESTAURANTS", tmp_path)
    d = tmp_path / "t" / "pos"
    d.mkdir(parents=True)
    e = lambda p, pt, c, ct, v, u: {"id": f"{p}{c}", "parent_id": p, "parent_item_type": pt, "child_id": c,
                                    "child_item_type": ct, "volume": v, "unit_type": u}
    _w(d, "menu_categories", [{"id": "cat", "name_en": "Bento", "name_zh": "便當", "order": 1}])
    _w(d, "menu_items", [{"id": "it", "category_id": "cat", "name_en": "Fried Chicken Bowl", "name_zh": "雞", "order": 1,
                          "status": "ACTIVE"}])
    _w(d, "menu_item_variants", [{"id": "v", "menu_item_id": "it", "product_id": "p", "name_en": "", "name_zh": "",
                                  "price": "10.00", "status": "ACTIVE"}])
    _w(d, "products", [{"id": "p", "label": "bowl"}])
    _w(d, "components", [{"id": "rice", "label": "Rice", "volume": "2.00", "unit_type": "份"}])
    _w(d, "ingredients", [{"id": "raw", "label": "Raw rice", "volume": "1", "unit_type": "kg"},
                          {"id": "oil", "label": "Peanut Oil", "volume": "1", "unit_type": "l"}])
    # rice batch (2 份) = 400 g raw rice; bowl = 1 份 of rice + 10 ml oil
    _w(d, "item_stacks", [e("rice", "COMPONENT", "raw", "INGREDIENT", "400", "g"),
                          e("p", "PRODUCT", "rice", "COMPONENT", "1", "份"),
                          e("p", "PRODUCT", "oil", "INGREDIENT", "10", "ML ")])
    for t in ("menu_item_add_on_combos", "menu_items_menu_items_add_on_combos", "menu_item_add_on_combos_items"):
        _w(d, t, [])
    (tmp_path / "t" / "nutrition-map.json").write_text(json.dumps({"ingredients": {
        "raw": {"per100g": {"kcal": 350, "protein": 7, "fat": 1, "carb": 78}},
        "oil": {"per100g": {"kcal": 880, "protein": 0, "fat": 100, "carb": 0}, "g_per_ml": 0.92}}}))
    return "t"


def test_compute(shop):
    out = menu.compute(shop)
    d = out["dishes"][0]
    n = d["nutrition"]
    assert n["grams"] == pytest.approx(209.2, abs=0.1)  # 200 g rice + 10 ml * 0.92
    assert d["oil_allowance_g"] == pytest.approx(20.9, abs=0.1)  # 10% of the fried mass
    assert n["kcal"] == pytest.approx(200 * 3.5 + 9.2 * 8.8 + 20.9 * 8.84, abs=0.2)
    assert d["coverage"] == 1.0 and d["warnings"] == ["yield_from_children: Rice"]
    assert d["has_oil"] and d["fried_flag"] and not d["pan_fried_flag"]
    rice = out["components"][0]
    assert rice["serve_g"] == 200.0 and rice["batch_g"] == 400.0
    assert rice["per100g"]["kcal"] == 350.0


def test_missing_density_and_unit_weight(shop, tmp_path):
    (tmp_path / "t" / "nutrition-map.json").unlink()
    out = menu.compute(shop)
    d = out["dishes"][0]
    assert "assumed_density: Peanut Oil [ml]" in d["warnings"]
    assert d["coverage"] == 0.0
    assert [m["label"] for m in out["summary"]["unmapped_ingredients"]] == ["Raw rice", "Peanut Oil"]


def test_cross_unit_component_edge(shop, tmp_path):
    d = tmp_path / "t" / "pos"
    rows = json.loads((d / "item_stacks.json").read_text())
    rows[1].update(volume="100", unit_type="g")  # 100 g of a 2 份 batch with no known weight
    _w(d, "item_stacks", rows)
    out = menu.compute(shop)
    # yield has no weight, so it falls back to the children sum (400 g): 100 g is a quarter
    w = out["dishes"][0]["warnings"]
    assert any(x.startswith("missing_unit_weight: Rice") for x in w)
    (tmp_path / "t" / "nutrition-map.json").write_text(json.dumps({"components": {"rice": {"g_per_unit": {"份": 200}}}}))
    assert menu.compute(shop)["dishes"][0]["nutrition"]["grams"] == 110.0


def test_cycle_guard(shop, tmp_path):
    d = tmp_path / "t" / "pos"
    rows = json.loads((d / "item_stacks.json").read_text())
    rows.append({"id": "x", "parent_id": "rice", "parent_item_type": "COMPONENT", "child_id": "rice",
                 "child_item_type": "COMPONENT", "volume": "1", "unit_type": "份"})
    _w(d, "item_stacks", rows)
    out = menu.compute(shop)
    assert out["summary"]["oddities"]["cycles"] == ["Rice"]


def _names(shop, tmp_path, name_zh, label="bowl", plabel=None):
    d = tmp_path / shop / "pos"
    items = json.loads((d / "menu_items.json").read_text())
    items[0]["name_zh"] = name_zh
    items[0]["name_en"] = name_zh
    _w(d, "menu_items", items)
    prods = json.loads((d / "products.json").read_text())
    prods[0]["label"] = plabel or label
    _w(d, "products", prods)
    return menu.compute(shop)["dishes"][0]


def test_deep_fry_oil_excludes_base(shop, tmp_path):
    # 209.2 g dish, rice component label is a base (飯): rename and mark it
    d = tmp_path / "t" / "pos"
    comps = json.loads((d / "components.json").read_text())
    comps[0]["label"] = "白飯"
    _w(d, "components", comps)
    out = _names(shop, tmp_path, "炸雞")
    # fried mass = 209.2 - 200 base = 9.2 g -> 0.9 g oil; the oil ingredient is 10 ml, no 'oil' in dish label
    assert out["oil_reason"] == "deep_fry_10pct"
    assert out["oil_allowance_g"] == pytest.approx(0.9, abs=0.1)


def test_stir_fry_skipped_when_oil_in_tree(shop, tmp_path):
    out = _names(shop, tmp_path, "炒飯")
    assert out["has_oil"] and out["oil_allowance_g"] == 0.0  # Peanut Oil is in the tree
    d = tmp_path / "t" / "pos"
    st = json.loads((d / "item_stacks.json").read_text())
    _w(d, "item_stacks", [x for x in st if x["child_id"] != "oil"])
    out = menu.compute("t")["dishes"][0]
    assert out["oil_reason"] == "stir_fry" and out["oil_allowance_g"] == 10.0
    assert out["nutrition"]["fat"] == pytest.approx(12.0, abs=0.1)  # 2 g rice fat + 10 g oil


def test_sesame_oil_is_not_cooking_oil(shop, tmp_path):
    d = tmp_path / "t" / "pos"
    ing = json.loads((d / "ingredients.json").read_text())
    ing[1]["label"] = "香油"
    _w(d, "ingredients", ing)
    out = _names(shop, tmp_path, "煎魚")
    assert not out["has_oil"] and out["oil_reason"] == "pan_fry" and out["oil_allowance_g"] == 5.0


def test_scaled_to_label_g_and_retail(shop, tmp_path):
    out = _names(shop, tmp_path, "泡菜(100g)")
    assert out["nutrition"]["grams"] == 100.0
    assert "scaled_to_label_g: 100 g" in out["warnings"]
    assert menu.compute("t")["summary"]["scaled_to_label_g"] == 1
    assert _names(shop, tmp_path, "黑龍玻璃瓶")["retail"] is True


def test_pan_fried_override(shop, tmp_path):
    d = tmp_path / "t" / "pos"
    comps = json.loads((d / "components.json").read_text())
    comps[0]["label"] = "香脆筍"  # a crispy side flags the whole dish as deep-fried...
    _w(d, "components", comps)
    _w(d, "item_stacks", [x for x in json.loads((d / "item_stacks.json").read_text()) if x["child_id"] != "oil"])
    assert _names(shop, tmp_path, "炸雞")["oil_reason"].startswith("deep_fry")
    out = _names(shop, tmp_path, "虱目魚肚飯")  # ...unless the dish is on the pan-fried list
    assert out["oil_reason"] == "pan_fry" and out["oil_allowance_g"] == 5.0
    assert out["pan_fried_flag"] and not out["fried_flag"]


def test_bowl_extra_ingredients_and_relink(shop, tmp_path):
    d = tmp_path / "t"
    (d / "overrides.json").write_text(json.dumps({
        "bowl_extra_ingredients": {"raw": {"label": "生米", "alias": "米粒", "serve_g": 50}},
        "relink_dishes": {"it": {"ingredient_id": "raw", "grams": 150, "reason": "test"}}}))
    _names(shop, tmp_path, "泡菜(150g)")  # plain name: no fry/stir-fry oil allowance
    out = menu.compute("t")
    ex = out["bowl_extras"][0]
    assert ex["label"] == "生米" and ex["serve_g"] == 50.0
    assert ex["per_serve"]["kcal"] == pytest.approx(175.0)
    items = menu.bowl_items(out)
    assert items[0]["key"] == "bowl:ing:raw" and items[0]["name_en"] == "米粒"
    dish = out["dishes"][0]  # relinked: 150 g raw rice, not the product tree (no oil allowance, no label scaling)
    assert dish["nutrition"]["grams"] == 150.0 and dish["nutrition"]["kcal"] == pytest.approx(525.0)
    assert dish["relinked"] == "test" and dish["oil_allowance_g"] == 0.0


def test_relink_skips_scaled_to_label_g(shop, tmp_path):
    (tmp_path / "t" / "overrides.json").write_text(json.dumps({
        "relink_dishes": {"it": {"ingredient_id": "raw", "grams": 150, "reason": "x"}}}))
    out = _names(shop, tmp_path, "泡菜(100g)")
    assert out["nutrition"]["grams"] == 150.0 and "scaled_to_label_g" not in out
