CREATE KEYSPACE IF NOT EXISTS market_data 
WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};

USE market_data;

-- Raw trades table
CREATE TABLE IF NOT EXISTS trades (
    symbol text,
    timestamp bigint,
    price double,
    volume double,
    conditions list<text>,
    processed_at bigint,
    kafka_timestamp timestamp,
    spark_processed_at timestamp,
    price_change_indicator text,
    trade_date date,
    trade_hour int,
    PRIMARY KEY (symbol, timestamp)
) WITH CLUSTERING ORDER BY (timestamp DESC);

-- Aggregated trades table
CREATE TABLE IF NOT EXISTS trade_aggregates (
    symbol text,
    window_start timestamp,
    window_end timestamp,
    avg_price double,
    max_price double,
    min_price double,
    total_volume double,
    trade_count bigint,
    PRIMARY KEY (symbol, window_start)
) WITH CLUSTERING ORDER BY (window_start DESC);

-- Indexes for better query performance
CREATE INDEX IF NOT EXISTS ON trades (trade_date);
CREATE INDEX IF NOT EXISTS ON trades (price_change_indicator);