CREATE TABLE IF NOT EXISTS radar_items (id TEXT PRIMARY KEY, source TEXT NOT NULL, category TEXT NOT NULL, title TEXT NOT NULL, url TEXT NOT NULL, published_at TEXT, first_seen TEXT NOT NULL, topic TEXT NOT NULL, signal TEXT, UNIQUE(source,url));
CREATE INDEX IF NOT EXISTS radar_items_time ON radar_items(first_seen);
CREATE INDEX IF NOT EXISTS radar_items_topic ON radar_items(topic,first_seen);
CREATE TABLE IF NOT EXISTS radar_fetches (id TEXT PRIMARY KEY, source TEXT NOT NULL, fetched_at TEXT NOT NULL, status TEXT NOT NULL, fetched INTEGER NOT NULL, inserted INTEGER NOT NULL, error TEXT, etag TEXT, modified TEXT);
CREATE INDEX IF NOT EXISTS radar_fetches_source ON radar_fetches(source,fetched_at);
CREATE TABLE IF NOT EXISTS radar_deliveries (id TEXT PRIMARY KEY, channel TEXT NOT NULL, created_at TEXT NOT NULL, status TEXT NOT NULL, receipt TEXT);
