from kafka import KafkaProducer
from kafka.errors import KafkaError
import json
import logging
from typing import Dict, Any
from .metrics import ProducerMetrics

logger = logging.getLogger(__name__)

class KafkaWriter:
    def __init__(self, config, metrics: ProducerMetrics = None):
        self.config = config
        self.metrics = metrics
        
        self.producer = KafkaProducer(
            bootstrap_servers=config.bootstrap_servers,
            client_id=config.client_id,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            key_serializer=lambda k: k.encode('utf-8') if k else None,
            acks=config.acks,
            retries=config.retries,
            compression_type=config.compression_type,
            max_in_flight_requests_per_connection=5,
            enable_idempotence=True
        )
        
        logger.info(f"Kafka producer initialized: {config.bootstrap_servers}")
    
    def write(self, trade: Dict[str, Any]) -> bool:
        """Write a single trade to Kafka"""
        try:
            symbol = trade["symbol"]
            future = self.producer.send(
                self.config.topic,
                key=symbol,
                value=trade
            )
            
            # Non-blocking send
            future.add_callback(self._on_send_success)
            future.add_errback(self._on_send_error)
            
            if self.metrics:
                self.metrics.messages_sent.labels(symbol=symbol).inc()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to write trade to Kafka: {e}")
            if self.metrics:
                self.metrics.messages_failed.labels(symbol=trade.get("symbol", "unknown")).inc()
            return False
    
    def write_batch(self, trades: list) -> int:
        """Write a batch of trades to Kafka"""
        success_count = 0
        for trade in trades:
            if self.write(trade):
                success_count += 1
        return success_count
    
    def _on_send_success(self, record_metadata):
        logger.debug(f"Message sent to {record_metadata.topic}:{record_metadata.partition}:{record_metadata.offset}")
    
    def _on_send_error(self, excp):
        logger.error(f"Failed to send message: {excp}")
        if self.metrics:
            self.metrics.kafka_errors.inc()
    
    def flush(self):
        """Flush pending messages"""
        self.producer.flush()
    
    def close(self):
        """Close the producer"""
        self.producer.close()
        logger.info("Kafka producer closed")