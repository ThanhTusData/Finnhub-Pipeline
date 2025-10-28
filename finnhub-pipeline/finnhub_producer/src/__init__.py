"""
Finnhub Producer Package

Real-time stock trading data ingestion from Finnhub WebSocket API.
"""

__version__ = "1.0.0"
__author__ = "Trading Pipeline Team"

from .producer import FinnhubProducer
from .validator import TradeValidator
from .kafka_writer import KafkaWriter
from .config import Config

__all__ = [
    "FinnhubProducer",
    "TradeValidator",
    "KafkaWriter",
    "Config",
]