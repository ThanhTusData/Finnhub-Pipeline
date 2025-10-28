import pytest
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, LongType
from src.transformations import (
    get_trade_schema,
    parse_kafka_messages,
    add_partitioning_columns,
    calculate_aggregates
)
from datetime import datetime

@pytest.fixture(scope="session")
def spark():
    """Create Spark session for testing"""
    return SparkSession.builder \
        .appName("TestTransformations") \
        .master("local[2]") \
        .getOrCreate()

class TestTransformations:
    def test_trade_schema(self):
        """Test trade schema definition"""
        schema = get_trade_schema()
        
        assert isinstance(schema, StructType)
        field_names = [field.name for field in schema.fields]
        assert "symbol" in field_names
        assert "price" in field_names
        assert "timestamp" in field_names
        assert "volume" in field_names
    
    def test_add_partitioning_columns(self, spark):
        """Test adding date partitioning columns"""
        # Create test data
        data = [
            ("AAPL", 150.0, 1635724800000, 100.0, datetime(2021, 11, 1, 10, 0, 0))
        ]
        schema = ["symbol", "price", "timestamp", "volume", "trade_time"]
        df = spark.createDataFrame(data, schema)
        
        # Add partitioning columns
        result = add_partitioning_columns(df)
        
        # Verify columns were added
        assert "trade_year" in result.columns
        assert "trade_month" in result.columns
        assert "trade_day" in result.columns
        assert "trade_hour" in result.columns
        
        # Verify values
        row = result.collect()[0]
        assert row.trade_year == 2021
        assert row.trade_month == 11
        assert row.trade_day == 1
        assert row.trade_hour == 10