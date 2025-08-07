"""
Tests for the base scraper interface.
"""

import pytest
from datetime import datetime
from typing import Dict, Any, Optional

from scrapers.base import BaseScraper
from models.core import ScraperResult


class TestScraper(BaseScraper):
    """Test implementation of BaseScraper for testing."""
    
    def __init__(self, data_source: str = "test", metric_name: str = "test_metric"):
        super().__init__(data_source, metric_name)
        self.mock_data = {"value": 100, "confidence": 1.0}
        self.should_trigger_alert = False
    
    def fetch_data(self) -> Dict[str, Any]:
        return self.mock_data
    
    def should_alert(self, current_data: Dict[str, Any], historical_data: Optional[Dict[str, Any]]) -> bool:
        return self.should_trigger_alert
    
    def generate_alert_message(self, current_data: Dict[str, Any], historical_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        return {
            "message": "Test alert",
            "current_value": current_data.get("value"),
            "data_source": self.data_source
        }


def test_scraper_initialization():
    """Test that scraper initializes correctly."""
    scraper = TestScraper("test_source", "test_metric")
    assert scraper.data_source == "test_source"
    assert scraper.metric_name == "test_metric"


def test_successful_execution():
    """Test successful scraper execution."""
    scraper = TestScraper()
    result = scraper.execute()
    
    assert isinstance(result, ScraperResult)
    assert result.success is True
    assert result.data == {"value": 100, "confidence": 1.0}
    assert result.error is None
    assert result.execution_time > 0


def test_failed_execution():
    """Test scraper execution with error."""
    scraper = TestScraper()
    # Make fetch_data raise an exception
    scraper.fetch_data = lambda: (_ for _ in ()).throw(ValueError("Test error"))
    
    result = scraper.execute()
    
    assert isinstance(result, ScraperResult)
    assert result.success is False
    assert result.data is None
    assert "Test error" in result.error
    assert result.execution_time > 0


def test_data_validation():
    """Test data validation."""
    scraper = TestScraper()
    
    # Test valid data
    valid_data = {"value": 100}
    validated = scraper.validate_data(valid_data)
    assert validated == valid_data
    
    # Test empty data
    with pytest.raises(ValueError, match="No data received from source"):
        scraper.validate_data({})


if __name__ == "__main__":
    pytest.main([__file__])