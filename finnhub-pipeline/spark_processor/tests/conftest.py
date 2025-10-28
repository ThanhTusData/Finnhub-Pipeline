import pytest
from pyspark.sql import SparkSession

@pytest.fixture(scope="session")
def spark_session():
    """Create Spark session for all tests"""
    spark = SparkSession.builder \
        .appName("TestSuite") \
        .master("local[2]") \
        .config("spark.sql.shuffle.partitions", "2") \
        .getOrCreate()
    
    yield spark
    
    spark.stop()

@pytest.fixture
def sample_trades():
    """Sample trade data for testing"""
    return [
        {
            "symbol": "AAPL",
            "price": 150.0,
            "timestamp": 1635724800000,
            "volume": 100.0,
            "conditions": [],
            "processed_at": 1635724800500
        },
        {
            "symbol": "GOOGL",
            "price": 2800.0,
            "timestamp": 1635724801000,
            "volume": 50.0,
            "conditions": [],
            "processed_at": 1635724801500
        }
    ]