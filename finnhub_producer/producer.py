# finnhub_producer/producer.py  (updated with validation + DLQ)
import websocket
import json
import logging
import time
import os
import io
import struct

from kafka import KafkaProducer
from config import FINNHUB_API_KEY, KAFKA_BOOTSTRAP_SERVERS, KAFKA_TOPIC, SYMBOLS, USE_AVRO, SCHEMA_REGISTRY_URL

# Try relative import for validation (keeps compatibility with how you import config)
try:
    from validation import validate_and_normalize
except Exception:
    # fallback if module load path differs
    from finnhub_producer.validation import validate_and_normalize

# only import fastavro & requests when needed (requirements.txt includes them)
if USE_AVRO:
    import requests
    from fastavro import schemaless_writer, parse_schema

# --- Prometheus instrumentation ---
from prometheus_client import Counter, Gauge, start_http_server

# Define basic metrics
PRODUCED_TOTAL = Counter("finnhub_produced_total", "Total number of messages produced")
PRODUCE_ERRORS = Counter("finnhub_produce_errors_total", "Total number of produce errors")
PARSE_ERRORS = Counter("finnhub_parse_errors_total", "Total number of parse errors")
LAST_PRODUCE_TIMESTAMP = Gauge("finnhub_last_produce_timestamp", "Unix ms timestamp of last successful produce")

# DQ / DLQ metrics
DQ_REJECTIONS = Counter("finnhub_dq_rejections_total", "Total number of messages rejected by data quality validation")
DLQ_PRODUCED = Counter("finnhub_dlq_produced_total", "Total number of messages produced to DLQ")

