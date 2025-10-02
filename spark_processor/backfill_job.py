# spark_processor/backfill_job.py
"""
Backfill script: export from old table (trades) into new time-series table (trades_v2).
Usage (example):
  spark-submit \
    --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.1,com.datastax.spark:spark-cassandra-connector_2.12:3.4.1 \
    backfill_job.py --start-date 2025-09-01 --end-date 2025-09-23 --batch-days 1 --throttle-seconds 5
"""
import argparse
import time
from datetime import datetime, timedelta
from pyspark.sql import SparkSession
from pyspark.sql.functions import date_format, to_timestamp, col
from cassandra_config import get_cassandra_config, CASSANDRA_KEYSPACE, CASSANDRA_TABLE_TRADES, CASSANDRA_TABLE_TRADES_V2

def create_spark():
    packages = ",".join([
        "com.datastax.spark:spark-cassandra-connector_2.12:3.4.1"
    ])
    builder = SparkSession.builder.appName("CassandraBackfill") \
        .config("spark.jars.packages", packages) \
        .config("spark.cassandra.input.consistency.level", "ONE")
    for k, v in get_cassandra_config().items():
        builder = builder.config(k, v)
    spark = builder.getOrCreate()
    spark.sparkContext.setLogLevel("WARN")
    return spark

def parse_date(s):
    return datetime.strptime(s, "%Y-%m-%d").date()

def main(args):
    spark = create_spark()
    start = parse_date(args.start_date)
    end = parse_date(args.end_date)
    cur = start
    while cur <= end:
        batch_start = cur
        batch_end = cur + timedelta(days=args.batch_days-1)
        if batch_end > end:
            batch_end = end
        print(f"[backfill] processing {batch_start} -> {batch_end}")

        # read by trade_date range (trade_date is a date column in original table)
        df = spark.read \
            .format("org.apache.spark.sql.cassandra") \
            .options(table=CASSANDRA_TABLE_TRADES, keyspace=CASSANDRA_KEYSPACE) \
            .load() \
            .filter((col("trade_date") >= batch_start) & (col("trade_date") <= batch_end))

        if df.rdd.isEmpty():
            print(f"[backfill] no rows for {batch_start}")
        else:
            # compute date_bucket according to granularity env set in stream processor
            gran = args.granularity.lower()
            if gran == "daily":
                df = df.withColumn("date_bucket", date_format(col("event_time"), "yyyyMMdd"))
            elif gran == "hourly":
                df = df.withColumn("date_bucket", date_format(col("event_time"), "yyyyMMddHH"))
            elif gran == "monthly":
                df = df.withColumn("date_bucket", date_format(col("event_time"), "yyyyMM"))
            else:
                df = df.withColumn("date_bucket", date_format(col("event_time"), "yyyyMMdd"))

            # repartition to spread writes
            df = df.repartition(args.partitions, "symbol", "date_bucket")

            df.write \
                .format("org.apache.spark.sql.cassandra") \
                .options(keyspace=CASSANDRA_KEYSPACE, table=CASSANDRA_TABLE_TRADES_V2) \
                .mode("append") \
                .save()
            print(f"[backfill] written approx {df.count()} rows for {batch_start} -> {batch_end}")

        # throttle between batches
        time.sleep(args.throttle_seconds)
        cur = batch_end + timedelta(days=1)

    print("[backfill] finished")
    spark.stop()

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--start-date", required=True, help="YYYY-MM-DD")
    p.add_argument("--end-date", required=True, help="YYYY-MM-DD")
    p.add_argument("--batch-days", type=int, default=1, help="How many days per batch (default 1)")
    p.add_argument("--throttle-seconds", type=int, default=5, help="Sleep seconds between batches")
    p.add_argument("--partitions", type=int, default=8, help="Number of partitions when writing to cassandra")
    p.add_argument("--granularity", type=str, default="daily", help="daily/hourly/monthly")
    args = p.parse_args()
    main(args)
