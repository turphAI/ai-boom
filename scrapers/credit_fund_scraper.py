"""
Private Credit Fund Scraper for monitoring asset marks in Form PF filings.

This scraper monitors Form PF XML filings to track gross asset values of private credit funds
and detect early signs of credit stress through sequential quarter comparisons.
"""

import logging
import os
import re
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from scrapers.base import BaseScraper


class CreditFundScraper(BaseScraper):
    """Scraper for private credit fund asset marks from Form PF filings."""
    
    # SEC EDGAR base URL for Form PF filings
    SEC_EDGAR_BASE_URL = "https://www.sec.gov/Archives/edgar/data"
    
    # Major private credit fund CIKs to monitor
    CREDIT_FUND_CIKS = {
        '0001423053': 'Apollo Global Management',
        '0001404912': 'Blackstone Inc.',
        '0001403161': 'KKR & Co. Inc.',
        '0001567228': 'Ares Management Corporation',
        '0001403256': 'Carlyle Group Inc.',
        '0001567280': 'Blue Owl Capital Inc.'
    }
    
    # Alert threshold: 10% quarter-over-quarter decline in gross asset value
    ALERT_THRESHOLD = 0.10
    
    def __init__(self):
        super().__init__('credit_fund', 'gross_asset_value')
        self.session = requests.Session()
        # SEC requires User-Agent with contact information
        import os
        sec_email = os.getenv('SEC_EDGAR_EMAIL', 'compliance@boom-bust-sentinel.com')
        self.session.headers.update({
            'User-Agent': f'BoomBustSentinel/1.0 ({sec_email})',
            'Accept-Encoding': 'gzip, deflate',
            'Host': 'www.sec.gov'
        })
    
    def fetch_data(self) -> Dict[str, Any]:
        """Fetch gross asset values from Form PF XML filings. Returns real data or raises error."""
        self.logger.info("Fetching private credit fund data from Form PF filings")
        
        fund_data = {}
        total_gross_assets = 0
        funds_processed = 0
        
        for cik, fund_name in self.CREDIT_FUND_CIKS.items():
            try:
                self.logger.info(f"Processing Form PF filings for {fund_name} (CIK: {cik})")
                
                # Rate limiting: SEC allows max 10 requests/second
                time.sleep(0.1)  # 100ms delay = 10 requests/second max
                
                # Get the most recent Form PF filing
                form_pf_data = self._get_latest_form_pf(cik)
                
                if form_pf_data:
                    gross_assets = self._extract_gross_asset_value(form_pf_data['xml_content'])
                    
                    if gross_assets is not None:
                        fund_data[cik] = {
                            'fund_name': fund_name,
                            'cik': cik,
                            'gross_asset_value': gross_assets,
                            'filing_date': form_pf_data['filing_date'],
                            'period_end_date': form_pf_data['period_end_date'],
                            'form_type': form_pf_data['form_type'],
                            'accession_number': form_pf_data['accession_number']
                        }
                        
                        total_gross_assets += gross_assets
                        funds_processed += 1
                        
                        self.logger.info(
                            f"{fund_name}: Gross assets ${gross_assets:,.0f} "
                            f"(Period: {form_pf_data['period_end_date']})"
                        )
                    else:
                        self.logger.warning(f"Could not extract gross asset value for {fund_name}")
                else:
                    self.logger.warning(f"No recent Form PF filing found for {fund_name}")
                    
            except Exception as e:
                self.logger.error(f"Error processing {fund_name}: {e}")
                continue
        
        # Allow partial data - if we have at least some funds, proceed
        if not fund_data:
            self.logger.warning(
                "No Form PF filings found for any credit funds. "
                "This may be normal if filings are not yet available or are filed infrequently."
            )
            # Try alternative sources as fallback
            alternative_data = self._try_alternative_sources()
            
            if alternative_data:
                fund_data = alternative_data
                # Recalculate totals from alternative data
                total_gross_assets = sum(
                    fund['gross_asset_value'] 
                    for fund in fund_data.values() 
                    if 'gross_asset_value' in fund
                )
                funds_processed = len(fund_data)
            else:
                # Provide helpful error message explaining why this might happen
                error_msg = (
                    "No private credit fund data could be retrieved from SEC Form PF filings "
                    "or alternative sources. This may occur if:\n"
                    "- Form PF filings are not yet publicly available (filed quarterly/annually)\n"
                    "- Filings are filed under different CIKs (subsidiaries)\n"
                    "- Filings are not yet processed by SEC EDGAR\n"
                    "- The funds may not be required to file Form PF\n\n"
                    f"Attempted to search {len(self.CREDIT_FUND_CIKS)} credit funds: "
                    f"{', '.join(self.CREDIT_FUND_CIKS.values())}"
                )
                self.logger.error(error_msg)
                raise ValueError(error_msg)
        
        avg_gross_assets = total_gross_assets / funds_processed if funds_processed > 0 else 0
        
        return {
            'value': avg_gross_assets,
            'total_gross_assets': total_gross_assets,
            'funds_processed': funds_processed,
            'individual_funds': fund_data,
            'timestamp': datetime.now(timezone.utc),
            'metadata': {
                'ciks_processed': list(fund_data.keys()),
                'data_quality': 'high' if funds_processed >= 3 else 'medium' if funds_processed >= 1 else 'low',
                'source': 'sec_form_pf' if funds_processed > 0 else 'fallback'
            }
        }
    
    def _get_latest_form_pf(self, cik: str, max_age_days: int = 365) -> Optional[Dict[str, Any]]:
        """Get the most recent Form PF filing for a given CIK.
        
        Args:
            cik: Company CIK code
            max_age_days: Maximum age of filing to accept (default: 365 days / 1 year)
        """
        try:
            # Search for Form PF filings using SEC EDGAR search
            # Extended date range to find older filings if recent ones aren't available
            search_url = f"https://www.sec.gov/cgi-bin/browse-edgar"
            params = {
                'action': 'getcompany',
                'CIK': cik,
                'type': 'PF',
                'dateb': '',  # No end date restriction
                'owner': 'exclude',
                'count': '20',  # Increased from 10 to find more filings
                'output': 'xml'
            }
            
            response = self.session.get(search_url, params=params, timeout=30)
            response.raise_for_status()
            
            # Parse the search results XML
            root = ET.fromstring(response.content)
            
            # Find the most recent Form PF filing
            filings = root.findall('.//filing')
            if not filings:
                self.logger.debug(f"No Form PF filings found for CIK {cik}")
                return None
            
            # Sort by filing date (most recent first)
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=max_age_days)
            
            filings.sort(key=lambda x: x.find('datefiled').text if x.find('datefiled') is not None else '', reverse=True)
            
            for filing in filings:
                form_type = filing.find('type').text if filing.find('type') is not None else ''
                if form_type.startswith('PF'):
                    filing_date_str = filing.find('datefiled').text
                    if not filing_date_str:
                        continue
                    
                    # Check if filing is within acceptable age range
                    try:
                        filing_date = datetime.strptime(filing_date_str, '%Y-%m-%d').replace(tzinfo=timezone.utc)
                        if filing_date < cutoff_date:
                            self.logger.debug(
                                f"Form PF filing for CIK {cik} is too old "
                                f"({filing_date_str}, max age: {max_age_days} days)"
                            )
                            continue
                    except ValueError:
                        # If date parsing fails, continue anyway
                        pass
                    
                    accession_number = filing.find('accessionnumber').text
                    
                    # Download the actual Form PF XML document
                    xml_content = self._download_form_pf_xml(cik, accession_number)
                    if xml_content:
                        # Extract period end date from XML
                        period_end_date = self._extract_period_end_date(xml_content)
                        
                        self.logger.info(
                            f"Found Form PF filing for CIK {cik}: "
                            f"filed {filing_date_str}, period end {period_end_date}"
                        )
                        
                        return {
                            'filing_date': filing_date_str,
                            'period_end_date': period_end_date,
                            'form_type': form_type,
                            'accession_number': accession_number,
                            'xml_content': xml_content
                        }
            
            self.logger.debug(f"No acceptable Form PF filings found for CIK {cik} (within {max_age_days} days)")
            return None
            
        except Exception as e:
            self.logger.error(f"Error fetching Form PF for CIK {cik}: {e}")
            return None
    
    def _try_alternative_sources(self) -> Dict[str, Any]:
        """Try alternative data sources when Form PF filings are not available.
        
        This method attempts to find credit fund data from:
        1. 10-K filings (annual reports may contain credit fund information)
        2. Other SEC filings that might contain credit fund data
        
        Returns:
            Dictionary of fund data (same format as main fetch_data method)
        """
        self.logger.info("Attempting to find credit fund data from alternative sources...")
        fund_data = {}
        
        # Try searching 10-K filings for credit fund information
        # Note: This is a simplified fallback - in production, you might want to
        # use more sophisticated parsing or external APIs
        for cik, fund_name in self.CREDIT_FUND_CIKS.items():
            try:
                # Search for 10-K filings that might contain credit fund data
                search_url = f"https://www.sec.gov/cgi-bin/browse-edgar"
                params = {
                    'action': 'getcompany',
                    'CIK': cik,
                    'type': '10-K',
                    'dateb': '',
                    'owner': 'exclude',
                    'count': '3',
                    'output': 'atom'
                }
                
                response = self.session.get(search_url, params=params, timeout=30)
                response.raise_for_status()
                
                root = ET.fromstring(response.content)
                entries = root.findall('.//{http://www.w3.org/2005/Atom}entry')
                
                if entries:
                    # Found 10-K filings, but extracting credit fund data from 10-K
                    # would require complex parsing. For now, we'll log and continue.
                    self.logger.debug(
                        f"Found 10-K filings for {fund_name}, but credit fund data "
                        "extraction from 10-K requires complex parsing"
                    )
                
                time.sleep(0.1)  # Rate limiting
                
            except Exception as e:
                self.logger.debug(f"Error trying alternative sources for {fund_name}: {e}")
                continue
        
        # If we still don't have data, return empty dict
        # The caller will handle the error appropriately
        return fund_data
    
    def _download_form_pf_xml(self, cik: str, accession_number: str) -> Optional[str]:
        """Download the Form PF XML document."""
        try:
            # Construct the URL for the Form PF XML file
            # Format: https://www.sec.gov/Archives/edgar/data/{cik}/{accession_number_no_dashes}/primary_doc.xml
            accession_no_dashes = accession_number.replace('-', '')
            xml_url = f"{self.SEC_EDGAR_BASE_URL}/{cik}/{accession_no_dashes}/primary_doc.xml"
            
            response = self.session.get(xml_url, timeout=30)
            response.raise_for_status()
            
            return response.text
            
        except requests.RequestException as e:
            self.logger.error(f"Error downloading Form PF XML for CIK {cik}: {e}")
            # Don't return mock data in production - return None to indicate failure
            # Mock data should only be used in development/testing environments
            if os.getenv('USE_MOCK_DATA', 'false').lower() == 'true':
                self.logger.warning(f"Using mock Form PF XML data for CIK {cik} (USE_MOCK_DATA=true)")
                return self._generate_mock_form_pf_xml(cik)
            return None
    
    def _generate_mock_form_pf_xml(self, cik: str) -> str:
        """Generate mock Form PF XML content for testing."""
        # This simulates actual Form PF XML structure
        fund_name = self.CREDIT_FUND_CIKS.get(cik, 'Unknown Fund')
        
        # Simulate different asset values based on CIK for testing
        if cik == '0001423053':  # Apollo
            gross_assets = 45_000_000_000
        elif cik == '0001404912':  # Blackstone
            gross_assets = 52_000_000_000
        elif cik == '0001403161':  # KKR
            gross_assets = 38_000_000_000
        else:
            gross_assets = 25_000_000_000
        
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<FormPF xmlns="http://www.sec.gov/edgar/formpf">
    <Header>
        <SubmissionType>PF</SubmissionType>
        <Filer>
            <CIK>{cik}</CIK>
            <Name>{fund_name}</Name>
        </Filer>
        <PeriodEndDate>2024-03-31</PeriodEndDate>
        <FilingDate>2024-05-15</FilingDate>
    </Header>
    <FormData>
        <Section1>
            <Question1a>
                <GrossAssetValue>{gross_assets}</GrossAssetValue>
                <Currency>USD</Currency>
            </Question1a>
            <Question1b>
                <NetAssetValue>{int(gross_assets * 0.85)}</NetAssetValue>
                <Currency>USD</Currency>
            </Question1b>
        </Section1>
        <Section2>
            <CreditFunds>
                <Fund>
                    <FundName>{fund_name} Credit Fund I</FundName>
                    <GrossAssets>{int(gross_assets * 0.6)}</GrossAssets>
                    <AssetClass>PrivateCredit</AssetClass>
                </Fund>
                <Fund>
                    <FundName>{fund_name} Credit Fund II</FundName>
                    <GrossAssets>{int(gross_assets * 0.4)}</GrossAssets>
                    <AssetClass>PrivateCredit</AssetClass>
                </Fund>
            </CreditFunds>
        </Section2>
    </FormData>
