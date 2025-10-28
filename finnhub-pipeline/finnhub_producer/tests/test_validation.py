import pytest
from src.validator import TradeValidator

class TestTradeValidator:
    def test_valid_trade(self):
        """Test validation of a valid trade"""
        trade = {
            "s": "AAPL",
            "p": 150.25,
            "t": 1635724800000,
            "v": 100.0
        }
        
        result = TradeValidator.validate_trade(trade)
        assert result is not None
        assert result["symbol"] == "AAPL"
        assert result["price"] == 150.25
        assert result["volume"] == 100.0
    
    def test_missing_required_field(self):
        """Test trade with missing required field"""
        trade = {
            "s": "AAPL",
            "p": 150.25,
            "v": 100.0
            # Missing 't' (timestamp)
        }
        
        result = TradeValidator.validate_trade(trade)
        assert result is None
    
    def test_invalid_price(self):
        """Test trade with invalid price"""
        trade = {
            "s": "AAPL",
            "p": -150.25,  # Negative price
            "t": 1635724800000,
            "v": 100.0
        }
        
        result = TradeValidator.validate_trade(trade)
        assert result is None
    
    def test_invalid_volume(self):
        """Test trade with invalid volume"""
        trade = {
            "s": "AAPL",
            "p": 150.25,
            "t": 1635724800000,
            "v": 0.0  # Zero volume
        }
        
        result = TradeValidator.validate_trade(trade)
        assert result is None
    
    def test_trade_enrichment(self):
        """Test that trades are enriched with processed_at timestamp"""
        trade = {
            "s": "AAPL",
            "p": 150.25,
            "t": 1635724800000,
            "v": 100.0,
            "c": ["12", "37"]
        }
        
        result = TradeValidator.validate_trade(trade)
        assert result is not None
        assert "processed_at" in result
        assert result["conditions"] == ["12", "37"]
    
    def test_batch_validation(self):
        """Test batch validation"""
        trades = [
            {"s": "AAPL", "p": 150.25, "t": 1635724800000, "v": 100.0},
            {"s": "GOOGL", "p": -10.0, "t": 1635724800000, "v": 50.0},  # Invalid
            {"s": "MSFT", "p": 300.0, "t": 1635724800000, "v": 75.0},
        ]
        
        result = TradeValidator.validate_batch(trades)
        assert len(result) == 2  # Only 2 valid trades
        assert result[0]["symbol"] == "AAPL"
        assert result[1]["symbol"] == "MSFT"