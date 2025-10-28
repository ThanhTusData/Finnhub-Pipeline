# finnhub_producer/tests/test_validation.py
import pytest
from finnhub_producer.validation import validate_and_normalize
from datetime import datetime, timedelta

def test_valid_record():
    now = datetime.utcnow()
    ts = int(now.timestamp() * 1000)
    rec = {"symbol":"AAPL", "price":"150.5", "volume":"10", "timestamp": ts}
    ok, errs, norm = validate_and_normalize(rec, now_fn=lambda: now)
    assert ok
    assert errs == []
    assert norm["symbol"] == "AAPL"
    assert isinstance(norm["price"], float)
    assert isinstance(norm["volume"], float)

def test_missing_fields():
    rec = {"symbol":"AAPL", "price": 100}
    ok, errs, _ = validate_and_normalize(rec)
    assert not ok
    assert "missing_volume" in errs or "missing_timestamp" in errs

def test_price_negative():
    now = datetime.utcnow()
    ts = int(now.timestamp() * 1000)
    rec = {"symbol":"AAPL", "price": -1, "volume": 5, "timestamp": ts}
    ok, errs, _ = validate_and_normalize(rec, now_fn=lambda: now)
    assert not ok
    assert "price_not_positive" in errs
