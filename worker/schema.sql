CREATE TABLE IF NOT EXISTS entries (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  tg_message_id INTEGER UNIQUE,
  received_at TEXT,
  kind TEXT,
  text TEXT,
  file_id TEXT,
  media_group_id TEXT,
  raw TEXT
);

CREATE TABLE IF NOT EXISTS pending (
  chat_id TEXT PRIMARY KEY,
  kind TEXT,
  set_at INTEGER
);

CREATE TABLE IF NOT EXISTS checkins (
  chat_id TEXT PRIMARY KEY,
  message_id INTEGER,
  step TEXT,
  answers TEXT,
  started_at INTEGER
);

-- /eat: the restaurant menu pushed from the Mac (`healthgo menu-push`), the open /eat flow, saved favourites.
CREATE TABLE IF NOT EXISTS menu (
  code INTEGER PRIMARY KEY,
  shop TEXT NOT NULL,
  kind TEXT NOT NULL,          -- dish | component | addon
  item_ref TEXT,               -- POS menu item / component / add-on id (a dish's variants share it)
  ref_id TEXT,                 -- POS uuid of this row (variant / component / add-on)
  category TEXT,
  name_zh TEXT,
  name_en TEXT,
  variant TEXT,
  kcal REAL,
  protein REAL,
  fat REAL,
  carb REAL,
  grams REAL,
  serve_g REAL,
  sort INTEGER,
  addon_combos TEXT,           -- JSON [{name, min, max, items: [code]}] (dishes)
  est INTEGER NOT NULL DEFAULT 0  -- 1 = no recipe, nutrition unknown
);
CREATE INDEX IF NOT EXISTS menu_shop_kind ON menu (shop, kind, sort);

CREATE TABLE IF NOT EXISTS eat_sessions (
  chat_id TEXT PRIMARY KEY,
  message_id INTEGER,
  state TEXT,
  started_at INTEGER
);

CREATE TABLE IF NOT EXISTS favourites (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  chat_id TEXT,
  name TEXT,
  items TEXT,
  created_at INTEGER
);
