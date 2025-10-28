# Finnhub Producer

Real-time WebSocket client for ingesting stock trade data from Finnhub API.

## Features

- WebSocket connection with automatic reconnection
- Data validation and enrichment
- Kafka producer with retry logic
- Prometheus metrics export
- Configurable symbol subscription
- Error handling and logging

## Configuration

Environment variables:

```bash
FINNHUB_API_KEY=your_api_key
SYMBOLS=AAPL,GOOGL,MSFT
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
KAFKA_TOPIC=stock-trades
METRICS_PORT=8000
METRICS_ENABLED=true
```

## Running

### Docker
```bash
docker build -t finnhub-producer .
docker run -e FINNHUB_API_KEY=xxx finnhub-producer
```

### Local
```bash
pip install -r requirements.txt
export FINNHUB_API_KEY=xxx
python -m src.producer
```

## Testing

```bash
pip install -r requirements.txt pytest
pytest tests/
```

## Metrics

Available at `http://localhost:8000/metrics`:

- `finnhub_messages_received_total`: Total messages received
- `kafka_messages_sent_total`: Total messages sent to Kafka
- `websocket_connected`: Connection status
- `message_processing_latency_seconds`: Processing latency