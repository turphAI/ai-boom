"""
Context Analyzer - Understands market context for intelligent anomaly detection.

This agent identifies market context such as:
- Holidays (market closures)
- Earnings seasons
- Market events (FOMC meetings, economic releases)
- Historical patterns

This context is used to adjust anomaly detection thresholds intelligently.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import calendar


class MarketContextType(Enum):
    """Types of market context."""
    NORMAL = "normal"
    HOLIDAY = "holiday"
    EARNINGS_SEASON = "earnings_season"
    FOMC_MEETING = "fomc_meeting"
    ECONOMIC_RELEASE = "economic_release"
    MARKET_EVENT = "market_event"
    YEAR_END = "year_end"
    QUARTER_END = "quarter_end"


@dataclass
class MarketContext:
    """Represents market context for a given date."""
    date: datetime
    context_types: List[MarketContextType]
    description: str
    expected_volatility: str  # 'low', 'normal', 'high', 'very_high'
    threshold_adjustment: float  # Multiplier for anomaly thresholds (1.0 = no change)
    metadata: Dict[str, Any]


class ContextAnalyzer:
    """
    Analyzes market context to inform anomaly detection.
    
    Usage:
        analyzer = ContextAnalyzer()
        context = analyzer.get_context(datetime.now())
        adjusted_threshold = base_threshold * context.threshold_adjustment
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # US Market holidays (simplified - can be enhanced with actual holiday calendar)
        self.us_holidays = self._load_us_holidays()
        
        # Earnings seasons (approximate)
        self.earnings_seasons = self._load_earnings_seasons()
        
        # FOMC meeting dates (approximate - 8 meetings per year)
        self.fomc_meetings = self._load_fomc_meetings()
    
    def get_context(self, date: Optional[datetime] = None) -> MarketContext:
        """
        Get market context for a given date.
        
        Args:
            date: Date to analyze (defaults to now)
            
        Returns:
            MarketContext object with context information
        """
        if date is None:
            date = datetime.now(timezone.utc)
        
        context_types = []
        descriptions = []
        expected_volatility = 'normal'
        threshold_adjustment = 1.0
        metadata = {}
        
        # Check for holidays
        if self._is_holiday(date):
            context_types.append(MarketContextType.HOLIDAY)
            holiday_name = self._get_holiday_name(date)
            descriptions.append(f"US Market Holiday: {holiday_name}")
            expected_volatility = 'low'
            threshold_adjustment = 0.5  # Lower threshold - less trading activity
        
        # Check for earnings season
        if self._is_earnings_season(date):
            context_types.append(MarketContextType.EARNINGS_SEASON)
            descriptions.append("Earnings Season - Higher volatility expected")
            if expected_volatility == 'normal':
                expected_volatility = 'high'
            threshold_adjustment = 1.5  # Higher threshold - more volatility expected
        
        # Check for FOMC meetings
        if self._is_fomc_meeting(date):
            context_types.append(MarketContextType.FOMC_MEETING)
            descriptions.append("FOMC Meeting - Higher volatility expected")
            if expected_volatility in ['normal', 'high']:
                expected_volatility = 'very_high'
            threshold_adjustment = 2.0  # Much higher threshold - very high volatility
        
        # Check for quarter/year end
        if self._is_quarter_end(date):
            context_types.append(MarketContextType.QUARTER_END)
            descriptions.append("Quarter End - Window dressing expected")
            if expected_volatility == 'normal':
                expected_volatility = 'high'
            threshold_adjustment = 1.3
        
        if self._is_year_end(date):
            context_types.append(MarketContextType.YEAR_END)
            descriptions.append("Year End - Tax loss harvesting, rebalancing")
            if expected_volatility == 'normal':
                expected_volatility = 'high'
            threshold_adjustment = 1.3
        
        # If no special context, it's normal
        if not context_types:
            context_types.append(MarketContextType.NORMAL)
            descriptions.append("Normal trading day")
        
        return MarketContext(
            date=date,
            context_types=context_types,
            description="; ".join(descriptions),
            expected_volatility=expected_volatility,
            threshold_adjustment=threshold_adjustment,
            metadata=metadata
        )
    
    def _load_us_holidays(self) -> Dict[str, List[Tuple[int, int]]]:
        """Load US market holidays (simplified)."""
        # Format: {year: [(month, day), ...]}
        # This is a simplified version - can be enhanced with actual holiday calendar API
        holidays = {}
        
        # Common holidays (approximate dates)
        # New Year's Day: Jan 1
        # Martin Luther King Jr. Day: 3rd Monday of January
        # Presidents Day: 3rd Monday of February
        # Good Friday: Varies (not included here)
        # Memorial Day: Last Monday of May
        # Juneteenth: June 19
        # Independence Day: July 4
        # Labor Day: 1st Monday of September
        # Thanksgiving: 4th Thursday of November
        # Christmas: December 25
        
        # For now, return empty dict - can be enhanced
        return holidays
    
    def _load_earnings_seasons(self) -> List[Tuple[datetime, datetime]]:
        """Load earnings season periods."""
        # Earnings seasons typically:
        # Q1: Late April - Early May
        # Q2: Late July - Early August
        # Q3: Late October - Early November
        # Q4: Late January - Early February
        
        current_year = datetime.now().year
        seasons = []
        
        # Q1 earnings (reporting Q4 results)
        seasons.append((
            datetime(current_year, 1, 15, tzinfo=timezone.utc),
            datetime(current_year, 2, 15, tzinfo=timezone.utc)
        ))
        
        # Q2 earnings (reporting Q1 results)
        seasons.append((
            datetime(current_year, 4, 15, tzinfo=timezone.utc),
            datetime(current_year, 5, 15, tzinfo=timezone.utc)
        ))
        
        # Q3 earnings (reporting Q2 results)
        seasons.append((
            datetime(current_year, 7, 15, tzinfo=timezone.utc),
            datetime(current_year, 8, 15, tzinfo=timezone.utc)
        ))
        
        # Q4 earnings (reporting Q3 results)
        seasons.append((
            datetime(current_year, 10, 15, tzinfo=timezone.utc),
            datetime(current_year, 11, 15, tzinfo=timezone.utc)
        ))
        
        return seasons
    
    def _load_fomc_meetings(self) -> List[datetime]:
        """Load FOMC meeting dates (approximate - 8 meetings per year)."""
        # FOMC typically meets 8 times per year
        # Approximate schedule: Jan, Mar, May, Jun, Jul, Sep, Nov, Dec
        current_year = datetime.now().year
        
        meetings = [
            datetime(current_year, 1, 31, tzinfo=timezone.utc),
            datetime(current_year, 3, 20, tzinfo=timezone.utc),
            datetime(current_year, 5, 1, tzinfo=timezone.utc),
            datetime(current_year, 6, 12, tzinfo=timezone.utc),
            datetime(current_year, 7, 31, tzinfo=timezone.utc),
            datetime(current_year, 9, 18, tzinfo=timezone.utc),
            datetime(current_year, 11, 6, tzinfo=timezone.utc),
            datetime(current_year, 12, 18, tzinfo=timezone.utc),
        ]
        
        return meetings
    
    def _is_holiday(self, date: datetime) -> bool:
        """Check if date is a US market holiday."""
        # Simplified check - can be enhanced with actual holiday calendar
        month = date.month
        day = date.day
        
        # New Year's Day
        if month == 1 and day == 1:
            return True
        
        # Independence Day
        if month == 7 and day == 4:
            return True
        
        # Christmas
        if month == 12 and day == 25:
            return True
        
        # Check if it's a weekend (markets closed)
        weekday = date.weekday()
        if weekday >= 5:  # Saturday = 5, Sunday = 6
            return True
        
        return False
    
    def _get_holiday_name(self, date: datetime) -> str:
        """Get name of holiday for a date."""
        month = date.month
        day = date.day
        
        if month == 1 and day == 1:
            return "New Year's Day"
        elif month == 7 and day == 4:
            return "Independence Day"
        elif month == 12 and day == 25:
            return "Christmas"
        elif date.weekday() >= 5:
            return "Weekend"
        else:
            return "Market Holiday"
    
    def _is_earnings_season(self, date: datetime) -> bool:
        """Check if date is during earnings season."""
        for start_date, end_date in self.earnings_seasons:
            if start_date <= date <= end_date:
                return True
        return False
    
    def _is_fomc_meeting(self, date: datetime) -> bool:
        """Check if date is near an FOMC meeting."""
        # Check within 3 days of FOMC meeting (before and after)
        for meeting_date in self.fomc_meetings:
            days_diff = abs((date - meeting_date).days)
            if days_diff <= 3:
                return True
        return False
    
    def _is_quarter_end(self, date: datetime) -> bool:
        """Check if date is near quarter end."""
        month = date.month
        day = date.day
        
        # Quarter ends: March 31, June 30, September 30, December 31
        quarter_end_months = [3, 6, 9, 12]
        
        if month in quarter_end_months:
            # Check if within last 5 days of month
            last_day = calendar.monthrange(date.year, month)[1]
            if day >= last_day - 5:
                return True
        
        return False
    
    def _is_year_end(self, date: datetime) -> bool:
        """Check if date is near year end."""
        month = date.month
        day = date.day
        
        if month == 12 and day >= 20:  # Last ~10 days of year
            return True
        
        return False
    
    def get_threshold_adjustment(self, date: Optional[datetime] = None) -> float:
        """
        Get threshold adjustment multiplier for anomaly detection.
        
        Args:
            date: Date to analyze (defaults to now)
            
        Returns:
            Multiplier for anomaly thresholds
            - < 1.0: Lower threshold (less volatility expected)
            - 1.0: Normal threshold
            - > 1.0: Higher threshold (more volatility expected)
        """
        context = self.get_context(date)
        return context.threshold_adjustment
    
    def is_high_volatility_expected(self, date: Optional[datetime] = None) -> bool:
        """Check if high volatility is expected for a date."""
        context = self.get_context(date)
        return context.expected_volatility in ['high', 'very_high']

