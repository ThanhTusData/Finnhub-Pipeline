.PHONY: help build start stop restart logs clean test lint

# Default target
help:
	@echo "Finnhub Trading Pipeline - Make Commands"
	@echo ""
	@echo "Available targets:"
	@echo "  build        - Build all Docker images"
	@echo "  start        - Start all services"
	@echo "  stop         - Stop all services"
	@echo "  restart      - Restart all services"
	@echo "  logs         - View logs from all services"
	@echo "  clean        - Remove all containers and volumes"
	@echo "  test         - Run tests"
	@echo "  lint         - Run linters"
	@echo "  schema       - Initialize Cassandra schema"
	@echo "  status       - Show status of all services"

# Build all images
build:
	docker-compose build

# Start all services
start:
	docker-compose up -d
	@echo "Waiting for services to be healthy..."
	@sleep 30
	@echo "Services started successfully!"
	@echo "Grafana: http://localhost:3000 (admin/admin)"
	@echo "Prometheus: http://localhost:9090"
	@echo "Producer Metrics: http://localhost:8000"

# Stop all services
stop:
	docker-compose down

# Restart all services
restart: stop start

# View logs
logs:
	docker-compose logs -f

# View specific service logs
logs-producer:
	docker-compose logs -f finnhub-producer

logs-spark:
	docker-compose logs -f spark-processor

logs-kafka:
	docker-compose logs -f kafka

logs-cassandra:
	docker-compose logs -f cassandra

# Clean everything
clean:
	docker-compose down -v
	docker system prune -f

# Initialize schema
schema:
	docker exec cassandra cqlsh -f /schema/keyspace.cql
	docker exec cassandra cqlsh -f /schema/trades_v2.cql
	docker exec cassandra cqlsh -f /schema/trade_aggregates.cql

# Check service status
status:
	docker-compose ps

# Run tests
test:
	docker-compose exec finnhub-producer pytest tests/
	docker-compose exec spark-processor pytest tests/

# Lint code
lint:
	black finnhub_producer/src spark_processor/src
	flake8 finnhub_producer/src spark_processor/src
	isort finnhub_producer/src spark_processor/src

# Access Cassandra shell
cql:
	docker exec -it cassandra cqlsh

# Check Kafka topics
kafka-topics:
	docker exec kafka kafka-topics --bootstrap-server localhost:9092 --list

# Monitor Kafka consumer lag
kafka-lag:
	docker exec kafka kafka-consumer-groups --bootstrap-server localhost:9092 --describe --group spark-streaming

# Reset Spark checkpoint (use with caution!)
reset-checkpoint:
	docker-compose exec spark-processor rm -rf /tmp/checkpoint/*
	@echo "Checkpoint cleared. Restart spark-processor to begin fresh."