# finnhub_producer/validation.py
"""
Validation + normalization for incoming tick records.

Functions:
- validate_and_normalize(record) -> (is_valid: bool, errors: list[str], normalized: dict)
"""
import re
from datetime import datetime, timedelta
from typing import Tuple, List, Dict, Any

SYMBOL_RE = re.compile(r'^[A-Z0-9\.\-:/]{1,32}$')  # allow exchange prefix like BINANCE:BTCUSDT

REQUIRED_FIELDS = ("symbol", "price", "volume", "timestamp")  # timestamp in ms

def _to_int(value) -> int:
    try:
        return int(value)
    except Exception:
        raise

def validate_and_normalize(rec: Dict[str, Any], now_fn=lambda: datetime.utcnow()) -> Tuple[bool, List[str], Dict[str, Any]]:
    """
    Validate record and return (is_valid, errors, normalized_record)
    Normalization:
      - ensure numeric fields converted to float/int
      - ensure timestamp as int (epoch ms)
      - keep original fields in case of DLQ
    """
    errors = []
    normalized = dict(rec) if isinstance(rec, dict) else {}

    # required fields
    for f in REQUIRED_FIELDS:
        if f not in rec or rec[f] is None or (isinstance(rec[f], str) and rec[f].strip() == ""):
            errors.append(f"missing_{f}")

    # stop early if missing required fields
    if errors:
        return False, errors, normalized

    # symbol
    sym = rec.get("symbol")
    if not isinstance(sym, str) or not SYMBOL_RE.match(sym):
        errors.append("symbol_invalid")
    else:
        normalized["symbol"] = sym.strip().upper()

    # price
    try:
        price = float(rec.get("price"))
        if not (price > 0):
            errors.append("price_not_positive")
        normalized["price"] = price
    except Exception:
        errors.append("price_not_number_or_invalid")

    # volume
    try:
        # volume might be float (amount) or int (trades count)
        vol_raw = rec.get("volume")
        volume = float(vol_raw)
        if volume < 0:
            errors.append("volume_negative")
        normalized["volume"] = volume
    except Exception:
        errors.append("volume_not_number_or_invalid")

    # timestamp: accept ms int or ISO string
    ts = rec.get("timestamp")
    parsed_ts = None
    try:
        if isinstance(ts, (int, float)):
            parsed_ts = int(ts)
        elif isinstance(ts, str):
            # try integer string
            if ts.isdigit():
                parsed_ts = int(ts)
            else:
                # try ISO format
                dt = datetime.fromisoformat(ts)
                parsed_ts = int(dt.timestamp() * 1000)
        else:
            errors.append("timestamp_invalid_type")
    except Exception:
        errors.append("timestamp_parse_failed")

    if parsed_ts is not None:
        now = now_fn()
        lower = int((now - timedelta(days=1)).timestamp() * 1000)
        upper = int((now + timedelta(minutes=5)).timestamp() * 1000)
        if parsed_ts < lower or parsed_ts > upper:
            errors.append("timestamp_out_of_range")
        normalized["timestamp"] = parsed_ts

    # optional: event_id presence (if not present, producer/spark will generate)
    if "event_id" in rec and (rec.get("event_id") is None or str(rec.get("event_id")).strip() == ""):
        errors.append("event_id_empty")

    is_valid = len(errors) == 0
    return is_valid, errors, normalized
