"""
Tests for enhanced scraper error handling and data validation.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, List

from scrapers.base import BaseScraper
from scrapers.bond_issuance_scraper import BondIssuanceScraper
from models.core import ScraperResult
from utils.error_handling import ValidationResult


class MockScraper(BaseScraper):
    """Mock scraper for testing base functionality."""
    
    def __init__(self):
        super().__init__('test_source', 'test_metric')
        self.fetch_data_calls = 0
        self.should_fail = False
        self.fail_count = 0
    
    def fetch_data(self) -> Dict[str, Any]:
        """Mock fetch_data implementation."""
        self.fetch_data_calls += 1
        
        if self.should_fail and self.fetch_data_calls <= self.fail_count:
            raise ConnectionError("Mock API failure")
        
        return {
            'value': 1000000,
            'timestamp': datetime.utcnow().isoformat(),
            'confidence': 0.95,
            'metadata': {'source': 'mock'}
        }
    
    def should_alert(self, current_data: Dict[str, Any], historical_data: Dict[str, Any]) -> bool:
        """Mock alert logic."""
        return False
    
    def generate_alert_message(self, current_data: Dict[str, Any], historical_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock alert message generation."""
        return {'message': 'Mock alert'}


class TestBaseScraper:
    """Test enhanced base scraper functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.scraper = MockScraper()
    
    @patch('scrapers.base.create_state_store')
    def test_successful_execution_with_validation(self, mock_state_store):
        """Test successful scraper execution with validation."""
        # Mock state store
        mock_store = Mock()
        mock_store.get_historical_data.return_value = []
        mock_store.get_latest_value.return_value = None
        mock_state_store.return_value = mock_store
        
        # Execute scraper
        result = self.scraper.execute()
        
        assert result.success
        assert result.data is not None
        assert 'confidence' in result.data
        assert 'validation_checksum' in result.data
        assert result.error is None
    
    @patch('scrapers.base.create_state_store')
    def test_execution_with_data_validation_failure(self, mock_state_store):
        """Test scraper execution when data validation fails."""
        # Mock state store
        mock_store = Mock()
        mock_store.get_historical_data.return_value = []
        mock_store.get_latest_value.return_value = None
        mock_state_store.return_value = mock_store
        
        # Mock validation to fail
        with patch.object(self.scraper.data_validator, 'validate_data') as mock_validate:
            mock_validate.return_value = ValidationResult(
                is_valid=False,
                confidence=0.0,
                errors=['Test validation error'],
                warnings=[]
            )
            
            result = self.scraper.execute()
            
            assert not result.success
            assert 'Data validation failed' in result.error
    
    @patch('scrapers.base.create_state_store')
    def test_execution_with_fallback_data(self, mock_state_store):
        """Test scraper execution using fallback data when primary fails."""
        # Mock state store
        mock_store = Mock()
        mock_store.get_historical_data.return_value = []
        mock_store.get_latest_value.return_value = {
            'value': 500000,
            'timestamp': datetime.utcnow().isoformat(),
            'confidence': 0.8
        }
        mock_state_store.return_value = mock_store
        
        # Make fetch_data fail
        self.scraper.should_fail = True
        self.scraper.fail_count = 10  # Always fail
        
        # Cache some data for fallback
        cache_key = f"{self.scraper.data_source}_{self.scraper.metric_name}"
        fallback_data = {
            'value': 750000,
            'timestamp': datetime.utcnow().isoformat(),
            'confidence': 0.9
        }
        self.scraper.cache_manager.cache_data(cache_key, fallback_data)
        
        result = self.scraper.execute()
        
        assert result.success  # Should succeed with fallback data
        assert result.data['_fallback']
        assert result.data['value'] == 750000
        assert 'Using fallback data' in result.error
    
    @patch('scrapers.base.create_state_store')
    def test_cross_validation_integration(self, mock_state_store):
        """Test cross-validation integration in scraper execution."""
        # Mock state store
        mock_store = Mock()
        mock_store.get_historical_data.return_value = []
        mock_store.get_latest_value.return_value = None
        mock_state_store.return_value = mock_store
        
        # Mock secondary data sources
        with patch.object(self.scraper, 'get_secondary_data_sources') as mock_secondary:
            mock_secondary.return_value = [
                {'value': 1010000, 'source': 'secondary1'},
                {'value': 990000, 'source': 'secondary2'}
            ]
            
            result = self.scraper.execute()
            
            assert result.success
            assert result.data['confidence'] > 0.8  # Should have high confidence with cross-validation
    
    def test_data_schema_validation(self):
        """Test data schema validation."""
        schema = self.scraper.get_data_schema()
        
        assert 'required' in schema
        assert 'types' in schema
        assert 'ranges' in schema
        assert 'value' in schema['required']
        assert 'timestamp' in schema['required']
    
    def test_historical_data_retrieval(self):
        """Test historical data retrieval for anomaly detection."""
        with patch.object(self.scraper.state_store, 'get_historical_data') as mock_historical:
            mock_historical.return_value = [
                {'value': 1000000, 'timestamp': '2024-01-01T00:00:00Z'},
                {'value': 1100000, 'timestamp': '2024-01-02T00:00:00Z'},
                {'value': 950000, 'timestamp': '2024-01-03T00:00:00Z'}
            ]
            
            historical_data = self.scraper._get_historical_data_list()
            
            assert len(historical_data) == 3
            assert all('value' in data for data in historical_data)


class TestBondIssuanceScraperEnhancements:
    """Test enhanced bond issuance scraper functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.scraper = BondIssuanceScraper()
    
    def test_bond_data_validation(self):
        """Test bond data validation logic."""
        # Valid bond data
        valid_bond = {
            'filing_date': datetime.now().date(),
            'notional_amount': 2000000000,
            'coupon_rate': 4.5,
            'form_type': '424B2'
        }
        
        assert self.scraper._validate_bond_data(valid_bond)
        
        # Invalid bond data - negative notional
        invalid_bond = valid_bond.copy()
        invalid_bond['notional_amount'] = -1000000
        
        assert not self.scraper._validate_bond_data(invalid_bond)
        
        # Invalid bond data - missing required field
        invalid_bond = valid_bond.copy()
        del invalid_bond['notional_amount']
        
        assert not self.scraper._validate_bond_data(invalid_bond)
        
        # Invalid bond data - unrealistic coupon rate
        invalid_bond = valid_bond.copy()
        invalid_bond['coupon_rate'] = 50.0  # 50% coupon rate is unrealistic
        
        assert not self.scraper._validate_bond_data(invalid_bond)
    
    def test_bond_checksum_calculation(self):
        """Test bond data checksum calculation."""
        bond_data = {
            'filing_date': datetime.now().date(),
            'notional_amount': 2000000000,
            'coupon_rate': 4.5,
            'form_type': '424B2'
        }
        
        checksum1 = self.scraper._calculate_bond_checksum(bond_data)
        checksum2 = self.scraper._calculate_bond_checksum(bond_data)
        
        # Same data should produce same checksum
        assert checksum1 == checksum2
        assert len(checksum1) == 8  # MD5 hash truncated to 8 chars
        
        # Different data should produce different checksum
        bond_data['notional_amount'] = 3000000000
        checksum3 = self.scraper._calculate_bond_checksum(bond_data)
        
        assert checksum1 != checksum3
    
    def test_data_schema_override(self):
        """Test bond issuance scraper data schema."""
        schema = self.scraper.get_data_schema()
        
        assert 'value' in schema['required']
        assert 'metadata' in schema['required']
        assert schema['ranges']['value'][1] == 500_000_000_000  # Max $500B
    
    @patch('scrapers.bond_issuance_scraper.requests')
    def test_retry_logic_on_sec_failure(self, mock_requests):
        """Test retry logic when SEC EDGAR fails."""
        # Mock SEC EDGAR failure
        mock_requests.get.side_effect = ConnectionError("SEC EDGAR unavailable")
        
        with patch.object(self.scraper, '_simulate_filing_data') as mock_simulate:
            mock_simulate.return_value = []
            
            # This should raise ConnectionError after retries
            with pytest.raises(ConnectionError):
                self.scraper._get_424b_filings_with_retry('0000789019', 
                                                        datetime.now().date() - timedelta(days=7),
                                                        datetime.now().date())
    
    def test_secondary_data_sources(self):
        """Test secondary data sources for cross-validation."""
        with patch.object(self.scraper, '_get_finra_trace_data') as mock_finra:
            with patch.object(self.scraper, '_get_sp_capitaliq_data') as mock_sp:
                mock_finra.return_value = {'value': 3200000000, 'source': 'finra_trace'}
                mock_sp.return_value = {'value': 3100000000, 'source': 'sp_capitaliq'}
                
                secondary_sources = self.scraper.get_secondary_data_sources()
                
                assert len(secondary_sources) == 2
                assert any(source['source'] == 'finra_trace' for source in secondary_sources)
                assert any(source['source'] == 'sp_capitaliq' for source in secondary_sources)
    
    @patch('scrapers.bond_issuance_scraper.datetime')
    def test_fetch_data_with_error_handling(self, mock_datetime):
        """Test fetch_data with comprehensive error handling."""
        # Mock datetime
        mock_now = datetime(2024, 1, 15, 10, 0, 0)
        mock_datetime.now.return_value = mock_now
        mock_datetime.utcnow.return_value = mock_now
        
        with patch.object(self.scraper, '_get_424b_filings_with_retry') as mock_filings:
            # Simulate one company succeeding, one failing
            def mock_filings_side_effect(cik, start_date, end_date):
                if cik == '0000789019':  # MSFT
                    return [{
                        'cik': cik,
                        'form_type': '424B2',
                        'filing_date': start_date + timedelta(days=1),
                        'document_url': 'https://example.com/filing.htm',
                        'content': self.scraper._generate_sample_prospectus_content(2000000000, 4.5)
                    }]
                else:
                    raise ConnectionError(f"Failed to get filings for {cik}")
            
            mock_filings.side_effect = mock_filings_side_effect
            
            result = self.scraper.fetch_data()
            
            assert result['value'] == 2000000000  # Only MSFT bond
            assert len(result['metadata']['companies']) == 1
            assert 'MSFT' in result['metadata']['companies']
            assert len(result['metadata']['failed_companies']) == 3  # META, AMZN, GOOGL
            assert result['metadata']['success_rate'] == 0.25  # 1 out of 4 succeeded


