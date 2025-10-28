import pytest
from unittest.mock import Mock, MagicMock, patch
from src.kafka_writer import KafkaWriter
from src.config import KafkaConfig

class TestKafkaWriter:
    @pytest.fixture
    def kafka_config(self):
        return KafkaConfig(
            bootstrap_servers="localhost:9092",
            topic="test-topic",
            client_id="test-client"
        )
    
    @pytest.fixture
    def mock_producer(self):
        with patch('src.kafka_writer.KafkaProducer') as mock:
            yield mock
    
    def test_initialization(self, kafka_config, mock_producer):
        """Test KafkaWriter initialization"""
        writer = KafkaWriter(kafka_config)
        
        mock_producer.assert_called_once()
        assert writer.config == kafka_config
    
    def test_write_success(self, kafka_config, mock_producer):
        """Test successful write to Kafka"""
        mock_producer_instance = Mock()
        mock_producer.return_value = mock_producer_instance
        mock_future = Mock()
        mock_producer_instance.send.return_value = mock_future
        
        writer = KafkaWriter(kafka_config)
        
        trade = {
            "symbol": "AAPL",
            "price": 150.0,
            "timestamp": 1635724800000,
            "volume": 100.0
        }
        
        result = writer.write(trade)
        
        assert result is True
        mock_producer_instance.send.assert_called_once()
    
    def test_write_batch(self, kafka_config, mock_producer):
        """Test batch write to Kafka"""
        mock_producer_instance = Mock()
        mock_producer.return_value = mock_producer_instance
        mock_future = Mock()
        mock_producer_instance.send.return_value = mock_future
        
        writer = KafkaWriter(kafka_config)
        
        trades = [
            {"symbol": "AAPL", "price": 150.0, "timestamp": 1635724800000, "volume": 100.0},
            {"symbol": "GOOGL", "price": 2800.0, "timestamp": 1635724800000, "volume": 50.0},
        ]
        
        result = writer.write_batch(trades)
        
        assert result == 2
        assert mock_producer_instance.send.call_count == 2