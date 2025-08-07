"""
Unit tests for BankProvisionScraper.

Tests the bank provision scraper functionality including XBRL parsing,
transcript analysis, and alert generation.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone
import xml.etree.ElementTree as ET

from scrapers.bank_provision_scraper import BankProvisionScraper


class TestBankProvisionScraper:
    """Test cases for BankProvisionScraper."""
    
    @pytest.fixture
    def scraper(self):
        """Create a BankProvisionScraper instance for testing."""
        return BankProvisionScraper()
    
    @pytest.fixture
    def mock_xbrl_content(self):
        """Mock XBRL content with credit loss allowances."""
        return """<?xml version="1.0" encoding="UTF-8"?>
        <xbrl xmlns:xbrli="http://www.xbrl.org/2003/instance" 
              xmlns:us-gaap="http://fasb.org/us-gaap/2023">
            <xbrli:context id="c1">
                <xbrli:entity>
                    <xbrli:identifier scheme="http://www.sec.gov/CIK">0000019617</xbrli:identifier>
                </xbrli:entity>
                <xbrli:period>
                    <xbrli:instant>2024-03-31</xbrli:instant>
                </xbrli:period>
                <xbrli:segment>
                    <us-gaap:StatementBusinessSegmentsAxis>NonBankFinancial</us-gaap:StatementBusinessSegmentsAxis>
                </xbrli:segment>
            </xbrli:context>
            <us-gaap:AllowanceForCreditLosses contextRef="c1">315000000</us-gaap:AllowanceForCreditLosses>
            <us-gaap:ProvisionForCreditLosses contextRef="c1">2100000000</us-gaap:ProvisionForCreditLosses>
        </xbrl>"""
    
    @pytest.fixture
    def mock_filing_page_content(self):
        """Mock SEC filing page content with XBRL links."""
        return """
        <html>
        <body>
            <div class="formGrouping">
                <a href="jpm-20240331_htm.xml">XBRL Instance Document</a>
                <a href="jpm-20240331.htm">HTML Document</a>
            </div>
        </body>
        </html>
        """
    
    @pytest.fixture
    def mock_atom_feed(self):
        """Mock SEC EDGAR Atom feed response."""
        return """<?xml version="1.0" encoding="UTF-8"?>
        <feed xmlns="http://www.w3.org/2005/Atom">
            <entry>
                <title>10-Q - Quarterly report [Sections 13 or 15(d)]</title>
                <link rel="alternate" href="https://www.sec.gov/Archives/edgar/data/19617/000001961724000123/0000019617-24-000123-index.htm"/>
                <updated>2024-04-15T16:30:00-04:00</updated>
            </entry>
        </feed>"""
    
    def test_init(self, scraper):
        """Test scraper initialization."""
        assert scraper.data_source == 'bank_provision'
        assert scraper.metric_name == 'non_bank_financial_provisions'
        assert scraper.ALERT_THRESHOLD == 0.20
        assert len(scraper.BANK_CIKS) == 6
        assert 'JPM' in scraper.BANK_CIKS.values()
    
    @patch('scrapers.bank_provision_scraper.BankProvisionScraper._get_latest_10q_filing')
    @patch('scrapers.bank_provision_scraper.BankProvisionScraper._parse_xbrl_provisions')
    def test_fetch_data_success(self, mock_parse_xbrl, mock_get_filing, scraper):
        """Test successful data fetching from XBRL."""
        # Mock filing URL retrieval
        mock_get_filing.return_value = "https://sec.gov/filing.htm"
        
        # Mock XBRL parsing to return provision amounts
        mock_parse_xbrl.side_effect = [315000000, 270000000, None, None, None, None]
        
        result = scraper.fetch_data()
        
        assert result['value'] == 585000000  # 315M + 270M
        assert result['bank_count'] == 2
        assert 'individual_banks' in result
        assert 'JPM' in result['individual_banks']
        assert 'BAC' in result['individual_banks']
        assert result['metadata']['data_quality'] == 'medium'  # < 4 banks
    
    @patch('scrapers.bank_provision_scraper.BankProvisionScraper._get_latest_10q_filing')
    @patch('scrapers.bank_provision_scraper.BankProvisionScraper._parse_xbrl_provisions')
    @patch('scrapers.bank_provision_scraper.BankProvisionScraper._analyze_earnings_transcript')
    def test_fetch_data_with_transcript_fallback(self, mock_transcript, mock_parse_xbrl, mock_get_filing, scraper):
        """Test data fetching with transcript analysis fallback."""
        # Mock filing URL retrieval
        mock_get_filing.return_value = "https://sec.gov/filing.htm"
        
        # Mock XBRL parsing to fail for first bank, succeed for second
        mock_parse_xbrl.side_effect = [None, 270000000, None, None, None, None]
        
        # Mock transcript analysis to succeed for first bank
        mock_transcript.side_effect = [225000000, None, None, None, None, None]
        
        result = scraper.fetch_data()
        
        assert result['value'] == 495000000  # 225M + 270M
        assert result['bank_count'] == 2
        assert result['individual_banks']['JPM']['data_source'] == 'transcript'
        assert result['individual_banks']['BAC']['data_source'] == 'xbrl'
    
    @patch('scrapers.bank_provision_scraper.BankProvisionScraper._get_latest_10q_filing')
    def test_fetch_data_no_data(self, mock_get_filing, scraper):
        """Test fetch_data when no data is available."""
        # Mock no filings found
        mock_get_filing.return_value = None
        
        with pytest.raises(ValueError, match="No bank provision data could be retrieved"):
            scraper.fetch_data()
    
    @patch('requests.Session.get')
    def test_get_latest_10q_filing_success(self, mock_get, scraper, mock_atom_feed):
        """Test successful retrieval of latest 10-Q filing URL."""
        mock_response = Mock()
        mock_response.content = mock_atom_feed.encode()
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = scraper._get_latest_10q_filing('0000019617')
        
        assert result == "https://www.sec.gov/Archives/edgar/data/19617/000001961724000123/0000019617-24-000123-index.htm"
        mock_get.assert_called_once()
    
    @patch('requests.Session.get')
    def test_get_latest_10q_filing_no_results(self, mock_get, scraper):
        """Test when no 10-Q filings are found."""
        mock_response = Mock()
        mock_response.content = b'<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom"></feed>'
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = scraper._get_latest_10q_filing('0000019617')
        
        assert result is None
    
    @patch('requests.Session.get')
    def test_parse_xbrl_provisions_success(self, mock_get, scraper, mock_filing_page_content, mock_xbrl_content):
        """Test successful XBRL parsing for provisions."""
        # Mock filing page response
        filing_response = Mock()
        filing_response.content = mock_filing_page_content.encode()
        filing_response.raise_for_status.return_value = None
        
        # Mock XBRL document response
        xbrl_response = Mock()
        xbrl_response.content = mock_xbrl_content.encode()
        xbrl_response.raise_for_status.return_value = None
        
        mock_get.side_effect = [filing_response, xbrl_response]
        
        result = scraper._parse_xbrl_provisions("https://sec.gov/filing.htm", "JPM")
        
        assert result == 315000000  # From mock XBRL content
        assert mock_get.call_count == 2
    
    @patch('requests.Session.get')
    def test_parse_xbrl_provisions_no_xbrl_link(self, mock_get, scraper):
        """Test XBRL parsing when no XBRL link is found."""
        mock_response = Mock()
        mock_response.content = b'<html><body>No XBRL links here</body></html>'
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = scraper._parse_xbrl_provisions("https://sec.gov/filing.htm", "JPM")
        
        assert result is None
    
    def test_extract_credit_loss_allowance(self, scraper, mock_xbrl_content):
        """Test extraction of credit loss allowance from XBRL."""
        root = ET.fromstring(mock_xbrl_content)
        namespaces = {
            'us-gaap': 'http://fasb.org/us-gaap/2023',
            'xbrli': 'http://www.xbrl.org/2003/instance'
        }
        
        result = scraper._extract_credit_loss_allowance(root, namespaces, "JPM")
        
        assert result == 315000000
    
    def test_is_non_bank_financial_context(self, scraper, mock_xbrl_content):
        """Test identification of non-bank financial context."""
        root = ET.fromstring(mock_xbrl_content)
        namespaces = {
            'us-gaap': 'http://fasb.org/us-gaap/2023',
            'xbrli': 'http://www.xbrl.org/2003/instance'
        }
        
        result = scraper._is_non_bank_financial_context(root, "c1", namespaces)
        
        assert result is True  # Mock content has NonBankFinancial segment
    
    def test_get_total_provisions(self, scraper, mock_xbrl_content):
        """Test extraction of total provisions from XBRL."""
        root = ET.fromstring(mock_xbrl_content)
        namespaces = {
            'us-gaap': 'http://fasb.org/us-gaap/2023',
            'xbrli': 'http://www.xbrl.org/2003/instance'
        }
        
        result = scraper._get_total_provisions(root, namespaces)
        
        assert result == 2100000000
    
    def test_get_simulated_transcript(self, scraper):
        """Test getting simulated transcript content."""
        result = scraper._get_simulated_transcript("JPM")
        
        assert result is not None
        assert "non-bank financial" in result.lower()
        assert "$315 million" in result
    
    def test_extract_provisions_from_transcript(self, scraper):
        """Test extraction of provision amounts from transcript text."""
        transcript = """
        Our provision for credit losses this quarter was $2.1 billion, with approximately 
        $315 million specifically related to our non-bank financial exposures, including 
        hedge funds and private equity counterparties.
        """
        
        result = scraper._extract_provisions_from_transcript(transcript)
        
        assert result == 315000000  # $315 million
    
    def test_extract_provisions_from_transcript_billion(self, scraper):
        """Test extraction when amount is in billions."""
        transcript = """
        We allocated roughly $1.2 billion for provisions against non-bank financial institutions.
        """
        
        result = scraper._extract_provisions_from_transcript(transcript)
        
        assert result == 1200000000  # $1.2 billion
    
    def test_extract_provisions_from_transcript_no_match(self, scraper):
        """Test extraction when no provision amounts are found."""
        transcript = """
        We had a good quarter with strong performance across all segments.
        """
        
        result = scraper._extract_provisions_from_transcript(transcript)
        
        assert result is None
    
    def test_get_current_quarter(self, scraper):
        """Test current quarter calculation."""
        with patch('scrapers.bank_provision_scraper.datetime') as mock_datetime:
            mock_datetime.utcnow.return_value = datetime(2024, 4, 15)  # Q2 2024
            
            result = scraper._get_current_quarter()
            
            assert result == "Q2 2024"
    
    def test_validate_data_success(self, scraper):
        """Test successful data validation."""
        data = {
            'value': 585000000,
            'bank_count': 4,
            'individual_banks': {
                'JPM': {'provisions': 315000000},
                'BAC': {'provisions': 270000000},
                'WFC': {'provisions': 0},
                'C': {'provisions': 0}
            },
            'metadata': {
                'extraction_methods': {'xbrl': 3, 'transcript': 1}
            }
        }
        
        result = scraper.validate_data(data)
        
        assert result['confidence'] == 0.95  # High confidence
        assert result['value'] == 585000000
    
    def test_validate_data_missing_value(self, scraper):
        """Test validation with missing value."""
        data = {'bank_count': 2}
        
        with pytest.raises(ValueError, match="Missing total provisions value"):
            scraper.validate_data(data)
    
    def test_validate_data_invalid_provisions(self, scraper):
        """Test validation with invalid provision amounts."""
        data = {
            'value': 585000000,
            'individual_banks': {
                'JPM': {'provisions': -100000}  # Negative provisions
            }
        }
        
        with pytest.raises(ValueError, match="Invalid provisions amount for JPM"):
            scraper.validate_data(data)
    
    def test_should_alert_no_historical_data(self, scraper):
        """Test alert logic with no historical data."""
        current_data = {'value': 585000000}
        
        result = scraper.should_alert(current_data, None)
        
        assert result is False
    
    def test_should_alert_below_threshold(self, scraper):
        """Test alert logic below threshold."""
        current_data = {'value': 550000000}
        historical_data = {'value': 500000000}  # 10% increase
        
        result = scraper.should_alert(current_data, historical_data)
        
        assert result is False
    
    def test_should_alert_above_threshold(self, scraper):
        """Test alert logic above threshold."""
        current_data = {'value': 650000000}
        historical_data = {'value': 500000000}  # 30% increase
        
        result = scraper.should_alert(current_data, historical_data)
        
        assert result is True
    
    def test_generate_alert_message(self, scraper):
        """Test alert message generation."""
        current_data = {
            'value': 650000000,
            'bank_count': 2,
            'individual_banks': {
                'JPM': {'provisions': 400000000, 'data_source': 'xbrl'},
                'BAC': {'provisions': 250000000, 'data_source': 'transcript'}
            },
            'metadata': {
                'quarter': 'Q2 2024',
                'data_quality': 'high',
                'extraction_methods': {'xbrl': 1, 'transcript': 1}
            },
            'confidence': 0.85
        }
        historical_data = {'value': 500000000}
        
        result = scraper.generate_alert_message(current_data, historical_data)
        
        assert result['alert_type'] == 'bank_provision_increase'
        assert result['severity'] == 'medium'  # 30% increase
        assert result['current_value'] == 650000000
        assert result['previous_value'] == 500000000
        assert result['change'] == 150000000
        assert result['change_percentage'] == 30.0
        assert 'JPM: $400,000,000' in result['message']
        assert 'BAC: $250,000,000' in result['message']
        assert result['context']['bank_count'] == 2
        assert result['context']['quarter'] == 'Q2 2024'
    
    def test_generate_alert_message_high_severity(self, scraper):
        """Test alert message with high severity."""
        current_data = {
            'value': 800000000,
            'bank_count': 1,
            'individual_banks': {
                'JPM': {'provisions': 800000000, 'data_source': 'xbrl'}
            },
            'metadata': {'quarter': 'Q2 2024'},
            'confidence': 0.95
        }
        historical_data = {'value': 500000000}  # 60% increase
        
        result = scraper.generate_alert_message(current_data, historical_data)
        
        assert result['severity'] == 'high'
        assert result['change_percentage'] == 60.0


class TestBankProvisionScraperIntegration:
    """Integration tests for BankProvisionScraper."""
    
    @pytest.fixture
    def scraper(self):
        """Create a BankProvisionScraper instance for testing."""
        return BankProvisionScraper()
    
    @patch('scrapers.bank_provision_scraper.BankProvisionScraper._get_latest_10q_filing')
    @patch('scrapers.bank_provision_scraper.BankProvisionScraper._parse_xbrl_provisions')
    @patch('scrapers.bank_provision_scraper.BankProvisionScraper._analyze_earnings_transcript')
    def test_full_execution_flow(self, mock_transcript, mock_parse_xbrl, mock_get_filing, scraper):
        """Test complete execution flow from fetch to alert."""
        # Mock successful data fetching
        mock_get_filing.return_value = "https://sec.gov/filing.htm"
        mock_parse_xbrl.side_effect = [315000000, 270000000, None, None, None, None]
        mock_transcript.side_effect = [None, None, 225000000, 180000000, None, None]
        
        # Mock state store and alert service
        with patch.object(scraper, 'state_store') as mock_state_store, \
             patch.object(scraper, 'alert_service') as mock_alert_service, \
             patch.object(scraper, 'metrics_service') as mock_metrics_service:
            
            # Mock historical data that would trigger an alert
            mock_state_store.get_latest_value.return_value = {'value': 600000000}
            
            # Execute the scraper
            result = scraper.execute()
            
            # Verify successful execution
            assert result.success is True
            assert result.data['value'] == 990000000  # 315M + 270M + 225M + 180M
            assert result.data['bank_count'] == 4
            
            # Verify alert was triggered (67% increase: 990M vs 600M)
            mock_alert_service.send_alert.assert_called_once()
            
            # Verify data was saved
            mock_state_store.save_data.assert_called_once()
            
            # Verify metrics were sent
            mock_metrics_service.send_metric.assert_called_once()