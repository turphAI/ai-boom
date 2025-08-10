"""
BDC (Business Development Company) discount-to-NAV scraper.

This scraper monitors BDC discount-to-NAV ratios by:
1. Fetching stock prices from Yahoo Finance
2. Parsing NAV data from RSS feeds
3. Calculating discount ratios
4. Alerting on significant changes
"""

import logging
import re
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
    
    # BDC symbols and their RSS feed URLs for NAV data
    BDC_CONFIG = {
        'ARCC': {
            'name': 'Ares Capital Corporation',
            'rss_url': 'https://www.arescapitalcorp.com/rss/press-releases',
            'nav_pattern': r'net\s+asset\s+value.*?(\$[\d,]+\.?\d*)',
        },
        'OCSL': {
            'name': 'Oaktree Specialty Lending Corporation',
            'rss_url': 'https://www.oaktreespecialtylending.com/rss/press-releases',
            'nav_pattern': r'net\s+asset\s+value.*?(\$[\d,]+\.?\d*)',
        },
        'MAIN': {
            'name': 'Main Street Capital Corporation',
            'rss_url': 'https://www.mainstcapital.com/rss/press-releases',
            'nav_pattern': r'net\s+asset\s+value.*?(\$[\d,]+\.?\d*)',
        },
        'PSEC': {
            'name': 'Prospect Capital Corporation',
            'rss_url': 'https://www.prospectstreet.com/rss/press-releases',
            'nav_pattern': r'net\s+asset\s+value.*?(\$[\d,]+\.?\d*)',
        }
    }
    
    # Alert threshold: 5% change in average discount
    ALERT_THRESHOLD = 0.05
    
    def __init__(self):
        super().__init__('bdc_discount', 'discount_to_nav')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def fetch_data(self) -> Dict[str, Any]:
        """Fetch BDC stock prices and NAV data."""
        bdc_data = {}
        
        for symbol, config in self.BDC_CONFIG.items():
            try:
                # Fetch stock price from Yahoo Finance
                stock_price = self._fetch_stock_price(symbol)
                
                # Fetch NAV from RSS feed
                nav_value = self._fetch_nav_from_rss(symbol, config)
                
                if stock_price and nav_value:
                    # Calculate discount-to-NAV: (NAV - Price) / NAV
                    discount = (nav_value - stock_price) / nav_value
                    
                    bdc_data[symbol] = {
                        'stock_price': stock_price,
                        'nav_value': nav_value,
                        'discount_to_nav': discount,
                        'discount_percentage': discount * 100,
                        'name': config['name'],
                        'timestamp': datetime.now(timezone.utc).isoformat()
                    }
                    
                    self.logger.info(
                        f"{symbol}: Price=${stock_price:.2f}, NAV=${nav_value:.2f}, "
                        f"Discount={discount*100:.2f}%"
                    )
                else:
                    self.logger.warning(f"Failed to get complete data for {symbol}")
                    
            except Exception as e:
                self.logger.error(f"Error processing {symbol}: {e}")
                continue
        
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
                'data_quality': 'high' if len(bdc_data) >= 3 else 'medium'
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
    
    def _fetch_nav_from_rss(self, symbol: str, config: Dict[str, str]) -> Optional[float]:
        """Fetch NAV data from RSS feed."""
        try:
            response = self.session.get(config['rss_url'], timeout=30)
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
                            # Remove timezone for simpler parsing
                            date_part = pub_date_str.replace(' GMT', '').replace(' UTC', '')
                            pub_date = datetime.strptime(date_part, "%a, %d %b %Y %H:%M:%S")
                            if pub_date < cutoff_date:
                                continue
                        except ValueError:
                            # If date parsing fails, continue processing the item
                            pass
                    
                    # Get title and description
                    title = item.find('title').text if item.find('title') is not None else ''
                    description = item.find('description').text if item.find('description') is not None else ''
                    
                    # Look for NAV information in title or description
                    content = f"{title} {description}".lower()
                    
                    if 'net asset value' in content or 'nav' in content:
                        # Extract NAV value using regex
                        nav_match = re.search(config['nav_pattern'], content, re.IGNORECASE)
                        if nav_match:
                            nav_str = nav_match.group(1).replace('$', '').replace(',', '')
                            nav_value = float(nav_str)
                            self.logger.info(f"Found NAV for {symbol}: ${nav_value:.2f}")
                            return nav_value
                            
                except Exception as e:
                    self.logger.debug(f"Error parsing RSS item for {symbol}: {e}")
                    continue
            
            self.logger.warning(f"No recent NAV data found in RSS feed for {symbol}")
            return None
            
        except requests.RequestException as e:
            self.logger.error(f"Error fetching RSS feed for {symbol}: {e}")
            return None
        except ET.ParseError as e:
            self.logger.error(f"Error parsing RSS XML for {symbol}: {e}")
            return None
    
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