import os

CASSANDRA_HOST = os.getenv('CASSANDRA_HOST', 'localhost')
CASSANDRA_PORT = int(os.getenv('CASSANDRA_PORT', '9042'))
CASSANDRA_KEYSPACE = os.getenv('CASSANDRA_KEYSPACE', 'market_data')

def get_cassandra_config():
    return {
        'spark.cassandra.connection.host': CASSANDRA_HOST,
        'spark.cassandra.connection.port': str(CASSANDRA_PORT),
        'spark.sql.adaptive.enabled': 'false',
        'spark.sql.adaptive.coalescePartitions.enabled': 'false'
    }