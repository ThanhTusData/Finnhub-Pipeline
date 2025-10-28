from pyspark.sql import SparkSession

class CassandraConfig:
    @staticmethod
    def get_spark_session(app_name: str = "FinnhubProcessor") -> SparkSession:
        """Create Spark session with Cassandra connector"""
        return SparkSession.builder \
            .appName(app_name) \
            .config("spark.cassandra.connection.host", "cassandra") \
            .config("spark.cassandra.connection.port", "9042") \
            .config("spark.cassandra.auth.username", "cassandra") \
            .config("spark.cassandra.auth.password", "cassandra") \
            .config("spark.sql.streaming.checkpointLocation", "/tmp/checkpoint") \
            .config("spark.sql.shuffle.partitions", "10") \
            .config("spark.streaming.kafka.maxRatePerPartition", "1000") \
            .config("spark.sql.streaming.statefulOperator.checkCorrectness.enabled", "false") \
            .getOrCreate()