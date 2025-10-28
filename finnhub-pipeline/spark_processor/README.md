# Spark Stream Processor

Apache Spark Streaming job for processing real-time stock trades.

## Features

- Kafka consumer with Spark Streaming
- Real-time data transformation
- Window-based aggregations (OHLCV)
- Cassandra writer
- Checkpoint management
- Exactly-once processing

## Processing Pipeline

1. Read from Kafka topic
2. Parse JSON messages
3. Validate and enrich data
4. Add time-series partitioning
5. Calculate 1-minute aggregates
6. Write to Cassandra

## Running

### Docker
```bash
docker build -t spark-processor .
docker run spark-processor
```

### Local
```bash
pip install -r requirements.txt
spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0 \
  src/stream_processor.py
```

## Backfill Historical Data

```bash
python src/backfill_job.py \
  --start-date 2025-01-01 \
  --end-date 2025-01-31 \
  --source /data/historical.parquet
```

## Configuration

Edit `spark-defaults.conf` for Spark settings.

## Testing

```bash
pytest tests/
```