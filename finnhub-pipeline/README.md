# Finnhub Real-Time Trading Data Pipeline

A production-ready, scalable real-time stock trading data pipeline that ingests market data from Finnhub API, processes it with Apache Spark Streaming, and stores it in Cassandra for analytics.

## 🏗️ Architecture

```
Finnhub WebSocket → Kafka → Spark Streaming → Cassandra
                                  ↓
                           Prometheus ← Grafana
```

### Components

- **Finnhub Producer**: WebSocket client that subscribes to real-time trades and publishes to Kafka
- **Apache Kafka**: Message broker for reliable data streaming
- **Spark Streaming**: Stream processor for real-time transformations and aggregations
- **Cassandra**: Time-series database optimized for write-heavy workloads
- **Prometheus**: Metrics collection and alerting
- **Grafana**: Visualization and dashboards
- **Alertmanager**: Alert routing and notifications

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Finnhub API Key (get free at https://finnhub.io)

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd finnhub-pipeline
```

2. Create environment file:
```bash
cp .env.example .env
# Edit .env and add your FINNHUB_API_KEY
```

3. Start the pipeline:
```bash
make start
```

4. Access the services:
- Grafana: http://localhost:3000 (admin/admin)
- Prometheus: http://localhost:9090
- Producer Metrics: http://localhost:8000

### Verify Data Flow

```bash
# Check Kafka topics
make kafka-topics

# View producer logs
make logs-producer

# Access Cassandra
make cql
SELECT * FROM trading.trades_v2 LIMIT 10;
```

## 📊 Data Schema

### Raw Trades (`trades_v2`)
Stores individual trades with time-series partitioning:
- Partition key: `(symbol, trade_year, trade_month, trade_day)`
- Clustering key: `timestamp DESC`
- TTL: 30 days

### Aggregates (`trade_aggregates`)
1-minute OHLCV data with statistics:
- Partition key: `(symbol, trade_year, trade_month)`
- Clustering key: `window_start DESC`
- TTL: 90 days

## 🔧 Configuration

### Producer Configuration
Edit `finnhub_producer/.env`:
```bash
FINNHUB_API_KEY=your_key
SYMBOLS=AAPL,GOOGL,MSFT  # Comma-separated list
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
```

### Spark Configuration
Edit `spark_processor/spark-defaults.conf`:
```
spark.executor.memory=2g
spark.sql.shuffle.partitions=10
```

## 📈 Monitoring

### Metrics Available

**Producer Metrics** (port 8000):
- `finnhub_messages_received_total`: Messages from Finnhub
- `kafka_messages_sent_total`: Messages sent to Kafka
- `websocket_connected`: Connection status
- `message_processing_latency_seconds`: Processing latency

**System Metrics**:
- Kafka consumer lag
- Cassandra write latency
- Spark processing rate

### Alerts

Pre-configured alerts for:
- Producer downtime
- WebSocket disconnection
- High validation error rate
- Kafka write failures
- Consumer lag
- Cassandra issues

Configure Slack webhook in `observability/alertmanager/alertmanager.yml`

## 🛠️ Development

### Running Tests
```bash
make test
```

### Code Quality
```bash
make lint
```

### Debugging

View logs:
```bash
make logs-producer
make logs-spark
make logs-kafka
```

Check service status:
```bash
make status
```

## 🔄 Operations

### Scaling

Horizontal scaling:
```bash
docker-compose up -d --scale finnhub-producer=3
```

### Backup Cassandra
```bash
./scripts/backup_cassandra.sh
```

### Reset Checkpoint (troubleshooting)
```bash
make reset-checkpoint
docker-compose restart spark-processor
```

## 📦 Production Deployment

### Best Practices

1. **Use Kubernetes** for production (see `kubernetes/` directory)
2. **Enable authentication** for all services
3. **Configure SSL/TLS** for Kafka and Cassandra
4. **Set up proper monitoring** and alerting
5. **Use external storage** for checkpoints
6. **Implement data retention** policies
7. **Regular backups** of Cassandra

### Environment Variables

Production settings in `.env`:
```bash
KAFKA_REPLICATION_FACTOR=3
CASSANDRA_REPLICATION_FACTOR=3
SPARK_EXECUTOR_MEMORY=4g
ENABLE_SSL=true
```

## 🐛 Troubleshooting

### Producer not connecting
- Verify FINNHUB_API_KEY is valid
- Check network connectivity
- View logs: `make logs-producer`

### Kafka consumer lag
- Check Spark processing capacity
- Monitor: `make kafka-lag`
- Scale Spark executors if needed

### Cassandra write errors
- Check disk space
- Verify schema is initialized
- Monitor write latency in Grafana

## 🤝 Contributing

See CONTRIBUTING.md for guidelines

## 📚 Documentation

- [Architecture](docs/architecture.md)
- [Data Flow](docs/data-flow.md)
- [Deployment Guide](docs/deployment.md)
- [API Reference](docs/api-reference.md)
- [Troubleshooting](docs/troubleshooting.md)