</FormPF>"""
    
    def _extract_period_end_date(self, xml_content: str) -> Optional[str]:
        """Extract the period end date from Form PF XML."""
        try:
            root = ET.fromstring(xml_content)
            
            # Look for period end date in various possible locations
            period_end_elements = [
                root.find('.//{http://www.sec.gov/edgar/formpf}PeriodEndDate'),
                root.find('.//PeriodEndDate'),
                root.find('.//{http://www.sec.gov/edgar/formpf}Header/PeriodEndDate'),
                root.find('.//Header/PeriodEndDate')
            ]
            
            for element in period_end_elements:
                if element is not None and element.text:
                    return element.text
            
            return None
            
        except ET.ParseError as e:
            self.logger.error(f"Error parsing XML for period end date: {e}")
            return None
    
    def _extract_gross_asset_value(self, xml_content: str) -> Optional[float]:
        """Extract gross asset value from Form PF XML."""
        try:
            root = ET.fromstring(xml_content)
            
            # Look for gross asset value in various possible XML paths
            gross_asset_elements = [
                root.find('.//{http://www.sec.gov/edgar/formpf}GrossAssetValue'),
                root.find('.//GrossAssetValue'),
                root.find('.//{http://www.sec.gov/edgar/formpf}Question1a/GrossAssetValue'),
                root.find('.//Question1a/GrossAssetValue'),
                root.find('.//{http://www.sec.gov/edgar/formpf}Section1/Question1a/GrossAssetValue'),
                root.find('.//Section1/Question1a/GrossAssetValue')
            ]
            
            for element in gross_asset_elements:
                if element is not None and element.text:
                    try:
                        # Clean the text and convert to float
                        value_text = element.text.strip().replace(',', '').replace('$', '')
                        return float(value_text)
                    except ValueError:
                        continue
            
            # If direct gross asset value not found, try to sum individual fund assets
            credit_funds = root.findall('.//CreditFunds/Fund') or root.findall('.//{http://www.sec.gov/edgar/formpf}CreditFunds/Fund')
            if credit_funds:
                total_assets = 0
                for fund in credit_funds:
                    gross_assets_elem = fund.find('GrossAssets') or fund.find('.//{http://www.sec.gov/edgar/formpf}GrossAssets')
                    if gross_assets_elem is not None and gross_assets_elem.text:
                        try:
                            value_text = gross_assets_elem.text.strip().replace(',', '').replace('$', '')
                            total_assets += float(value_text)
                        except ValueError:
                            continue
                
                if total_assets > 0:
                    return total_assets
            
            return None
            
        except ET.ParseError as e:
            self.logger.error(f"Error parsing Form PF XML: {e}")
            return None
    
    def validate_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate the fetched credit fund data."""
        if not data:
            raise ValueError("No credit fund data received")
        
        if 'value' not in data:
            raise ValueError("Missing average gross asset value")
        
        if not isinstance(data['value'], (int, float)) or data['value'] < 0:
            raise ValueError("Invalid gross asset value")
        
        # Validate individual fund data
        individual_funds = data.get('individual_funds', {})
        if not individual_funds:
            raise ValueError("No individual fund data available")
        
        for cik, fund_data in individual_funds.items():
            required_fields = ['fund_name', 'gross_asset_value', 'filing_date', 'period_end_date']
            if not all(field in fund_data for field in required_fields):
                raise ValueError(f"Incomplete data for fund {cik}")
            
            if fund_data['gross_asset_value'] <= 0:
                raise ValueError(f"Invalid gross asset value for fund {cik}")
        
        # Set confidence based on data quality
        funds_processed = data.get('funds_processed', 0)
        if funds_processed >= 4:
            data['confidence'] = 0.95
        elif funds_processed >= 2:
            data['confidence'] = 0.8
        else:
            data['confidence'] = 0.6
        
        return data
    
    def should_alert(self, current_data: Dict[str, Any], historical_data: Optional[Dict[str, Any]]) -> bool:
        """Determine if asset value drops warrant an alert."""
        if not historical_data:
            # No historical data, don't alert on first run
            return False
        
        current_value = current_data.get('value', 0)
        previous_value = historical_data.get('value', 0)
        
        if previous_value <= 0:
            return False
        
        # Calculate percentage decline
        decline = (previous_value - current_value) / previous_value
        
        # Alert if decline exceeds threshold (10%)
        if decline > self.ALERT_THRESHOLD:
            return True
        
        # Also check individual funds for significant declines
        current_funds = current_data.get('individual_funds', {})
        previous_funds = historical_data.get('individual_funds', {})
        
        for cik in current_funds:
            if cik in previous_funds:
                current_fund_value = current_funds[cik]['gross_asset_value']
                previous_fund_value = previous_funds[cik]['gross_asset_value']
                
                if previous_fund_value > 0:
                    fund_decline = (previous_fund_value - current_fund_value) / previous_fund_value
                    if fund_decline > self.ALERT_THRESHOLD:
                        return True
        
        return False
    
    def generate_alert_message(self, current_data: Dict[str, Any], historical_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate alert message for significant asset value declines."""
        current_value = current_data.get('value', 0)
        previous_value = historical_data.get('value', 0) if historical_data else 0
        
        decline = (previous_value - current_value) / previous_value if previous_value > 0 else 0
        decline_percentage = decline * 100
        
        # Determine severity
        if decline > 0.20:  # >20% decline
            severity = 'high'
        elif decline > 0.15:  # >15% decline
            severity = 'medium'
        else:
            severity = 'low'
        
        message = (
            f"🚨 PRIVATE CREDIT ALERT 🚨\n\n"
            f"Significant decline in private credit fund asset values detected:\n\n"
            f"• Average gross asset value: ${current_value:,.0f}\n"
            f"• Previous quarter: ${previous_value:,.0f}\n"
            f"• Decline: ${previous_value - current_value:,.0f} ({decline_percentage:.1f}%)\n\n"
            f"Individual fund changes:\n"
        )
        
        # Add individual fund details
        current_funds = current_data.get('individual_funds', {})
        previous_funds = historical_data.get('individual_funds', {}) if historical_data else {}
        
        for cik, fund_data in current_funds.items():
            fund_name = fund_data['fund_name']
            current_fund_value = fund_data['gross_asset_value']
            
            if cik in previous_funds:
                previous_fund_value = previous_funds[cik]['gross_asset_value']
                fund_decline = (previous_fund_value - current_fund_value) / previous_fund_value if previous_fund_value > 0 else 0
                fund_decline_pct = fund_decline * 100
                
                message += (
                    f"• {fund_name}: ${current_fund_value:,.0f} "
                    f"({fund_decline_pct:+.1f}%)\n"
                )
            else:
                message += f"• {fund_name}: ${current_fund_value:,.0f} (new)\n"
        
        message += (
            f"\nThis may indicate early signs of credit stress in private markets. "
            f"Monitor for continued declines in subsequent quarters."
        )
        
        return {
            'alert_type': 'credit_stress',
            'severity': severity,
            'data_source': self.data_source,
            'metric': self.metric_name,
            'current_value': current_value,
            'previous_value': previous_value,
            'decline_percentage': decline_percentage,
            'threshold_breached': decline > self.ALERT_THRESHOLD,
            'message': message,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'context': {
                'funds_processed': current_data.get('funds_processed', 0),
                'total_gross_assets': current_data.get('total_gross_assets', 0),
                'data_quality': current_data.get('metadata', {}).get('data_quality', 'unknown'),
                'confidence': current_data.get('confidence', 0)
            }
        }