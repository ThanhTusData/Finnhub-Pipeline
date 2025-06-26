import websocket
import json
import logging
from kafka import KafkaProducer
from kafka.errors import KafkaError
import time
from config import FINNHUB_API_KEY, KAFKA_BOOTSTRAP_SERVERS, KAFKA_TOPIC, SYMBOLS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FinnhubProducer:
    def __init__(self):
        self.producer = None
        self.ws = None
        self.setup_kafka_producer()
        
    def setup_kafka_producer(self):
        """Initialize Kafka producer with retry logic"""
        max_retries = 10
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                self.producer = KafkaProducer(
                    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                    key_serializer=lambda k: k.encode('utf-8') if k else None,
                    acks='all',
                    retries=3,
                    batch_size=16384,
                    linger_ms=10
                )
                logger.info("Kafka producer initialized successfully")
                break
            except Exception as e:
                retry_count += 1
                logger.error(f"Failed to connect to Kafka (attempt {retry_count}): {e}")
                time.sleep(5)
        
        if retry_count >= max_retries:
            raise Exception("Failed to connect to Kafka after maximum retries")

    def on_message(self, ws, message):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(message)
            
            if data.get('type') == 'trade' and 'data' in data:
                for trade in data['data']:
                    # Enrich trade data with timestamp
                    enriched_trade = {
                        'symbol': trade.get('s'),
                        'price': trade.get('p'),
                        'volume': trade.get('v'),
                        'timestamp': trade.get('t'),
                        'conditions': trade.get('c', []),
                        'processed_at': int(time.time() * 1000)
                    }
                    
                    # Send to Kafka
                    future = self.producer.send(
                        KAFKA_TOPIC,
                        key=trade.get('s'),
                        value=enriched_trade
                    )
                    
                    # Optional: Add callback for delivery confirmation
                    future.add_callback(self.on_send_success)
                    future.add_errback(self.on_send_error)
                    
                    logger.info(f"Sent trade: {trade.get('s')} @ {trade.get('p')}")
                    
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON message: {e}")
        except Exception as e:
            logger.error(f"Error processing message: {e}")

    def on_send_success(self, record_metadata):
        """Callback for successful message delivery"""
        logger.debug(f"Message delivered to {record_metadata.topic} partition {record_metadata.partition}")

    def on_send_error(self, excp):
        """Callback for failed message delivery"""
        logger.error(f"Failed to deliver message: {excp}")

    def on_error(self, ws, error):
        """Handle WebSocket errors"""
        logger.error(f"WebSocket error: {error}")
        
        # Close the connection on error to ensure clean state
        if self.ws == ws:
            try:
                self.ws.close()
            except:
                pass
            self.ws = None

    def on_close(self, ws, close_status_code, close_msg):
        """Handle WebSocket close"""
        logger.info(f"WebSocket connection closed - Status: {close_status_code}, Message: {close_msg}")
        
        # Clean up the WebSocket reference
        if self.ws == ws:
            self.ws = None

    def on_open(self, ws):
        """Handle WebSocket open - subscribe to symbols"""
        logger.info("WebSocket connection opened")
        
        for symbol in SYMBOLS:
            subscribe_msg = json.dumps({
                "type": "subscribe",
                "symbol": symbol
            })
            ws.send(subscribe_msg)
            logger.info(f"Subscribed to {symbol}")

    def start(self):
        """Start the WebSocket connection"""
        websocket.enableTrace(False)  # Disable trace to reduce logs
        
        ws_url = f"wss://ws.finnhub.io?token={FINNHUB_API_KEY}"
        
        # Run forever with proper reconnection logic
        while True:
            try:
                # Create new WebSocket instance for each connection attempt
                self.ws = websocket.WebSocketApp(
                    ws_url,
                    on_message=self.on_message,
                    on_error=self.on_error,
                    on_close=self.on_close
                )
                self.ws.on_open = self.on_open
                
                logger.info("Starting WebSocket connection...")
                self.ws.run_forever(
                    ping_interval=30,      # Send ping every 30 seconds
                    ping_timeout=10,       # Wait 10 seconds for pong
                    reconnect=3            # Retry 3 times before giving up
                )
                
            except Exception as e:
                logger.error(f"WebSocket connection failed: {e}")
                
                # Ensure WebSocket is properly closed
                if self.ws:
                    try:
                        self.ws.close()
                    except:
                        pass
                    self.ws = None
                
                logger.info("Reconnecting in 10 seconds...")
                time.sleep(10)

    def stop(self):
        """Stop the producer"""
        logger.info("Stopping producer...")
        
        if self.ws:
            try:
                self.ws.close()
            except:
                pass
            self.ws = None
            
        if self.producer:
            self.producer.flush()
            self.producer.close()
            logger.info("Producer stopped successfully")

if __name__ == "__main__":
    producer = FinnhubProducer()
    try:
        producer.start()
    except KeyboardInterrupt:
        logger.info("Shutting down producer...")
        producer.stop()