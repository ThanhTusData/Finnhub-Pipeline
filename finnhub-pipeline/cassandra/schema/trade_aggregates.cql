-- Aggregated trading data (1-minute windows)
CREATE TABLE IF NOT EXISTS trading.trade_aggregates (
    symbol text,
    trade_year int,
    trade_month int,
    trade_day int,
    window_start timestamp,
    window_end timestamp,
    trade_time timestamp,
    trade_hour int,
    total_volume double,
    avg_price double,
    high_price double,
    low_price double,
    open_price double,
    close_price double,
    trade_count bigint,
    price_volatility double,
    PRIMARY KEY ((symbol, trade_year, trade_month), window_start)
) WITH CLUSTERING ORDER BY (window_start DESC)
    AND compaction = {
        'class': 'TimeWindowCompactionStrategy',
        'compaction_window_size': 7,
        'compaction_window_unit': 'DAYS'
    }
    AND gc_grace_seconds = 86400
    AND default_time_to_live = 7776000  -- 90 days retention
    AND comment = '1-minute aggregated OHLCV data';

-- Index for querying aggregates by time
CREATE INDEX IF NOT EXISTS agg_time_idx 
ON trading.trade_aggregates (window_start);