# spark_processor/tests/test_partitioning.py
import pytest
from datetime import datetime
from spark_processor.stream_processor import compute_date_bucket_str

def test_daily_bucket_from_datetime():
    dt = datetime(2025, 9, 24, 13, 45, 0)
    assert compute_date_bucket_str(dt, "daily") == "20250924"

def test_hourly_bucket_from_ms():
    dt_ms = int(datetime(2025, 9, 24, 13, 0).timestamp() * 1000)
    assert compute_date_bucket_str(dt_ms, "hourly") == "2025092413"

def test_monthly_bucket():
    dt = datetime(2025, 1, 5)
    assert compute_date_bucket_str(dt, "monthly") == "202501"

def test_invalid_ts():
    with pytest.raises(ValueError):
        compute_date_bucket_str("bad", "daily")
