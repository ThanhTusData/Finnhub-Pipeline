-- Create keyspace for trading data
CREATE KEYSPACE IF NOT EXISTS trading
WITH replication = {
    'class': 'SimpleStrategy',
    'replication_factor': 1
};

USE trading;