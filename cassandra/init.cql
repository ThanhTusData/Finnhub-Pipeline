-- cassandra/init.cql
CREATE KEYSPACE IF NOT EXISTS market_data
WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};

USE market_data;

-- ========== ORIGINAL (kept) ==========
CREATE TABLE IF NOT EXISTS trades (
    symbol text,
    event_id text,
    event_time timestamp,
    price double,
    volume double,
    conditions list<text>,
    processed_at bigint,
    kafka_timestamp timestamp,
    spark_processed_at timestamp,
    price_change_indicator text,
    trade_date date,
    trade_hour int,
    PRIMARY KEY (symbol, event_id)
) WITH CLUSTERING ORDER BY (event_id DESC);

CREATE INDEX IF NOT EXISTS ON trades (trade_date);
CREATE INDEX IF NOT EXISTS ON trades (price_change_indicator);

-- ========== NEW: time-series optimized table ==========
-- Partitioning: (symbol, date_bucket) -> reduces number of partitions and allows TWCS
-- Clustering: event_time desc, event_id -> keep event_time ordering and uniqueness

CREATE TABLE IF NOT EXISTS trades_v2 (
    symbol text,
    date_bucket text,        -- e.g. '20250924' for daily, or '2025092413' for hourly
    event_time timestamp,
    event_id text,
    price double,
    volume double,
    conditions list<text>,
    processed_at bigint,
    kafka_timestamp timestamp,
    spark_processed_at timestamp,
    price_change_indicator text,
    trade_date date,
    trade_hour int,
    PRIMARY KEY ((symbol, date_bucket), event_time, event_id)
) WITH CLUSTERING ORDER BY (event_time DESC, event_id DESC)
AND compaction = {
  'class': 'TimeWindowCompactionStrategy',
  'compaction_window_unit': 'DAYS',   -- change to HOURS if you use hourly buckets
  'compaction_window_size': '1'
}
AND default_time_to_live = 0
AND compression = {'sstable_compression': 'LZ4Compressor'};

-- Optional: light secondary index if needed for ad-hoc queries (use sparingly)
CREATE INDEX IF NOT EXISTS ON trades_v2 (price_change_indicator);
