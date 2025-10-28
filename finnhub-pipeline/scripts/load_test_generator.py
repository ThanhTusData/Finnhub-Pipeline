#!/usr/bin/env python3
"""
Load test generator for the Finnhub pipeline
Generates synthetic trade data for testing
"""

import json
import time
import random
from kafka import KafkaProducer
from datetime import datetime

SYMBOLS = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"]
KAFKA_BOOTSTRAP = "localhost:9093"
KAFKA_TOPIC = "stock-trades"

def generate_trade(symbol: str):
    """Generate a synthetic trade"""
    base_prices = {
        "AAPL": 150.0,
        "GOOGL": 2800.0,
        "MSFT": 300.0,
        "AMZN": 3300.0,
        "TSLA": 700.0
    }
    
    base_price = base_prices.get(symbol, 100.0)
    price_variation = random.uniform(-5, 5)
    
    return {
        "symbol": symbol,
        "price": round(base_price + price_variation, 2),
        "timestamp": int(datetime.now().timestamp() * 1000),
        "volume": random.randint(10, 1000),
        "conditions": [],
        "processed_at": int(datetime.now().timestamp() * 1000)
    }

def main():
    """Generate and send synthetic trades"""
    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP,
        value_serializer=lambda v: json.dumps(v).encode('utf-8'),
        key_serializer=lambda k: k.encode('utf-8')
    )
    
    print(f"🚀 Starting load test generator")
    print(f"Target: {KAFKA_BOOTSTRAP}/{KAFKA_TOPIC}")
    print(f"Symbols: {', '.join(SYMBOLS)}")
    print("Press Ctrl+C to stop\n")
    
    trades_sent = 0
    
    try:
        while True:
            for symbol in SYMBOLS:
                trade = generate_trade(symbol)
                producer.send(KAFKA_TOPIC, key=symbol, value=trade)
                trades_sent += 1
                
                if trades_sent % 100 == 0:
                    print(f"📊 Sent {trades_sent} trades")
            
            time.sleep(0.1)  # Adjust rate here
            
    except KeyboardInterrupt:
        print(f"\n✅ Sent total of {trades_sent} trades")
        producer.close()

if __name__ == "__main__":
    main()