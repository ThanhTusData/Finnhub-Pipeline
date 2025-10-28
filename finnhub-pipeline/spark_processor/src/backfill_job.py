"""
Backfill job for loading historical trade data into Cassandra
"""

import argparse
from datetime import datetime, timedelta
from pyspark.sql import SparkSession
from pyspark.sql.functions import lit
from cassandra_config import CassandraConfig
from transformations import add_partitioning_columns
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BackfillJob:
    def __init__(self, start_date: str, end_date: str):
        self.spark = CassandraConfig.get_spark_session("BackfillJob")
        self.start_date = datetime.strptime(start_date, "%Y-%m-%d")
        self.end_date = datetime.strptime(end_date, "%Y-%m-%d")
        self.keyspace = "trading"
    
    def load_historical_data(self, source_path: str):
        """Load historical data from parquet/csv files"""
        logger.info(f"Loading data from {source_path}")
        
        # Read historical data
        df = self.spark.read \
            .option("header", "true") \
            .option("inferSchema", "true") \
            .parquet(source_path)  # or .csv(source_path)
        
        # Filter by date range
        df = df.filter(
            (df.trade_time >= lit(self.start_date)) &
            (df.trade_time <= lit(self.end_date))
        )
        
        # Add partitioning columns
        df = add_partitioning_columns(df)
        
        return df
    
    def write_to_cassandra(self, df, table: str):
        """Write data to Cassandra"""
        logger.info(f"Writing to Cassandra table: {table}")
        
        df.write \
            .format("org.apache.spark.sql.cassandra") \
            .mode("append") \
            .option("keyspace", self.keyspace) \
            .option("table", table) \
            .save()
        
        logger.info(f"Successfully wrote {df.count()} records")
    
    def run(self, source_path: str, table: str = "trades_v2"):
        """Run backfill job"""
        logger.info(f"Starting backfill from {self.start_date} to {self.end_date}")
        
        # Load and transform data
        df = self.load_historical_data(source_path)
        
        # Write to Cassandra
        self.write_to_cassandra(df, table)
        
        logger.info("Backfill complete!")

def main():
    parser = argparse.ArgumentParser(description="Backfill historical trade data")
    parser.add_argument("--start-date", required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", required=True, help="End date (YYYY-MM-DD)")
    parser.add_argument("--source", required=True, help="Source data path")
    parser.add_argument("--table", default="trades_v2", help="Target table")
    
    args = parser.parse_args()
    
    job = BackfillJob(args.start_date, args.end_date)
    job.run(args.source, args.table)

if __name__ == "__main__":
    main()