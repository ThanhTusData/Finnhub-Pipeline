# Cassandra Schema

Time-series optimized schema for stock trading data.

## Tables

### trades_v2
Raw trade data with time-series partitioning:
- Partition: `(symbol, year, month, day)`
- Clustering: `timestamp DESC`
- TTL: 30 days
- Compaction: TimeWindowCompactionStrategy

### trade_aggregates
1-minute OHLCV aggregations:
- Partition: `(symbol, year, month)`
- Clustering: `window_start DESC`
- TTL: 90 days
- Compaction: TimeWindowCompactionStrategy

## Initialization

```bash
# Automatically initialized by docker-compose
# Manual initialization:
cqlsh -f schema/keyspace.cql
cqlsh -f schema/trades_v2.cql
cqlsh -f schema/trade_aggregates.cql
```

## Queries

```sql
-- Get recent trades for a symbol
SELECT * FROM trading.trades_v2
WHERE symbol = 'AAPL'
  AND trade_year = 2025
  AND trade_month = 10
  AND trade_day = 17
LIMIT 100;

-- Get hourly aggregates
SELECT * FROM trading.trade_aggregates
WHERE symbol = 'AAPL'
  AND trade_year = 2025
  AND trade_month = 10
LIMIT 24;
```

## Maintenance

```bash
# Repair
nodetool repair trading

# Compact
nodetool compact trading trades_v2

# Check disk usage
nodetool tablestats trading
```