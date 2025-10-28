# Grafana Dashboards

Visualization and monitoring dashboards.

## Access

URL: http://localhost:3000
Username: admin
Password: admin (change in production!)

## Dashboards

### Stock Trading Pipeline
- Real-time message rates
- WebSocket connection status
- Processing latency
- Kafka consumer lag
- Live stock prices

## Data Sources

- **Prometheus**: System metrics
- **Cassandra**: Trade data queries

## Adding Custom Dashboards

1. Create dashboard in Grafana UI
2. Export JSON
3. Save to `provisioning/dashboards/`
4. Restart Grafana

## Variables

Configure dashboard variables for:
- Symbol selection
- Time range
- Aggregation interval