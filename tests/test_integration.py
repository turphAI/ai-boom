"""
Integration tests for the state store and scraper interaction.
"""

import tempfile
import shutil
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from scrapers.base import BaseScraper
from services.state_store import FileStateStore


class TestIntegrationScraper(BaseScraper):
    """Test scraper for integration testing."""
    
    def __init__(self, data_source: str = "integration_test", metric_name: str = "test_metric"):
        super().__init__(data_source, metric_name)
        self.mock_data = {
            "value": 150, 
            "confidence": 0.9, 
            "timestamp": datetime.now(timezone.utc),
            "metadata": {"test": True}
        }
        self.should_trigger_alert = False
    
    def fetch_data(self) -> Dict[str, Any]:
        return self.mock_data
    
    def should_alert(self, current_data: Dict[str, Any], historical_data: Optional[Dict[str, Any]]) -> bool:
        return self.should_trigger_alert
    
    def generate_alert_message(self, current_data: Dict[str, Any], historical_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        return {
            "message": "Integration test alert",
            "current_value": current_data.get("value"),
            "data_source": self.data_source
        }


def test_scraper_state_store_integration():
    """Test that scraper and state store work together correctly."""
    # Create temporary directory for test data
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Create scraper with file-based state store
        scraper = TestIntegrationScraper()
        scraper.state_store = FileStateStore(temp_dir)
        
        # Execute scraper
        result = scraper.execute()
        
        # Verify execution was successful
        assert result.success is True
        assert result.data is not None
        assert result.error is None
        
        # Verify data was saved to state store
        latest_value = scraper.state_store.get_latest_value("integration_test", "test_metric")
        assert latest_value is not None
        assert latest_value['data']['value'] == 150
        # Confidence may be adjusted during validation, so just check it's reasonable
        assert 0.0 <= latest_value['data']['confidence'] <= 1.0
        
        # Execute scraper again with different data
        scraper.mock_data = {
            "value": 200, 
            "confidence": 0.95,
            "timestamp": datetime.now(timezone.utc),
            "metadata": {"test": True}
        }
        result2 = scraper.execute()
        
        # Verify second execution
        assert result2.success is True
        
        # Verify historical data retrieval
        historical_data = scraper.state_store.get_historical_data("integration_test", "test_metric", days=1)
        assert len(historical_data) == 2
        
        # Verify data is sorted by timestamp (newest first)
        assert historical_data[0]['data']['value'] == 200  # Most recent
        assert historical_data[1]['data']['value'] == 150  # Older
        
    finally:
        # Clean up
        shutil.rmtree(temp_dir)


def test_multiple_metrics_storage():
    """Test storing multiple metrics for the same data source."""
    temp_dir = tempfile.mkdtemp()
    
    try:
        store = FileStateStore(temp_dir)
        
        # Save data for different metrics
        store.save_data("test_source", "metric1", {"value": 100})
        store.save_data("test_source", "metric2", {"value": 200})
        store.save_data("other_source", "metric1", {"value": 300})
        
        # Verify each metric can be retrieved independently
        metric1_data = store.get_latest_value("test_source", "metric1")
        metric2_data = store.get_latest_value("test_source", "metric2")
        other_data = store.get_latest_value("other_source", "metric1")
        
        assert metric1_data['data']['value'] == 100
        assert metric2_data['data']['value'] == 200
        assert other_data['data']['value'] == 300
        
    finally:
        shutil.rmtree(temp_dir)


if __name__ == "__main__":
    import pytest
    pytest.main([__file__])