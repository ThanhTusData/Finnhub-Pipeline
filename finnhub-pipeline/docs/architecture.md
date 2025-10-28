# Architecture Overview

## System Architecture

The Finnhub pipeline follows a Lambda architecture pattern with real-time stream processing.

### High-Level Flow

```
┌─────────────┐     ┌───────┐     ┌───────────────┐     ┌───────────┐
│  Finnhub    │────▶│ Kafka │────▶│ Spark         │────▶│ Cassandra │
│  WebSocket  │     │       │     │ Streaming     │     │           │
└─────────────┘     └───────┘     └───────────────┘     └───────────┘
                         │              │                      │
                         │              ▼                      │
                         │         ┌──────────┐               │
                         └────────▶│Prometheus│◀──────────────┘
                                   └──────────┘
                                        │
                                        ▼
                                   ┌─────────┐
                                   │ Grafana │
                                   └─────────┘
```

## Components

### 1. Finnhub Producer
- **Purpose**: Ingest real-time trade data
- **Technology**: Python, WebSocket, Kafka Producer
- **Features**:
  - WebSocket connection with auto-reconnect
  - Data validation and enrichment
  - Prometheus metrics export
  - Error handling and retry logic

### 2. Apache Kafka
- **Purpose**: Message broker for reliable streaming
- **Configuration**:
  - Single broker (dev), 3+ brokers (prod)
  - Replication factor: 3
  - Log retention: 7 days
  - Compression: snappy

### 3. Spark Streaming
- **Purpose**: Real-time data processing
- **Operations**:
  - Parse and validate messages
  - Time-series partitioning
  - Window aggregations (1-minute OHLCV)
  - Write to Cassandra
- **Configuration**:
  - Micro-batch: 5 seconds
  - Checkpointing enabled
  - Exactly-once semantics

### 4. Cassandra
- **Purpose**: Time-series data storage
- **Tables**:
  - `trades_v2`: Raw trades (30-day TTL)
  - `trade_aggregates`: OHLCV data (90-day TTL)
- **Partitioning**: By symbol and date
- **Compaction**: TimeWindowCompactionStrategy

### 5. Observability Stack
- **Prometheus**: Metrics collection
- **Alertmanager**: Alert routing
- **Grafana**: Visualization

## Data Flow

### 1. Ingestion Phase
```python
Finnhub API → WebSocket → Validation → Kafka Topic
```

### 2. Processing Phase
```python
Kafka → Spark Consumer → Transformation → Aggregation → Cassandra
```

### 3. Storage Layout

**Raw Trades Partition Key:**
```
(symbol, trade_year, trade_month, trade_day)
```

**Clustering Key:**
```
timestamp DESC
```

This design ensures:
- Efficient time-range queries
- Even data distribution
- Optimal compaction

## Scaling Strategy

### Horizontal Scaling
- **Producer**: Multiple instances with load balancing
- **Kafka**: Add brokers, increase partitions
- **Spark**: Increase executor count
- **Cassandra**: Add nodes to ring

### Vertical Scaling
- Increase memory for Spark executors
- More CPU cores for Kafka brokers
- Additional RAM for Cassandra heap

## Fault Tolerance

### Producer
- Auto-reconnect on WebSocket disconnect
- Kafka retry mechanism
- Metrics for monitoring health

### Kafka
- Replication (min ISR = 2)
- Acks = all for durability
- Consumer group auto-rebalancing

### Spark
- Checkpoint for state recovery
- Write-ahead logs
- Exactly-once processing

### Cassandra
- Multi-datacenter replication
- Hinted handoff
- Repair operations

## Performance Characteristics

### Throughput
- Producer: 10K-50K msgs/sec per instance
- Kafka: 100K+ msgs/sec per broker
- Spark: 50K-100K msgs/sec
- Cassandra: 10K-50K writes/sec per node

### Latency
- End-to-end: < 5 seconds (p95)
- Kafka write: < 10ms (p99)
- Spark micro-batch: 5 seconds
- Cassandra write: < 5ms (p99)

## Security Considerations

### Production Recommendations
1. Enable SSL/TLS for all connections
2. Use SASL authentication for Kafka
3. Enable Cassandra authentication
4. Network segmentation
5. Encrypt data at rest
6. Regular security audits