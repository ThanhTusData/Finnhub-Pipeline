from pyspark.sql import DataFrame
from pyspark.sql.functions import (
    col, from_json, window, avg, sum as _sum, max as _max, 
    min as _min, count, stddev, first, last, 
    year, month, dayofmonth, hour, from_unixtime, to_timestamp
)
from pyspark.sql.types import (
    StructType, StructField, StringType, 
    DoubleType, LongType, ArrayType
)

def get_trade_schema():
    """Define schema for incoming trade data"""
    return StructType([
        StructField("symbol", StringType(), False),
        StructField("price", DoubleType(), False),
        StructField("timestamp", LongType(), False),
        StructField("volume", DoubleType(), False),
        StructField("conditions", ArrayType(StringType()), True),
        StructField("processed_at", LongType(), True)
    ])

def parse_kafka_messages(df: DataFrame) -> DataFrame:
    """Parse Kafka messages from JSON"""
    schema = get_trade_schema()
    
    return df.select(
        from_json(col("value").cast("string"), schema).alias("data")
    ).select("data.*") \
    .withColumn("trade_time", to_timestamp(col("timestamp") / 1000))

def add_partitioning_columns(df: DataFrame) -> DataFrame:
    """Add date partitioning columns for Cassandra"""
    return df \
        .withColumn("trade_year", year(col("trade_time"))) \
        .withColumn("trade_month", month(col("trade_time"))) \
        .withColumn("trade_day", dayofmonth(col("trade_time"))) \
        .withColumn("trade_hour", hour(col("trade_time")))

def calculate_aggregates(df: DataFrame, window_duration: str = "1 minute") -> DataFrame:
    """Calculate trading aggregates over time windows"""
    return df \
        .withWatermark("trade_time", "10 seconds") \
        .groupBy(
            window(col("trade_time"), window_duration),
            col("symbol")
        ) \
        .agg(
            _sum("volume").alias("total_volume"),
            avg("price").alias("avg_price"),
            _max("price").alias("high_price"),
            _min("price").alias("low_price"),
            first("price").alias("open_price"),
            last("price").alias("close_price"),
            count("*").alias("trade_count"),
            stddev("price").alias("price_volatility")
        ) \
        .select(
            col("symbol"),
            col("window.start").alias("window_start"),
            col("window.end").alias("window_end"),
            col("total_volume"),
            col("avg_price"),
            col("high_price"),
            col("low_price"),
            col("open_price"),
            col("close_price"),
            col("trade_count"),
            col("price_volatility")
        )