class TestErrorHandlingIntegration:
    """Test integration of all error handling components."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.scraper = MockScraper()
    
    @patch('scrapers.base.create_state_store')
    def test_complete_error_recovery_scenario(self, mock_state_store):
        """Test complete error recovery scenario."""
        # Mock state store
        mock_store = Mock()
        mock_store.get_historical_data.return_value = [
            {'value': 1000000, 'timestamp': '2024-01-01T00:00:00Z'},
            {'value': 1100000, 'timestamp': '2024-01-02T00:00:00Z'}
        ]
        mock_store.get_latest_value.return_value = {
            'value': 950000,
            'timestamp': '2024-01-03T00:00:00Z',
            'confidence': 0.8
        }
        mock_state_store.return_value = mock_store
        
        # Set up scraper to fail initially then succeed
        self.scraper.should_fail = True
        self.scraper.fail_count = 2  # Fail first 2 attempts
        
        # Mock secondary data sources
        with patch.object(self.scraper, 'get_secondary_data_sources') as mock_secondary:
            mock_secondary.return_value = [
                {'value': 1010000, 'source': 'secondary1'},
                {'value': 990000, 'source': 'secondary2'}
            ]
            
            result = self.scraper.execute()
            
            # Should succeed after retries
            assert result.success
            assert result.data is not None
            assert 'confidence' in result.data
            assert 'validation_checksum' in result.data
            assert 'anomaly_score' in result.data
            
            # Should have made multiple fetch attempts due to retry logic
            assert self.scraper.fetch_data_calls >= 2
    
    @patch('scrapers.base.create_state_store')
    def test_graceful_degradation_with_stale_data_warning(self, mock_state_store):
        """Test graceful degradation with stale data warnings."""
        # Mock state store
        mock_store = Mock()
        mock_store.get_historical_data.return_value = []
        mock_store.get_latest_value.return_value = {
            'value': 800000,
            'timestamp': (datetime.utcnow() - timedelta(days=2)).isoformat(),  # 2 days old
            'confidence': 0.7
        }
        mock_state_store.return_value = mock_store
        
        # Make scraper always fail
        self.scraper.should_fail = True
        self.scraper.fail_count = 10
        
        result = self.scraper.execute()
        
        # Should succeed with fallback data
        assert result.success
        assert result.data['_stale']
        assert 'Using last known good data' in result.data['_stale_reason']
        assert 'Using fallback data' in result.error


if __name__ == "__main__":
    pytest.main([__file__, "-v"])