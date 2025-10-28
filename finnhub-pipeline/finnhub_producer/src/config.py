import os
from dataclasses import dataclass
from typing import List

@dataclass
class FinnhubConfig:
    api_key: str
    websocket_url: str = "wss://ws.finnhub.io"
    symbols: List[str] = None
    
    def __post_init__(self):
        if self.symbols is None:
            self.symbols = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"]

@dataclass
class KafkaConfig:
    bootstrap_servers: str
    topic: str
    client_id: str = "finnhub-producer"
    acks: str = "all"
    retries: int = 3
    compression_type: str = "snappy"
    
@dataclass
class MetricsConfig:
    port: int = 8000
    enabled: bool = True

class Config:
    def __init__(self):
        self.finnhub = FinnhubConfig(
            api_key=os.getenv("FINNHUB_API_KEY", ""),
            symbols=os.getenv("SYMBOLS", "AAPL,GOOGL,MSFT,AMZN,TSLA,META,NVDA,NFLX").split(",")
        )
        
        self.kafka = KafkaConfig(
            bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092"),
            topic=os.getenv("KAFKA_TOPIC", "stock-trades")
        )
        
        self.metrics = MetricsConfig(
            port=int(os.getenv("METRICS_PORT", "8000")),
            enabled=os.getenv("METRICS_ENABLED", "true").lower() == "true"
        )
        
    def validate(self):
        if not self.finnhub.api_key:
            raise ValueError("FINNHUB_API_KEY is required")
        if not self.kafka.bootstrap_servers:
            raise ValueError("KAFKA_BOOTSTRAP_SERVERS is required")