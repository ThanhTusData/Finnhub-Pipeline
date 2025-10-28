-- Legacy trades table (deprecated - for reference only)
-- DO NOT USE - Use trades_v2 instead

CREATE TABLE IF NOT EXISTS trading.trades_legacy (
    symbol text,
    timestamp bigint,
    price double,
    volume double,
    PRIMARY KEY (symbol, timestamp)
) WITH CLUSTERING ORDER BY (timestamp DESC)
    AND comment = 'DEPRECATED: Legacy table, use trades_v2 instead';