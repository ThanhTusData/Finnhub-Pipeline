import pytest
from unittest.mock import Mock, patch, MagicMock
from src.producer import FinnhubProducer
from src.config import Config
import json

class TestFinnhubProducer:
    @pytest.fixture
    def mock_config(self):
        config = Mock(spec=Config)
        config.finnhub.api_key = "test_key"
        config.finnhub.websocket_url = "wss://test.finnhub.io"
        config.finnhub.symbols = ["AAPL", "GOOGL"]
        config.kafka.bootstrap_servers = "localhost:9092"
        config.kafka.topic = "test-topic"
        config.metrics.enabled = False
        return config
    
    @patch('src.producer.KafkaWriter')
    def test_initialization(self, mock_kafka_writer, mock_config):
        """Test producer initialization"""
        producer = FinnhubProducer(mock_config)
        
        assert producer.config == mock_config
        assert producer.validator is not None
        assert producer.kafka_writer is not None
        assert producer.running is False
    
    @patch('src.producer.KafkaWriter')
    def test_on_message_valid_trades(self, mock_kafka_writer, mock_config):
        """Test handling valid trade messages"""
        producer = FinnhubProducer(mock_config)
        
        message = json.dumps({
            "type": "trade",
            "data": [
                {"s": "AAPL", "p": 150.0, "t": 1635724800000, "v": 100.0}
            ]
        })
        
        ws_mock = Mock()
        producer.on_message(ws_mock, message)
        
        # Verify kafka writer was called
        assert producer.kafka_writer.write_batch.called
    
    @patch('src.producer.KafkaWriter')
    def test_on_error(self, mock_kafka_writer, mock_config):
        """Test error handling"""
        producer = FinnhubProducer(mock_config)
        
        ws_mock = Mock()
        producer.on_error(ws_mock, Exception("Test error"))
        
        # Should not raise exception
        assert True
    
    @patch('src.producer.KafkaWriter')
    def test_on_open_subscribes_symbols(self, mock_kafka_writer, mock_config):
        """Test that on_open subscribes to all symbols"""
        producer = FinnhubProducer(mock_config)
        
        ws_mock = Mock()
        producer.on_open(ws_mock)
        
        # Should send subscribe message for each symbol
        assert ws_mock.send.call_count == len(mock_config.finnhub.symbols)