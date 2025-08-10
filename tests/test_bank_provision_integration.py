"""
Integration tests for BankProvisionScraper.

Tests the bank provision scraper with realistic data scenarios and
end-to-end functionality.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone
import xml.etree.ElementTree as ET

from scrapers.bank_provision_scraper import BankProvisionScraper
from models.core import ScraperResult


class TestBankProvisionScraperIntegration:
    """Integration tests for BankProvisionScraper."""
    
    @pytest.fixture
    def scraper(self):
        """Create a BankProvisionScraper instance for testing."""
        return BankProvisionScraper()
    
    @pytest.fixture
    def realistic_xbrl_content(self):
        """Realistic XBRL content based on actual bank filings."""
        return """<?xml version="1.0" encoding="UTF-8"?>
        <xbrl xmlns:xbrli="http://www.xbrl.org/2003/instance" 
              xmlns:us-gaap="http://fasb.org/us-gaap/2023"
              xmlns:jpm="http://www.jpmorganchase.com/20240331">
            
            <!-- Context for non-bank financial segment -->
            <xbrli:context id="c_NonBankFinancial_Q1_2024">
                <xbrli:entity>
                    <xbrli:identifier scheme="http://www.sec.gov/CIK">0000019617</xbrli:identifier>
                </xbrli:entity>
                <xbrli:period>
                    <xbrli:startDate>2024-01-01</xbrli:startDate>
                    <xbrli:endDate>2024-03-31</xbrli:endDate>
                </xbrli:period>
                <xbrli:segment>
                    <xbrli:explicitMember dimension="us-gaap:StatementBusinessSegmentsAxis">
                        jpm:NonBankFinancialMember
                    </xbrli:explicitMember>
                </xbrli:segment>
            </xbrli:context>
            
            <!-- Context for total provisions -->
            <xbrli:context id="c_Total_Q1_2024">
                <xbrli:entity>
                    <xbrli:identifier scheme="http://www.sec.gov/CIK">0000019617</xbrli:identifier>
                </xbrli:entity>
                <xbrli:period>
                    <xbrli:startDate>2024-01-01</xbrli:startDate>
                    <xbrli:endDate>2024-03-31</xbrli:endDate>
                </xbrli:period>
            </xbrli:context>
            
            <!-- Non-bank financial provisions -->
            <us-gaap:AllowanceForCreditLosses contextRef="c_NonBankFinancial_Q1_2024" unitRef="usd">
                315000000
            </us-gaap:AllowanceForCreditLosses>
            
            <!-- Total provisions for reference -->
            <us-gaap:ProvisionForCreditLosses contextRef="c_Total_Q1_2024" unitRef="usd">
                2100000000
            </us-gaap:ProvisionForCreditLosses>
            
            <xbrli:unit id="usd">
                <xbrli:measure>iso4217:USD</xbrli:measure>
            </xbrli:unit>
        </xbrl>"""
    
    @pytest.fixture
    def realistic_filing_page(self):
        """Realistic SEC filing page with XBRL links."""
        return """
        <!DOCTYPE html>
        <html>
        <head><title>JPMorgan Chase &amp; Co. 10-Q</title></head>
        <body>
            <div class="formGrouping">
                <div class="formContent">
                    <h4>Documents</h4>
                    <table>
                        <tr>
                            <td><a href="jpm-20240331.htm">10-Q</a></td>
                            <td>HTML</td>
                        </tr>
                        <tr>
                            <td><a href="jpm-20240331_htm.xml">XBRL Instance Document</a></td>
                            <td>XML</td>
                        </tr>
                        <tr>
                            <td><a href="jpm-20240331_cal.xml">XBRL Calculation Linkbase</a></td>
                            <td>XML</td>
                        </tr>
                    </table>
                </div>
            </div>
        </body>
        </html>
        """
    
    @pytest.fixture
    def realistic_atom_feed(self):
        """Realistic SEC EDGAR Atom feed with multiple filings."""
        return """<?xml version="1.0" encoding="UTF-8"?>
        <feed xmlns="http://www.w3.org/2005/Atom">
            <title>Recent Filings for JPMorgan Chase &amp; Co.</title>
            <entry>
                <title>10-Q - Quarterly report [Sections 13 or 15(d)]</title>
                <link rel="alternate" href="https://www.sec.gov/Archives/edgar/data/19617/000001961724000123/0000019617-24-000123-index.htm"/>
                <updated>2024-04-15T16:30:00-04:00</updated>
                <summary>Form 10-Q for the quarterly period ended March 31, 2024</summary>
            </entry>
            <entry>
                <title>8-K - Current report</title>
                <link rel="alternate" href="https://www.sec.gov/Archives/edgar/data/19617/000001961724000122/0000019617-24-000122-index.htm"/>
                <updated>2024-04-12T08:15:00-04:00</updated>
            </entry>
        </feed>"""
    
    @pytest.fixture
    def realistic_transcript_content(self):
        """Realistic earnings call transcript content."""
        return {
            'JPM': """
            Thank you, operator. Good morning, everyone, and thank you for joining our first quarter 2024 earnings call.
            
            Starting with our credit metrics, our provision for credit losses this quarter was $2.1 billion, 
            reflecting our continued cautious approach to credit risk. Within this total, approximately 
            $315 million was specifically allocated to provisions for our non-bank financial exposures, 
            including hedge funds, private equity firms, and other asset managers where we've seen some 
            stress in the current market environment.
            
            Our exposure to non-bank financials has grown over the past year as we've expanded our 
            prime brokerage and securities lending businesses. While these relationships are generally 
            well-collateralized, we're taking a prudent approach to provisioning given the volatility 
            we're seeing in certain market segments.
            """,
            'BAC': """
            Good morning and thank you for joining our first quarter earnings call. I'm pleased to 
            report solid results across our key business segments.
            
            Turning to credit, our total provision expense was $1.8 billion for the quarter, up from 
            $1.5 billion in the prior quarter. This increase reflects both loan growth and a more 
            cautious outlook for certain sectors. Specifically, we allocated roughly $270 million 
            for provisions against our non-bank financial institution exposures, primarily asset 
            managers and broker-dealers where we're seeing some pressure from market conditions.
            
            We continue to monitor these exposures closely, particularly given the interconnected 
            nature of the financial services ecosystem and potential for contagion effects.
            """
        }
    
    @patch('requests.Session.get')
    def test_realistic_xbrl_parsing_flow(self, mock_get, scraper, realistic_atom_feed, 
                                       realistic_filing_page, realistic_xbrl_content):
        """Test realistic XBRL parsing flow with actual-like data."""
        # Mock the sequence of HTTP requests
        atom_response = Mock()
        atom_response.content = realistic_atom_feed.encode()
        atom_response.raise_for_status.return_value = None
        
        filing_response = Mock()
        filing_response.content = realistic_filing_page.encode()
        filing_response.raise_for_status.return_value = None
        
        xbrl_response = Mock()
        xbrl_response.content = realistic_xbrl_content.encode()
        xbrl_response.raise_for_status.return_value = None
        
        mock_get.side_effect = [atom_response, filing_response, xbrl_response]
        
        # Test the XBRL parsing flow
        filing_url = scraper._get_latest_10q_filing('0000019617')
        assert filing_url is not None
        
        provisions = scraper._parse_xbrl_provisions(filing_url, 'JPM')
        assert provisions == 315000000
        
        # Verify all expected requests were made
        assert mock_get.call_count == 3
    
    def test_realistic_transcript_analysis(self, scraper, realistic_transcript_content):
        """Test transcript analysis with realistic content."""
        # Mock the transcript retrieval
        with patch.object(scraper, '_get_simulated_transcript') as mock_transcript:
            mock_transcript.return_value = realistic_transcript_content['JPM']
            
            result = scraper._analyze_earnings_transcript('JPM')
            
            assert result == 315000000  # $315 million extracted from transcript
    
    @patch('scrapers.bank_provision_scraper.BankProvisionScraper._get_latest_10q_filing')
    @patch('scrapers.bank_provision_scraper.BankProvisionScraper._parse_xbrl_provisions')
    @patch('scrapers.bank_provision_scraper.BankProvisionScraper._analyze_earnings_transcript')
    def test_mixed_data_sources_scenario(self, mock_transcript, mock_parse_xbrl, 
                                       mock_get_filing, scraper, realistic_transcript_content):
        """Test scenario with mixed XBRL and transcript data sources."""
        # Mock filing URLs available for all banks
        mock_get_filing.return_value = "https://sec.gov/filing.htm"
        
        # Mock XBRL success for some banks, failure for others
        mock_parse_xbrl.side_effect = [
            315000000,  # JPM - XBRL success
            None,       # BAC - XBRL failure
            225000000,  # WFC - XBRL success
            None,       # C - XBRL failure
            None,       # GS - XBRL failure
            180000000   # MS - XBRL success
        ]
        
        # Mock transcript analysis for failed XBRL cases
        mock_transcript.side_effect = [
            None,       # JPM - not called (XBRL succeeded)
            270000000,  # BAC - transcript success
            None,       # WFC - not called (XBRL succeeded)
            200000000,  # C - transcript success
            150000000,  # GS - transcript success
            None        # MS - not called (XBRL succeeded)
        ]
        
        result = scraper.fetch_data()
        
        # Verify mixed data sources
        # JPM: 315M (XBRL), WFC: 225M (XBRL), C: 270M (transcript), MS: 180M (XBRL)
        # BAC and GS fail both XBRL and transcript
        assert result['value'] == 990000000  # 315M + 225M + 270M + 180M
        assert result['bank_count'] == 4
        
        # Check data source attribution (only successful banks)
        individual_banks = result['individual_banks']
        assert individual_banks['JPM']['data_source'] == 'xbrl'
        assert individual_banks['WFC']['data_source'] == 'xbrl'
        assert individual_banks['C']['data_source'] == 'transcript'
        assert individual_banks['MS']['data_source'] == 'xbrl'
        
        # BAC and GS should not be in results since they failed
        assert 'BAC' not in individual_banks
        assert 'GS' not in individual_banks
        
        # Check extraction method counts
        extraction_methods = result['metadata']['extraction_methods']
        assert extraction_methods['xbrl'] == 3
        assert extraction_methods['transcript'] == 1
    
    @patch('scrapers.bank_provision_scraper.BankProvisionScraper._get_latest_10q_filing')
    @patch('scrapers.bank_provision_scraper.BankProvisionScraper._parse_xbrl_provisions')
    def test_high_confidence_scenario(self, mock_parse_xbrl, mock_get_filing, scraper):
        """Test scenario that should result in high confidence rating."""
        # Mock successful XBRL parsing for most banks
        mock_get_filing.return_value = "https://sec.gov/filing.htm"
        mock_parse_xbrl.side_effect = [
            315000000,  # JPM
            270000000,  # BAC
            225000000,  # WFC
            200000000,  # C
            None,       # GS - failed
            None        # MS - failed
        ]
        
        result = scraper.fetch_data()
        validated_result = scraper.validate_data(result)
        
        # Should have high confidence (4+ banks, 4 XBRL successes)
        assert validated_result['confidence'] == 0.95
        assert validated_result['metadata']['data_quality'] == 'high'
    
    @patch('scrapers.bank_provision_scraper.BankProvisionScraper._get_latest_10q_filing')
    @patch('scrapers.bank_provision_scraper.BankProvisionScraper._parse_xbrl_provisions')
    def test_medium_confidence_scenario(self, mock_parse_xbrl, mock_get_filing, scraper):
        """Test scenario that should result in medium confidence rating."""
        # Mock limited success
        mock_get_filing.return_value = "https://sec.gov/filing.htm"
        mock_parse_xbrl.side_effect = [
            315000000,  # JPM
            270000000,  # BAC
            None,       # WFC - failed
            None,       # C - failed
            None,       # GS - failed
            None        # MS - failed
        ]
        
        result = scraper.fetch_data()
        validated_result = scraper.validate_data(result)
        
        # Should have medium confidence (2 banks, 2 XBRL successes)
        assert validated_result['confidence'] == 0.75
        assert validated_result['metadata']['data_quality'] == 'medium'
    
    def test_alert_threshold_scenarios(self, scraper):
        """Test various alert threshold scenarios."""
        base_historical = {'value': 1000000000}  # $1B baseline
        
        # Test cases: (current_value, should_alert, expected_severity)
        test_cases = [
            (1100000000, False, None),      # 10% increase - no alert
            (1150000000, False, None),      # 15% increase - no alert
            (1250000000, True, 'low'),      # 25% increase - low severity (exactly at threshold)
            (1300000000, True, 'medium'),   # 30% increase - medium severity
            (1600000000, True, 'high'),     # 60% increase - high severity
        ]
        
        for current_value, should_alert, expected_severity in test_cases:
            current_data = {'value': current_value}
            
            # Test alert decision
            alert_result = scraper.should_alert(current_data, base_historical)
            assert alert_result == should_alert, f"Failed for {current_value}"
            
            # Test severity if alert should be triggered
            if should_alert:
                alert_message = scraper.generate_alert_message(current_data, base_historical)
                assert alert_message['severity'] == expected_severity, f"Wrong severity for {current_value}"
    
    @patch('scrapers.bank_provision_scraper.BankProvisionScraper.fetch_data')
    def test_end_to_end_execution_success(self, mock_fetch_data, scraper):
        """Test complete end-to-end execution with mocked dependencies."""
        # Mock successful data fetch
        mock_fetch_data.return_value = {
            'value': 1200000000,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'bank_count': 4,
            'individual_banks': {
                'JPM': {'provisions': 315000000, 'data_source': 'xbrl'},
                'BAC': {'provisions': 270000000, 'data_source': 'xbrl'},
                'WFC': {'provisions': 225000000, 'data_source': 'transcript'},
                'C': {'provisions': 390000000, 'data_source': 'xbrl'}
            },
            'metadata': {
                'banks_processed': ['JPM', 'BAC', 'WFC', 'C'],
                'data_quality': 'high',
                'quarter': 'Q1 2024',
                'extraction_methods': {'xbrl': 3, 'transcript': 1}
            }
        }
        
        # Mock dependencies
        with patch.object(scraper, 'state_store') as mock_state_store, \
             patch.object(scraper, 'alert_service') as mock_alert_service, \
             patch.object(scraper, 'metrics_service') as mock_metrics_service:
            
            # Mock historical data that triggers alert (50% increase)
            mock_state_store.get_latest_value.return_value = {'value': 800000000}
            
            # Execute scraper
            result = scraper.execute()
            
            # Verify successful execution
            assert isinstance(result, ScraperResult)
            assert result.success is True
            assert result.data_source == 'bank_provision'
            assert result.metric_name == 'non_bank_financial_provisions'
            assert result.data['value'] == 1200000000
            assert result.error is None
            
            # Verify alert was sent (50% increase should trigger alert)
            mock_alert_service.send_alert.assert_called_once()
            alert_call = mock_alert_service.send_alert.call_args[0][0]
            assert alert_call['alert_type'] == 'bank_provision_increase'
            assert alert_call['severity'] == 'medium'  # 50% increase (25-50% = medium)
            
            # Verify data was saved
            mock_state_store.save_data.assert_called_once_with(
                'bank_provision', 'non_bank_financial_provisions', result.data
            )
            
            # Verify metrics were sent
            mock_metrics_service.send_metric.assert_called_once()
    
    @patch('scrapers.bank_provision_scraper.BankProvisionScraper.fetch_data')
    def test_end_to_end_execution_failure(self, mock_fetch_data, scraper):
        """Test complete end-to-end execution with failure scenario."""
        # Mock fetch_data to raise an exception
        mock_fetch_data.side_effect = Exception("SEC EDGAR service unavailable")
        
        # Mock dependencies
        with patch.object(scraper, 'state_store') as mock_state_store, \
             patch.object(scraper, 'alert_service') as mock_alert_service, \
             patch.object(scraper, 'metrics_service') as mock_metrics_service:
            
            # Mock no fallback data available
            mock_state_store.get_latest_value.return_value = None
            
            # Execute scraper
            result = scraper.execute()
            
            # Verify failed execution
            assert isinstance(result, ScraperResult)
            assert result.success is False
            assert result.data is None
            assert "SEC EDGAR service unavailable" in result.error
            
            # Verify no alert was sent
            mock_alert_service.send_alert.assert_not_called()
            
            # Verify no data was saved
            mock_state_store.save_data.assert_not_called()
            
            # Verify error metric was attempted (may fail but should be attempted)
            mock_metrics_service.send_metric.assert_called()
    
    def test_quarter_calculation_edge_cases(self, scraper):
        """Test quarter calculation for various dates."""
        test_cases = [
            (datetime(2024, 1, 15), "Q1 2024"),   # January
            (datetime(2024, 3, 31), "Q1 2024"),   # End of Q1
            (datetime(2024, 4, 1), "Q2 2024"),    # Start of Q2
            (datetime(2024, 6, 30), "Q2 2024"),   # End of Q2
            (datetime(2024, 7, 1), "Q3 2024"),    # Start of Q3
            (datetime(2024, 9, 30), "Q3 2024"),   # End of Q3
            (datetime(2024, 10, 1), "Q4 2024"),   # Start of Q4
            (datetime(2024, 12, 31), "Q4 2024"),  # End of Q4
        ]
        
        for test_date, expected_quarter in test_cases:
            with patch('scrapers.bank_provision_scraper.datetime') as mock_datetime:
                mock_datetime.now.return_value = test_date.replace(tzinfo=timezone.utc)
                
                result = scraper._get_current_quarter()
                assert result == expected_quarter, f"Failed for {test_date}"
    
    def test_data_quality_assessment(self, scraper):
        """Test data quality assessment logic."""
        # Test high quality scenario
        high_quality_data = {
            'value': 1000000000,
            'bank_count': 5,
            'individual_banks': {f'BANK{i}': {'provisions': 200000000} for i in range(5)},
            'metadata': {'extraction_methods': {'xbrl': 4, 'transcript': 1}}
        }
        
        result = scraper.validate_data(high_quality_data)
        assert result['confidence'] == 0.95
        
        # Test medium quality scenario
        medium_quality_data = {
            'value': 600000000,
            'bank_count': 3,
            'individual_banks': {f'BANK{i}': {'provisions': 200000000} for i in range(3)},
            'metadata': {'extraction_methods': {'xbrl': 1, 'transcript': 2}}
        }
        
        result = scraper.validate_data(medium_quality_data)
        assert result['confidence'] == 0.75
        
        # Test low quality scenario
        low_quality_data = {
            'value': 200000000,
            'bank_count': 1,
            'individual_banks': {'BANK1': {'provisions': 200000000}},
            'metadata': {'extraction_methods': {'xbrl': 0, 'transcript': 1}}
        }
        
        result = scraper.validate_data(low_quality_data)
        assert result['confidence'] == 0.5