import os
from dotenv import load_dotenv

load_dotenv()

FINNHUB_API_KEY = os.getenv('FINNHUB_API_KEY')
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
KAFKA_TOPIC = os.getenv('KAFKA_TOPIC', 'market')

# Symbols to subscribe
SYMBOLS = [
    'AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA',
    'NVDA', 'META', 'NFLX', 'BINANCE:BTCUSDT',
    'BINANCE:ETHUSDT'
]