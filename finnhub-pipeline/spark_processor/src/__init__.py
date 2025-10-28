"""
Spark Stream Processor Package

Real-time processing of stock trading data using Apache Spark Streaming.
"""

__version__ = "1.0.0"
__author__ = "Trading Pipeline Team"

from .stream_processor import StreamProcessor
from .transformations import (
    get_trade_schema,
    parse_kafka_messages,
    add_partitioning_columns,
    calculate_aggregates,
)
from .cassandra_config import CassandraConfig

__all__ = [
    "StreamProcessor",
    "get_trade_schema",
    "parse_kafka_messages",
    "add_partitioning_columns",
    "calculate_aggregates",
    "CassandraConfig",
]