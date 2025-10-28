# Observability Stack

Monitoring and alerting for the trading pipeline.

## Components

- **Prometheus**: Metrics collection and storage
- **Alertmanager**: Alert routing and notifications
- **Grafana**: Dashboards and visualization
- **Exporters**: Cassandra metrics exporter

## Access

- Prometheus: http://localhost:9090
- Alertmanager: http://localhost:9093
- Grafana: http://localhost:3000 (admin/admin)

## Metrics

### Producer Metrics
- `finnhub_messages_received_total`: Messages from Finnhub
- `kafka_messages_sent_total`: Messages sent to Kafka
- `websocket_connected`: Connection status

### Kafka Metrics
- `kafka_server_brokertopicmetrics_messagesin_total`
- `kafka_server_brokertopicmetrics_bytesin_total`
- `kafka_controller_kafkacontroller_offlinepartitionscount`

### Spark Metrics
- `spark_streaming_records_received`
- `spark_streaming_processing_time`
- `spark_streaming_scheduling_delay`

### Cassandra Metrics
- `cassandra_table_write_latency_seconds`
- `cassandra_table_read_latency_seconds`
- `cassandra_compaction_pending_tasks`

## Alerts

Pre-configured alerts:
- Producer down
- WebSocket disconnected
- High validation error rate
- Kafka write failures
- Consumer lag
- Cassandra down
- High write latency

Configure Slack webhook in `alertmanager/alertmanager.yml`.

## Custom Dashboards

Add custom dashboards to `grafana/provisioning/dashboards/`.