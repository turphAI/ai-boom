"""
Debt Scraper for Market Players.

This scraper fetches debt data from Yahoo Finance balance sheets to provide
current debt levels for tracked companies.

Data Retrieved:
- Total Debt: Combined short-term and long-term debt
- Long-term Debt: Bonds, notes, and long-term borrowings
- Current Debt: Short-term borrowings and current portion of long-term debt
"""

import logging
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional

import yfinance as yf

from scrapers.base import BaseScraper


class DebtScraper(BaseScraper):
    """Scraper for company debt data from Yahoo Finance."""
    
    # All public tickers from the Market Players page
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
        
        # Infrastructure
        'DBRG': {'name': 'DigitalBridge Group', 'category': 'financing'},
        'AMT': {'name': 'American Tower', 'category': 'financing'},
        'CCI': {'name': 'Crown Castle', 'category': 'financing'},
    }
    
    def __init__(self):
        super().__init__('debt', 'total')
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def fetch_data(self) -> Dict[str, Any]:
        """Fetch debt data for all tracked tickers."""
        debt_data = {}
        errors = []
        
        for symbol, config in self.TICKER_CONFIG.items():
            try:
                data = self._fetch_debt_metrics(symbol, config)
                
                if data:
                    debt_data[symbol] = data
                    self.logger.info(
                        f"{symbol}: Total Debt={data['total_debt_formatted']}, "
                        f"LT Debt={data['long_term_debt_formatted']}"
                    )
                else:
                    errors.append(f"No data for {symbol}")
                    self.logger.warning(f"Failed to get debt data for {symbol}")
                    
            except Exception as e:
                errors.append(f"{symbol}: {str(e)}")
                self.logger.error(f"Error processing {symbol}: {e}")
                continue
            
            # Rate limiting
            time.sleep(0.3)
        
        if not debt_data:
            raise ValueError("No debt data could be retrieved")
        
        # Calculate totals by category
        category_totals = {}
        for data in debt_data.values():
            category = data['category']
            if category not in category_totals:
                category_totals[category] = {
                    'total_debt': 0,
                    'long_term_debt': 0,
                    'current_debt': 0
                }
            if data['total_debt']:
                category_totals[category]['total_debt'] += data['total_debt']
            if data['long_term_debt']:
                category_totals[category]['long_term_debt'] += data['long_term_debt']
            if data['current_debt']:
                category_totals[category]['current_debt'] += data['current_debt']
        
        # Format category totals
        for cat in category_totals:
            category_totals[cat]['total_debt_formatted'] = self._format_value(category_totals[cat]['total_debt'])
            category_totals[cat]['long_term_debt_formatted'] = self._format_value(category_totals[cat]['long_term_debt'])
            category_totals[cat]['current_debt_formatted'] = self._format_value(category_totals[cat]['current_debt'])
        
        # Calculate overall total
        total_debt = sum(
            data['total_debt'] for data in debt_data.values() 
            if data['total_debt']
        )
        
        return {
            'value': total_debt,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'total_debt': total_debt,
            'total_debt_formatted': self._format_value(total_debt),
            'ticker_count': len(debt_data),
            'individual_tickers': debt_data,
            'category_totals': category_totals,
            'metadata': {
                'tickers_processed': list(debt_data.keys()),
                'tickers_failed': errors,
                'data_quality': 'high' if len(debt_data) >= len(self.TICKER_CONFIG) * 0.7 else 'medium',
                'source': 'yahoo_finance',
                'methodology': {
                    'description': 'Total debt outstanding from company balance sheets',
                    'metrics': {
                        'total_debt': 'Combined short-term and long-term debt obligations',
                        'long_term_debt': 'Bonds, notes, and borrowings due after one year',
                        'current_debt': 'Short-term borrowings and current portion of long-term debt'
                    },
                    'data_sources': [
                        'Yahoo Finance Balance Sheet',
                        'Most recent quarterly filing (10-Q) or annual filing (10-K)'
                    ],
                    'notes': [
                        'Represents debt on the balance sheet, not lending capacity',
                        'For banks/BDCs, this is their own borrowings, not loans made to others',
                        'Updated quarterly with company filings',
                        'Does not include off-balance-sheet obligations'
                    ]
                }
            },
            'confidence': 0.9  # High confidence - direct from financial statements
        }
    
    def _fetch_debt_metrics(self, symbol: str, config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Fetch debt metrics for a single ticker."""
        try:
            ticker = yf.Ticker(symbol)
            
            # Get balance sheet
            balance_sheet = ticker.balance_sheet
            
            if balance_sheet is None or balance_sheet.empty:
                return None
            
            # Extract debt values
            total_debt = None
            long_term_debt = None
            current_debt = None
            period = None
            
            # Get the most recent column date
            if len(balance_sheet.columns) > 0:
                period = str(balance_sheet.columns[0])[:10]
            
            # Total Debt
            if 'Total Debt' in balance_sheet.index:
                val = balance_sheet.loc['Total Debt'].iloc[0]
                if val and val > 0:
                    total_debt = float(val)
            
            # Long Term Debt
            for field in ['Long Term Debt', 'Long Term Debt And Capital Lease Obligation']:
                if field in balance_sheet.index:
                    val = balance_sheet.loc[field].iloc[0]
                    if val and val > 0:
                        long_term_debt = float(val)
                        break
            
            # Current Debt
            for field in ['Current Debt', 'Current Debt And Capital Lease Obligation']:
                if field in balance_sheet.index:
                    val = balance_sheet.loc[field].iloc[0]
                    if val and val > 0:
                        current_debt = float(val)
                        break
            
            # If no total debt but have components, calculate it
            if not total_debt and (long_term_debt or current_debt):
                total_debt = (long_term_debt or 0) + (current_debt or 0)
            
            # Calculate debt-to-equity if equity available
            debt_to_equity = None
            if 'Total Equity Gross Minority Interest' in balance_sheet.index and total_debt:
                equity = balance_sheet.loc['Total Equity Gross Minority Interest'].iloc[0]
                if equity and equity > 0:
                    debt_to_equity = total_debt / equity
            elif 'Stockholders Equity' in balance_sheet.index and total_debt:
                equity = balance_sheet.loc['Stockholders Equity'].iloc[0]
                if equity and equity > 0:
                    debt_to_equity = total_debt / equity
            
            return {
                'ticker': symbol,
                'name': config['name'],
                'category': config['category'],
                'total_debt': total_debt,
                'total_debt_formatted': self._format_value(total_debt),
                'long_term_debt': long_term_debt,
                'long_term_debt_formatted': self._format_value(long_term_debt),
                'current_debt': current_debt,
                'current_debt_formatted': self._format_value(current_debt),
                'debt_to_equity': round(debt_to_equity, 2) if debt_to_equity else None,
                'period': period,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error fetching debt metrics for {symbol}: {e}")
            return None
    
    def _format_value(self, value: Optional[float]) -> str:
        """Format value for display."""
        if not value:
            return '-'
        
        value = abs(value)
        
        if value >= 1_000_000_000_000:  # Trillion
            return f"${value / 1_000_000_000_000:.2f}T"
        elif value >= 1_000_000_000:  # Billion
            return f"${value / 1_000_000_000:.1f}B"
        elif value >= 1_000_000:  # Million
            return f"${value / 1_000_000:.0f}M"
        else:
            return f"${value:,.0f}"
    
    def validate_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate debt data."""
        if not data:
            raise ValueError("No debt data received")
        
        if 'individual_tickers' not in data:
            raise ValueError("Missing individual ticker data")
        
        return data
    
    def should_alert(self, current_data: Dict[str, Any], historical_data: Optional[Dict[str, Any]]) -> bool:
        """Debt changes don't typically warrant immediate alerts."""
        return False
    
    def generate_alert_message(self, current_data: Dict[str, Any], historical_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate alert message (not typically used for this scraper)."""
        return {
            'alert_type': 'debt_change',
            'severity': 'low',
            'message': 'Debt data updated',
            'timestamp': datetime.now(timezone.utc).isoformat()
        }

