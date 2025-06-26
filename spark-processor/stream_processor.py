import os
import logging
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
from cassandra_config import get_cassandra_config, CASSANDRA_KEYSPACE

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StreamProcessor:
    def __init__(self):
        self.spark = None
        self.setup_spark_session()
        
    def setup_spark_session(self):
        """Initialize Spark session with Cassandra connector"""
        cassandra_config = get_cassandra_config()
        
        builder = SparkSession.builder \
            .appName("FinnhubStreamProcessor") \
            .config("spark.jars.packages", 
                    "org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.1,"
                    "com.datastax.spark:spark-cassandra-connector_2.12:3.4.1") \
            .config("spark.sql.streaming.checkpointLocation", "/tmp/checkpoint")
            
        for key, value in cassandra_config.items():
            builder = builder.config(key, value)
            
        self.spark = builder.getOrCreate()
        self.spark.sparkContext.setLogLevel("WARN")
        logger.info("Spark session initialized")

    def define_schema(self):
        """Define schema for incoming JSON data"""
        return StructType([
            StructField("symbol", StringType(), True),
            StructField("price", DoubleType(), True),
            StructField("volume", DoubleType(), True),
            StructField("timestamp", LongType(), True),
            StructField("conditions", ArrayType(StringType()), True),
            StructField("processed_at", LongType(), True)
        ])

    def process_stream(self):
        """Process Kafka stream and write to Cassandra"""
        schema = self.define_schema()
        
        # Read from Kafka
        df = self.spark \
            .readStream \
            .format("kafka") \
            .option("kafka.bootstrap.servers", "kafka:9092") \
            .option("subscribe", "market") \
            .option("startingOffsets", "latest") \
            .load()

        # Parse JSON and add processing timestamp
        parsed_df = df.select(
            col("key").cast("string").alias("key"),
            from_json(col("value").cast("string"), schema).alias("data"),
            col("timestamp").alias("kafka_timestamp")
        ).select(
            col("data.*"),
            col("kafka_timestamp"),
            current_timestamp().alias("spark_processed_at")
        )

        # Add derived columns
        enriched_df = parsed_df.withColumn(
            "price_change_indicator", 
            when(col("volume") > 1000, "high_volume").otherwise("normal_volume")
        ).withColumn(
            "trade_date", 
            to_date(from_unixtime(col("timestamp") / 1000))
        ).withColumn(
            "trade_hour", 
            hour(from_unixtime(col("timestamp") / 1000))
        )

        # Write to Cassandra
        query = enriched_df.writeStream \
            .outputMode("append") \
            .format("org.apache.spark.sql.cassandra") \
            .option("keyspace", CASSANDRA_KEYSPACE) \
            .option("table", "trades") \
            .option("checkpointLocation", "/tmp/checkpoint/trades") \
            .start()

        # Also create aggregated data for analytics
        windowed_df = parsed_df \
            .withWatermark("spark_processed_at", "1 minute") \
            .groupBy(
                window(col("spark_processed_at"), "1 minute"),
                col("symbol")
            ).agg(
                avg("price").alias("avg_price"),
                max("price").alias("max_price"),
                min("price").alias("min_price"),
                sum("volume").alias("total_volume"),
                count("*").alias("trade_count")
            ).select(
                col("window.start").alias("window_start"),
                col("window.end").alias("window_end"),
                col("symbol"),
                col("avg_price"),
                col("max_price"),
                col("min_price"),
                col("total_volume"),
                col("trade_count")
            )

        # Write aggregated data
        agg_query = windowed_df.writeStream \
            .outputMode("update") \
            .format("org.apache.spark.sql.cassandra") \
            .option("keyspace", CASSANDRA_KEYSPACE) \
            .option("table", "trade_aggregates") \
            .option("checkpointLocation", "/tmp/checkpoint/aggregates") \
            .start()

        return query, agg_query

    def start_processing(self):
        """Start stream processing"""
        logger.info("Starting stream processing...")
        
        try:
            query, agg_query = self.process_stream()
            
            # Wait for both queries
            query.awaitTermination()
            agg_query.awaitTermination()
            
        except Exception as e:
            logger.error(f"Stream processing failed: {e}")
            raise

if __name__ == "__main__":
    processor = StreamProcessor()
    processor.start_processing()