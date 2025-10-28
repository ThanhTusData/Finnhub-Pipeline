import pytest
from pyspark.sql import SparkSession
from datetime import datetime
from src.transformations import add_partitioning_columns

@pytest.fixture(scope="module")
def spark():
    return SparkSession.builder \
        .appName("TestPartitioning") \
        .master("local[2]") \
        .getOrCreate()

class TestPartitioning:
    def test_partitioning_columns(self, spark):
        """Test that partitioning columns are correctly added"""
        data = [
            ("AAPL", 150.0, 1635724800000, 100.0, datetime(2021, 11, 1, 10, 30, 0))
        ]
        columns = ["symbol", "price", "timestamp", "volume", "trade_time"]
        df = spark.createDataFrame(data, columns)
        
        result = add_partitioning_columns(df)
        
        # Check columns exist
        assert "trade_year" in result.columns
        assert "trade_month" in result.columns
        assert "trade_day" in result.columns
        assert "trade_hour" in result.columns
        
        # Check values
        row = result.first()
        assert row.trade_year == 2021
        assert row.trade_month == 11
        assert row.trade_day == 1
        assert row.trade_hour == 10
    
    def test_partitioning_multiple_dates(self, spark):
        """Test partitioning with multiple dates"""
        data = [
            ("AAPL", 150.0, 1635724800000, 100.0, datetime(2021, 11, 1, 10, 0, 0)),
            ("AAPL", 151.0, 1635811200000, 150.0, datetime(2021, 11, 2, 11, 0, 0)),
            ("GOOGL", 2800.0, 1635897600000, 50.0, datetime(2021, 11, 3, 12, 0, 0)),
        ]
        columns = ["symbol", "price", "timestamp", "volume", "trade_time"]
        df = spark.createDataFrame(data, columns)
        
        result = add_partitioning_columns(df)
        
        # Should have 3 different partition combinations
        partitions = result.select("trade_year", "trade_month", "trade_day").distinct().count()
        assert partitions == 3