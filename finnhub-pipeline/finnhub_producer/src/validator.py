from typing import Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class TradeValidator:
    REQUIRED_FIELDS = {"s", "p", "t", "v"}
    
    @staticmethod
    def validate_trade(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Validate and enrich trade data"""
        try:
            # Check required fields
            if not all(field in data for field in TradeValidator.REQUIRED_FIELDS):
                logger.warning(f"Missing required fields in trade: {data}")
                return None
            
            # Validate types
            symbol = str(data["s"])
            price = float(data["p"])
            timestamp = int(data["t"])
            volume = float(data["v"])
            
            # Validate ranges
            if price <= 0:
                logger.warning(f"Invalid price {price} for {symbol}")
                return None
                
            if volume <= 0:
                logger.warning(f"Invalid volume {volume} for {symbol}")
                return None
            
            # Enrich data
            enriched = {
                "symbol": symbol,
                "price": price,
                "timestamp": timestamp,
                "volume": volume,
                "conditions": data.get("c", []),
                "processed_at": int(datetime.now().timestamp() * 1000)
            }
            
            return enriched
            
        except (ValueError, TypeError) as e:
            logger.error(f"Validation error for trade {data}: {e}")
            return None
    
    @staticmethod
    def validate_batch(trades: list) -> list:
        """Validate a batch of trades"""
        valid_trades = []
        for trade in trades:
            validated = TradeValidator.validate_trade(trade)
            if validated:
                valid_trades.append(validated)
        return valid_trades