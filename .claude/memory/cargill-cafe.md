---
name: cargill-cafe
description: Darren co-owns Cargill Cafe (Taiwanese, Perth), his usual eating-out spot; its recipes in the Storium POS prod DB can give real kcal; he also free-assembles bowls in its kitchen
metadata:
  type: project
---

- **Darren is a co-owner of Cargill Cafe** (stated 2026-10-11) and eats there often. He has full rights to its
  dish and recipe data, so recipes may be stored in this repo. No privacy hedging needed.
- **Data source:** the Storium POS (`~/Projects/storium/pos-workplace`), shop slug `cargill-cafe`. Read prod
  read-only with `pos-workplace/.claude/skills/investigate-db/query.py` (`--close` when done). Chain:
  `menu_items` → `menu_item_variants.product_id` → `products` → `item_stacks` (recursive, children are `components`
  or `ingredients`, quantity + free-text unit) → `ingredients`. Filter `deleted_at IS NULL` everywhere.
- **No nutrition columns exist** in the POS. kcal must come from a per-100 g map of its ~281 ingredients plus piece
  weights for 份/個/pcs and densities for ml. About 83 % of recipe rows are already in g/ml/kg/l (2026-10-11).
- **Two ways he eats there:** off the menu (a menu item + variant + add-ons), or **walking into the kitchen and
  assembling his own bowl** from the components (rice, braised meats, egg, veg…). Both should be recordable in
  the Telegram `/eat` flow without weighing.
- **Recipe data is trustworthy as plated (Darren, 2026-10-11):** every meat/seafood is **boneless** (no edible-portion
  factor), and every portion is **weighed and matches the POS numbers** (1 serve rice = 300 g cooked, 便當基底 = 450 g).
  The fish in 虱目魚肚飯 is **pan-fried**, not deep-fried. Frying oil is not in the recipes: `healthgo menu-sync` adds
  an allowance (deep-fry 10 % of fried mass, fries 6 %, pan 5 g, stir 10 g).
- Built 2026-10-11: `healthgo menu-sync` / `menu-show`, `data/restaurants/cargill-cafe/` (pos export, TFDA/USDA
  `nutrition-map.json`, `dishes.json`, `adjustments.json`), `healthgo menu-push` → Worker D1 `menu`; Telegram `/eat`
  = 🍱 menu / 🥣 廚房自己配 / ⭐ 常吃 / ✏️ 其他外食, plus `/eat 雞排飯` text matching. Recipe-based eats auto-record
  into `eating_out` (with protein/fat/carb) on inbox pull; `/review`'s `healthgo pull` re-syncs and pushes the menu (no daily job since 2026-10-12).
- **Name map (Darren, 2026-10-11):** his 筍乾 = POS ingredient **香脆筍**; his 黃金泡菜 = POS ingredient **泡菜**, which is
  **homemade** (no POS recipe). Both are small bento sides he adds to self-assembled bowls. POS menu item 泡菜(150g) is
  wrongly linked to the 泡菜鍋 product; `overrides.json` re-points it. A bowl scoop of each is **50 g** (confirmed).
  香脆筍 nutrition is from its can label (Darren supplied): 71 kcal/100 g.
- **Bento side alternates** between 筍乾 and 黃金泡菜 (50 g either way). 便當基底 uses the average (+10 kcal adjustment
  in `adjustments.json`), so no extra tap in the bot; the ~20 kcal swing is noise next to a ~1,200-1,600 kcal bento.
- **Eat-out pattern seen in W41 (2026-10-10/11):** all eat-outs that week were here. On 10/10 he skipped his
  planned meals (only 2 energy bars + shake), then ate ~3,600 kcal across lunch, beef noodles and a loaded 豆花
  (day ≈ 4,100). A typical self-assembled bowl is ~1,560 kcal (滷牛腱×2 + 滷肉 + ½ rice + 炒青菜 + 煎蛋×2).
  **Advised at that review:** don't arrive empty (eat the shake + eggs first). The lighter default bowl drops the
  滷肉 (362 kcal, 28 g fat) and one egg: 滷牛腱×2 + ½ rice + 炒青菜 + 煎蛋×1 ≈ 1,070 kcal / ~90 g protein.
- **Bulk-phase plan (asked 2026-10-23):** he wants to take lunch from here daily during the future lean bulk (food is free,
  saves money; no meal prep). Plan sent: `reports/2026-10-23-bulk-cargill-plan.md`. Fixed no-cook breakfast/dinner
  (bar, shake, yogurt 500 g, oats 80 g, walnuts 20 g, fish oil ≈ 1,340 kcal) + a kitchen bowl that scales:
  滷牛腱×2 + rice 1 / 1.5 serves + 炒青菜 + 筍乾 ± 煎蛋 → days ≈ 2,710 / 2,850 / 2,975. Start at 2,700; fried bentos ≤1×/wk;
  椒鹽魚排飯 and 土魠魚便當 recipes look like they miss frying oil (batter, no oil allowance), so don't rely on their kcal.
- `adjustments.json` assumes ~1,800 g of the 2,000 g 豬肥油 in 滷肉 renders out and is skimmed (an estimate, not
  confirmed by Darren). See [[data-sources]], [[daily-diet-baseline]].
