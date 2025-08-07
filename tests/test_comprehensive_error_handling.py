"""
Comprehensive integration tests for error handling and data validation.

This test suite demonstrates all error handling features working together:
- Exponential backoff retry logic
- Data integrity validation with checksums
- Anomaly detection
- Graceful degradation with cached data
- Cross-validation between multiple sources
"""

import pytest
import time
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, List

from scrapers.base import BaseScraper
from scrapers.bond_issuance_scraper import BondIssuanceScraper
from scrapers.bdc_discount_scraper import BDCDiscountScraper
from utils.error_handling import (
    DataValidator, CachedDataManager, CrossValidator,
    retry_with_backoff, graceful_degradation, RetryConfig
)
from models.core import ScraperResult


class ComprehensiveTestScraper(BaseScraper):
    """Test scraper that demonstrates all error handling features."""
    
    def __init__(self):
        super().__init__('comprehensive_test', 'test_metric')
        self.api_call_count = 0
        self.failure_scenarios = []
        self.secondary_data_enabled = True
    
    def fetch_data(self) -> Dict[str, Any]:
        """Fetch data with configurable failure scenarios."""
        self.api_call_count += 1
        
        # Check if we should simulate a failure
        for scenario in self.failure_scenarios:
            if scenario['call_number'] == self.api_call_count:
                if scenario['exception'] == 'connection':
                    raise ConnectionError(scenario['message'])
                elif scenario['exception'] == 'timeout':
                    raise TimeoutError(scenario['message'])
                elif scenario['exception'] == 'value':
                    raise ValueError(scenario['message'])
        
        # Return test data
        return {
            'value': 1000000 + (self.api_call_count * 10000),  # Slightly different each time
            'timestamp': datetime.utcnow().isoformat(),
            'confidence': 0.95,
            'metadata': {
                'source': 'test_api',
                'call_number': self.api_call_count,
                'data_points': 100
            }
        }
    
    def should_alert(self, current_data: Dict[str, Any], historical_data: Dict[str, Any]) -> bool:
        """Simple alert logic for testing."""
        if not historical_data:
            return False
        
        current_value = current_data.get('value', 0)
        historical_value = historical_data.get('value', 0)
        
        # Alert if change is more than 20%
        if historical_value > 0:
            change_ratio = abs(current_value - historical_value) / historical_value
            return change_ratio > 0.2
        
        return False
    
    def generate_alert_message(self, current_data: Dict[str, Any], historical_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate test alert message."""
        return {
            'alert_type': 'test_alert',
            'message': 'Test alert triggered',
            'current_value': current_data.get('value'),
            'historical_value': historical_data.get('value') if historical_data else None
        }
    
    def get_secondary_data_sources(self) -> List[Dict[str, Any]]:
        """Get secondary data sources for cross-validation."""
        if not self.secondary_data_enabled:
            return []
        
        # Simulate secondary data sources with slight variations
        base_value = 1000000 + (self.api_call_count * 10000)
        
        return [
            {
                'value': base_value + 5000,  # 0.5% difference
                'source': 'secondary_api_1',
                'confidence': 0.9,
                'timestamp': datetime.utcnow().isoformat()
            },
            {
                'value': base_value - 3000,  # 0.3% difference
                'source': 'secondary_api_2',
                'confidence': 0.85,
                'timestamp': datetime.utcnow().isoformat()
            }
        ]
    
    def get_data_schema(self) -> Dict[str, Any]:
        """Get enhanced data schema for validation."""
        return {
            'required': ['value', 'timestamp', 'confidence', 'metadata'],
            'types': {
                'value': (int, float),
                'timestamp': str,
                'confidence': (int, float),
                'metadata': dict
            },
            'ranges': {
                'value': (0, 10000000),
                'confidence': (0.0, 1.0)
            }
        }


class TestComprehensiveErrorHandling:
    """Comprehensive error handling integration tests."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.scraper = ComprehensiveTestScraper()
    
    @patch('scrapers.base.create_state_store')
    def test_successful_execution_with_all_features(self, mock_state_store):
        """Test successful execution with all error handling features enabled."""
        # Mock state store with historical data
        mock_store = Mock()
        mock_store.get_historical_data.return_value = [
            {'value': 950000, 'timestamp': '2024-01-01T00:00:00Z'},
            {'value': 980000, 'timestamp': '2024-01-02T00:00:00Z'},
            {'value': 1020000, 'timestamp': '2024-01-03T00:00:00Z'}
        ]
        mock_store.get_latest_value.return_value = None
        mock_state_store.return_value = mock_store
        
        # Execute scraper
        result = self.scraper.execute()
        
        # Verify successful execution
        assert result.success
        assert result.data is not None
        assert result.error is None
        
        # Verify data validation features
        assert 'confidence' in result.data
        assert 'validation_checksum' in result.data
        assert 'anomaly_score' in result.data
        
        # Verify confidence is high due to cross-validation
        assert result.data['confidence'] > 0.8
        
        # Verify data was saved and cached
        mock_store.save_data.assert_called_once()
        
        # Verify only one API call was made (no retries needed)
        assert self.scraper.api_call_count == 1
    
    @patch('scrapers.base.create_state_store')
    def test_retry_logic_with_eventual_success(self, mock_state_store):
        """Test retry logic with eventual success after failures."""
        # Mock state store
        mock_store = Mock()
        mock_store.get_historical_data.return_value = []
        mock_store.get_latest_value.return_value = None
        mock_state_store.return_value = mock_store
        
        # Configure scraper to fail first 2 attempts
        self.scraper.failure_scenarios = [
            {'call_number': 1, 'exception': 'connection', 'message': 'First failure'},
            {'call_number': 2, 'exception': 'timeout', 'message': 'Second failure'}
        ]
        
        # Execute scraper
        result = self.scraper.execute()
        
        # Should succeed on third attempt
        assert result.success
        assert result.data is not None
        assert self.scraper.api_call_count == 3
    
    @patch('scrapers.base.create_state_store')
    def test_graceful_degradation_with_cached_data(self, mock_state_store):
        """Test graceful degradation using cached data when all attempts fail."""
        # Mock state store
        mock_store = Mock()
        mock_store.get_historical_data.return_value = []
        mock_store.get_latest_value.return_value = None
        mock_state_store.return_value = mock_store
        
        # Pre-populate cache with fallback data
        cache_key = f"{self.scraper.data_source}_{self.scraper.metric_name}"
        cached_data = {
            'value': 800000,
            'timestamp': datetime.utcnow().isoformat(),
            'confidence': 0.7,
            'metadata': {'source': 'cached'}
        }
        self.scraper.cache_manager.cache_data(cache_key, cached_data)
        
        # Configure scraper to always fail
        self.scraper.failure_scenarios = [
            {'call_number': i, 'exception': 'connection', 'message': f'Failure {i}'}
            for i in range(1, 10)
        ]
        
        # Execute scraper
        result = self.scraper.execute()
        
        # Should succeed with cached data
        assert result.success
        assert result.data['value'] == 800000
        assert result.data['_fallback']
        assert 'Using fallback data' in result.error
    
    @patch('scrapers.base.create_state_store')
    def test_anomaly_detection_with_historical_data(self, mock_state_store):
        """Test anomaly detection with historical data."""
        # Mock state store with consistent historical data
        historical_data = []
        for i in range(30):
            historical_data.append({
                'value': 1000000 + (i * 1000),  # Gradual increase
                'timestamp': (datetime.utcnow() - timedelta(days=30-i)).isoformat()
            })
        
        mock_store = Mock()
        mock_store.get_historical_data.return_value = historical_data
        mock_store.get_latest_value.return_value = None
        mock_state_store.return_value = mock_store
        
        # Configure scraper to return anomalous data
        original_fetch = self.scraper.fetch_data
        def anomalous_fetch():
            data = original_fetch()
            data['value'] = 5000000  # Significantly higher than historical data
            return data
        
        self.scraper.fetch_data = anomalous_fetch
        
        # Execute scraper
        result = self.scraper.execute()
        
        # Should succeed but with lower confidence due to anomaly
        assert result.success
        assert result.data['anomaly_score'] > 0.5  # High anomaly score
        assert result.data['confidence'] < 0.9  # Reduced confidence
    
    @patch('scrapers.base.create_state_store')
    def test_cross_validation_with_disagreeing_sources(self, mock_state_store):
        """Test cross-validation when secondary sources disagree."""
        # Mock state store
        mock_store = Mock()
        mock_store.get_historical_data.return_value = []
        mock_store.get_latest_value.return_value = None
        mock_state_store.return_value = mock_store
        
        # Override secondary data sources to return disagreeing values
        def disagreeing_secondary_sources():
            return [
                {
                    'value': 2000000,  # 100% higher than primary
                    'source': 'disagreeing_source_1',
                    'confidence': 0.9
                },
                {
                    'value': 500000,  # 50% lower than primary
                    'source': 'disagreeing_source_2',
                    'confidence': 0.8
                }
            ]
        
        self.scraper.get_secondary_data_sources = disagreeing_secondary_sources
        
        # Execute scraper
        result = self.scraper.execute()
        
        # Should succeed but with lower confidence due to disagreement
        assert result.success
        assert result.data['confidence'] < 0.8  # Reduced confidence due to disagreement
    
    @patch('scrapers.base.create_state_store')
    def test_data_integrity_validation_failure(self, mock_state_store):
        """Test data integrity validation failure."""
        # Mock state store
        mock_store = Mock()
        mock_store.get_historical_data.return_value = []
        mock_store.get_latest_value.return_value = None
        mock_state_store.return_value = mock_store
        
        # Override fetch_data to return invalid data
        def invalid_fetch():
            return {
                'value': -1000000,  # Negative value (invalid per schema)
                'timestamp': 'invalid_timestamp',
                'confidence': 1.5,  # Above valid range
                'metadata': 'not_a_dict'  # Wrong type
            }
        
        self.scraper.fetch_data = invalid_fetch
        
        # Execute scraper
        result = self.scraper.execute()
        
        # Should fail due to validation errors
        assert not result.success
        assert 'Data validation failed' in result.error
    
    @patch('scrapers.base.create_state_store')
    def test_complete_failure_scenario(self, mock_state_store):
        """Test complete failure scenario with no fallback options."""
        # Mock state store with no cached data
        mock_store = Mock()
        mock_store.get_historical_data.return_value = []
        mock_store.get_latest_value.return_value = None
        mock_state_store.return_value = mock_store
        
        # Configure scraper to always fail
        self.scraper.failure_scenarios = [
            {'call_number': i, 'exception': 'connection', 'message': f'Failure {i}'}
            for i in range(1, 10)
        ]
        
        # Disable secondary data sources
        self.scraper.secondary_data_enabled = False
        
        # Execute scraper
        result = self.scraper.execute()
        
        # Should fail completely
        assert not result.success
        assert result.data is None
        assert 'Error in comprehensive_test scraper' in result.error
    
    @patch('scrapers.base.create_state_store')
    def test_performance_under_load(self, mock_state_store):
        """Test performance characteristics under load."""
        # Mock state store
        mock_store = Mock()
        mock_store.get_historical_data.return_value = []
        mock_store.get_latest_value.return_value = None
        mock_state_store.return_value = mock_store
        
        # Execute multiple times to test performance
        execution_times = []
        
        for i in range(5):
            start_time = time.time()
            result = self.scraper.execute()
            execution_time = time.time() - start_time
            execution_times.append(execution_time)
            
            assert result.success
            assert result.execution_time > 0
        
        # Verify reasonable performance (should complete within 1 second each)
        assert all(t < 1.0 for t in execution_times)
        
        # Verify consistent performance (no significant degradation)
        avg_time = sum(execution_times) / len(execution_times)
        assert all(abs(t - avg_time) < 0.5 for t in execution_times)


class TestRealWorldScenarios:
    """Test real-world error scenarios with actual scrapers."""
    
    @patch('scrapers.bond_issuance_scraper.Downloader')
    @patch('scrapers.base.create_state_store')
    def test_bond_scraper_sec_outage_scenario(self, mock_state_store, mock_downloader):
        """Test bond scraper behavior during SEC EDGAR outage."""
        # Mock state store
        mock_store = Mock()
        mock_store.get_historical_data.return_value = []
        mock_store.get_latest_value.return_value = {
            'value': 2500000000,
            'timestamp': (datetime.utcnow() - timedelta(hours=6)).isoformat(),
            'confidence': 0.9
        }
        mock_state_store.return_value = mock_store
        
        # Mock SEC downloader to fail
        mock_downloader_instance = Mock()
        mock_downloader_instance.get.side_effect = ConnectionError("SEC EDGAR unavailable")
        mock_downloader.return_value = mock_downloader_instance
        
        scraper = BondIssuanceScraper()
        
        # Pre-populate cache with recent data
        cache_key = f"{scraper.data_source}_{scraper.metric_name}"
        cached_data = {
            'value': 2800000000,
            'timestamp': datetime.utcnow().isoformat(),
            'confidence': 0.85,
            'metadata': {
                'companies': ['MSFT', 'GOOGL'],
                'bond_count': 2,
                'source': 'sec_edgar'
            }
        }
        scraper.cache_manager.cache_data(cache_key, cached_data)
        
        # Execute scraper
        result = scraper.execute()
        
        # Should succeed with cached data
        assert result.success
        assert result.data['_fallback']
        assert result.data['value'] == 2800000000
    
    @patch('yfinance.Ticker')
    @patch('requests.Session.get')
    @patch('scrapers.base.create_state_store')
    def test_bdc_scraper_mixed_failure_scenario(self, mock_state_store, mock_requests, mock_yf):
        """Test BDC scraper with mixed success/failure from data sources."""
        # Mock state store
        mock_store = Mock()
        mock_store.get_historical_data.return_value = []
        mock_store.get_latest_value.return_value = None
        mock_state_store.return_value = mock_store
        
        # Mock Yahoo Finance - some succeed, some fail
        def mock_ticker_side_effect(symbol):
            ticker_mock = Mock()
            if symbol in ['ARCC', 'MAIN']:
                # Successful tickers
                hist_mock = Mock()
                hist_mock.empty = False
                hist_mock.__getitem__.return_value.iloc = [25.50]  # Mock closing price
                ticker_mock.history.return_value = hist_mock
            else:
                # Failed tickers
                hist_mock = Mock()
                hist_mock.empty = True
                ticker_mock.history.return_value = hist_mock
            return ticker_mock
        
        mock_yf.side_effect = mock_ticker_side_effect
        
        # Mock RSS feeds - some succeed, some fail
        def mock_requests_side_effect(url, **kwargs):
            response_mock = Mock()
            if 'arescapitalcorp.com' in url or 'mainstcapital.com' in url:
                # Successful RSS feeds
                response_mock.content = b'''<?xml version="1.0"?>
                <rss><channel>
                <item>
                    <title>Quarterly NAV Announcement</title>
                    <description>Net asset value per share: $18.50</description>
                    <pubDate>Mon, 15 Jan 2024 10:00:00 GMT</pubDate>
                </item>
                </channel></rss>'''
                response_mock.raise_for_status.return_value = None
            else:
                # Failed RSS feeds
                response_mock.raise_for_status.side_effect = ConnectionError("RSS feed unavailable")
            return response_mock
        
        mock_requests.side_effect = mock_requests_side_effect
        
        scraper = BDCDiscountScraper()
        
        # Execute scraper
        result = scraper.execute()
        
        # Should succeed with partial data
        assert result.success
        assert result.data is not None
        
        # Should have data for successful BDCs only
        individual_bdcs = result.data.get('individual_bdcs', {})
        assert len(individual_bdcs) >= 1  # At least some BDCs should succeed
        
        # Confidence should be reduced due to partial failures
        assert result.data['confidence'] < 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])