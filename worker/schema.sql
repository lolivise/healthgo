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
