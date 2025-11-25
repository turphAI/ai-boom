"""
BDC (Business Development Company) discount-to-NAV scraper.

This scraper monitors BDC discount-to-NAV ratios by:
1. Fetching stock prices from Yahoo Finance
2. Parsing NAV data from SEC EDGAR filings (10-Q/10-K) - PRIMARY SOURCE
3. Falling back to investor relations pages if SEC fails
4. Falling back to RSS feeds if available (legacy support)
5. Calculating discount ratios
6. Alerting on significant changes
"""

import logging
import os
import re
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional, Tuple
from urllib.parse import urljoin

import requests
import yfinance as yf
from bs4 import BeautifulSoup

from scrapers.base import BaseScraper


class BDCDiscountScraper(BaseScraper):
    """Scraper for BDC discount-to-NAV ratios."""
    
    # BDC symbols with CIK codes, investor relations URLs, and RSS feeds (fallback)
    BDC_CONFIG = {
        'ARCC': {
            'name': 'Ares Capital Corporation',
            'cik': '0001288879',
            'ir_url': 'https://www.arescapitalcorp.com/investor-relations',
            'rss_url': 'https://www.arescapitalcorp.com/rss/press-releases',
            'nav_pattern': r'net\s+asset\s+value.*?(\$[\d,]+\.?\d*)',
        },
        'OCSL': {
            'name': 'Oaktree Specialty Lending Corporation',
            'cik': '0001414932',
            'ir_url': 'https://www.oaktreespecialtylending.com/investor-relations',
            'rss_url': 'https://www.oaktreespecialtylending.com/rss/press-releases',
            'nav_pattern': r'net\s+asset\s+value.*?(\$[\d,]+\.?\d*)',
        },
        'MAIN': {
            'name': 'Main Street Capital Corporation',
            'cik': '0001396440',
            'ir_url': 'https://www.mainstcapital.com/investor-relations',
            'rss_url': 'https://www.mainstcapital.com/rss/press-releases',
            'nav_pattern': r'net\s+asset\s+value.*?(\$[\d,]+\.?\d*)',
        },
        'PSEC': {
            'name': 'Prospect Capital Corporation',
            'cik': '0001176438',
            'ir_url': 'https://www.prospectstreet.com/investor-relations',
            'rss_url': 'https://www.prospectstreet.com/rss/press-releases',
            'nav_pattern': r'net\s+asset\s+value.*?(\$[\d,]+\.?\d*)',
        }
    }
    
    # SEC EDGAR base URL
    SEC_EDGAR_BASE_URL = "https://www.sec.gov"
    
    # Alert threshold: 5% change in average discount
    ALERT_THRESHOLD = 0.05
    
    def __init__(self):
        super().__init__('bdc_discount', 'discount_to_nav')
        self.session = requests.Session()
        # SEC requires User-Agent with contact information
        sec_email = os.getenv('SEC_EDGAR_EMAIL', 'compliance@boom-bust-sentinel.com')
        self.session.headers.update({
            'User-Agent': f'BoomBustSentinel/1.0 ({sec_email})',
            'Accept-Encoding': 'gzip, deflate',
            'Host': 'www.sec.gov'
        })
    
    def fetch_data(self) -> Dict[str, Any]:
        """Fetch BDC stock prices and NAV data using multiple fallback sources."""
        bdc_data = {}
        
        for symbol, config in self.BDC_CONFIG.items():
            try:
                # Fetch stock price from Yahoo Finance
                stock_price = self._fetch_stock_price(symbol)
                
                if not stock_price:
                    self.logger.warning(f"Failed to get stock price for {symbol}")
                    continue
                
                # Try multiple sources for NAV data (with fallbacks)
                nav_value = None
                nav_source = None
                
                # Method 1: SEC EDGAR filings (10-Q/10-K) - PRIMARY SOURCE
                nav_value, nav_source = self._fetch_nav_from_sec_edgar(symbol, config)
                
                # Method 2: Investor relations page scraping - FALLBACK 1
                if not nav_value:
                    nav_value, nav_source = self._fetch_nav_from_ir_page(symbol, config)
                
                # Method 3: RSS feed (legacy) - FALLBACK 2
                if not nav_value:
                    nav_value, nav_source = self._fetch_nav_from_rss(symbol, config)
                
                # Method 4: Yahoo Finance (if NAV available) - FALLBACK 3
                if not nav_value:
                    nav_value, nav_source = self._fetch_nav_from_yahoo(symbol)
                
                if stock_price and nav_value:
                    # Calculate discount-to-NAV: (NAV - Price) / NAV
                    discount = (nav_value - stock_price) / nav_value
                    
                    bdc_data[symbol] = {
                        'stock_price': stock_price,
                        'nav_value': nav_value,
                        'discount_to_nav': discount,
                        'discount_percentage': discount * 100,
                        'name': config['name'],
                        'nav_source': nav_source,
                        'timestamp': datetime.now(timezone.utc).isoformat()
                    }
                    
                    self.logger.info(
                        f"{symbol}: Price=${stock_price:.2f}, NAV=${nav_value:.2f} "
                        f"(from {nav_source}), Discount={discount*100:.2f}%"
                    )
                else:
                    self.logger.warning(
                        f"Failed to get NAV data for {symbol} from all sources"
                    )
                    
            except Exception as e:
                self.logger.error(f"Error processing {symbol}: {e}")
                continue
            
            # Rate limiting: SEC allows max 10 requests/second
            time.sleep(0.1)
        
        if not bdc_data:
            raise ValueError("No BDC data could be retrieved")
        
        # Calculate average discount across all BDCs
        discounts = [data['discount_to_nav'] for data in bdc_data.values()]
        avg_discount = sum(discounts) / len(discounts)
        
        return {
            'value': avg_discount,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'average_discount_percentage': avg_discount * 100,
            'bdc_count': len(bdc_data),
            'individual_bdcs': bdc_data,
            'metadata': {
                'symbols_processed': list(bdc_data.keys()),
                'data_quality': 'high' if len(bdc_data) >= 3 else 'medium',
                'nav_sources': {symbol: data['nav_source'] for symbol, data in bdc_data.items()}
            }
        }
    
    def _fetch_stock_price(self, symbol: str) -> Optional[float]:
        """Fetch current stock price from Yahoo Finance."""
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1d")
            
            if hist.empty:
                self.logger.warning(f"No price data available for {symbol}")
                return None
            
            # Get the most recent closing price
            price = float(hist['Close'].iloc[-1])
            return price
            
        except Exception as e:
            self.logger.error(f"Error fetching price for {symbol}: {e}")
            return None
    
    def _fetch_nav_from_sec_edgar(self, symbol: str, config: Dict[str, str]) -> Tuple[Optional[float], Optional[str]]:
        """Fetch NAV data from SEC EDGAR filings (10-Q/10-K) - PRIMARY SOURCE."""
        try:
            cik = config.get('cik')
            if not cik:
                return None, None
            
            # Get the most recent 10-Q or 10-K filing
            filing_url = self._get_latest_bdc_filing(cik)
            if not filing_url:
                self.logger.debug(f"No recent SEC filing found for {symbol}")
                return None, None
            
            # Parse NAV from the filing
            nav_value = self._parse_nav_from_filing(filing_url, symbol)
            
            if nav_value:
                self.logger.info(f"Found NAV for {symbol} from SEC EDGAR: ${nav_value:.2f}")
                return nav_value, 'sec_edgar'
            
            return None, None
            
        except Exception as e:
            self.logger.debug(f"Error fetching NAV from SEC EDGAR for {symbol}: {e}")
            return None, None
    
    def _get_latest_bdc_filing(self, cik: str) -> Optional[str]:
        """Get the URL of the most recent 10-Q or 10-K filing for a BDC."""
        try:
            # Search for 10-Q filings first (more frequent)
            for filing_type in ['10-Q', '10-K']:
                search_url = f"{self.SEC_EDGAR_BASE_URL}/cgi-bin/browse-edgar"
                params = {
                    'action': 'getcompany',
                    'CIK': cik,
                    'type': filing_type,
                    'dateb': '',
                    'count': '5',
                    'output': 'atom'
                }
                
                response = self.session.get(search_url, params=params, timeout=30)
                response.raise_for_status()
                
                # Parse the Atom feed
                root = ET.fromstring(response.content)
                
                # Find the first entry (most recent)
                for entry in root.findall('.//{http://www.w3.org/2005/Atom}entry'):
                    title_elem = entry.find('.//{http://www.w3.org/2005/Atom}title')
                    if title_elem is not None and filing_type in title_elem.text:
                        # Get the filing URL
                        link_elem = entry.find('.//{http://www.w3.org/2005/Atom}link[@rel="alternate"]')
                        if link_elem is not None:
                            filing_url = link_elem.get('href')
                            return filing_url
                
                # Rate limiting
                time.sleep(0.1)
            
            return None
            
        except Exception as e:
            self.logger.debug(f"Error fetching SEC filing for CIK {cik}: {e}")
            return None
    
    def _parse_nav_from_filing(self, filing_url: str, symbol: str) -> Optional[float]:
        """Parse NAV value from SEC filing (tries XBRL first, then HTML/text)."""
        try:
            # Get the filing page
            response = self.session.get(filing_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Method 1: Try XBRL instance document
            xbrl_links = soup.find_all('a', href=re.compile(r'.*\.xml$'))
            for link in xbrl_links:
                href = link.get('href')
                if href and ('_htm.xml' in href or 'instance' in href.lower()):
                    instance_url = urljoin(filing_url, href)
                    nav_value = self._parse_nav_from_xbrl(instance_url, symbol)
                    if nav_value:
                        return nav_value
            
            # Method 2: Parse from HTML/text filing
            nav_value = self._parse_nav_from_html(soup, symbol)
            if nav_value:
                return nav_value
            
            return None
            
        except Exception as e:
            self.logger.debug(f"Error parsing filing for {symbol}: {e}")
            return None
    
    def _parse_nav_from_xbrl(self, xbrl_url: str, symbol: str) -> Optional[float]:
        """Parse NAV from XBRL instance document."""
        try:
            response = self.session.get(xbrl_url, timeout=30)
            response.raise_for_status()
            
            root = ET.fromstring(response.content)
            
            # Common XBRL element names for NAV
            nav_elements = [
                'NetAssetValuePerShare',
                'NetAssetsValuePerShare',
                'NAVPerShare',
                'NetAssetValue',
                'NetAssetsValue'
            ]
            
            # Try different namespaces
            namespaces = {
                'us-gaap': 'http://fasb.org/us-gaap/2023',
                'us-gaap-2022': 'http://fasb.org/us-gaap/2022',
                'dei': 'http://xbrl.sec.gov/dei/2023',
                'xbrli': 'http://www.xbrl.org/2003/instance'
            }
            
            for ns_prefix, ns_uri in namespaces.items():
                for element_name in nav_elements:
                    xpath = f".//{{{ns_uri}}}{element_name}"
                    elements = root.findall(xpath)
                    
                    for element in elements:
                        try:
                            nav_value = float(element.text)
                            if nav_value > 0:
                                return nav_value
                        except (ValueError, TypeError):
                            continue
            
            return None
            
        except Exception as e:
            self.logger.debug(f"Error parsing XBRL for {symbol}: {e}")
            return None
    
    def _parse_nav_from_html(self, soup: BeautifulSoup, symbol: str) -> Optional[float]:
        """Parse NAV from HTML filing text."""
        try:
            # Look for NAV patterns in the HTML text
            text = soup.get_text()
            
            # Common NAV patterns
            nav_patterns = [
                r'net\s+asset\s+value\s+per\s+share[:\s]+[\$]?([\d,]+\.?\d*)',
                r'nav\s+per\s+share[:\s]+[\$]?([\d,]+\.?\d*)',
                r'net\s+asset\s+value[:\s]+[\$]?([\d,]+\.?\d*)',
                r'nav[:\s]+[\$]?([\d,]+\.?\d*)',
            ]
            
            for pattern in nav_patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    try:
                        nav_str = match.group(1).replace(',', '')
                        nav_value = float(nav_str)
                        # NAV per share should be reasonable (between $1 and $1000)
                        if 1 <= nav_value <= 1000:
                            return nav_value
                    except (ValueError, IndexError):
                        continue
            
            return None
            
        except Exception as e:
            self.logger.debug(f"Error parsing HTML for {symbol}: {e}")
            return None
    
    def _fetch_nav_from_ir_page(self, symbol: str, config: Dict[str, str]) -> Tuple[Optional[float], Optional[str]]:
        """Fetch NAV data from investor relations page - FALLBACK 1."""
        try:
            ir_url = config.get('ir_url')
            if not ir_url:
                return None, None
            
            # Use a different session for non-SEC requests
            ir_session = requests.Session()
            ir_session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            response = ir_session.get(ir_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            text = soup.get_text()
            
            # Look for NAV patterns
            nav_pattern = config.get('nav_pattern', r'net\s+asset\s+value.*?(\$[\d,]+\.?\d*)')
            nav_match = re.search(nav_pattern, text, re.IGNORECASE)
            
            if nav_match:
                nav_str = nav_match.group(1).replace('$', '').replace(',', '')
                nav_value = float(nav_str)
                self.logger.info(f"Found NAV for {symbol} from IR page: ${nav_value:.2f}")
                return nav_value, 'ir_page'
            
            return None, None
            
        except Exception as e:
            self.logger.debug(f"Error fetching NAV from IR page for {symbol}: {e}")
            return None, None
    
    def _fetch_nav_from_rss(self, symbol: str, config: Dict[str, str]) -> Tuple[Optional[float], Optional[str]]:
        """Fetch NAV data from RSS feed - FALLBACK 2 (legacy support)."""
        try:
            rss_url = config.get('rss_url')
            if not rss_url:
                return None, None
            
            # Use a different session for non-SEC requests
            rss_session = requests.Session()
            rss_session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            response = rss_session.get(rss_url, timeout=30)
            response.raise_for_status()
            
            # Parse RSS feed
            root = ET.fromstring(response.content)
            
            # Look for recent NAV announcements (within last 90 days)
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=90)
            
            for item in root.findall('.//item'):
                try:
                    # Get publication date
                    pub_date_str = item.find('pubDate').text if item.find('pubDate') is not None else ''
                    if pub_date_str:
                        try:
                            # Parse date (RSS date format: "Wed, 15 Jan 2024 10:00:00 GMT")
                            date_part = pub_date_str.replace(' GMT', '').replace(' UTC', '')
                            pub_date = datetime.strptime(date_part, "%a, %d %b %Y %H:%M:%S")
                            if pub_date < cutoff_date:
                                continue
                        except ValueError:
                            pass
                    
                    # Get title and description
                    title = item.find('title').text if item.find('title') is not None else ''
                    description = item.find('description').text if item.find('description') is not None else ''
                    
                    # Look for NAV information
                    content = f"{title} {description}".lower()
                    
                    if 'net asset value' in content or 'nav' in content:
                        nav_pattern = config.get('nav_pattern', r'net\s+asset\s+value.*?(\$[\d,]+\.?\d*)')
                        nav_match = re.search(nav_pattern, content, re.IGNORECASE)
                        if nav_match:
                            nav_str = nav_match.group(1).replace('$', '').replace(',', '')
                            nav_value = float(nav_str)
                            self.logger.info(f"Found NAV for {symbol} from RSS: ${nav_value:.2f}")
                            return nav_value, 'rss_feed'
                            
                except Exception as e:
                    self.logger.debug(f"Error parsing RSS item for {symbol}: {e}")
                    continue
            
            return None, None
            
        except requests.RequestException:
            # RSS feed may not exist (404) - this is expected
            return None, None
        except ET.ParseError:
            return None, None
    
    def _fetch_nav_from_yahoo(self, symbol: str) -> Tuple[Optional[float], Optional[str]]:
        """Fetch NAV data from Yahoo Finance - FALLBACK 3."""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Yahoo Finance may have NAV in various fields
            nav_fields = ['nav', 'netAssetValue', 'navPerShare', 'bookValue']
            
            for field in nav_fields:
                if field in info and info[field]:
                    try:
                        nav_value = float(info[field])
                        if nav_value > 0:
                            self.logger.info(f"Found NAV for {symbol} from Yahoo Finance: ${nav_value:.2f}")
                            return nav_value, 'yahoo_finance'
                    except (ValueError, TypeError):
                        continue
            
            return None, None
            
        except Exception as e:
            self.logger.debug(f"Error fetching NAV from Yahoo Finance for {symbol}: {e}")
            return None, None
    
    def validate_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate BDC discount data."""
        if not data:
            raise ValueError("No BDC data received")
        
        if 'value' not in data:
            raise ValueError("Missing average discount value")
        
        if not isinstance(data['value'], (int, float)):
            raise ValueError("Average discount value must be numeric")
        
        # Check if discount is within reasonable bounds (-1 to 1, i.e., -100% to 100%)
        if not -1 <= data['value'] <= 1:
            self.logger.warning(f"Unusual discount value: {data['value']*100:.2f}%")
        
        # Validate individual BDC data
        individual_bdcs = data.get('individual_bdcs', {})
        if not individual_bdcs:
            raise ValueError("No individual BDC data available")
        
        for symbol, bdc_data in individual_bdcs.items():
            if not all(key in bdc_data for key in ['stock_price', 'nav_value', 'discount_to_nav']):
                raise ValueError(f"Incomplete data for {symbol}")
            
            if bdc_data['stock_price'] <= 0 or bdc_data['nav_value'] <= 0:
                raise ValueError(f"Invalid price/NAV values for {symbol}")
        
        return data
    
    def should_alert(self, current_data: Dict[str, Any], historical_data: Optional[Dict[str, Any]]) -> bool:
        """Determine if discount change warrants an alert."""
        if not historical_data:
            # No historical data, don't alert on first run
            return False
        
        current_discount = current_data['value']
        previous_discount = historical_data.get('value')
        
        if previous_discount is None:
            return False
        
        # Calculate percentage change in discount
        change = abs(current_discount - previous_discount)
        
        # Alert if change exceeds threshold (5%)
        return change > self.ALERT_THRESHOLD
    
    def generate_alert_message(self, current_data: Dict[str, Any], historical_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate alert message for significant discount changes."""
        current_discount = current_data['value']
        previous_discount = historical_data.get('value', 0) if historical_data else 0
        
        change = current_discount - previous_discount
        change_percentage = (change / abs(previous_discount)) * 100 if previous_discount != 0 else 0
        
        # Determine alert severity
        if abs(change) > 0.10:  # >10% change
            severity = 'high'
        elif abs(change) > 0.07:  # >7% change
            severity = 'medium'
        else:
            severity = 'low'
        
        # Create detailed message
        direction = "increased" if change > 0 else "decreased"
        
        message = (
            f"🏦 BDC Discount Alert\n\n"
            f"Average BDC discount-to-NAV has {direction} significantly:\n"
            f"• Current: {current_discount*100:.2f}%\n"
            f"• Previous: {previous_discount*100:.2f}%\n"
            f"• Change: {change*100:+.2f}% ({change_percentage:+.1f}%)\n\n"
            f"Individual BDCs:\n"
        )
        
        # Add individual BDC details
        for symbol, bdc_data in current_data['individual_bdcs'].items():
            message += (
                f"• {symbol}: {bdc_data['discount_percentage']:.2f}% "
                f"(${bdc_data['stock_price']:.2f} vs NAV ${bdc_data['nav_value']:.2f})\n"
            )
        
        return {
            'alert_type': 'bdc_discount_change',
            'severity': severity,
            'data_source': self.data_source,
            'metric': self.metric_name,
            'current_value': current_discount,
            'previous_value': previous_discount,
            'change': change,
            'change_percentage': change_percentage,
            'message': message,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'context': {
                'bdc_count': current_data['bdc_count'],
                'symbols': list(current_data['individual_bdcs'].keys()),
                'data_quality': current_data['metadata']['data_quality']
            }
        }