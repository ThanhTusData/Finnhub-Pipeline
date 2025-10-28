# Utility Scripts

Collection of operational and maintenance scripts for the trading pipeline.

## Available Scripts

### reset_checkpoint.sh
Reset Spark Streaming checkpoint (use with caution).

**Usage**:
```bash
./scripts/reset_checkpoint.sh
```

**Warning**: This will cause Spark to reprocess data from the beginning.

---

### load_test_generator.py
Generate synthetic trade data for load testing.

**Usage**:
```bash
# Install dependencies
pip install kafka-python

# Run generator
python scripts/load_test_generator.py

# Customize
# Edit SYMBOLS and adjust sleep time in the script
```

**Features**:
- Generates realistic trade data
- Configurable symbols
- Adjustable rate (default: ~10 trades/sec per symbol)

---

### check_kafka_lag.sh
Monitor Kafka consumer group lag.

**Usage**:
```bash
# Check default group (spark-streaming)
./scripts/check_kafka_lag.sh

# Check specific group
./scripts/check_kafka_lag.sh my-consumer-group
```

**Output**:
```
GROUP           TOPIC          PARTITION  CURRENT-OFFSET  LOG-END-OFFSET  LAG
spark-streaming stock-trades   0          12345           12350           5
```

---

### backup_cassandra.sh
Backup Cassandra data and schema.

**Usage**:
```bash
# Default backup location (./backups)
./scripts/backup_cassandra.sh

# Custom backup location
./scripts/backup_cassandra.sh /path/to/backup
```

**Output**:
- `schema_YYYYMMDD_HHMMSS.cql`: Schema definitions
- `data_YYYYMMDD_HHMMSS/`: Snapshot data

**Restore**:
```bash
# Restore schema
docker exec cassandra cqlsh -f schema_20251017_120000.cql

# Restore data
docker cp data_20251017_120000 cassandra:/var/lib/cassandra/data/
docker-compose restart cassandra
```

---

## Scheduled Backups

Add to crontab:
```bash
# Daily backup at 2 AM
0 2 * * * /path/to/scripts/backup_cassandra.sh /backups >> /var/log/backup.log 2>&1
```

## Monitoring Scripts

### Monitor System Health
```bash
#!/bin/bash
# health_check.sh

echo "=== Service Status ==="
docker-compose ps

echo -e "\n=== Kafka Lag ==="
./scripts/check_kafka_lag.sh

echo -e "\n=== Cassandra Status ==="
docker exec cassandra nodetool status

echo -e "\n=== Disk Usage ==="
df -h
```

### Alert on High Lag
```bash
#!/bin/bash
# alert_on_lag.sh

LAG=$(./scripts/check_kafka_lag.sh | awk 'NR>1 {print $6}' | sort -rn | head -1)
THRESHOLD=10000

if [ "$LAG" -gt "$THRESHOLD" ]; then
    echo "ALERT: Kafka lag is $LAG (threshold: $THRESHOLD)"
    # Send notification (Slack, email, etc.)
fi
```

## Troubleshooting

### Script Permission Denied
```bash
chmod +x scripts/*.sh
```

### Python Script Errors
```bash
# Install dependencies
pip install kafka-python websocket-client
```

### Cassandra Backup Fails
```bash
# Check disk space
df -h

# Check Cassandra is running
docker-compose ps cassandra

# Check permissions
docker exec cassandra ls -la /var/lib/cassandra
```