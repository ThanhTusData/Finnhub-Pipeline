import logging
from pyspark.sql import DataFrame
from pyspark.sql.functions import col
from cassandra_config import CassandraConfig
from transformations import (
    parse_kafka_messages,
    add_partitioning_columns,
    calculate_aggregates
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StreamProcessor:
    def __init__(self):
        self.spark = CassandraConfig.get_spark_session()
        self.kafka_bootstrap_servers = "kafka:9092"
        self.kafka_topic = "stock-trades"
        self.cassandra_keyspace = "trading"
        
    def read_from_kafka(self) -> DataFrame:
        """Read streaming data from Kafka"""
        return self.spark \
            .readStream \
            .format("kafka") \
            .option("kafka.bootstrap.servers", self.kafka_bootstrap_servers) \
            .option("subscribe", self.kafka_topic) \
            .option("startingOffsets", "latest") \
            .option("maxOffsetsPerTrigger", 10000) \
            .option("failOnDataLoss", "false") \
            .load()
    
    def write_to_cassandra(self, df: DataFrame, table: str, checkpoint_location: str):
        """Write streaming data to Cassandra"""
        return df.writeStream \
            .format("org.apache.spark.sql.cassandra") \
            .outputMode("append") \
            .option("keyspace", self.cassandra_keyspace) \
            .option("table", table) \
            .option("checkpointLocation", checkpoint_location) \
            .trigger(processingTime="5 seconds") \
            .start()
    
    def process_raw_trades(self):
        """Process and store raw trade data"""
        logger.info("Starting raw trades processor...")
        
        # Read from Kafka
        raw_df = self.read_from_kafka()
        
        # Parse and transform
        trades_df = parse_kafka_messages(raw_df)
        trades_df = add_partitioning_columns(trades_df)
        
        # Write to Cassandra
        query = self.write_to_cassandra(
            trades_df,
            "trades_v2",
            "/tmp/checkpoint/trades"
        )
        
        return query
    
    def process_aggregates(self):
        """Process and store aggregated trade data"""
        logger.info("Starting aggregates processor...")
        
        # Read from Kafka
        raw_df = self.read_from_kafka()
        
        # Parse trades
        trades_df = parse_kafka_messages(raw_df)
        
        # Calculate 1-minute aggregates
        agg_df = calculate_aggregates(trades_df, "1 minute")
        
        # Add partitioning columns
        agg_df = add_partitioning_columns(agg_df.withColumnRenamed("window_start", "trade_time"))
        
        # Write to Cassandra
        query = self.write_to_cassandra(
            agg_df,
            "trade_aggregates",
            "/tmp/checkpoint/aggregates"
        )
        
        return query
    
    def start(self):
        """Start all streaming queries"""
        logger.info("Starting Finnhub stream processor...")
        
        # Start both queries
        trades_query = self.process_raw_trades()
        aggregates_query = self.process_aggregates()
        
        # Wait for termination
        self.spark.streams.awaitAnyTermination()

def main():
    processor = StreamProcessor()
    processor.start()

if __name__ == "__main__":
    main()