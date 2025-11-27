"""
Market Cap Scraper for AI Datacenter Market Players.

This scraper fetches current market capitalization data for all public companies
tracked in the Market Players database using Yahoo Finance.
"""

import logging
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

import yfinance as yf

from scrapers.base import BaseScraper


class MarketCapScraper(BaseScraper):
    """Scraper for market capitalization data of tracked companies."""
    
    # All public tickers from the Market Players page
    # Organized by category for clarity
    TICKER_CONFIG = {
        # Demand Side - Tech Giants
        'AMZN': {'name': 'Amazon', 'category': 'demand'},
        'GOOGL': {'name': 'Alphabet (Google)', 'category': 'demand'},
        'META': {'name': 'Meta Platforms', 'category': 'demand'},
        'MSFT': {'name': 'Microsoft', 'category': 'demand'},
        'NVDA': {'name': 'NVIDIA', 'category': 'demand'},
        'TSLA': {'name': 'Tesla', 'category': 'demand'},
        'AMD': {'name': 'Advanced Micro Devices', 'category': 'demand'},
        'AVGO': {'name': 'Broadcom', 'category': 'demand'},
        'TSM': {'name': 'Taiwan Semiconductor', 'category': 'demand'},
        'PLTR': {'name': 'Palantir', 'category': 'demand'},
        'CSCO': {'name': 'Cisco Systems', 'category': 'demand'},
        'INTC': {'name': 'Intel', 'category': 'demand'},
        
        # Supply Side - Data Center REITs
        'EQIX': {'name': 'Equinix', 'category': 'supply'},
        'DLR': {'name': 'Digital Realty', 'category': 'supply'},
        'IRM': {'name': 'Iron Mountain', 'category': 'supply'},
        
        # Financing Side - Institutional Banks
        'JPM': {'name': 'JPMorgan Chase', 'category': 'financing'},
        'GS': {'name': 'Goldman Sachs', 'category': 'financing'},
        'BAC': {'name': 'Bank of America', 'category': 'financing'},
        'WFC': {'name': 'Wells Fargo', 'category': 'financing'},
        'C': {'name': 'Citigroup', 'category': 'financing'},
        'BCS': {'name': 'Barclays', 'category': 'financing'},
        'DB': {'name': 'Deutsche Bank', 'category': 'financing'},
        'HSBC': {'name': 'HSBC', 'category': 'financing'},
        
        # Financing Side - BDCs
        'ARCC': {'name': 'Ares Capital', 'category': 'financing'},
        'MAIN': {'name': 'Main Street Capital', 'category': 'financing'},
        'HTGC': {'name': 'Hercules Capital', 'category': 'financing'},
        'OBDC': {'name': 'Blue Owl Capital Corp', 'category': 'financing'},
        'TRIN': {'name': 'Trinity Capital', 'category': 'financing'},
        'HRZN': {'name': 'Horizon Technology Finance', 'category': 'financing'},
        'OFS': {'name': 'OFS Capital Corp', 'category': 'financing'},
        'TPVG': {'name': 'TP Venture Growth BDC', 'category': 'financing'},
        
        # Financing Side - Private Equity
        'BX': {'name': 'Blackstone Group', 'category': 'financing'},
        'KKR': {'name': 'KKR & Co', 'category': 'financing'},
        'APO': {'name': 'Apollo Global Management', 'category': 'financing'},
        'CG': {'name': 'Carlyle Group', 'category': 'financing'},
        'BAM': {'name': 'Brookfield Asset Management', 'category': 'financing'},
        
        # Financing Side - Infrastructure
        'DBRG': {'name': 'DigitalBridge Group', 'category': 'financing'},
        'AMT': {'name': 'American Tower', 'category': 'financing'},
        'CCI': {'name': 'Crown Castle', 'category': 'financing'},
    }
    
    # Alert threshold: 10% change in any single stock's market cap
    ALERT_THRESHOLD = 0.10
    
    def __init__(self):
        super().__init__('market_cap', 'daily')
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def fetch_data(self) -> Dict[str, Any]:
        """Fetch market cap data for all tracked tickers."""
        market_caps = {}
        errors = []
        
        for symbol, config in self.TICKER_CONFIG.items():
            try:
                market_cap_data = self._fetch_market_cap(symbol)
                
                if market_cap_data:
                    market_caps[symbol] = {
                        'ticker': symbol,
                        'name': config['name'],
                        'category': config['category'],
                        'market_cap': market_cap_data['market_cap'],
                        'market_cap_formatted': self._format_market_cap(market_cap_data['market_cap']),
                        'price': market_cap_data.get('price'),
                        'currency': market_cap_data.get('currency', 'USD'),
                        'timestamp': datetime.now(timezone.utc).isoformat()
                    }
                    
                    self.logger.info(
                        f"{symbol}: Market Cap = {market_caps[symbol]['market_cap_formatted']}"
                    )
                else:
                    errors.append(f"Failed to get market cap for {symbol}")
                    self.logger.warning(f"Failed to get market cap for {symbol}")
                    
            except Exception as e:
                errors.append(f"{symbol}: {str(e)}")
                self.logger.error(f"Error processing {symbol}: {e}")
                continue
            
            # Rate limiting to avoid hitting Yahoo Finance limits
            time.sleep(0.2)
        
        if not market_caps:
            raise ValueError("No market cap data could be retrieved")
        
        # Calculate total market cap by category
        category_totals = {}
        for data in market_caps.values():
            category = data['category']
            if category not in category_totals:
                category_totals[category] = 0
            if data['market_cap']:
                category_totals[category] += data['market_cap']
        
        # Calculate overall total
        total_market_cap = sum(
            data['market_cap'] for data in market_caps.values() 
            if data['market_cap']
        )
        
        return {
            'value': total_market_cap,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'total_market_cap': total_market_cap,
            'total_market_cap_formatted': self._format_market_cap(total_market_cap),
            'ticker_count': len(market_caps),
            'individual_tickers': market_caps,
            'category_totals': {
                cat: {
                    'total': total,
                    'formatted': self._format_market_cap(total)
                }
                for cat, total in category_totals.items()
            },
            'metadata': {
                'tickers_processed': list(market_caps.keys()),
                'tickers_failed': errors,
                'data_quality': 'high' if len(market_caps) >= len(self.TICKER_CONFIG) * 0.8 else 'medium',
                'source': 'yahoo_finance'
            }
        }
    
    def _fetch_market_cap(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch market cap for a single ticker from Yahoo Finance."""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Try different fields for market cap
            market_cap = info.get('marketCap')
            
            if not market_cap:
                # Fallback: calculate from shares * price
                shares = info.get('sharesOutstanding')
                price = info.get('currentPrice') or info.get('regularMarketPrice')
                if shares and price:
                    market_cap = shares * price
            
            if market_cap:
                return {
                    'market_cap': float(market_cap),
                    'price': info.get('currentPrice') or info.get('regularMarketPrice'),
                    'currency': info.get('currency', 'USD')
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error fetching market cap for {symbol}: {e}")
            return None
    
    def _format_market_cap(self, value: Optional[float]) -> str:
        """Format market cap value for display."""
        if not value:
            return '-'
        
        if value >= 1_000_000_000_000:  # Trillion
            return f"${value / 1_000_000_000_000:.2f}T"
        elif value >= 1_000_000_000:  # Billion
            return f"${value / 1_000_000_000:.1f}B"
        elif value >= 1_000_000:  # Million
            return f"${value / 1_000_000:.1f}M"
        else:
            return f"${value:,.0f}"
    
    def validate_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate market cap data."""
        if not data:
            raise ValueError("No market cap data received")
        
        if 'individual_tickers' not in data:
            raise ValueError("Missing individual ticker data")
        
        individual_tickers = data.get('individual_tickers', {})
        if not individual_tickers:
            raise ValueError("No individual ticker data available")
        
        for symbol, ticker_data in individual_tickers.items():
            if 'market_cap' not in ticker_data:
                raise ValueError(f"Missing market cap for {symbol}")
            
            if ticker_data['market_cap'] and ticker_data['market_cap'] <= 0:
                raise ValueError(f"Invalid market cap value for {symbol}")
        
        return data
    
    def should_alert(self, current_data: Dict[str, Any], historical_data: Optional[Dict[str, Any]]) -> bool:
        """Determine if market cap change warrants an alert."""
        if not historical_data:
            return False
        
        current_tickers = current_data.get('individual_tickers', {})
        previous_tickers = historical_data.get('individual_tickers', {})
        
        if not previous_tickers:
            return False
        
        # Check for significant changes in any ticker
        for symbol, current in current_tickers.items():
            if symbol not in previous_tickers:
                continue
            
            current_cap = current.get('market_cap')
            previous_cap = previous_tickers[symbol].get('market_cap')
            
            if not current_cap or not previous_cap:
                continue
            
            change = abs(current_cap - previous_cap) / previous_cap
            
            if change > self.ALERT_THRESHOLD:
                return True
        
        return False
    
    def generate_alert_message(self, current_data: Dict[str, Any], historical_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate alert message for significant market cap changes."""
        current_tickers = current_data.get('individual_tickers', {})
        previous_tickers = historical_data.get('individual_tickers', {}) if historical_data else {}
        
        significant_changes = []
        
        for symbol, current in current_tickers.items():
            if symbol not in previous_tickers:
                continue
            
            current_cap = current.get('market_cap')
            previous_cap = previous_tickers[symbol].get('market_cap')
            
            if not current_cap or not previous_cap:
                continue
            
            change = (current_cap - previous_cap) / previous_cap
            
            if abs(change) > self.ALERT_THRESHOLD:
                significant_changes.append({
                    'symbol': symbol,
                    'name': current.get('name'),
                    'current_cap': current_cap,
                    'previous_cap': previous_cap,
                    'change_percentage': change * 100
                })
        
        # Sort by absolute change percentage
        significant_changes.sort(key=lambda x: abs(x['change_percentage']), reverse=True)
        
        # Determine severity based on number of significant changes
        if len(significant_changes) >= 5:
            severity = 'high'
        elif len(significant_changes) >= 3:
            severity = 'medium'
        else:
            severity = 'low'
        
        message = "📊 Market Cap Alert\n\nSignificant market cap changes detected:\n\n"
        
        for change in significant_changes[:10]:  # Top 10
            direction = "📈" if change['change_percentage'] > 0 else "📉"
            message += (
                f"{direction} {change['symbol']} ({change['name']}): "
                f"{change['change_percentage']:+.1f}%\n"
                f"   {self._format_market_cap(change['previous_cap'])} → "
                f"{self._format_market_cap(change['current_cap'])}\n\n"
            )
        
        return {
            'alert_type': 'market_cap_change',
            'severity': severity,
            'data_source': self.data_source,
            'metric': self.metric_name,
            'current_total': current_data.get('total_market_cap'),
            'significant_changes': significant_changes,
            'message': message,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'context': {
                'ticker_count': current_data.get('ticker_count'),
                'data_quality': current_data['metadata']['data_quality']
            }
        }

