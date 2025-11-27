"""
AI Investment Proxy Scraper for Market Players.

This scraper fetches R&D spending and Capital Expenditure (CapEx) data from Yahoo Finance
to calculate a proxy for AI investment. Since companies don't separately report "AI investment",
we use these metrics as reasonable proxies for technology infrastructure spending.

Methodology:
- R&D Spending: Research and Development expenses from income statement
- CapEx: Capital Expenditure from cash flow statement
- AI Investment Proxy = R&D + (CapEx * tech_multiplier)
  - Tech companies: 60% of CapEx assumed AI/infrastructure related
  - Data center companies: 80% of CapEx assumed AI/infrastructure related
  - Financial companies: 30% of CapEx assumed tech-related
"""

import logging
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional

import yfinance as yf

from scrapers.base import BaseScraper


class AIInvestmentScraper(BaseScraper):
    """Scraper for AI investment proxy data using R&D and CapEx."""
    
    # Ticker configuration with category-specific multipliers
    # multiplier = what percentage of CapEx is likely AI/tech infrastructure
    TICKER_CONFIG = {
        # Demand Side - Tech Giants (high AI focus)
        'AMZN': {'name': 'Amazon', 'category': 'demand', 'capex_multiplier': 0.6},
        'GOOGL': {'name': 'Alphabet (Google)', 'category': 'demand', 'capex_multiplier': 0.7},
        'META': {'name': 'Meta Platforms', 'category': 'demand', 'capex_multiplier': 0.8},
        'MSFT': {'name': 'Microsoft', 'category': 'demand', 'capex_multiplier': 0.7},
        'NVDA': {'name': 'NVIDIA', 'category': 'demand', 'capex_multiplier': 0.9},
        'TSLA': {'name': 'Tesla', 'category': 'demand', 'capex_multiplier': 0.4},
        'AMD': {'name': 'Advanced Micro Devices', 'category': 'demand', 'capex_multiplier': 0.8},
        'AVGO': {'name': 'Broadcom', 'category': 'demand', 'capex_multiplier': 0.6},
        'TSM': {'name': 'Taiwan Semiconductor', 'category': 'demand', 'capex_multiplier': 0.7},
        'PLTR': {'name': 'Palantir', 'category': 'demand', 'capex_multiplier': 0.9},
        'CSCO': {'name': 'Cisco Systems', 'category': 'demand', 'capex_multiplier': 0.5},
        'INTC': {'name': 'Intel', 'category': 'demand', 'capex_multiplier': 0.6},
        
        # Supply Side - Data Center REITs (infrastructure focused)
        'EQIX': {'name': 'Equinix', 'category': 'supply', 'capex_multiplier': 0.9},
        'DLR': {'name': 'Digital Realty', 'category': 'supply', 'capex_multiplier': 0.9},
        'IRM': {'name': 'Iron Mountain', 'category': 'supply', 'capex_multiplier': 0.7},
        
        # Financing Side - Banks and Financial (lower tech focus)
        'JPM': {'name': 'JPMorgan Chase', 'category': 'financing', 'capex_multiplier': 0.3},
        'GS': {'name': 'Goldman Sachs', 'category': 'financing', 'capex_multiplier': 0.4},
        'BAC': {'name': 'Bank of America', 'category': 'financing', 'capex_multiplier': 0.3},
        'WFC': {'name': 'Wells Fargo', 'category': 'financing', 'capex_multiplier': 0.25},
        'C': {'name': 'Citigroup', 'category': 'financing', 'capex_multiplier': 0.3},
        
        # Financing Side - PE/Asset Managers
        'BX': {'name': 'Blackstone Group', 'category': 'financing', 'capex_multiplier': 0.2},
        'KKR': {'name': 'KKR & Co', 'category': 'financing', 'capex_multiplier': 0.2},
        'APO': {'name': 'Apollo Global Management', 'category': 'financing', 'capex_multiplier': 0.2},
        
        # Infrastructure
        'AMT': {'name': 'American Tower', 'category': 'financing', 'capex_multiplier': 0.5},
        'CCI': {'name': 'Crown Castle', 'category': 'financing', 'capex_multiplier': 0.5},
    }
    
    def __init__(self):
        super().__init__('ai_investment', 'proxy')
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def fetch_data(self) -> Dict[str, Any]:
        """Fetch R&D and CapEx data to calculate AI investment proxy."""
        investment_data = {}
        errors = []
        
        for symbol, config in self.TICKER_CONFIG.items():
            try:
                data = self._fetch_investment_metrics(symbol, config)
                
                if data:
                    investment_data[symbol] = data
                    self.logger.info(
                        f"{symbol}: R&D={data['rd_formatted']}, "
                        f"CapEx={data['capex_formatted']}, "
                        f"AI Proxy={data['ai_investment_formatted']}"
                    )
                else:
                    errors.append(f"No data for {symbol}")
                    self.logger.warning(f"Failed to get investment data for {symbol}")
                    
            except Exception as e:
                errors.append(f"{symbol}: {str(e)}")
                self.logger.error(f"Error processing {symbol}: {e}")
                continue
            
            # Rate limiting
            time.sleep(0.3)
        
        if not investment_data:
            raise ValueError("No AI investment proxy data could be retrieved")
        
        # Calculate totals by category
        category_totals = {}
        for data in investment_data.values():
            category = data['category']
            if category not in category_totals:
                category_totals[category] = {
                    'total_rd': 0,
                    'total_capex': 0,
                    'total_ai_investment': 0
                }
            if data['rd']:
                category_totals[category]['total_rd'] += data['rd']
            if data['capex']:
                category_totals[category]['total_capex'] += abs(data['capex'])
            if data['ai_investment_proxy']:
                category_totals[category]['total_ai_investment'] += data['ai_investment_proxy']
        
        # Format category totals
        for cat in category_totals:
            category_totals[cat]['total_rd_formatted'] = self._format_value(category_totals[cat]['total_rd'])
            category_totals[cat]['total_capex_formatted'] = self._format_value(category_totals[cat]['total_capex'])
            category_totals[cat]['total_ai_investment_formatted'] = self._format_value(category_totals[cat]['total_ai_investment'])
        
        # Calculate overall total
        total_ai_investment = sum(
            data['ai_investment_proxy'] for data in investment_data.values() 
            if data['ai_investment_proxy']
        )
        
        return {
            'value': total_ai_investment,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'total_ai_investment': total_ai_investment,
            'total_ai_investment_formatted': self._format_value(total_ai_investment),
            'ticker_count': len(investment_data),
            'individual_tickers': investment_data,
            'category_totals': category_totals,
            'metadata': {
                'tickers_processed': list(investment_data.keys()),
                'tickers_failed': errors,
                'data_quality': 'high' if len(investment_data) >= len(self.TICKER_CONFIG) * 0.7 else 'medium',
                'source': 'yahoo_finance',
                'methodology': {
                    'description': 'AI Investment Proxy calculated from R&D spending and weighted CapEx',
                    'formula': 'AI Investment Proxy = R&D + (CapEx × category_multiplier)',
                    'data_sources': ['Yahoo Finance Income Statement (R&D)', 'Yahoo Finance Cash Flow (CapEx)'],
                    'multipliers': {
                        'tech_companies': '60-90% of CapEx',
                        'data_centers': '70-90% of CapEx',
                        'financial': '20-40% of CapEx'
                    },
                    'limitations': [
                        'Not all R&D is AI-related',
                        'CapEx includes non-AI infrastructure',
                        'Based on most recent annual figures',
                        'Multipliers are estimates based on industry analysis'
                    ]
                }
            },
            'confidence': 0.7  # Moderate confidence as this is a proxy
        }
    
    def _fetch_investment_metrics(self, symbol: str, config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Fetch R&D and CapEx for a single ticker."""
        try:
            ticker = yf.Ticker(symbol)
            
            # Get R&D from income statement
            rd = None
            rd_period = None
            income_stmt = ticker.income_stmt
            if income_stmt is not None and not income_stmt.empty:
                if 'Research And Development' in income_stmt.index:
                    rd_series = income_stmt.loc['Research And Development']
                    # Get most recent non-null value
                    for date, value in rd_series.items():
                        if value and value > 0:
                            rd = float(value)
                            rd_period = str(date.year) if hasattr(date, 'year') else str(date)[:4]
                            break
            
            # Get CapEx from cash flow statement
            capex = None
            capex_period = None
            cashflow = ticker.cashflow
            if cashflow is not None and not cashflow.empty:
                if 'Capital Expenditure' in cashflow.index:
                    capex_series = cashflow.loc['Capital Expenditure']
                    # Get most recent non-null value (CapEx is typically negative)
                    for date, value in capex_series.items():
                        if value is not None:
                            capex = float(value)
                            capex_period = str(date.year) if hasattr(date, 'year') else str(date)[:4]
                            break
            
            # Calculate AI investment proxy
            multiplier = config.get('capex_multiplier', 0.5)
            ai_investment_proxy = 0
            
            if rd:
                ai_investment_proxy += rd
            if capex:
                # CapEx is negative (outflow), so we take absolute value and apply multiplier
                ai_investment_proxy += abs(capex) * multiplier
            
            return {
                'ticker': symbol,
                'name': config['name'],
                'category': config['category'],
                'rd': rd,
                'rd_formatted': self._format_value(rd),
                'rd_period': rd_period,
                'capex': capex,
                'capex_abs': abs(capex) if capex else None,
                'capex_formatted': self._format_value(abs(capex) if capex else None),
                'capex_period': capex_period,
                'capex_multiplier': multiplier,
                'ai_investment_proxy': ai_investment_proxy if ai_investment_proxy > 0 else None,
                'ai_investment_formatted': self._format_value(ai_investment_proxy if ai_investment_proxy > 0 else None),
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'calculation': {
                    'formula': f"R&D ({self._format_value(rd)}) + CapEx ({self._format_value(abs(capex) if capex else None)}) × {multiplier:.0%}",
                    'rd_component': rd or 0,
                    'capex_component': (abs(capex) * multiplier) if capex else 0
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error fetching investment metrics for {symbol}: {e}")
            return None
    
    def _format_value(self, value: Optional[float]) -> str:
        """Format value for display."""
        if not value:
            return '-'
        
        value = abs(value)  # Ensure positive for display
        
        if value >= 1_000_000_000_000:  # Trillion
            return f"${value / 1_000_000_000_000:.2f}T"
        elif value >= 1_000_000_000:  # Billion
            return f"${value / 1_000_000_000:.1f}B"
        elif value >= 1_000_000:  # Million
            return f"${value / 1_000_000:.0f}M"
        else:
            return f"${value:,.0f}"
    
    def validate_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate AI investment proxy data."""
        if not data:
            raise ValueError("No AI investment data received")
        
        if 'individual_tickers' not in data:
            raise ValueError("Missing individual ticker data")
        
        return data
    
    def should_alert(self, current_data: Dict[str, Any], historical_data: Optional[Dict[str, Any]]) -> bool:
        """AI investment proxy changes don't typically warrant alerts."""
        return False
    
    def generate_alert_message(self, current_data: Dict[str, Any], historical_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate alert message (not typically used for this scraper)."""
        return {
            'alert_type': 'ai_investment_change',
            'severity': 'low',
            'message': 'AI Investment proxy data updated',
            'timestamp': datetime.now(timezone.utc).isoformat()
        }

