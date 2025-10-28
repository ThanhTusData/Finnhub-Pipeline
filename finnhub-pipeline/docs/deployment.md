# Deployment Guide

## Development Deployment

### Prerequisites
- Docker 20.10+
- Docker Compose 2.0+
- 8GB RAM minimum
- 20GB disk space

### Quick Start
```bash
# Clone repository
git clone <repo-url>
cd finnhub-pipeline

# Configure
cp .env.example .env
# Edit .env and add FINNHUB_API_KEY

# Deploy
make start

# Verify
make status
make logs
```

## Production Deployment

### Option 1: Docker Swarm

```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.prod.yaml trading

# Scale services
docker service scale trading_finnhub-producer=3
docker service scale trading_spark-processor=2
```

### Option 2: Kubernetes

```bash
# Apply base configuration
kubectl apply -f kubernetes/base/

# Apply production overlay
kubectl apply -k kubernetes/overlays/production/

# Verify deployment
kubectl get pods -n trading
kubectl get svc -n trading
```

## Configuration

### Environment Variables

**Required:**
- `FINNHUB_API_KEY`: Your Finnhub API key
- `KAFKA_BOOTSTRAP_SERVERS`: Kafka connection string
- `CASSANDRA_HOST`: Cassandra hostname

**Optional:**
- `SYMBOLS`: Stock symbols to track
- `KAFKA_TOPIC`: Topic name (default: stock-trades)
- `METRICS_PORT`: Metrics port (default: 8000)

### Resource Allocation

**Minimum (Dev):**
- Producer: 512MB RAM, 1 CPU
- Kafka: 2GB RAM, 2 CPU
- Spark: 2GB RAM, 2 CPU
- Cassandra: 4GB RAM, 2 CPU

**Recommended (Prod):**
- Producer: 1GB RAM, 2 CPU
- Kafka: 8GB RAM, 4 CPU
- Spark: 8GB RAM, 4 CPU
- Cassandra: 16GB RAM, 8 CPU

## Monitoring

### Health Checks

```bash
# Check all services
make status

# Check specific service
docker-compose ps finnhub-producer

# View metrics
curl http://localhost:8000/metrics
curl http://localhost:9090/api/v1/targets
```

### Dashboards

Access via Grafana:
- URL: http://localhost:3000
- Username: admin
- Password: admin (change in production!)

Pre-configured dashboards:
- Trading Pipeline Overview
- Kafka Metrics
- Spark Streaming Stats
- Cassandra Performance

## Backup and Recovery

### Cassandra Backup

```bash
# Manual backup
./scripts/backup_cassandra.sh

# Scheduled backup (cron)
0 2 * * * /path/to/backup_cassandra.sh /backups
```

### Kafka Backup

```bash
# Mirror topics to backup cluster
kafka-mirror-maker \
  --consumer.config source.properties \
  --producer.config target.properties \
  --whitelist "stock-trades"
```

### Recovery

```bash
# Restore Cassandra from backup
docker cp backup_dir/schema.cql cassandra:/tmp/
docker exec cassandra cqlsh -f /tmp/schema.cql

# Restore data
docker cp backup_dir/data cassandra:/var/lib/cassandra/

# Reset Spark checkpoint
make reset-checkpoint
```

## Upgrades

### Rolling Update

```bash
# Update producer
docker-compose up -d --no-deps --build finnhub-producer

# Update processor
docker-compose up -d --no-deps --build spark-processor
```

### Major Version Upgrade

1. Backup all data
2. Stop services
3. Update images
4. Migrate schemas if needed
5. Start services
6. Verify functionality

## Troubleshooting

See [troubleshooting.md](troubleshooting.md) for detailed guides.