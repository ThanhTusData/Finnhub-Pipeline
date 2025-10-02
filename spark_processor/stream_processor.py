# spark_processor/stream_processor.py  (updated)
import os
import logging
import uuid
from datetime import datetime
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
from cassandra_config import get_cassandra_config, CASSANDRA_KEYSPACE, CASSANDRA_TABLE_TRADES_V2, CASSANDRA_TABLE_TRADES

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configurable via env
KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "market")
CHECKPOINT_DIR = os.getenv("CHECKPOINT_LOCATION", "/tmp/checkpoint")
MAX_OFFSETS = int(os.getenv("MAX_OFFSETS_PER_TRIGGER", "10000"))
WATERMARK_DELAY = os.getenv("WATERMARK_DELAY", "5 minutes")
TRIGGER_PROCESSING = os.getenv("TRIGGER_PROCESSING", "5 seconds")  # processingTime
USE_AVRO = os.getenv("USE_AVRO", "false").lower() == "true"

# NEW: bucket granularity
BUCKET_GRANULARITY = os.getenv("CASSANDRA_BUCKET_GRANULARITY", "daily").lower()  # daily/hourly/monthly
DEFAULT_PARTITIONS = int(os.getenv("CASSANDRA_WRITE_PARTITIONS", "8"))
CASSANDRA_WRITE_TABLE = os.getenv("CASSANDRA_TABLE_TRADES_V2", "trades_v2")

# Helper for tests/backfill
def compute_date_bucket_str(ts, granularity="daily"):
    """
    ts: python datetime OR timestamp in ms (int)
    returns string bucket:
      - daily -> YYYYMMDD
      - hourly -> YYYYMMDDHH
      - monthly -> YYYYMM
    """
    if isinstance(ts, (int, float)):
        dt = datetime.utcfromtimestamp(ts / 1000.0)
    elif isinstance(ts, datetime):
        dt = ts
    else:
        raise ValueError("ts must be int(ms) or datetime")

    if granularity == "daily":
        return dt.strftime("%Y%m%d")
    if granularity == "hourly":
        return dt.strftime("%Y%m%d%H")
    if granularity == "monthly":
        return dt.strftime("%Y%m")
    raise ValueError("unsupported granularity")

