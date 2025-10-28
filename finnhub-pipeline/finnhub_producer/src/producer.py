import websocket
import json
import logging
import time
from typing import List
import signal
import sys
from .config import Config
from .validator import TradeValidator
from .kafka_writer import KafkaWriter
from .metrics import ProducerMetrics

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FinnhubProducer:
    def __init__(self, config: Config):
        self.config = config
        self.validator = TradeValidator()
        self.metrics = ProducerMetrics(config.metrics.port) if config.metrics.enabled else None
        self.kafka_writer = KafkaWriter(config.kafka, self.metrics)
        self.ws = None
        self.running = False
        
    def on_message(self, ws, message):
        """Handle incoming WebSocket messages"""
        try:
            start_time = time.time()
            data = json.loads(message)
            
            if data.get("type") == "trade":
                trades = data.get("data", [])
                
                # Validate trades
                valid_trades = self.validator.validate_batch(trades)
                
                # Track metrics
                for trade in trades:
                    symbol = trade.get("s", "unknown")
                    if self.metrics:
                        self.metrics.messages_received.labels(symbol=symbol).inc()
                
                # Write to Kafka
                success_count = self.kafka_writer.write_batch(valid_trades)
                
                logger.debug(f"Processed {len(trades)} trades, {success_count} sent to Kafka")
                
                # Track latency
                if self.metrics:
                    latency = time.time() - start_time
                    self.metrics.message_latency.observe(latency)
                    
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    def on_error(self, ws, error):
        """Handle WebSocket errors"""
        logger.error(f"WebSocket error: {error}")
        if self.metrics:
            self.metrics.websocket_connected.set(0)
    
    def on_close(self, ws, close_status_code, close_msg):
        """Handle WebSocket connection close"""
        logger.warning(f"WebSocket closed: {close_status_code} - {close_msg}")
        if self.metrics:
            self.metrics.websocket_connected.set(0)
    
    def on_open(self, ws):
        """Handle WebSocket connection open"""
        logger.info("WebSocket connection established")
        if self.metrics:
            self.metrics.websocket_connected.set(1)
            self.metrics.active_symbols.set(len(self.config.finnhub.symbols))
        
        # Subscribe to symbols
        for symbol in self.config.finnhub.symbols:
            subscribe_message = {
                "type": "subscribe",
                "symbol": symbol
            }
            ws.send(json.dumps(subscribe_message))
            logger.info(f"Subscribed to {symbol}")
    
    def start(self):
        """Start the producer"""
        self.running = True
        
        # Start metrics server
        if self.metrics:
            self.metrics.start()
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Connect to WebSocket with retry logic
        while self.running:
            try:
                logger.info("Connecting to Finnhub WebSocket...")
                
                ws_url = f"{self.config.finnhub.websocket_url}?token={self.config.finnhub.api_key}"
                
                self.ws = websocket.WebSocketApp(
                    ws_url,
                    on_message=self.on_message,
                    on_error=self.on_error,
                    on_close=self.on_close,
                    on_open=self.on_open
                )
                
                self.ws.run_forever()
                
                if self.running:
                    logger.warning("WebSocket disconnected, reconnecting in 5 seconds...")
                    if self.metrics:
                        self.metrics.websocket_reconnects.inc()
                    time.sleep(5)
                    
            except Exception as e:
                logger.error(f"Fatal error: {e}")
                if self.running:
                    time.sleep(5)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.stop()
    
    def stop(self):
        """Stop the producer gracefully"""
        self.running = False
        
        if self.ws:
            self.ws.close()
        
        self.kafka_writer.flush()
        self.kafka_writer.close()
        
        logger.info("Producer stopped")
        sys.exit(0)

def main():
    config = Config()
    config.validate()
    
    producer = FinnhubProducer(config)
    producer.start()

if __name__ == "__main__":
    main()