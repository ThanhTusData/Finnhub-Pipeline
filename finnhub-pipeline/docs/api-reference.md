# API Reference

## Producer Metrics API

**Endpoint**: `http://localhost:8000/metrics`

### Metrics

#### Counters
```
finnhub_messages_received_total{symbol="AAPL"} 12345
kafka_messages_sent_total{symbol="AAPL"} 12340
kafka_messages_failed_total{symbol="AAPL"} 5
validation_errors_total{symbol="AAPL"} 10
websocket_reconnects_total 3
kafka_errors_total 2
```

#### Gauges
```
websocket_connected 1
active_symbols_count 8
```

#### Histograms
```
message_processing_latency_seconds_bucket{le="0.001"} 1000
message_processing_latency_seconds_bucket{le="0.005"} 5000
message_processing_latency_seconds_sum 125.5
message_processing_latency_seconds_count 10000
```

## Cassandra Query API

### Get Recent Trades

```sql
SELECT * FROM trading.trades_v2
WHERE symbol = ?
  AND trade_year = ?
  AND trade_month = ?
  AND trade_day = ?
  AND timestamp > ?
ORDER BY timestamp DESC
LIMIT 1000;
```

**Parameters**:
- `symbol`: Stock symbol (e.g., 'AAPL')
- `trade_year`: Year (e.g., 2025)
- `trade_month`: Month (1-12)
- `trade_day`: Day (1-31)
- `timestamp`: Unix timestamp in milliseconds

**Example**:
```sql
SELECT * FROM trading.trades_v2
WHERE symbol = 'AAPL'
  AND trade_year = 2025
  AND trade_month = 10
  AND trade_day = 17
  AND timestamp > 1697529600000
ORDER BY timestamp DESC
LIMIT 100;
```

### Get Aggregates

```sql
SELECT * FROM trading.trade_aggregates
WHERE symbol = ?
  AND trade_year = ?
  AND trade_month = ?
  AND window_start >= ?
  AND window_start <= ?
ORDER BY window_start DESC;
```

**Parameters**:
- `symbol`: Stock symbol
- `trade_year`: Year
- `trade_month`: Month
- `window_start`: Start timestamp
- `window_end`: End timestamp (optional)

**Example**:
```sql
SELECT 
  symbol,
  window_start,
  open_price,
  high_price,
  low_price,
  close_price,
  total_volume,
  trade_count
FROM trading.trade_aggregates
WHERE symbol = 'AAPL'
  AND trade_year = 2025
  AND trade_month = 10
  AND window_start >= '2025-10-17 00:00:00'
ORDER BY window_start DESC
LIMIT 1440;  -- 24 hours of 1-min bars
```

## Prometheus Query API

**Endpoint**: `http://localhost:9090/api/v1/query`

### Examples

#### Current Message Rate
```bash
curl -G http://localhost:9090/api/v1/query \
  --data-urlencode 'query=rate(finnhub_messages_received_total[1m])'
```

#### Consumer Lag
```bash
curl -G http://localhost:9090/api/v1/query \
  --data-urlencode 'query=kafka_consumergroup_lag'
```

#### P95 Latency
```bash
curl -G http://localhost:9090/api/v1/query \
  --data-urlencode 'query=histogram_quantile(0.95, rate(message_processing_latency_seconds_bucket[5m]))'
```

## Data Schemas

### Trade Message (Kafka)

```json
{
  "symbol": "string",
  "price": "float",
  "timestamp": "long",
  "volume": "float",
  "conditions": ["string"],
  "processed_at": "long"
}
```

### Trades Table (Cassandra)

```
symbol text
trade_year int
trade_month int
trade_day int
timestamp bigint
price double
volume double
trade_time timestamp
trade_hour int
conditions list<text>
processed_at bigint
PRIMARY KEY ((symbol, trade_year, trade_month, trade_day), timestamp)
```

### Aggregates Table (Cassandra)

```
symbol text
trade_year int
trade_month int
trade_day int
window_start timestamp
window_end timestamp
trade_time timestamp
trade_hour int
total_volume double
avg_price double
high_price double
low_price double
open_price double
close_price double
trade_count bigint
price_volatility double
PRIMARY KEY ((symbol, trade_year, trade_month), window_start)
```