# Finnhub Pipeline

## Project Overview

Finnhub Pipeline is a real‑time streaming data pipeline that ingests market data from Finnhub (WebSocket/REST), routes messages through Kafka, processes streams using Apache Spark Structured Streaming, and persists results into Apache Cassandra for fast time‑series queries and dashboards. The stack also includes observability components (Prometheus, Alertmanager, Grafana) and tools for testing, backfill, and operational maintenance.

This repository contains code and infrastructure for a development-ready end‑to‑end pipeline that demonstrates best practices for streaming architectures: schema contracts (Avro), message buffering (Kafka), scalable stream processing (Spark), durable time-series storage (Cassandra), and monitoring.

---

## Business Value

* **Real-time market data delivery**: Provide low-latency tick and quote data to traders, analysts, or downstream services.
* **Reliable buffering and replay**: Kafka decouples producers and consumers and supports replay for backfill and recovery.
* **Scalable processing**: Spark Structured Streaming allows windowed aggregations, enrichment, and fault-tolerant processing at scale.
* **Fast queryable storage**: Cassandra stores time-series data for dashboards and analytics with high write throughput and horizontal scalability.
* **Operational visibility**: Prometheus + Grafana + Alertmanager allow teams to monitor pipeline health and react fast to incidents.

---

## Repository Structure

```
Finnhub Pipeline/

├── .github/
│   └── workflows/
│       ├── ci.yml
│       └── release.yml

├── cassandra/
│   └── init.cql

├── finnhub_producer/
│   ├── producer.py
│   ├── validation.py
│   ├── config.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── tests/

├── spark_processor/
│   ├── stream_processor.py
│   ├── backfill_job.py
│   ├── cassandra_config.py
│   ├── requirements.txt
│   └── tests/

├── grafana/
│   ├── dashboards/ (stock_dashboard.json)
│   └── provisioning/

├── observability/
│   ├── prometheus/
│   ├── alertmanager/
│   └── jmx/

├── schemas/ (stock_tick.avsc)
├── scripts/ (load_test_generator.py, reset_checkpoint.sh)
├── docker-compose.yaml
├── Makefile
├── .env.example
└── README.md
```

> Note: The above tree is a high-level summary. See the repository root for the exact file list and locations.

---

## Components & Tools (what and why)

* **Finnhub Producer** (`finnhub_producer/`) — Python script that connects to Finnhub (WebSocket), validates messages (Avro-like contract), and publishes to Kafka. Responsible for schema validation and minimal enrichment.

* **Apache Kafka** — durable, scalable message broker used as the central streaming backbone. Decouples producers and consumers and supports replay for backfill.

* **Apache Spark Structured Streaming** (`spark_processor/`) — consumes from Kafka, performs transformations, windowed aggregations, enrichment, and writes results to Cassandra (or other sinks). Chosen for maturity, stability, and rich streaming APIs.

* **Apache Cassandra** (`cassandra/init.cql`) — time-series optimized NoSQL DB to persist ticks and aggregated results with high write throughput and horizontal scalability.

* **Grafana** (`grafana/`) — dashboards for visualizing metrics and Cassandra-derived data (stock dashboards, service health).

* **Prometheus + Alertmanager + JMX** (`observability/`) — collect, store, and alert on metrics from producer, Kafka, and Spark.

* **Avro Schema** (`schemas/stock_tick.avsc`) — enforce message contract between producer and consumer to prevent breaking changes.

* **Helper scripts** (`scripts/`) — utilities for load testing (`load_test_generator.py`), checkpoint resets, and backfill operations.

* **CI/CD** (`.github/workflows/`) — automated tests and release workflow to build and publish service images.

---

## Requirements

* Docker & Docker Compose (recommended for development). For production consider Kubernetes.
* Python 3.10+ (for local script development and tests).
* Sufficient system resources for local multi-container stack (Kafka, Zookeeper, Spark, Cassandra, Grafana).
* Finnhub API Key (set in `.env`).

---

## Quick Start (Development)

1. **Clone repository**

```bash
git clone <repo-url>
cd finnhub-pipeline
```

2. **Copy and configure environment**

```bash
cp .env.example .env
# Edit .env: set FINNHUB_API_KEY, KAFKA_HOST, CASSANDRA credentials, and any ports.
```

3. **Start full stack with Docker Compose**

```bash
docker-compose up --build -d
# or use Makefile if provided
make up
```

4. **Check logs**

```bash
docker-compose logs -f finnhub_producer
docker-compose logs -f spark_processor
```

5. **Run the producer locally (optional)**

```bash
cd finnhub_producer
pip install -r requirements.txt
python producer.py
```

6. **Run Spark processor locally or via container**

Local Python run (for development):

```bash
cd spark_processor
pip install -r requirements.txt
python stream_processor.py
```

Production/cluster run: submit via `spark-submit` with appropriate dependencies and configuration.

7. **Import Grafana dashboard**

If Grafana container is up, import `grafana/dashboards/stock_dashboard.json` or rely on provisioning files included in `grafana/provisioning/`.

---

## Backfill & Checkpointing

* Use `spark_processor/backfill_job.py` to process historical data stored in object storage or files.
* To re-run streaming job from scratch, you may reset Spark checkpoints with `scripts/reset_checkpoint.sh <job-checkpoint-path>` (use carefully in production).

---

## Testing

* Unit tests live in each component's `tests/` directory (e.g., `finnhub_producer/tests`, `spark_processor/tests`).
* Run tests with `pytest`:

```bash
pytest finnhub_producer/tests
pytest spark_processor/tests
```

* Use `scripts/load_test_generator.py` to generate synthetic load for performance testing.

---

## Observability & Alerts

* Prometheus scrapes metrics exposed by the producer, Spark, and Kafka (via JMX exporters).
* Grafana dashboards visualize latency, throughput, topic lag, and Cassandra write metrics.
* Alertmanager handles alert routing (email/Slack/pager) based on rules in `observability/prometheus/rules.yml`.

---

## Troubleshooting (common issues)

* **Producer not publishing**: verify FINNHUB_API_KEY, internet access, and Kafka broker endpoint in `.env`.
* **Spark not consuming**: check topic name, Kafka bootstrap servers, and checkpoint path. Look for schema mismatches.
* **Cassandra writes failing**: check keyspace, table schema, and Cassandra logs. Ensure credentials and replication settings are correct.
* **Grafana empty dashboards**: confirm datasource provisioning and that metrics are being written to the target store.

---

## Roadmap & Suggested Improvements

1. **Schema Registry**: integrate Confluent Schema Registry for managed schema versions and compatibility checks.
2. **TLS & Auth**: enable TLS/SASL for Kafka and secure connections for Cassandra and Grafana.
3. **Kubernetes**: migrate to k8s + Helm for production-grade orchestration and autoscaling.
4. **Data Lake**: persist raw events into S3 or MinIO (Parquet/Delta) for historical analytics and ML training.
5. **Kafka Connect**: add sink connectors (S3, ElasticSearch) for simplified data export.
6. **Tracing**: integrate OpenTelemetry for end-to-end tracing across services.
7. **Flink option**: consider Apache Flink for complex event-time processing and lower latency guarantees.
8. **Contract testing**: add integration/contract tests (Pact or schema-based) to prevent producer/consumer breakages.
