"""
Integration tests for the BondIssuanceScraper.
"""

import pytest
from unittest.mock import patch, MagicMock
from scrapers.bond_issuance_scraper import BondIssuanceScraper


class TestBondIssuanceIntegration:
    """Integration tests for BondIssuanceScraper."""
    
    @pytest.fixture
    def scraper(self):
        """Create a BondIssuanceScraper instance for testing."""
        with patch('scrapers.bond_issuance_scraper.Downloader'):
            return BondIssuanceScraper()
    
    @patch.object(BondIssuanceScraper, '_get_424b_filings')
    def test_full_execution_with_alert(self, mock_get_filings, scraper):
        """Test full scraper execution that triggers an alert."""
        # Mock filing data that will trigger an alert
        mock_filings = [{
            'cik': '0000789019',
            'form_type': '424B2',
            'filing_date': '2024-01-15',
            'document_url': 'https://example.com/msft.htm',
            'content': scraper._generate_sample_prospectus_content(6_000_000_000, 4.5)
        }]
        
        def mock_get_filings_side_effect(cik, start_date, end_date):
            if cik == '0000789019':  # MSFT
                return mock_filings
            else:
                return []
        
        mock_get_filings.side_effect = mock_get_filings_side_effect
        
        # Mock the state store to return no historical data (first run)
        scraper.state_store.get_latest_value = MagicMock(return_value=None)
        scraper.state_store.save_data = MagicMock()
        
        # Mock the alert service
        scraper.alert_service.send_alert = MagicMock()
        
        # Mock the metrics service
        scraper.metrics_service.send_metric = MagicMock()
        
        # Execute the scraper
        result = scraper.execute()
        
        # Verify successful execution
        assert result.success is True
        assert result.data_source == 'bond_issuance'
        assert result.metric_name == 'weekly'
        assert result.data['value'] == 6_000_000_000
        assert 'MSFT' in result.data['metadata']['companies']
        
        # Verify alert was triggered (value > 5B threshold)
        scraper.alert_service.send_alert.assert_called_once()
        alert_call = scraper.alert_service.send_alert.call_args[0][0]
        assert alert_call['alert_type'] == 'threshold_breach'
        assert alert_call['current_value'] == 6_000_000_000
        
        # Verify data was saved
        scraper.state_store.save_data.assert_called_once()
        
        # Verify metrics were sent
        scraper.metrics_service.send_metric.assert_called()
    
    @patch.object(BondIssuanceScraper, '_get_424b_filings')
    def test_full_execution_no_alert(self, mock_get_filings, scraper):
        """Test full scraper execution that doesn't trigger an alert."""
        # Mock filing data that won't trigger an alert
        mock_filings = [{
            'cik': '0001326801',
            'form_type': '424B5',
            'filing_date': '2024-01-15',
            'document_url': 'https://example.com/meta.htm',
            'content': scraper._generate_sample_prospectus_content(1_000_000_000, 4.2)
        }]
        
        def mock_get_filings_side_effect(cik, start_date, end_date):
            if cik == '0001326801':  # META
                return mock_filings
            else:
                return []
        
        mock_get_filings.side_effect = mock_get_filings_side_effect
        
        # Mock the state store
        scraper.state_store.get_latest_value = MagicMock(return_value={'value': 800_000_000})
        scraper.state_store.save_data = MagicMock()
        
        # Mock the alert service
        scraper.alert_service.send_alert = MagicMock()
        
        # Mock the metrics service
        scraper.metrics_service.send_metric = MagicMock()
        
        # Execute the scraper
        result = scraper.execute()
        
        # Verify successful execution
        assert result.success is True
        assert result.data['value'] == 1_000_000_000
        assert 'META' in result.data['metadata']['companies']
        
        # Verify no alert was triggered (1B < 5B threshold, increase 200M < 5B threshold)
        scraper.alert_service.send_alert.assert_not_called()
        
        # Verify data was still saved and metrics sent
        scraper.state_store.save_data.assert_called_once()
        scraper.metrics_service.send_metric.assert_called()
    
    @patch.object(BondIssuanceScraper, '_get_424b_filings')
    def test_execution_with_error_handling(self, mock_get_filings, scraper):
        """Test scraper execution with error handling."""
        # Mock an exception during data fetching for all companies
        mock_get_filings.side_effect = Exception("SEC API unavailable")
        
        # Mock the state store and services
        scraper.state_store.get_latest_value = MagicMock(return_value=None)
        scraper.state_store.save_data = MagicMock()
        scraper.alert_service.send_alert = MagicMock()
        scraper.metrics_service.send_metric = MagicMock()
        
        # Execute the scraper
        result = scraper.execute()
        
        # Verify graceful error handling - scraper continues and returns success
        # with empty data when all companies fail (this is the expected behavior)
        assert result.success is True
        assert result.data['value'] == 0  # No data collected
        assert result.data['metadata']['companies'] == []  # No companies processed
        assert result.data['confidence'] == 0.0  # Low confidence due to no data
        
        # Verify no alert was triggered (no data to alert on)
        scraper.alert_service.send_alert.assert_not_called()
        
        # Verify data was still saved (empty data is valid)
        scraper.state_store.save_data.assert_called_once()
        
        # Verify metrics were sent (including the empty result)
        scraper.metrics_service.send_metric.assert_called()
    
    @patch.object(BondIssuanceScraper, 'fetch_data')
    def test_execution_with_validation_error(self, mock_fetch_data, scraper):
        """Test scraper execution with validation error."""
        # Mock fetch_data to return invalid data
        mock_fetch_data.return_value = {'invalid': 'data'}  # Missing 'value' field
        
        # Mock the metrics service for error reporting
        scraper.metrics_service.send_metric = MagicMock()
        
        # Execute the scraper
        result = scraper.execute()
        
        # Verify error handling for validation failure
        assert result.success is False
        assert result.error is not None
        assert "Missing total notional value" in result.error
        
        # Verify error metric was sent
        scraper.metrics_service.send_metric.assert_called()
        error_call = scraper.metrics_service.send_metric.call_args_list[-1]
        assert error_call[0][1] == 'errors'  # metric_name
        assert error_call[0][2].value == 1  # error count


if __name__ == '__main__':
    pytest.main([__file__])