"""
Unit tests for the BondIssuanceScraper.
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch, MagicMock
from scrapers.bond_issuance_scraper import BondIssuanceScraper


class TestBondIssuanceScraper:
    """Test cases for BondIssuanceScraper."""
    
    @pytest.fixture
    def scraper(self):
        """Create a BondIssuanceScraper instance for testing."""
        with patch('scrapers.bond_issuance_scraper.Downloader'):
            return BondIssuanceScraper()
    
    @pytest.fixture
    def mock_sec_response(self):
        """Mock SEC filing response data."""
        return {
            'filings': [
                {
                    'cik': '0000789019',  # MSFT
                    'form_type': '424B2',
                    'filing_date': datetime.now().date() - timedelta(days=1),
                    'document_url': 'https://www.sec.gov/Archives/edgar/data/789019/sample.htm',
                    'content': '''
                    <html>
                    <body>
                    <p>This prospectus relates to the offering of $2,000,000,000 aggregate principal amount of 
                    4.5% Senior Notes due 2034.</p>
                    <p>The notes will bear interest at a rate of 4.5% per annum.</p>
                    </body>
                    </html>
                    '''
                },
                {
                    'cik': '0001326801',  # META
                    'form_type': '424B5',
                    'filing_date': datetime.now().date() - timedelta(days=2),
                    'document_url': 'https://www.sec.gov/Archives/edgar/data/1326801/sample.htm',
                    'content': '''
                    <html>
                    <body>
                    <p>Principal amount: $1,500,000,000</p>
                    <p>Interest rate: 4.2% per annum</p>
                    </body>
                    </html>
                    '''
                }
            ]
        }
    
    def test_init(self, scraper):
        """Test scraper initialization."""
        assert scraper.data_source == 'bond_issuance'
        assert scraper.metric_name == 'weekly'
        assert scraper.ALERT_THRESHOLD == 5_000_000_000
        assert len(scraper.TECH_COMPANY_CIKS) == 4
    
    def test_extract_notional_amount_aggregate_principal(self, scraper):
        """Test notional amount extraction with aggregate principal pattern."""
        text = "This prospectus relates to $2,000,000,000 aggregate principal amount"
        result = scraper._extract_notional_amount(text)
        assert result == 2_000_000_000
    
    def test_extract_notional_amount_principal_amount(self, scraper):
        """Test notional amount extraction with principal amount pattern."""
        text = "Principal amount: $1,500,000,000"
        result = scraper._extract_notional_amount(text)
        assert result == 1_500_000_000
    
    def test_extract_notional_amount_billion_format(self, scraper):
        """Test notional amount extraction with billion format."""
        text = "The offering consists of $2.5 billion of senior notes"
        result = scraper._extract_notional_amount(text)
        assert result == 2_500_000_000
    
    def test_extract_notional_amount_million_format(self, scraper):
        """Test notional amount extraction with million format."""
        text = "The offering consists of $500 million of senior notes"
        result = scraper._extract_notional_amount(text)
        assert result == 500_000_000
    
    def test_extract_notional_amount_no_match(self, scraper):
        """Test notional amount extraction when no pattern matches."""
        text = "This is a prospectus with no amount information"
        result = scraper._extract_notional_amount(text)
        assert result is None
    
    def test_extract_coupon_rate_per_annum(self, scraper):
        """Test coupon rate extraction with per annum pattern."""
        text = "The notes will bear interest at 4.5% per annum"
        result = scraper._extract_coupon_rate(text)
        assert result == 4.5
    
    def test_extract_coupon_rate_interest_rate(self, scraper):
        """Test coupon rate extraction with interest rate pattern."""
        text = "interest at a rate of 3.75%"
        result = scraper._extract_coupon_rate(text)
        assert result == 3.75
    
    def test_extract_coupon_rate_senior_notes(self, scraper):
        """Test coupon rate extraction with senior notes pattern."""
        text = "4.25% Senior Notes due 2034"
        result = scraper._extract_coupon_rate(text)
        assert result == 4.25
    
    def test_extract_coupon_rate_no_match(self, scraper):
        """Test coupon rate extraction when no pattern matches."""
        text = "This is a prospectus with no coupon information"
        result = scraper._extract_coupon_rate(text)
        assert result is None
    
    def test_parse_prospectus_success(self, scraper):
        """Test successful prospectus parsing."""
        filing = {
            'filing_date': datetime.now().date(),
            'form_type': '424B2',
            'document_url': 'https://example.com/filing.htm',
            'content': '''
            <html>
            <body>
            <p>$2,000,000,000 aggregate principal amount of 4.5% Senior Notes</p>
            <p>The notes will bear interest at a rate of 4.5% per annum.</p>
            </body>
            </html>
            '''
        }
        
        result = scraper._parse_prospectus(filing)
        
        assert result is not None
        assert result['notional_amount'] == 2_000_000_000
        assert result['coupon_rate'] == 4.5
        assert result['form_type'] == '424B2'
        assert result['filing_date'] == filing['filing_date']
    
    def test_parse_prospectus_no_notional(self, scraper):
        """Test prospectus parsing when notional amount is missing."""
        filing = {
            'filing_date': datetime.now().date(),
            'form_type': '424B2',
            'content': '<html><body><p>No amount information</p></body></html>'
        }
        
        result = scraper._parse_prospectus(filing)
        assert result is None
    
    def test_parse_prospectus_empty_content(self, scraper):
        """Test prospectus parsing with empty content."""
        filing = {
            'filing_date': datetime.now().date(),
            'form_type': '424B2',
            'content': ''
        }
        
        result = scraper._parse_prospectus(filing)
        assert result is None
    
    @patch.object(BondIssuanceScraper, '_get_424b_filings')
    def test_fetch_data_success(self, mock_get_filings, scraper):
        """Test successful data fetching."""
        # Mock filing data
        mock_filings = [
            {
                'cik': '0000789019',
                'form_type': '424B2',
                'filing_date': datetime.now().date() - timedelta(days=1),
                'document_url': 'https://example.com/msft.htm',
                'content': scraper._generate_sample_prospectus_content(2_000_000_000, 4.5)
            },
            {
                'cik': '0001326801',
                'form_type': '424B5',
                'filing_date': datetime.now().date() - timedelta(days=2),
                'document_url': 'https://example.com/meta.htm',
                'content': scraper._generate_sample_prospectus_content(1_500_000_000, 4.2)
            }
        ]
        
        # Configure mock to return different filings for different CIKs
        def mock_get_filings_side_effect(cik, start_date, end_date):
            if cik == '0000789019':  # MSFT
                return [mock_filings[0]]
            elif cik == '0001326801':  # META
                return [mock_filings[1]]
            else:
                return []
        
        mock_get_filings.side_effect = mock_get_filings_side_effect
        
        result = scraper.fetch_data()
        
        assert result['value'] == 3_500_000_000  # 2B + 1.5B
        assert result['confidence'] == 0.95
        assert 'MSFT' in result['metadata']['companies']
        assert 'META' in result['metadata']['companies']
        assert result['metadata']['bond_count'] == 2
        assert result['metadata']['avg_coupon'] == 4.35  # (4.5 + 4.2) / 2
        assert result['metadata']['source'] == 'sec_edgar'
    
    @patch.object(BondIssuanceScraper, '_get_424b_filings')
    def test_fetch_data_no_filings(self, mock_get_filings, scraper):
        """Test data fetching when no filings are found."""
        mock_get_filings.return_value = []
        
        result = scraper.fetch_data()
        
        assert result['value'] == 0
        assert result['confidence'] == 0.0
        assert result['metadata']['companies'] == []
        assert result['metadata']['bond_count'] == 0
        assert result['metadata']['avg_coupon'] == 0
    
    def test_validate_data_success(self, scraper):
        """Test successful data validation."""
        data = {
            'value': 2_000_000_000,
            'timestamp': datetime.now(timezone.utc),
            'confidence': 0.95,
            'metadata': {
                'companies': ['MSFT', 'META'],
                'bond_count': 2,
                'avg_coupon': 4.35
            }
        }
        
        result = scraper.validate_data(data)
        assert result == data
    
    def test_validate_data_missing_value(self, scraper):
        """Test data validation with missing value."""
        data = {
            'timestamp': datetime.now(timezone.utc),
            'metadata': {}
        }
        
        with pytest.raises(ValueError, match="Missing total notional value"):
            scraper.validate_data(data)
    
    def test_validate_data_invalid_value(self, scraper):
        """Test data validation with invalid value."""
        data = {
            'value': -1000,
            'metadata': {}
        }
        
        with pytest.raises(ValueError, match="Invalid notional amount"):
            scraper.validate_data(data)
    
    def test_validate_data_invalid_companies(self, scraper):
        """Test data validation with invalid companies list."""
        data = {
            'value': 1000000,
            'metadata': {
                'companies': 'not_a_list'
            }
        }
        
        with pytest.raises(ValueError, match="Invalid companies list"):
            scraper.validate_data(data)
    
    def test_validate_data_confidence_adjustment(self, scraper):
        """Test confidence adjustment based on bond count."""
        # Test high confidence (3+ bonds)
        data_high = {
            'value': 1000000,
            'metadata': {'companies': [], 'bond_count': 3}
        }
        result = scraper.validate_data(data_high)
        assert result['confidence'] == 0.95
        
        # Test medium confidence (1-2 bonds)
        data_medium = {
            'value': 1000000,
            'metadata': {'companies': [], 'bond_count': 1}
        }
        result = scraper.validate_data(data_medium)
        assert result['confidence'] == 0.7
        
        # Test low confidence (0 bonds)
        data_low = {
            'value': 1000000,
            'metadata': {'companies': [], 'bond_count': 0}
        }
        result = scraper.validate_data(data_low)
        assert result['confidence'] == 0.0
    
    def test_should_alert_absolute_threshold(self, scraper):
        """Test alert triggering based on absolute threshold."""
        current_data = {'value': 6_000_000_000}  # Above 5B threshold
        historical_data = {'value': 1_000_000_000}
        
        result = scraper.should_alert(current_data, historical_data)
        assert result is True
    
    def test_should_alert_increase_threshold(self, scraper):
        """Test alert triggering based on increase threshold."""
        current_data = {'value': 7_000_000_000}
        historical_data = {'value': 1_000_000_000}  # 6B increase > 5B threshold
        
        result = scraper.should_alert(current_data, historical_data)
        assert result is True
    
    def test_should_alert_no_threshold_breach(self, scraper):
        """Test no alert when thresholds are not breached."""
        current_data = {'value': 2_000_000_000}  # Below 5B threshold
        historical_data = {'value': 1_000_000_000}  # 1B increase < 5B threshold
        
        result = scraper.should_alert(current_data, historical_data)
        assert result is False
    
    def test_should_alert_no_historical_data(self, scraper):
        """Test alert logic with no historical data."""
        current_data = {'value': 6_000_000_000}  # Above threshold
        historical_data = None
        
        result = scraper.should_alert(current_data, historical_data)
        assert result is True
        
        current_data = {'value': 2_000_000_000}  # Below threshold
        result = scraper.should_alert(current_data, historical_data)
        assert result is False
    
    def test_generate_alert_message(self, scraper):
        """Test alert message generation."""
        current_data = {
            'value': 7_000_000_000,
            'confidence': 0.95,
            'metadata': {
                'companies': ['MSFT', 'META'],
                'bond_count': 2,
                'avg_coupon': 4.35
            }
        }
        historical_data = {'value': 2_000_000_000}
        
        result = scraper.generate_alert_message(current_data, historical_data)
        
        assert result['alert_type'] == 'threshold_breach'
        assert result['data_source'] == 'bond_issuance'
        assert result['metric'] == 'weekly'
        assert result['current_value'] == 7_000_000_000
        assert result['previous_value'] == 2_000_000_000
        assert result['threshold'] == 5_000_000_000
        assert result['change_percent'] == 250.0  # (7B - 2B) / 2B * 100
        assert 'MSFT' in result['message']
        assert 'META' in result['message']
        assert result['context']['companies_involved'] == ['MSFT', 'META']
        assert result['context']['bond_count'] == 2
        assert result['context']['avg_coupon'] == 4.35
        assert result['context']['data_quality'] == 'high'
    
    def test_generate_alert_message_no_historical(self, scraper):
        """Test alert message generation with no historical data."""
        current_data = {
            'value': 6_000_000_000,
            'confidence': 0.8,
            'metadata': {
                'companies': ['GOOGL'],
                'bond_count': 1,
                'avg_coupon': 4.0
            }
        }
        historical_data = None
        
        result = scraper.generate_alert_message(current_data, historical_data)
        
        assert result['previous_value'] == 0
        assert result['change_percent'] == 0
        assert result['context']['data_quality'] == 'medium'  # confidence < 0.8
    
    @patch.object(BondIssuanceScraper, '_get_424b_filings')
    def test_fetch_data_with_exception(self, mock_get_filings, scraper):
        """Test data fetching when an exception occurs for one company."""
        def mock_get_filings_side_effect(cik, start_date, end_date):
            if cik == '0000789019':  # MSFT
                raise Exception("SEC API error")
            elif cik == '0001326801':  # META
                return [{
                    'cik': cik,
                    'form_type': '424B2',
                    'filing_date': datetime.now().date(),
                    'document_url': 'https://example.com/meta.htm',
                    'content': scraper._generate_sample_prospectus_content(1_500_000_000, 4.2)
                }]
            else:
                return []
        
        mock_get_filings.side_effect = mock_get_filings_side_effect
        
        # Should continue processing other companies despite exception
        result = scraper.fetch_data()
        
        assert result['value'] == 1_500_000_000  # Only META data
        assert 'META' in result['metadata']['companies']
        assert 'MSFT' not in result['metadata']['companies']
        assert result['metadata']['bond_count'] == 1
    
    def test_simulate_filing_data(self, scraper):
        """Test the simulation of filing data."""
        start_date = datetime.now().date() - timedelta(days=7)
        end_date = datetime.now().date()
        
        # Test MSFT simulation
        msft_filings = scraper._simulate_filing_data('0000789019', start_date, end_date)
        assert len(msft_filings) == 1
        assert msft_filings[0]['cik'] == '0000789019'
        assert msft_filings[0]['form_type'] == '424B2'
        
        # Test META simulation
        meta_filings = scraper._simulate_filing_data('0001326801', start_date, end_date)
        assert len(meta_filings) == 1
        assert meta_filings[0]['cik'] == '0001326801'
        assert meta_filings[0]['form_type'] == '424B5'
        
        # Test unknown company
        unknown_filings = scraper._simulate_filing_data('0000000000', start_date, end_date)
        assert len(unknown_filings) == 0
    
    def test_generate_sample_prospectus_content(self, scraper):
        """Test sample prospectus content generation."""
        content = scraper._generate_sample_prospectus_content(2_000_000_000, 4.5)
        
        assert '$2,000,000,000' in content
        assert '4.5%' in content
        assert 'Senior Notes' in content
        assert '<html>' in content
        assert '</html>' in content


if __name__ == '__main__':
    pytest.main([__file__])