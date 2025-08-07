"""
Unit tests for BDC discount-to-NAV scraper.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET
import pandas as pd

from scrapers.bdc_discount_scraper import BDCDiscountScraper


class TestBDCDiscountScraper:
    """Test cases for BDCDiscountScraper."""
    
    @pytest.fixture
    def scraper(self):
        """Create a BDCDiscountScraper instance for testing."""
        with patch('services.state_store.create_state_store'), \
             patch('services.alert_service.AlertService'), \
             patch('services.metrics_service.MetricsService'):
            return BDCDiscountScraper()
    
    @pytest.fixture
    def mock_yahoo_data(self):
        """Mock Yahoo Finance data."""
        mock_hist = pd.DataFrame({
            'Close': [25.50]
        })
        return mock_hist
    
    @pytest.fixture
    def mock_rss_response(self):
        """Mock RSS feed response with NAV data."""
        rss_content = '''<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
            <channel>
                <title>Press Releases</title>
                <item>
                    <title>Quarterly NAV Update</title>
                    <description>Net asset value per share is $28.50 as of quarter end</description>
                    <pubDate>Wed, 15 Jan 2025 10:00:00 GMT</pubDate>
                </item>
                <item>
                    <title>Old Update</title>
                    <description>Old net asset value data</description>
                    <pubDate>Wed, 15 Jan 2020 10:00:00 GMT</pubDate>
                </item>
            </channel>
        </rss>'''
        return rss_content
    
    @pytest.fixture
    def sample_bdc_data(self):
        """Sample BDC data for testing."""
        # ARCC: (28.50 - 25.50) / 28.50 = 0.105 (10.5% discount)
        # OCSL: (24.00 - 22.00) / 24.00 = 0.083 (8.3% discount)
        arcc_discount = (28.50 - 25.50) / 28.50
        ocsl_discount = (24.00 - 22.00) / 24.00
        avg_discount = (arcc_discount + ocsl_discount) / 2
        
        return {
            'value': avg_discount,
            'average_discount_percentage': avg_discount * 100,
            'bdc_count': 2,
            'individual_bdcs': {
                'ARCC': {
                    'stock_price': 25.50,
                    'nav_value': 28.50,
                    'discount_to_nav': arcc_discount,
                    'discount_percentage': arcc_discount * 100,
                    'name': 'Ares Capital Corporation',
                    'timestamp': '2024-01-15T10:00:00'
                },
                'OCSL': {
                    'stock_price': 22.00,
                    'nav_value': 24.00,
                    'discount_to_nav': ocsl_discount,
                    'discount_percentage': ocsl_discount * 100,
                    'name': 'Oaktree Specialty Lending Corporation',
                    'timestamp': '2024-01-15T10:00:00'
                }
            },
            'metadata': {
                'symbols_processed': ['ARCC', 'OCSL'],
                'data_quality': 'medium'
            }
        }
    
    def test_init(self, scraper):
        """Test scraper initialization."""
        assert scraper.data_source == 'bdc_discount'
        assert scraper.metric_name == 'discount_to_nav'
        assert scraper.ALERT_THRESHOLD == 0.05
        assert len(scraper.BDC_CONFIG) == 4
        assert 'ARCC' in scraper.BDC_CONFIG
        assert 'OCSL' in scraper.BDC_CONFIG
        assert 'MAIN' in scraper.BDC_CONFIG
        assert 'PSEC' in scraper.BDC_CONFIG
    
    @patch('yfinance.Ticker')
    def test_fetch_stock_price_success(self, mock_ticker, scraper, mock_yahoo_data):
        """Test successful stock price fetching."""
        mock_ticker_instance = Mock()
        mock_ticker_instance.history.return_value = mock_yahoo_data
        mock_ticker.return_value = mock_ticker_instance
        
        price = scraper._fetch_stock_price('ARCC')
        
        assert price == 25.50
        mock_ticker.assert_called_once_with('ARCC')
        mock_ticker_instance.history.assert_called_once_with(period="1d")
    
    @patch('yfinance.Ticker')
    def test_fetch_stock_price_no_data(self, mock_ticker, scraper):
        """Test stock price fetching with no data."""
        mock_ticker_instance = Mock()
        mock_ticker_instance.history.return_value = pd.DataFrame()  # Empty DataFrame
        mock_ticker.return_value = mock_ticker_instance
        
        price = scraper._fetch_stock_price('ARCC')
        
        assert price is None
    
    @patch('yfinance.Ticker')
    def test_fetch_stock_price_exception(self, mock_ticker, scraper):
        """Test stock price fetching with exception."""
        mock_ticker.side_effect = Exception("API Error")
        
        price = scraper._fetch_stock_price('ARCC')
        
        assert price is None
    
    @patch('requests.Session.get')
    @patch('scrapers.bdc_discount_scraper.datetime')
    def test_fetch_nav_from_rss_success(self, mock_datetime, mock_get, scraper, mock_rss_response):
        """Test successful NAV fetching from RSS."""
        # Mock current time to be after the test date
        from datetime import datetime, timedelta
        mock_now = datetime(2025, 2, 1, 12, 0, 0)  # Feb 1, 2025
        mock_datetime.utcnow.return_value = mock_now
        mock_datetime.strptime.side_effect = datetime.strptime
        mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
        
        mock_response = Mock()
        mock_response.content = mock_rss_response.encode('utf-8')
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        config = scraper.BDC_CONFIG['ARCC']
        nav = scraper._fetch_nav_from_rss('ARCC', config)
        
        assert nav == 28.50
        mock_get.assert_called_once_with(config['rss_url'], timeout=30)
    
    @patch('requests.Session.get')
    def test_fetch_nav_from_rss_no_recent_data(self, mock_get, scraper):
        """Test NAV fetching with no recent data."""
        old_rss_content = '''<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
            <channel>
                <title>Press Releases</title>
                <item>
                    <title>Old NAV Update</title>
                    <description>Net asset value per share is $28.50</description>
                    <pubDate>Wed, 15 Jan 2020 10:00:00 GMT</pubDate>
                </item>
            </channel>
        </rss>'''
        
        mock_response = Mock()
        mock_response.content = old_rss_content.encode('utf-8')
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        config = scraper.BDC_CONFIG['ARCC']
        nav = scraper._fetch_nav_from_rss('ARCC', config)
        
        assert nav is None
    
    @patch('requests.Session.get')
    def test_fetch_nav_from_rss_request_exception(self, mock_get, scraper):
        """Test NAV fetching with request exception."""
        import requests
        mock_get.side_effect = requests.RequestException("Network error")
        
        config = scraper.BDC_CONFIG['ARCC']
        nav = scraper._fetch_nav_from_rss('ARCC', config)
        
        assert nav is None
    
    @patch('requests.Session.get')
    def test_fetch_nav_from_rss_parse_error(self, mock_get, scraper):
        """Test NAV fetching with XML parse error."""
        mock_response = Mock()
        mock_response.content = b"Invalid XML content"
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        config = scraper.BDC_CONFIG['ARCC']
        nav = scraper._fetch_nav_from_rss('ARCC', config)
        
        assert nav is None
    
    @patch.object(BDCDiscountScraper, '_fetch_nav_from_rss')
    @patch.object(BDCDiscountScraper, '_fetch_stock_price')
    def test_fetch_data_success(self, mock_fetch_price, mock_fetch_nav, scraper):
        """Test successful data fetching."""
        # Mock successful price and NAV fetching for two BDCs
        mock_fetch_price.side_effect = [25.50, 22.00, None, None]  # ARCC, OCSL succeed; MAIN, PSEC fail
        mock_fetch_nav.side_effect = [28.50, 24.00, None, None]
        
        data = scraper.fetch_data()
        
        assert 'value' in data
        assert 'individual_bdcs' in data
        assert len(data['individual_bdcs']) == 2
        assert 'ARCC' in data['individual_bdcs']
        assert 'OCSL' in data['individual_bdcs']
        
        # Check ARCC data
        arcc_data = data['individual_bdcs']['ARCC']
        assert arcc_data['stock_price'] == 25.50
        assert arcc_data['nav_value'] == 28.50
        # Discount calculation: (NAV - Price) / NAV = (28.50 - 25.50) / 28.50 = 0.105 (positive discount)
        expected_discount = (28.50 - 25.50) / 28.50  # 0.105
        assert abs(arcc_data['discount_to_nav'] - expected_discount) < 0.001
        
        # Check average calculation
        arcc_discount = (28.50 - 25.50) / 28.50  # 0.105
        ocsl_discount = (24.00 - 22.00) / 24.00  # 0.083
        expected_avg = (arcc_discount + ocsl_discount) / 2
        assert abs(data['value'] - expected_avg) < 0.001
    
    @patch.object(BDCDiscountScraper, '_fetch_nav_from_rss')
    @patch.object(BDCDiscountScraper, '_fetch_stock_price')
    def test_fetch_data_no_data(self, mock_fetch_price, mock_fetch_nav, scraper):
        """Test data fetching when no data is available."""
        mock_fetch_price.return_value = None
        mock_fetch_nav.return_value = None
        
        with pytest.raises(ValueError, match="No BDC data could be retrieved"):
            scraper.fetch_data()
    
    def test_validate_data_success(self, scraper, sample_bdc_data):
        """Test successful data validation."""
        validated = scraper.validate_data(sample_bdc_data)
        assert validated == sample_bdc_data
    
    def test_validate_data_empty(self, scraper):
        """Test validation with empty data."""
        with pytest.raises(ValueError, match="No BDC data received"):
            scraper.validate_data({})
    
    def test_validate_data_missing_value(self, scraper):
        """Test validation with missing value."""
        data = {'individual_bdcs': {}}
        with pytest.raises(ValueError, match="Missing average discount value"):
            scraper.validate_data(data)
    
    def test_validate_data_invalid_value_type(self, scraper):
        """Test validation with invalid value type."""
        data = {'value': 'invalid', 'individual_bdcs': {}}
        with pytest.raises(ValueError, match="Average discount value must be numeric"):
            scraper.validate_data(data)
    
    def test_validate_data_no_individual_bdcs(self, scraper):
        """Test validation with no individual BDC data."""
        data = {'value': -0.1}
        with pytest.raises(ValueError, match="No individual BDC data available"):
            scraper.validate_data(data)
    
    def test_validate_data_incomplete_bdc_data(self, scraper):
        """Test validation with incomplete BDC data."""
        data = {
            'value': -0.1,
            'individual_bdcs': {
                'ARCC': {'stock_price': 25.50}  # Missing nav_value and discount_to_nav
            }
        }
        with pytest.raises(ValueError, match="Incomplete data for ARCC"):
            scraper.validate_data(data)
    
    def test_validate_data_invalid_prices(self, scraper):
        """Test validation with invalid price values."""
        data = {
            'value': -0.1,
            'individual_bdcs': {
                'ARCC': {
                    'stock_price': -5.0,  # Invalid negative price
                    'nav_value': 28.50,
                    'discount_to_nav': -0.1
                }
            }
        }
        with pytest.raises(ValueError, match="Invalid price/NAV values for ARCC"):
            scraper.validate_data(data)
    
    def test_should_alert_no_historical_data(self, scraper, sample_bdc_data):
        """Test alert logic with no historical data."""
        should_alert = scraper.should_alert(sample_bdc_data, None)
        assert should_alert is False
    
    def test_should_alert_no_change(self, scraper, sample_bdc_data):
        """Test alert logic with no significant change."""
        current_value = sample_bdc_data['value']  # ~0.094
        historical_data = {'value': current_value - 0.01}  # Very small change
        should_alert = scraper.should_alert(sample_bdc_data, historical_data)
        assert should_alert is False
    
    def test_should_alert_significant_change(self, scraper, sample_bdc_data):
        """Test alert logic with significant change."""
        historical_data = {'value': -0.02}  # Large change from -0.105 (8.5% change)
        should_alert = scraper.should_alert(sample_bdc_data, historical_data)
        assert should_alert is True
    
    def test_should_alert_threshold_boundary(self, scraper, sample_bdc_data):
        """Test alert logic at threshold boundary."""
        current_value = sample_bdc_data['value']  # ~0.094
        
        # Exactly at threshold (5% change)
        historical_data = {'value': current_value - 0.05}  # Change of 0.05
        should_alert = scraper.should_alert(sample_bdc_data, historical_data)
        assert should_alert is False  # Should be False because change equals threshold
        
        # Just over threshold
        historical_data = {'value': current_value - 0.051}  # Change of 0.051
        should_alert = scraper.should_alert(sample_bdc_data, historical_data)
        assert should_alert is True
    
    def test_generate_alert_message(self, scraper, sample_bdc_data):
        """Test alert message generation."""
        current_value = sample_bdc_data['value']  # ~0.094
        historical_data = {'value': current_value - 0.08}  # Previous discount was smaller
        
        alert = scraper.generate_alert_message(sample_bdc_data, historical_data)
        
        assert alert['alert_type'] == 'bdc_discount_change'
        assert alert['data_source'] == 'bdc_discount'
        assert alert['metric'] == 'discount_to_nav'
        assert abs(alert['current_value'] - current_value) < 0.001
        assert abs(alert['previous_value'] - (current_value - 0.08)) < 0.001
        # Change should be current - previous = ~0.08
        assert abs(alert['change'] - 0.08) < 0.001
        assert alert['severity'] == 'medium'  # 8% change
        assert 'increased significantly' in alert['message']
        assert 'ARCC: 10.53%' in alert['message']
        assert 'OCSL: 8.33%' in alert['message']
        
        # Test context
        assert alert['context']['bdc_count'] == 2
        assert alert['context']['symbols'] == ['ARCC', 'OCSL']
        assert alert['context']['data_quality'] == 'medium'
    
    def test_generate_alert_message_high_severity(self, scraper, sample_bdc_data):
        """Test alert message with high severity."""
        current_value = sample_bdc_data['value']  # ~0.094
        historical_data = {'value': current_value - 0.12}  # Large change for high severity
        
        alert = scraper.generate_alert_message(sample_bdc_data, historical_data)
        
        assert alert['severity'] == 'high'  # >10% change
        assert abs(alert['change'] - 0.12) < 0.001
    
    def test_generate_alert_message_increase(self, scraper, sample_bdc_data):
        """Test alert message for discount increase."""
        # Modify sample data to show smaller discount
        sample_bdc_data['value'] = 0.02  # Small discount
        historical_data = {'value': 0.10}  # Previous discount was larger
        
        alert = scraper.generate_alert_message(sample_bdc_data, historical_data)
        
        assert 'decreased significantly' in alert['message']  # Discount decreased (less discount)
        assert abs(alert['change'] - (-0.08)) < 0.001  # 0.02 - 0.10 = -0.08
    
    @patch.object(BDCDiscountScraper, '_fetch_nav_from_rss')
    @patch.object(BDCDiscountScraper, '_fetch_stock_price')
    def test_integration_fetch_and_validate(self, mock_fetch_price, mock_fetch_nav, scraper):
        """Test integration of fetch_data and validate_data."""
        mock_fetch_price.side_effect = [25.50, None, None, None]  # Only ARCC succeeds
        mock_fetch_nav.side_effect = [28.50, None, None, None]
        
        data = scraper.fetch_data()
        validated_data = scraper.validate_data(data)
        
        assert validated_data['bdc_count'] == 1
        assert 'ARCC' in validated_data['individual_bdcs']
        assert validated_data['metadata']['data_quality'] == 'medium'  # Only 1 BDC < 3