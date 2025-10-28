"""
Utility functions for Spark processing
"""

from pyspark.sql import DataFrame
from pyspark.sql.functions import col, when, lit
import logging

logger = logging.getLogger(__name__)

def deduplicate_trades(df: DataFrame) -> DataFrame:
    """Remove duplicate trades based on symbol and timestamp"""
    return df.dropDuplicates(["symbol", "timestamp"])

def filter_outliers(df: DataFrame, price_col: str = "price", std_dev: float = 3.0) -> DataFrame:
    """Filter out price outliers using standard deviation"""
    stats = df.select(
        mean(price_col).alias("mean"),
        stddev(price_col).alias("stddev")
    ).first()
    
    if stats.stddev is None:
        return df
    
    lower_bound = stats.mean - (std_dev * stats.stddev)
    upper_bound = stats.mean + (std_dev * stats.stddev)
    
    return df.filter(
        (col(price_col) >= lower_bound) &
        (col(price_col) <= upper_bound)
    )

def add_market_hours_flag(df: DataFrame) -> DataFrame:
    """Add flag indicating if trade occurred during market hours (9:30 AM - 4:00 PM ET)"""
    return df.withColumn(
        "is_market_hours",
        when(
            (col("trade_hour") >= 9) & (col("trade_hour") < 16),
            lit(True)
        ).otherwise(lit(False))
    )

def calculate_vwap(df: DataFrame) -> DataFrame:
    """Calculate Volume Weighted Average Price"""
    return df.withColumn(
        "price_volume",
        col("price") * col("volume")
    )

def log_dataframe_info(df: DataFrame, name: str):
    """Log DataFrame information for debugging"""
    logger.info(f"DataFrame: {name}")
    logger.info(f"  Schema: {df.schema}")
    logger.info(f"  Count: {df.count()}")
    logger.info(f"  Partitions: {df.rdd.getNumPartitions()}")

def repartition_by_symbol(df: DataFrame, num_partitions: int = 10) -> DataFrame:
    """Repartition DataFrame by symbol for better parallelism"""
    return df.repartition(num_partitions, "symbol")