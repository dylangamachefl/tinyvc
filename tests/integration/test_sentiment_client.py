"""Integration test for sentiment client."""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch

from src.ingestion.sentiment_client import SentimentClient


class TestSentimentClientIntegration:
    """Integration tests for sentiment scraping."""
    
    @pytest.fixture
    def sentiment_fixture(self, fixtures_dir):
        """Load sentiment API response fixture."""
        fixture_path = fixtures_dir / "fear_greed_response.json"
        with open(fixture_path) as f:
            return json.load(f)
    
    @patch('src.ingestion.sentiment_client.requests.get')
    def test_fetch_fear_greed_success(self, mock_get, sentiment_fixture):
        """Test successful Fear & Greed fetch."""
        # Mock the API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = sentiment_fixture
        mock_get.return_value = mock_response
        
        # Fetch sentiment
        client = SentimentClient()
        sentiment = client.fetch_fear_greed()
        
        # Verify
        assert sentiment.score == 42
        assert sentiment.label == "Fear"
        assert sentiment.one_week_ago == 38
        assert sentiment.is_fearful == True
    
    @patch('src.ingestion.sentiment_client.requests.get')
    def test_fetch_handles_network_error(self, mock_get):
        """Test handling of network failures."""
        mock_get.side_effect = Exception("Network error")
        
        client = SentimentClient()
        
        with pytest.raises(Exception):
            client.fetch_fear_greed()
