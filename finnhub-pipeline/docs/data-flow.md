# Data Flow Documentation

## Overview

This document describes the complete data flow through the trading pipeline.

## Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         Finnhub API                             │
│                  (WebSocket Real-time Trades)                   │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           │ WebSocket Connection
                           │ {"type":"trade", "data":[...]}
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Finnhub Producer                            │
│  • Receive trades                                               │
│  • Validate data (price > 0, volume > 0)                        │
│  • Enrich with processed_at timestamp                           │
│  • Export metrics (Prometheus)                                  │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           │ Kafka Producer
                           │ Key: symbol, Value: JSON
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Kafka Topic                              │
│                      (stock-trades)                             │
│  • Partitioned by symbol                                        │
│  • Retention: 7 days                                            │
│  • Compression: snappy                                          │
└──────────────┬──────────────────────────┬───────────────────────┘
               │                          │
               │ Spark Consumer           │ Monitoring
               │ (Micro-batch: 5s)        │
               ▼                          ▼
┌────────────────────────────┐  ┌────────────────────────────┐
│  Spark Streaming           │  │     Prometheus             │
│  • Parse JSON              │  │  • Scrape metrics          │
│  • Transform data          │  │  • Alert evaluation        │
│  • Add partitions          │  └─────────┬──────────────────┘
│  • Calculate aggregates    │            │
└─────────┬──────────────────┘            ▼
          │                      ┌────────────────────────────┐
          │                      │     Alertmanager           │
          │                      │  • Route alerts            │
          │                      │  • Send notifications      │
          │                      └─────────┬──────────────────┘
          │                                │
          │ Cassandra Writer               ▼
          │                      ┌────────────────────────────┐
          ▼                      │       Slack/Email          │
┌────────────────────────────┐  └────────────────────────────┘
│      Cassandra             │
│  • trades_v2 (raw)         │            ▲
│  • trade_aggregates        │            │
└─────────┬──────────────────┘            │
          │                                │
          │ CQL Query                      │
          ▼                                │
┌────────────────────────────┐            │
│       Grafana              │            │
│  • Dashboards              │────────────┘
│  • Visualizations          │  Prometheus Query
└────────────────────────────┘
```

## Detailed Flow

### 1. Data Ingestion (Producer)

**Input**: Finnhub WebSocket messages
```json
{
  "type": "trade",
  "data": [
    {
      "s": "AAPL",
      "p": 150.25,
      "t": 1635724800000,
      "v": 100.0,
      "c": ["12", "37"]
    }
  ]
}
```

**Processing**:
1. Receive WebSocket message
2. Validate required fields: s, p, t, v
3. Validate ranges: price > 0, volume > 0
4. Enrich with processed_at timestamp
5. Export metrics to Prometheus

**Output**: Kafka message
```json
{
  "symbol": "AAPL",
  "price": 150.25,
  "timestamp": 1635724800000,
  "volume": 100.0,
  "conditions": ["12", "37"],
  "processed_at": 1635724800500
}
```

### 2. Message Queue (Kafka)

**Partitioning**: By symbol key
- Ensures all trades for a symbol go to same partition
- Maintains order within symbol

**Configuration**:
- Replication factor: 3
- Min in-sync replicas: 2
- Compression: snappy
- Retention: 7 days

### 3. Stream Processing (Spark)

**Raw Trades Processing**:
```python
Kafka → Parse JSON → Add Partitions → Write to Cassandra
```

Partitioning columns added:
- trade_year: YYYY
- trade_month: MM
- trade_day: DD
- trade_hour: HH

**Aggregation Processing**:
```python
Kafka → Parse JSON → 1-min Window → Calculate OHLCV → Write Aggregates
```

Calculations:
- Open: first price in window
- High: max price in window
- Low: min price in window
- Close: last price in window
- Volume: sum of volumes
- Trade count: count of trades
- Volatility: standard deviation of prices

### 4. Data Storage (Cassandra)

**trades_v2 Schema**:
```
Partition: (symbol, trade_year, trade_month, trade_day)
Clustering: timestamp DESC
```

Example query:
```sql
SELECT * FROM trading.trades_v2
WHERE symbol = 'AAPL'
  AND trade_year = 2025
  AND trade_month = 10
  AND trade_day = 17
  AND timestamp > 1635724800000
ORDER BY timestamp DESC;
```

**trade_aggregates Schema**:
```
Partition: (symbol, trade_year, trade_month)
Clustering: window_start DESC
```

### 5. Monitoring (Prometheus/Grafana)

**Metrics Collection**:
- Producer exports to :8000/metrics
- Kafka JMX metrics
- Cassandra exporter
- Spark metrics

**Alert Flow**:
```
Metric Threshold → Prometheus Alert → Alertmanager → Slack/Email
```

## Performance Characteristics

### Throughput
- Producer: 10K-50K trades/sec
- Kafka: 100K+ messages/sec
- Spark: 50K-100K trades/sec
- Cassandra: 10K-50K writes/sec

### Latency (P95)
- Producer → Kafka: < 10ms
- Kafka → Spark: < 1s
- Spark → Cassandra: < 2s
- End-to-end: < 5s

## Error Handling

### Producer Errors
- WebSocket disconnect → Auto-reconnect
- Validation failure → Log & skip
- Kafka write failure → Retry with backoff

### Spark Errors
- Parse error → Log to DLQ
- Cassandra write failure → Retry
- Checkpoint failure → Recover from last checkpoint

### Data Quality
- Deduplication by (symbol, timestamp)
- Outlier detection (3-sigma rule)
- Missing data imputation