class StreamProcessor:
    def __init__(self):
        self.spark = None
        self.setup_spark_session()

    def setup_spark_session(self):
        cass_cfg = get_cassandra_config()
        # Packages: kafka + spark-cassandra-connector (version aligned with pyspark)
        packages = ",".join([
            "org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.1",
            "com.datastax.spark:spark-cassandra-connector_2.12:3.4.1"
        ])
        builder = SparkSession.builder.appName("FinnhubStreamProcessor") \
            .config("spark.jars.packages", packages) \
            .config("spark.sql.streaming.checkpointLocation", CHECKPOINT_DIR)

        for k, v in cass_cfg.items():
            builder = builder.config(k, v)

        self.spark = builder.getOrCreate()
        self.spark.sparkContext.setLogLevel("WARN")
        logger.info("Spark session initialized")

    def define_schema(self):
        return StructType([
            StructField("event_id", StringType(), True),  # unique id for dedupe
            StructField("symbol", StringType(), True),
            StructField("price", DoubleType(), True),
            StructField("volume", DoubleType(), True),
            StructField("timestamp", LongType(), True),  # epoch ms
            StructField("conditions", ArrayType(StringType()), True),
            StructField("processed_at", LongType(), True)
        ])

    def _parse_input(self, raw_df, schema):
        """
        raw_df: DataFrame from Kafka with columns key, value, timestamp
        If messages are Avro via Schema Registry you should deserialize accordingly.
        For now we support JSON payloads (string) and will generate event_id if missing.
        """
        parsed = raw_df.select(
            col("key").cast("string").alias("key"),
            from_json(col("value").cast("string"), schema).alias("data"),
            col("timestamp").alias("kafka_timestamp")
        ).select("data.*", "kafka_timestamp")

        # if event_id missing, generate one (helps idempotency on producer without event ids)
        parsed = parsed.withColumn("event_id", when(col("event_id").isNull(), expr("uuid()")).otherwise(col("event_id")))

        # convert epoch ms -> timestamp
        parsed = parsed.withColumn("event_time", to_timestamp((col("timestamp")/1000).cast("double")))
        parsed = parsed.withColumn("spark_ingest_time", current_timestamp())

        # compute date_bucket according to granularity
        if BUCKET_GRANULARITY == "daily":
            parsed = parsed.withColumn("date_bucket", date_format(col("event_time"), "yyyyMMdd"))
        elif BUCKET_GRANULARITY == "hourly":
            parsed = parsed.withColumn("date_bucket", date_format(col("event_time"), "yyyyMMddHH"))
        elif BUCKET_GRANULARITY == "monthly":
            parsed = parsed.withColumn("date_bucket", date_format(col("event_time"), "yyyyMM"))
        else:
            parsed = parsed.withColumn("date_bucket", date_format(col("event_time"), "yyyyMMdd"))

        return parsed

    def write_batch_to_cassandra(self, batch_df, batch_id):
        """
        foreachBatch function: writes micro-batch to Cassandra using connector.
        Cassandra upsert semantics will make writes idempotent if primary key is stable.
        """
        logger.info(f"Writing batch {batch_id} to Cassandra, rows: {batch_df.count()}")
        if batch_df.rdd.isEmpty():
            logger.info("Empty batch, skipping write.")
            return

        try:
            # repartition to avoid a lot of small writes; include date_bucket to align with PK
            out_df = batch_df.repartition(DEFAULT_PARTITIONS, "symbol", "date_bucket")
            out_df.write \
                .format("org.apache.spark.sql.cassandra") \
                .options(keyspace=CASSANDRA_KEYSPACE, table=CASSANDRA_WRITE_TABLE) \
                .mode("append") \
                .save()
            logger.info(f"Batch {batch_id} written to Cassandra (approx rows: {out_df.count()})")
        except Exception as e:
            logger.error(f"Failed to write batch {batch_id} to Cassandra: {e}")
            raise

    def process_stream(self):
        schema = self.define_schema()

        raw = self.spark \
            .readStream \
            .format("kafka") \
            .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP) \
            .option("subscribe", KAFKA_TOPIC) \
            .option("startingOffsets", os.getenv("KAFKA_STARTING_OFFSETS", "latest")) \
            .option("maxOffsetsPerTrigger", str(MAX_OFFSETS)) \
            .load()

        parsed = self._parse_input(raw, schema)

        # derive columns
        enriched = parsed.withColumn(
            "price_change_indicator",
            when(col("volume") > 1000, "high_volume").otherwise("normal_volume")
        ).withColumn(
            "trade_date",
            to_date(col("event_time"))
        ).withColumn(
            "trade_hour",
            hour(col("event_time"))
        )

        # apply watermark and dedupe by event_id (dropDuplicates requires watermark on event_time)
        deduped = enriched.withWatermark("event_time", WATERMARK_DELAY).dropDuplicates(["event_id"])

        # write raw trades with foreachBatch (idempotent because of Cassandra PK)
        trades_write_query = deduped.writeStream \
            .outputMode("append") \
            .foreachBatch(self.write_batch_to_cassandra) \
            .option("checkpointLocation", os.path.join(CHECKPOINT_DIR, "trades")) \
            .trigger(processingTime=TRIGGER_PROCESSING) \
            .start()

        # aggregated windowed query (1m windows as example)
        windowed = parsed \
            .withWatermark("event_time", WATERMARK_DELAY) \
            .groupBy(window(col("event_time"), "1 minute"), col("symbol")) \
            .agg(
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

        # write aggregates also via foreachBatch
        def write_aggregates(batch_df, batch_id):
            if batch_df.rdd.isEmpty(): return
            try:
                batch_df.write \
                    .format("org.apache.spark.sql.cassandra") \
                    .options(keyspace=CASSANDRA_KEYSPACE, table="trade_aggregates") \
                    .mode("append") \
                    .save()
                logger.info(f"Aggregates batch {batch_id} written")
            except Exception as e:
                logger.error(f"Failed to write aggregates batch {batch_id}: {e}")
                raise

        agg_query = windowed.writeStream \
            .outputMode("update") \
            .foreachBatch(write_aggregates) \
            .option("checkpointLocation", os.path.join(CHECKPOINT_DIR, "aggregates")) \
            .trigger(processingTime=TRIGGER_PROCESSING) \
            .start()

        return trades_write_query, agg_query

    def start_processing(self):
        logger.info("Starting stream processing...")
        try:
            q1, q2 = self.process_stream()
            q1.awaitTermination()
            q2.awaitTermination()
        except KeyboardInterrupt:
            logger.info("Stopping due to keyboard interrupt")
        except Exception as e:
            logger.error(f"Stream processing failed: {e}")
            raise


if __name__ == "__main__":
    StreamProcessor().start_processing()