# metrics server port (can be overriden via env if you want)
METRICS_PORT = int(os.getenv("METRICS_PORT", "8000"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# DLQ topic default (can be overridden via env)
KAFKA_DLQ_TOPIC = os.getenv("KAFKA_DLQ_TOPIC", f"{KAFKA_TOPIC}_dlq")

# If use Avro: load local schema
AVRO_SCHEMA = None
AVRO_SCHEMA_ID = None
AVRO_SUBJECT = f"{KAFKA_TOPIC}-value"
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "../schemas/stock_tick.avsc")


class FinnhubProducer:
    def __init__(self):
        self.producer = None
        self.ws = None

        # start metrics HTTP server early
        try:
            start_http_server(METRICS_PORT)
            logger.info(f"Prometheus metrics server started on port {METRICS_PORT}")
        except Exception as e:
            logger.warning(f"Failed to start Prometheus HTTP server on port {METRICS_PORT}: {e}")

        self.setup_kafka_producer()
        if USE_AVRO:
            self.setup_avro_schema()

    def setup_kafka_producer(self):
        """Initialize Kafka producer with retry logic"""
        max_retries = 10
        retry_count = 0

        while retry_count < max_retries:
            try:
                # For Avro mode we send bytes (already serialized), for JSON we send utf-8 encoded json
                if USE_AVRO:
                    value_serializer = lambda v: v  # already bytes
                else:
                    value_serializer = lambda v: json.dumps(v).encode('utf-8')

                self.producer = KafkaProducer(
                    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                    value_serializer=value_serializer,
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

    def setup_avro_schema(self):
        """Load Avro schema and register with Schema Registry (returns schema id)"""
        global AVRO_SCHEMA, AVRO_SCHEMA_ID
        try:
            with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
                schema_json = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load Avro schema file {SCHEMA_PATH}: {e}")
            raise

        AVRO_SCHEMA = parse_schema(schema_json)

        # Register schema (or get existing id)
        try:
            logger.info("Registering/fetching schema from Schema Registry...")
            register_url = f"{SCHEMA_REGISTRY_URL}/subjects/{AVRO_SUBJECT}/versions"
            headers = {"Content-Type": "application/vnd.schemaregistry.v1+json"}
            payload = {"schema": json.dumps(schema_json)}
            resp = requests.post(register_url, headers=headers, json=payload, timeout=10)
            if resp.status_code in (200, 201):
                AVRO_SCHEMA_ID = resp.json().get("id")
                logger.info(f"Schema registered with id {AVRO_SCHEMA_ID}")
            else:
                # There may be a case it already exists; try to get latest
                logger.warning(f"Schema registry returned status {resp.status_code}, trying to get latest...")
                latest_url = f"{SCHEMA_REGISTRY_URL}/subjects/{AVRO_SUBJECT}/versions/latest"
                resp2 = requests.get(latest_url, timeout=10)
                resp2.raise_for_status()
                AVRO_SCHEMA_ID = resp2.json().get("id")
                logger.info(f"Using existing schema id {AVRO_SCHEMA_ID}")
        except Exception as e:
            logger.error(f"Failed to register/get schema from Schema Registry: {e}")
            raise

    def avro_serialize_with_confluent_wire_format(self, record: dict) -> bytes:
        """
        Produce message in Confluent wire format:
        [magic byte 0][schema id (4 bytes big-endian)][avro payload bytes]
        """
        if AVRO_SCHEMA is None or AVRO_SCHEMA_ID is None:
            raise RuntimeError("Avro schema not initialized")

        bio = io.BytesIO()
        schemaless_writer(bio, AVRO_SCHEMA, record)
        avro_bytes = bio.getvalue()
        # magic byte 0 + 4-byte schema id (big-endian)
        header = struct.pack(">bI", 0, int(AVRO_SCHEMA_ID))
        return header + avro_bytes

    def send_to_dlq(self, original_payload, errors, key=None):
        """
        Send a JSON DLQ message to DLQ topic. Attach header with reasons (joined).
        """
        try:
            dlq_payload = {
                "original": original_payload,
                "errors": errors,
                "dlq_timestamp": int(time.time() * 1000),
                "source_topic": KAFKA_TOPIC
            }
            # send as JSON bytes regardless of producer mode to keep DLQ readable
            value = json.dumps(dlq_payload).encode("utf-8")
            headers = [("error_reasons", ";".join(errors).encode("utf-8"))]
            future = self.producer.send(KAFKA_DLQ_TOPIC, key=(key.encode('utf-8') if key else None), value=value, headers=headers)
            future.add_callback(lambda md: DLQ_PRODUCED.inc())
            future.add_errback(lambda exc: logger.error(f"Failed to send to DLQ: {exc}"))
            DQ_REJECTIONS.inc(len(errors) if len(errors) > 0 else 1)
        except Exception as e:
            logger.error(f"Exception while sending to DLQ: {e}")

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

                    # ---- NEW: validate record before sending ----
                    try:
                        is_valid, errors, norm = validate_and_normalize(enriched_trade)
                    except Exception as e:
                        logger.exception(f"Validation function crashed: {e}")
                        # Treat as parse error -> send to DLQ with reason function_error
                        self.send_to_dlq(enriched_trade, ["validation_func_exception"], key=trade.get('s'))
                        PARSE_ERRORS.inc()
                        continue

                    if not is_valid:
                        logger.info(f"Record failed validation for {enriched_trade.get('symbol')}: {errors}")
                        # send to DLQ (include original payload & reasons)
                        self.send_to_dlq(enriched_trade, errors, key=trade.get('s'))
                        continue

                    # If valid, produce to main topic
                    if USE_AVRO:
                        try:
                            # try to serialize the normalized record with avro
                            payload = self.avro_serialize_with_confluent_wire_format(norm)
                        except Exception as e:
                            logger.error(f"Avro serialization failed, sending to DLQ: {e}")
                            PARSE_ERRORS.inc()
                            # send original/enriched to DLQ with reason 'avro_serialize_failed'
                            self.send_to_dlq(enriched_trade, ["avro_serialize_failed"], key=trade.get('s'))
                            continue
                        future = self.producer.send(KAFKA_TOPIC, key=trade.get('s'), value=payload)
                    else:
                        future = self.producer.send(KAFKA_TOPIC, key=trade.get('s'), value=norm)

                    future.add_callback(self.on_send_success)
                    future.add_errback(self.on_send_error)

                    logger.info(f"Sent trade: {trade.get('s')} @ {trade.get('p')}")

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON message: {e}")
            PARSE_ERRORS.inc()
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            PARSE_ERRORS.inc()

    def on_send_success(self, record_metadata):
        """Callback for successful message delivery"""
        logger.debug(f"Message delivered to {record_metadata.topic} partition {record_metadata.partition}")
        PRODUCED_TOTAL.inc()
        LAST_PRODUCE_TIMESTAMP.set(int(time.time() * 1000))

    def on_send_error(self, excp):
        """Callback for failed message delivery"""
        logger.error(f"Failed to deliver message: {excp}")
        PRODUCE_ERRORS.inc()

    def on_error(self, ws, error):
        """Handle WebSocket errors"""
        logger.error(f"WebSocket error: {error}")
        if self.ws == ws:
            try:
                self.ws.close()
            except:
                pass
            self.ws = None

    def on_close(self, ws, close_status_code, close_msg):
        """Handle WebSocket close"""
        logger.info(f"WebSocket connection closed - Status: {close_status_code}, Message: {close_msg}")
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
                    # websocket-client reconnection handled by our while loop
                )

            except Exception as e:
                logger.error(f"WebSocket connection failed: {e}")
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
