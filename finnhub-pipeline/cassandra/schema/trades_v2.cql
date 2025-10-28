-- Optimized time-series table for raw trades
CREATE TABLE IF NOT EXISTS trading.trades_v2 (
    symbol text,
    trade_year int,
    trade_month int,
    trade_day int,
    timestamp bigint,
    price double,
    volume double,
    trade_time timestamp,
    trade_hour int,
    conditions list,
    processed_at bigint,
    PRIMARY KEY ((symbol, trade_year, trade_month, trade_day), timestamp)
) WITH CLUSTERING ORDER BY (timestamp DESC)
    AND compaction = {
        'class': 'TimeWindowCompactionStrategy',
        'compaction_window_size': 1,
        'compaction_window_unit': 'DAYS'
    }
    AND gc_grace_seconds = 86400
    AND default_time_to_live = 2592000  -- 30 days retention
    AND comment = 'Raw trade data partitioned by symbol and date';

-- Index for querying by time range
CREATE INDEX IF NOT EXISTS trades_v2_time_idx 
ON trading.trades_v2 (trade_time);