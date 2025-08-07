"""
Integration tests for BDC discount scraper.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import pandas as pd

from scrapers.bdc_discount_scraper import BDCDiscountScraper
from models.core import ScraperResult


class TestBDCDiscountIntegration:
    """Integration tests for BDC discount scraper."""
    
    @pytest.fixture
    def mock_dependencies(self):
        """Mock all external dependencies."""
        with patch('services.state_store.create_state_store') as mock_state_store, \
             patch('services.alert_service.AlertService') as mock_alert_service, \
             patch('services.metrics_service.MetricsService') as mock_metrics_service:
            
            # Configure state store mock
            state_store_instance = Mock()
            mock_state_store.return_value = state_store_instance
            
            # Configure alert service mock
            alert_service_instance = Mock()
            mock_alert_service.return_value = alert_service_instance
            
            # Configure metrics service mock
            metrics_service_instance = Mock()
            mock_metrics_service.return_value = metrics_service_instance
            
            yield {
                'state_store': state_store_instance,
                'alert_service': alert_service_instance,
                'metrics_service': metrics_service_instance
            }
    
    @pytest.fixture
    def mock_yahoo_finance(self):
        """Mock Yahoo Finance responses."""
        with patch('yfinance.Ticker') as mock_ticker:
            # Create mock ticker instances for different symbols
            mock_instances = {}
            
            def get_ticker_instance(symbol):
                if symbol not in mock_instances:
                    instance = Mock()
                    # Set up different prices for different symbols
                    prices = {
                        'ARCC': 25.50,
                        'OCSL': 22.00,
                        'MAIN': 18.75,
                        'PSEC': 15.25
                    }
                    hist_data = pd.DataFrame({'Close': [prices.get(symbol, 20.00)]})
                    instance.history.return_value = hist_data
                    mock_instances[symbol] = instance
                return mock_instances[symbol]
            
            mock_ticker.side_effect = get_ticker_instance
            yield mock_ticker
    
    @pytest.fixture
    def mock_rss_feeds(self):
        """Mock RSS feed responses."""
        with patch('requests.Session.get') as mock_get:
            def get_rss_response(url, **kwargs):
                # Different RSS responses for different BDCs
                if 'arescapitalcorp.com' in url:
                    content = '''<?xml version="1.0" encoding="UTF-8"?>
                    <rss version="2.0">
                        <channel>
                            <item>
                                <title>Q4 2024 NAV Update</title>
                                <description>Ares Capital reports net asset value of $28.50 per share</description>
                                <pubDate>Wed, 15 Jan 2025 10:00:00 GMT</pubDate>
                            </item>
                        </channel>
                    </rss>'''
                elif 'oaktreespecialtylending.com' in url:
                    content = '''<?xml version="1.0" encoding="UTF-8"?>
                    <rss version="2.0">
                        <channel>
                            <item>
                                <title>Quarterly Results</title>
                                <description>Net asset value per share is $24.00 as of quarter end</description>
                                <pubDate>Wed, 15 Jan 2025 10:00:00 GMT</pubDate>
                            </item>
                        </channel>
                    </rss>'''
                elif 'mainstcapital.com' in url:
                    content = '''<?xml version="1.0" encoding="UTF-8"?>
                    <rss version="2.0">
                        <channel>
                            <item>
                                <title>Financial Update</title>
                                <description>Main Street Capital net asset value is $21.00 per share</description>
                                <pubDate>Wed, 15 Jan 2025 10:00:00 GMT</pubDate>
                            </item>
                        </channel>
                    </rss>'''
                else:  # PSEC - simulate RSS feed failure
                    raise Exception("RSS feed unavailable")
                
                mock_response = Mock()
                mock_response.content = content.encode('utf-8')
                mock_response.raise_for_status.return_value = None
                return mock_response
            
            mock_get.side_effect = get_rss_response
            yield mock_get
    
    def test_full_execution_success(self, mock_dependencies, mock_yahoo_finance, mock_rss_feeds):
        """Test full scraper execution with successful data collection."""
        # Set up state store to return no historical data (first run)
        mock_dependencies['state_store'].get_latest_value.return_value = None
        
        scraper = BDCDiscountScraper()
        result = scraper.execute()
        
        # Verify successful execution
        assert isinstance(result, ScraperResult)
        assert result.success is True
        assert result.data_source == 'bdc_discount'
        assert result.metric_name == 'discount_to_nav'
        assert result.error is None
        
        # Verify data structure
        data = result.data
        assert 'value' in data
        assert 'individual_bdcs' in data
        assert data['bdc_count'] == 3  # ARCC, OCSL, MAIN (PSEC failed)
        
        # Verify individual BDC data
        assert 'ARCC' in data['individual_bdcs']
        assert 'OCSL' in data['individual_bdcs']
        assert 'MAIN' in data['individual_bdcs']
        assert 'PSEC' not in data['individual_bdcs']  # Should fail due to RSS error
        
        # Verify ARCC calculations
        arcc_data = data['individual_bdcs']['ARCC']
        assert arcc_data['stock_price'] == 25.50
        assert arcc_data['nav_value'] == 28.50
        expected_discount = (28.50 - 25.50) / 28.50  # Should be negative (discount)
        assert abs(arcc_data['discount_to_nav'] - (-expected_discount)) < 0.001
        
        # Verify state store was called
        mock_dependencies['state_store'].save_data.assert_called_once()
        
        # Verify metrics were sent
        mock_dependencies['metrics_service'].send_metric.assert_called()
        
        # Verify no alert was sent (first run)
        mock_dependencies['alert_service'].send_alert.assert_not_called()
    
    def test_execution_with_alert_trigger(self, mock_dependencies, mock_yahoo_finance, mock_rss_feeds):
        """Test execution that triggers an alert due to significant change."""
        # Set up historical data that will trigger an alert
        historical_data = {
            'value': -0.02,  # Previous average discount was -2%
            'timestamp': '2024-01-14T10:00:00Z'
        }
        mock_dependencies['state_store'].get_latest_value.return_value = historical_data
        
        scraper = BDCDiscountScraper()
        result = scraper.execute()
        
        # Verify successful execution
        assert result.success is True
        
        # Verify alert was triggered
        mock_dependencies['alert_service'].send_alert.assert_called_once()
        
        # Verify alert message structure
        alert_call = mock_dependencies['alert_service'].send_alert.call_args[0][0]
        assert alert_call['alert_type'] == 'bdc_discount_change'
        assert alert_call['current_value'] < -0.05  # Should be significant discount
        assert alert_call['previous_value'] == -0.02
        assert 'decreased significantly' in alert_call['message']
    
    def test_execution_no_alert_small_change(self, mock_dependencies, mock_yahoo_finance, mock_rss_feeds):
        """Test execution with small change that doesn't trigger alert."""
        # Set up historical data with small change
        historical_data = {
            'value': -0.08,  # Previous average discount was -8% (small change expected)
            'timestamp': '2024-01-14T10:00:00Z'
        }
        mock_dependencies['state_store'].get_latest_value.return_value = historical_data
        
        scraper = BDCDiscountScraper()
        result = scraper.execute()
        
        # Verify successful execution
        assert result.success is True
        
        # Verify no alert was triggered
        mock_dependencies['alert_service'].send_alert.assert_not_called()
    
    def test_execution_partial_failure(self, mock_dependencies, mock_yahoo_finance):
        """Test execution with partial data source failures."""
        # Mock RSS feeds to fail for all BDCs
        with patch('requests.Session.get') as mock_get:
            mock_get.side_effect = Exception("All RSS feeds down")
            
            scraper = BDCDiscountScraper()
            result = scraper.execute()
            
            # Should fail because no data could be retrieved
            assert result.success is False
            assert "No BDC data could be retrieved" in result.error
            
            # Verify error handling
            mock_dependencies['metrics_service'].send_metric.assert_called()
            error_call = mock_dependencies['metrics_service'].send_metric.call_args_list[-1]
            assert error_call[0][1] == 'errors'  # Error metric sent
    
    def test_execution_yahoo_finance_failure(self, mock_dependencies, mock_rss_feeds):
        """Test execution with Yahoo Finance API failure."""
        with patch('yfinance.Ticker') as mock_ticker:
            mock_ticker.side_effect = Exception("Yahoo Finance API down")
            
            scraper = BDCDiscountScraper()
            result = scraper.execute()
            
            # Should fail because no stock prices could be retrieved
            assert result.success is False
            assert "No BDC data could be retrieved" in result.error
    
    def test_data_quality_assessment(self, mock_dependencies, mock_yahoo_finance, mock_rss_feeds):
        """Test data quality assessment based on successful data retrieval."""
        scraper = BDCDiscountScraper()
        result = scraper.execute()
        
        # With 3 successful BDCs (ARCC, OCSL, MAIN), quality should be 'high'
        assert result.data['metadata']['data_quality'] == 'high'
        
        # Test with fewer successful BDCs
        with patch.object(scraper, '_fetch_stock_price') as mock_price:
            mock_price.side_effect = [25.50, None, None, None]  # Only ARCC succeeds
            
            result = scraper.execute()
            assert result.data['metadata']['data_quality'] == 'medium'
    
    def test_discount_calculation_accuracy(self, mock_dependencies, mock_yahoo_finance, mock_rss_feeds):
        """Test accuracy of discount-to-NAV calculations."""
        scraper = BDCDiscountScraper()
        result = scraper.execute()
        
        # Verify discount calculations for each BDC
        bdcs = result.data['individual_bdcs']
        
        # ARCC: Price $25.50, NAV $28.50 -> Discount = (28.50 - 25.50) / 28.50 = 0.105 (10.5%)
        arcc_expected = (28.50 - 25.50) / 28.50
        assert abs(bdcs['ARCC']['discount_to_nav'] - (-arcc_expected)) < 0.001
        
        # OCSL: Price $22.00, NAV $24.00 -> Discount = (24.00 - 22.00) / 24.00 = 0.083 (8.3%)
        ocsl_expected = (24.00 - 22.00) / 24.00
        assert abs(bdcs['OCSL']['discount_to_nav'] - (-ocsl_expected)) < 0.001
        
        # MAIN: Price $18.75, NAV $21.00 -> Discount = (21.00 - 18.75) / 21.00 = 0.107 (10.7%)
        main_expected = (21.00 - 18.75) / 21.00
        assert abs(bdcs['MAIN']['discount_to_nav'] - (-main_expected)) < 0.001
        
        # Verify average calculation
        expected_avg = ((-arcc_expected) + (-ocsl_expected) + (-main_expected)) / 3
        assert abs(result.data['value'] - expected_avg) < 0.001
    
    def test_error_recovery_and_logging(self, mock_dependencies, mock_yahoo_finance, mock_rss_feeds, caplog):
        """Test error recovery and logging behavior."""
        # Force an error in one BDC while others succeed
        with patch.object(BDCDiscountScraper, '_fetch_stock_price') as mock_price:
            mock_price.side_effect = [25.50, Exception("Network error"), 18.75, 15.25]
            
            scraper = BDCDiscountScraper()
            result = scraper.execute()
            
            # Should still succeed with partial data
            assert result.success is True
            assert result.data['bdc_count'] == 3  # ARCC, MAIN, PSEC (OCSL failed)
            
            # Verify error was logged
            assert "Error processing OCSL" in caplog.text
    
    @patch('time.time')
    def test_execution_timing(self, mock_time, mock_dependencies, mock_yahoo_finance, mock_rss_feeds):
        """Test execution timing measurement."""
        # Mock time progression
        mock_time.side_effect = [1000.0, 1005.5]  # 5.5 second execution
        
        scraper = BDCDiscountScraper()
        result = scraper.execute()
        
        assert result.execution_time == 5.5
        assert result.success is True