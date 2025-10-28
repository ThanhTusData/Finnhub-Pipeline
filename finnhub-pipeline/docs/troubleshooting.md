# Troubleshooting Guide

## Common Issues

### Producer Issues

#### WebSocket Connection Fails

**Symptoms**:
- `websocket_connected = 0`
- Logs show "Connection refused" or "Authentication failed"

**Solutions**:
```bash
# Check API key
echo $FINNHUB_API_KEY

# Verify connectivity
curl https://finnhub.io/api/v1/quote?symbol=AAPL&token=$FINNHUB_API_KEY

# Restart producer
docker-compose restart finnhub-producer

# Check logs
make logs-producer
```

#### High Validation Error Rate

**Symptoms**:
- `validation_errors_total` increasing
- Trades being rejected

**Solutions**:
```bash
# Check logs for validation errors
docker-compose logs finnhub-producer | grep "validation error"

# Inspect invalid trades
# Look for negative prices, zero volumes, missing fields
```

### Kafka Issues

#### Consumer Lag Growing

**Symptoms**:
- `kafka_consumergroup_lag > 10000`
- Spark not keeping up with ingestion

**Solutions**:
```bash
# Check consumer lag
make kafka-lag

# Scale Spark processor
docker-compose up -d --scale spark-processor=2

# Increase Spark resources
# Edit docker-compose.yaml:
SPARK_EXECUTOR_MEMORY=8g
SPARK_EXECUTOR_CORES=4

# Restart Spark
docker-compose restart spark-processor
```

#### Broker Down

**Symptoms**:
- Producer can't connect to Kafka
- `kafka_errors_total` increasing

**Solutions**:
```bash
# Check Kafka status
docker-compose ps kafka

# View Kafka logs
docker-compose logs kafka

# Restart Kafka
docker-compose restart kafka zookeeper

# Verify topics
docker exec kafka kafka-topics --list --bootstrap-server localhost:9092
```

### Spark Issues

#### Processing Stopped

**Symptoms**:
- No new data in Cassandra
- Spark logs show errors

**Solutions**:
```bash
# Check Spark logs
make logs-spark

# Check checkpoint corruption
docker-compose exec spark-processor ls -la /tmp/checkpoint

# Reset checkpoint (CAUTION: Will reprocess data)
make reset-checkpoint

# Verify Kafka connectivity
docker-compose exec spark-processor nc -zv kafka 9092
```

#### Out of Memory

**Symptoms**:
- Spark logs show "OutOfMemoryError"
- Container restarts frequently

**Solutions**:
```bash
# Increase memory
# Edit docker-compose.yaml:
environment:
  SPARK_DRIVER_MEMORY: 4g
  SPARK_EXECUTOR_MEMORY: 8g

# Reduce batch size
# Edit spark-defaults.conf:
spark.sql.shuffle.partitions=20

# Restart
docker-compose restart spark-processor
```

### Cassandra Issues

#### Write Timeouts

**Symptoms**:
- Spark logs show "WriteTimeoutException"
- High write latency in Grafana

**Solutions**:
```bash
# Check Cassandra health
docker exec cassandra nodetool status

# Check disk space
docker exec cassandra df -h

# Compact tables
docker exec cassandra nodetool compact trading

# Increase timeout
# Edit cassandra.yaml:
write_request_timeout_in_ms: 5000

# Restart Cassandra
docker-compose restart cassandra
```

#### Schema Not Initialized

**Symptoms**:
- Spark logs show "Keyspace 'trading' does not exist"
- Queries fail with "Table not found"

**Solutions**:
```bash
# Re-initialize schema
make schema

# Or manually:
docker exec cassandra cqlsh -f /schema/keyspace.cql
docker exec cassandra cqlsh -f /schema/trades_v2.cql
docker exec cassandra cqlsh -f /schema/trade_aggregates.cql

# Verify
docker exec cassandra cqlsh -e "DESC KEYSPACE trading"
```

### Monitoring Issues

#### Prometheus Not Scraping

**Symptoms**:
- Targets show "DOWN" in Prometheus UI
- No metrics in Grafana

**Solutions**:
```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# Verify services are exposing metrics
curl http://localhost:8000/metrics  # Producer

# Check Prometheus config
docker exec prometheus cat /etc/prometheus/prometheus.yml

# Restart Prometheus
docker-compose restart prometheus
```

#### Grafana Shows No Data

**Symptoms**:
- Dashboards show "No data"
- Queries return empty results

**Solutions**:
```bash
# Verify Prometheus datasource
curl http://localhost:3000/api/datasources

# Check Prometheus is receiving data
curl 'http://localhost:9090/api/v1/query?query=up'

# Verify time range in Grafana dashboard
# Check that data exists for selected time range

# Restart Grafana
docker-compose restart grafana
```

## Debugging Steps

### 1. Check Service Health

```bash
# All services
make status

# Individual service
docker-compose ps finnhub-producer
docker-compose ps spark-processor
docker-compose ps kafka
docker-compose ps cassandra
```

### 2. View Logs

```bash
# All logs
make logs

# Specific service
make logs-producer
make logs-spark
make logs-kafka
make logs-cassandra

# Follow logs
docker-compose logs -f finnhub-producer
```

### 3. Verify Data Flow

```bash
# Check Kafka topics
make kafka-topics

# Check consumer groups
make kafka-lag

# Query Cassandra
make cql
> SELECT COUNT(*) FROM trading.trades_v2;
> SELECT * FROM trading.trade_aggregates LIMIT 5;
```

### 4. Check Metrics

```bash
# Producer metrics
curl http://localhost:8000/metrics

# Prometheus health
curl http://localhost:9090/-/healthy

# Grafana health
curl http://localhost:3000/api/health
```

## Performance Tuning

### Optimize Producer

```bash
# Increase batch size
# Edit kafka_writer.py:
batch_size=100
linger_ms=10

# Add more producer instances
docker-compose up -d --scale finnhub-producer=3
```

### Optimize Spark

```bash
# Increase parallelism
spark.sql.shuffle.partitions=20
spark.default.parallelism=20

# Optimize checkpointing
spark.streaming.stopGracefullyOnShutdown=true
spark.sql.streaming.checkpointLocation=/checkpoint

# Enable adaptive query execution
spark.sql.adaptive.enabled=true
```

### Optimize Cassandra

```bash
# Run compaction
docker exec cassandra nodetool compact trading

# Increase write throughput
# Edit cassandra.yaml:
concurrent_writes=64
memtable_flush_writers=8

# Add more nodes (production)
docker-compose up -d --scale cassandra=3
```

## Emergency Procedures

### Complete Reset

```bash
# CAUTION: This deletes ALL data!
make clean
make start
```

### Restore from Backup

```bash
# Restore Cassandra
docker cp backup/schema.cql cassandra:/tmp/
docker exec cassandra cqlsh -f /tmp/schema.cql
docker cp backup/data cassandra:/var/lib/cassandra/

# Restart services
docker-compose restart cassandra spark-processor
```

### Contact Support

For issues not covered here:
1. Collect logs: `make logs > debug.log`
2. Export metrics: `curl http://localhost:9090/api/v1/query`
3. Open GitHub issue with details