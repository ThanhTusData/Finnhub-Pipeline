# spark_processor/cassandra_config.py  (updated)
import os

CASSANDRA_HOST = os.getenv('CASSANDRA_HOST', 'cassandra')
CASSANDRA_PORT = os.getenv('CASSANDRA_PORT', '9042')
CASSANDRA_KEYSPACE = os.getenv('CASSANDRA_KEYSPACE', 'market_data')
CASSANDRA_TABLE_TRADES = os.getenv('CASSANDRA_TABLE_TRADES', 'trades')       # original table
CASSANDRA_TABLE_TRADES_V2 = os.getenv('CASSANDRA_TABLE_TRADES_V2', 'trades_v2')  # new table

def get_cassandra_config():
    return {
        'spark.cassandra.connection.host': CASSANDRA_HOST,
        'spark.cassandra.connection.port': CASSANDRA_PORT,
        # tuning
        'spark.cassandra.output.concurrent.writes': os.getenv('CASSANDRA_CONCURRENT_WRITES', '8'),
        'spark.cassandra.output.batch.size.bytes': os.getenv('CASSANDRA_BATCH_SIZE_BYTES', '1024'),
        'spark.cassandra.output.throughput_mb_per_sec': os.getenv('CASSANDRA_THROUGHPUT_MB', '16'),
        # other helpful spark configs
        'spark.sql.shuffle.partitions': os.getenv('SPARK_SHUFFLE_PARTITIONS', '200'),
        'spark.sql.adaptive.enabled': os.getenv('SPARK_ADAPTIVE_ENABLED', 'false'),
    }
