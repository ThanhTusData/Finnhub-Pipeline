from prometheus_client import Counter, Gauge, Histogram, start_http_server
import logging

logger = logging.getLogger(__name__)

class ProducerMetrics:
    def __init__(self, port: int = 8000):
        self.port = port
        
        # Counters
        self.messages_received = Counter(
            'finnhub_messages_received_total',
            'Total messages received from Finnhub',
            ['symbol']
        )
        
        self.messages_sent = Counter(
            'kafka_messages_sent_total',
            'Total messages sent to Kafka',
            ['symbol']
        )
        
        self.messages_failed = Counter(
            'kafka_messages_failed_total',
            'Total messages failed to send to Kafka',
            ['symbol']
        )
        
        self.validation_errors = Counter(
            'validation_errors_total',
            'Total validation errors',
            ['symbol']
        )
        
        self.websocket_reconnects = Counter(
            'websocket_reconnects_total',
            'Total WebSocket reconnection attempts'
        )
        
        self.kafka_errors = Counter(
            'kafka_errors_total',
            'Total Kafka errors'
        )
        
        # Gauges
        self.websocket_connected = Gauge(
            'websocket_connected',
            'WebSocket connection status (1=connected, 0=disconnected)'
        )
        
        self.active_symbols = Gauge(
            'active_symbols_count',
            'Number of active symbols subscribed'
        )
        
        # Histograms
        self.message_latency = Histogram(
            'message_processing_latency_seconds',
            'Message processing latency',
            buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0]
        )
        
    def start(self):
        """Start metrics HTTP server"""
        try:
            start_http_server(self.port)
            logger.info(f"Metrics server started on port {self.port}")
        except Exception as e:
            logger.error(f"Failed to start metrics server: {e}")