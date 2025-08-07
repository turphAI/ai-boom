"""
Bond Issuance Scraper for monitoring weekly investment-grade tech bond issuance.

This scraper monitors SEC Rule 424B prospectuses for new filings from major tech companies
(MSFT, META, AMZN, GOOGL) and tracks notional amounts and coupon rates to detect unusual
spikes in corporate debt activity that may signal market stress.
"""

import re
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional
from sec_edgar_downloader import Downloader
import requests
from bs4 import BeautifulSoup
import logging

from scrapers.base import BaseScraper
from utils.error_handling import retry_with_backoff, RetryConfig


class BondIssuanceScraper(BaseScraper):
    """Scraper for monitoring bond issuance from major tech companies."""
    
    # CIK codes for major tech companies
    TECH_COMPANY_CIKS = {
        '0000789019': 'MSFT',  # Microsoft
        '0001326801': 'META',  # Meta (Facebook)
        '0001018724': 'AMZN',  # Amazon
        '0001652044': 'GOOGL'  # Alphabet (Google)
    }
    
    # Alert threshold: $5B weekly issuance increase
    ALERT_THRESHOLD = 5_000_000_000
    
    def __init__(self):
        super().__init__('bond_issuance', 'weekly')
        self.downloader = Downloader("BoomBustSentinel", "user@example.com")
        
    @retry_with_backoff(RetryConfig(max_retries=3, base_delay=2.0))
    def fetch_data(self) -> Dict[str, Any]:
        """Fetch bond issuance data from SEC EDGAR filings with retry logic."""
        self.logger.info("Fetching bond issuance data from SEC EDGAR")
        
        # Calculate date range for the past week
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=7)
        
        total_notional = 0
        bond_details = []
        companies_involved = []
        failed_companies = []
        
        for cik, company_symbol in self.TECH_COMPANY_CIKS.items():
            try:
                self.logger.info(f"Processing filings for {company_symbol} (CIK: {cik})")
                
                # Download 424B filings for the company with retry
                filings = self._get_424b_filings_with_retry(cik, start_date, end_date)
                
                for filing in filings:
                    bond_data = self._parse_prospectus(filing)
                    if bond_data:
                        # Validate individual bond data
                        if self._validate_bond_data(bond_data):
                            bond_details.append({
                                'company': company_symbol,
                                'cik': cik,
                                'filing_date': bond_data['filing_date'],
                                'notional_amount': bond_data['notional_amount'],
                                'coupon_rate': bond_data['coupon_rate'],
                                'form_type': bond_data['form_type'],
                                'data_checksum': self._calculate_bond_checksum(bond_data)
                            })
                            
                            total_notional += bond_data['notional_amount']
                            if company_symbol not in companies_involved:
                                companies_involved.append(company_symbol)
                        else:
                            self.logger.warning(f"Invalid bond data for {company_symbol}: {bond_data}")
                            
            except Exception as e:
                self.logger.warning(f"Failed to process {company_symbol}: {e}")
                failed_companies.append(company_symbol)
                continue
        
        # Calculate average coupon rate
        coupon_rates = [bond['coupon_rate'] for bond in bond_details if bond['coupon_rate'] is not None]
        avg_coupon = sum(coupon_rates) / len(coupon_rates) if coupon_rates else 0
        
        # Calculate confidence based on success rate and data quality
        success_rate = (len(self.TECH_COMPANY_CIKS) - len(failed_companies)) / len(self.TECH_COMPANY_CIKS)
        base_confidence = 0.95 if bond_details else 0.0
        confidence = base_confidence * success_rate
        
        return {
            'value': total_notional,
            'timestamp': datetime.now(timezone.utc),
            'confidence': confidence,
            'metadata': {
                'companies': companies_involved,
                'failed_companies': failed_companies,
                'avg_coupon': round(avg_coupon, 2),
                'bond_count': len(bond_details),
                'bond_details': bond_details,
                'source': 'sec_edgar',
                'success_rate': success_rate,
                'date_range': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat()
                }
            }
        }
    
    @retry_with_backoff(RetryConfig(max_retries=2, base_delay=1.0))
    def _get_424b_filings_with_retry(self, cik: str, start_date, end_date) -> List[Dict[str, Any]]:
        """Get 424B filings for a specific CIK within date range with retry logic."""
        return self._get_424b_filings(cik, start_date, end_date)
    
    def _get_424b_filings(self, cik: str, start_date, end_date) -> List[Dict[str, Any]]:
        """Get 424B filings for a specific CIK within date range."""
        filings = []
        
        try:
            # Download filings using sec-edgar-downloader
            # Note: This is a simplified approach - in production, you'd want to
            # use the SEC's REST API for more precise date filtering
            self.downloader.get("424B2", cik, limit=10, download_details=True)
            self.downloader.get("424B5", cik, limit=10, download_details=True)
            
            # For this implementation, we'll simulate the filing data
            # In a real implementation, you would parse the downloaded files
            filings = self._simulate_filing_data(cik, start_date, end_date)
            
        except Exception as e:
            self.logger.error(f"Failed to download filings for CIK {cik}: {e}")
            # Re-raise as retryable error for the retry decorator
            raise ConnectionError(f"SEC EDGAR connection failed for CIK {cik}: {e}")
            
        return filings
    
    def _validate_bond_data(self, bond_data: Dict[str, Any]) -> bool:
        """Validate individual bond data for integrity."""
        try:
            # Check required fields
            required_fields = ['filing_date', 'notional_amount', 'form_type']
            for field in required_fields:
                if field not in bond_data or bond_data[field] is None:
                    return False
            
            # Validate notional amount
            notional = bond_data['notional_amount']
            if not isinstance(notional, (int, float)) or notional <= 0:
                return False
            
            # Check for reasonable bounds (between $1M and $100B)
            if notional < 1_000_000 or notional > 100_000_000_000:
                self.logger.warning(f"Unusual notional amount: ${notional:,}")
                return False
            
            # Validate coupon rate if present
            if 'coupon_rate' in bond_data and bond_data['coupon_rate'] is not None:
                coupon = bond_data['coupon_rate']
                if not isinstance(coupon, (int, float)) or coupon < 0 or coupon > 20:
                    self.logger.warning(f"Unusual coupon rate: {coupon}%")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating bond data: {e}")
            return False
    
    def _calculate_bond_checksum(self, bond_data: Dict[str, Any]) -> str:
        """Calculate checksum for bond data integrity."""
        import hashlib
        import json
        
        # Create a consistent string representation
        checksum_data = {
            'notional_amount': bond_data.get('notional_amount'),
            'coupon_rate': bond_data.get('coupon_rate'),
            'filing_date': str(bond_data.get('filing_date')),
            'form_type': bond_data.get('form_type')
        }
        
        json_str = json.dumps(checksum_data, sort_keys=True)
        return hashlib.md5(json_str.encode()).hexdigest()[:8]
    
    def _simulate_filing_data(self, cik: str, start_date, end_date) -> List[Dict[str, Any]]:
        """Simulate filing data for testing purposes."""
        # This is a placeholder implementation for demonstration
        # In production, this would parse actual SEC filing data
        
        company_symbol = self.TECH_COMPANY_CIKS.get(cik, 'UNKNOWN')
        
        # Simulate some bond issuances based on the company
        if company_symbol == 'MSFT':
            return [{
                'cik': cik,
                'form_type': '424B2',
                'filing_date': start_date + timedelta(days=1),
                'document_url': f'https://www.sec.gov/Archives/edgar/data/{cik}/sample.htm',
                'content': self._generate_sample_prospectus_content(2_000_000_000, 4.5)
            }]
        elif company_symbol == 'META':
            return [{
                'cik': cik,
                'form_type': '424B5',
                'filing_date': start_date + timedelta(days=3),
                'document_url': f'https://www.sec.gov/Archives/edgar/data/{cik}/sample.htm',
                'content': self._generate_sample_prospectus_content(1_500_000_000, 4.2)
            }]
        
        return []
    
    def _generate_sample_prospectus_content(self, notional: int, coupon: float) -> str:
        """Generate sample prospectus content for testing."""
        return f"""
        <html>
        <body>
        <p>This prospectus relates to the offering of ${notional:,} aggregate principal amount of 
        {coupon}% Senior Notes due 2034.</p>
        <p>The notes will bear interest at a rate of {coupon}% per annum.</p>
        <p>Principal amount: ${notional:,}</p>
        </body>
        </html>
        """
    
    def _parse_prospectus(self, filing: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse prospectus content to extract bond details."""
        try:
            content = filing.get('content', '')
            if not content:
                return None
            
            soup = BeautifulSoup(content, 'html.parser')
            text = soup.get_text()
            
            # Extract notional amount
            notional_amount = self._extract_notional_amount(text)
            if notional_amount is None:
                return None
            
            # Extract coupon rate
            coupon_rate = self._extract_coupon_rate(text)
            
            return {
                'filing_date': filing['filing_date'],
                'form_type': filing['form_type'],
                'notional_amount': notional_amount,
                'coupon_rate': coupon_rate,
                'document_url': filing.get('document_url')
            }
            
        except Exception as e:
            self.logger.error(f"Failed to parse prospectus: {e}")
            return None
    
    def _extract_notional_amount(self, text: str) -> Optional[int]:
        """Extract notional amount from prospectus text."""
        # Look for patterns like "$2,000,000,000" or "$2 billion"
        patterns = [
            r'\$([0-9,]+)\s*aggregate principal amount',
            r'\$([0-9,]+)\s*principal amount',
            r'Principal amount:\s*\$([0-9,]+)',
            r'\$([0-9,]+)\s*of.*notes',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(',', '')
                try:
                    return int(amount_str)
                except ValueError:
                    continue
        
        # Look for billion/million patterns
        billion_pattern = r'\$([0-9.]+)\s*billion'
        match = re.search(billion_pattern, text, re.IGNORECASE)
        if match:
            try:
                return int(float(match.group(1)) * 1_000_000_000)
            except ValueError:
                pass
        
        million_pattern = r'\$([0-9.]+)\s*million'
        match = re.search(million_pattern, text, re.IGNORECASE)
        if match:
            try:
                return int(float(match.group(1)) * 1_000_000)
            except ValueError:
                pass
        
        return None
    
    def _extract_coupon_rate(self, text: str) -> Optional[float]:
        """Extract coupon rate from prospectus text."""
        patterns = [
            r'([0-9.]+)%\s*per annum',
            r'interest at a rate of ([0-9.]+)%',
            r'([0-9.]+)%\s*Senior Notes',
            r'bear interest.*?([0-9.]+)%',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    continue
        
        return None
    
    def validate_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate the fetched bond issuance data."""
        if not data:
            raise ValueError("No bond issuance data received")
        
        # Validate required fields
        if 'value' not in data:
            raise ValueError("Missing total notional value")
        
        if not isinstance(data['value'], (int, float)) or data['value'] < 0:
            raise ValueError("Invalid notional amount")
        
        # Validate metadata
        metadata = data.get('metadata', {})
        if not isinstance(metadata.get('companies', []), list):
            raise ValueError("Invalid companies list in metadata")
        
        # Set confidence based on data quality
        bond_count = metadata.get('bond_count', 0)
        if bond_count == 0:
            data['confidence'] = 0.0
        elif bond_count >= 3:
            data['confidence'] = 0.95
        else:
            data['confidence'] = 0.7
        
        return data
    
    def should_alert(self, current_data: Dict[str, Any], historical_data: Optional[Dict[str, Any]]) -> bool:
        """Determine if an alert should be triggered based on issuance threshold."""
        current_value = current_data.get('value', 0)
        
        # Always alert if current week exceeds absolute threshold
        if current_value > self.ALERT_THRESHOLD:
            return True
        
        # Alert if significant increase from previous week
        if historical_data:
            previous_value = historical_data.get('value', 0)
            increase = current_value - previous_value
            
            if increase > self.ALERT_THRESHOLD:
                return True
        
        return False
    
    def generate_alert_message(self, current_data: Dict[str, Any], historical_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate alert message for bond issuance threshold breach."""
        current_value = current_data.get('value', 0)
        metadata = current_data.get('metadata', {})
        
        previous_value = 0
        if historical_data:
            previous_value = historical_data.get('value', 0)
        
        change_amount = current_value - previous_value
        change_percent = (change_amount / previous_value * 100) if previous_value > 0 else 0
        
        companies = metadata.get('companies', [])
        avg_coupon = metadata.get('avg_coupon', 0)
        bond_count = metadata.get('bond_count', 0)
        
        message = f"""
🚨 BOND ISSUANCE ALERT 🚨

Weekly tech bond issuance: ${current_value:,.0f}
Previous week: ${previous_value:,.0f}
Change: ${change_amount:,.0f} ({change_percent:+.1f}%)

Companies involved: {', '.join(companies)}
Number of bonds: {bond_count}
Average coupon rate: {avg_coupon:.2f}%

This represents a significant increase in corporate debt activity that may signal market stress.
        """.strip()
        
        return {
            'alert_type': 'threshold_breach',
            'data_source': self.data_source,
            'metric': self.metric_name,
            'current_value': current_value,
            'previous_value': previous_value,
            'threshold': self.ALERT_THRESHOLD,
            'change_percent': change_percent,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'message': message,
            'context': {
                'companies_involved': companies,
                'bond_count': bond_count,
                'avg_coupon': avg_coupon,
                'data_quality': 'high' if current_data.get('confidence', 0) > 0.8 else 'medium',
                'confidence': current_data.get('confidence', 0)
            }
        }
    
    def get_data_schema(self) -> Dict[str, Any]:
        """Get data schema for bond issuance validation."""
        return {
            'required': ['value', 'timestamp', 'confidence', 'metadata'],
            'types': {
                'value': (int, float),
                'timestamp': (str, datetime),
                'confidence': (int, float),
                'metadata': dict
            },
            'ranges': {
                'value': (0, 500_000_000_000),  # Max $500B
                'confidence': (0.0, 1.0)
            }
        }
    
    def get_secondary_data_sources(self) -> List[Dict[str, Any]]:
        """Get secondary data sources for cross-validation."""
        # In a real implementation, this would fetch data from FINRA TRACE
        # or other bond data providers for cross-validation
        secondary_sources = []
        
        try:
            # Simulate FINRA TRACE data
            finra_data = self._get_finra_trace_data()
            if finra_data:
                secondary_sources.append(finra_data)
            
            # Simulate S&P CapitalIQ data
            sp_data = self._get_sp_capitaliq_data()
            if sp_data:
                secondary_sources.append(sp_data)
                
        except Exception as e:
            self.logger.warning(f"Failed to get secondary data sources: {e}")
        
        return secondary_sources
    
    def _get_finra_trace_data(self) -> Optional[Dict[str, Any]]:
        """Simulate FINRA TRACE data for cross-validation."""
        # This is a placeholder - in production, this would call FINRA TRACE API
        return {
            'value': 3_200_000_000,  # Simulated value
            'source': 'finra_trace',
            'confidence': 0.85,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    
    def _get_sp_capitaliq_data(self) -> Optional[Dict[str, Any]]:
        """Simulate S&P CapitalIQ data for cross-validation."""
        # This is a placeholder - in production, this would call S&P CapitalIQ API
        return {
            'value': 3_100_000_000,  # Simulated value
            'source': 'sp_capitaliq',
            'confidence': 0.90,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }