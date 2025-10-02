# scripts/load_test_generator.py
"""
Simple load generator for Kafka - JSON mode.
Usage:
  python scripts/load_test_generator.py --qps 100 --symbols AAPL,TSLA,GOOG --duration 60
"""
import argparse
import json
import random
import time
from kafka import KafkaProducer
from datetime import datetime

def gen_trade(symbol):
    return {
        "event_id": None,   # streamer will generate if missing
        "symbol": symbol,
        "price": round(random.uniform(10, 1000), 2),
        "volume": round(random.uniform(1, 2000), 2),
        "timestamp": int(time.time() * 1000),
        "conditions": [],
        "processed_at": int(time.time() * 1000)
    }

def main(args):
    producer = KafkaProducer(
        bootstrap_servers=args.bootstrap,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        key_serializer=lambda k: k.encode("utf-8") if k else None,
        retries=3
    )
    symbols = args.symbols.split(",")
    interval = 1.0 / args.qps
    end = time.time() + args.duration
    sent = 0
    try:
        while time.time() < end:
            sym = random.choice(symbols)
            trade = gen_trade(sym)
            producer.send(args.topic, key=sym, value=trade)
            sent += 1
            time.sleep(interval)
    except KeyboardInterrupt:
        pass
    finally:
        producer.flush()
        producer.close()
    print(f"Sent ~{sent} messages")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--bootstrap", default="kafka:9092")
    p.add_argument("--topic", default="market")
    p.add_argument("--qps", type=int, default=100, help="messages per second")
    p.add_argument("--symbols", default="AAPL,TSLA,GOOG,MSFT", help="comma-separated")
    p.add_argument("--duration", type=int, default=30, help="seconds to run")
    args = p.parse_args()
    main(args)
