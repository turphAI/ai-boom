"""
Pattern Analyzer - Identifies recurring failure patterns.

This analyzes execution history to find patterns like:
- Same error happening multiple times
- Errors that correlate with time/date
- Errors that suggest website structure changes
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from collections import Counter
from dataclasses import dataclass

from agents.scraper_monitoring.scraper_monitor import ScraperExecution, ScraperMonitor


@dataclass
class FailurePattern:
    """Represents a detected failure pattern."""
    pattern_type: str  # e.g., 'RECURRING_ERROR', 'WEBSITE_CHANGE', 'RATE_LIMITING'
    scraper_name: str
    error_type: str
    error_message: str
    frequency: int  # How many times this occurred
    first_seen: datetime
    last_seen: datetime
    confidence: float  # 0.0 to 1.0 - how confident we are this is a pattern
    suggested_fix: Optional[str] = None  # Human-readable suggestion
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'pattern_type': self.pattern_type,
            'scraper_name': self.scraper_name,
            'error_type': self.error_type,
            'error_message': self.error_message,
            'frequency': self.frequency,
            'first_seen': self.first_seen.isoformat(),
            'last_seen': self.last_seen.isoformat(),
            'confidence': self.confidence,
            'suggested_fix': self.suggested_fix
        }


class PatternAnalyzer:
    """
    Analyzes scraper execution history to identify failure patterns.
    
    This helps understand:
    - What errors are recurring?
    - Are there patterns in when errors occur?
    - What might be causing the errors?
    
    Usage:
        analyzer = PatternAnalyzer(monitor)
        patterns = analyzer.analyze_patterns()
        for pattern in patterns:
            print(f"Found pattern: {pattern.pattern_type}")
    """
    
    def __init__(self, monitor: ScraperMonitor):
        """
        Initialize pattern analyzer.
        
        Args:
            monitor: ScraperMonitor instance with execution history
        """
        self.monitor = monitor
        self.logger = logging.getLogger(__name__)
    
    def analyze_patterns(self, scraper_name: Optional[str] = None,
                        min_frequency: int = 2) -> List[FailurePattern]:
        """
        Analyze execution history and identify failure patterns.
        
        Args:
            scraper_name: Analyze specific scraper (None for all)
            min_frequency: Minimum occurrences to consider it a pattern
            
        Returns:
            List of detected FailurePattern objects
        """
        self.logger.info(f"🔍 Analyzing failure patterns (min_frequency={min_frequency})...")
        
        # Get failures
        failures = self.monitor.get_recent_failures(scraper_name, limit=1000)
        
        if len(failures) < min_frequency:
            self.logger.info("Not enough failures to detect patterns")
            return []
        
        patterns = []
        
        # Pattern 1: Recurring errors (same error happening multiple times)
        patterns.extend(self._detect_recurring_errors(failures, min_frequency))
        
        # Pattern 2: Website structure changes (selector errors)
        patterns.extend(self._detect_website_changes(failures))
        
        # Pattern 3: Rate limiting patterns
        patterns.extend(self._detect_rate_limiting(failures))
        
        # Pattern 4: Time-based patterns (errors at specific times)
        patterns.extend(self._detect_time_patterns(failures))
        
        # Sort by confidence (highest first)
        patterns.sort(key=lambda p: p.confidence, reverse=True)
        
        self.logger.info(f"✅ Found {len(patterns)} failure patterns")
        
        return patterns
    
    def _detect_recurring_errors(self, failures: List[ScraperExecution],
                                 min_frequency: int) -> List[FailurePattern]:
        """Detect errors that occur repeatedly."""
        patterns = []
        
        # Group failures by error type and message
        error_groups: Dict[str, List[ScraperExecution]] = {}
        
        for failure in failures:
            # Create a key from error type and message
            key = f"{failure.error_type}:{failure.error_message}"
            if key not in error_groups:
                error_groups[key] = []
            error_groups[key].append(failure)
        
        # Find groups with multiple occurrences
        for key, group_failures in error_groups.items():
            if len(group_failures) >= min_frequency:
                # Calculate confidence based on frequency
                # More occurrences = higher confidence
                confidence = min(len(group_failures) / 10.0, 1.0)
                
                # Get first and last occurrence
                timestamps = [f.timestamp for f in group_failures]
                first_seen = min(timestamps)
                last_seen = max(timestamps)
                
                # Generate suggested fix based on error type
                suggested_fix = self._suggest_fix_for_error(
                    group_failures[0].error_type,
                    group_failures[0].error_message
                )
                
                pattern = FailurePattern(
                    pattern_type='RECURRING_ERROR',
                    scraper_name=group_failures[0].scraper_name,
                    error_type=group_failures[0].error_type or 'UNKNOWN',
                    error_message=group_failures[0].error_message or 'Unknown error',
                    frequency=len(group_failures),
                    first_seen=first_seen,
                    last_seen=last_seen,
                    confidence=confidence,
                    suggested_fix=suggested_fix
                )
                
                patterns.append(pattern)
        
        return patterns
    
    def _detect_website_changes(self, failures: List[ScraperExecution]) -> List[FailurePattern]:
        """Detect patterns suggesting website structure changes."""
        patterns = []
        
        # Look for selector/parsing errors
        selector_errors = [
            f for f in failures 
            if f.error_type in ['PARSING_SELECTOR_ERROR', 'PARSING_ERROR']
        ]
        
        if len(selector_errors) >= 2:
            # Group by scraper
            scraper_groups: Dict[str, List[ScraperExecution]] = {}
            for error in selector_errors:
                scraper = error.scraper_name
                if scraper not in scraper_groups:
                    scraper_groups[scraper] = []
                scraper_groups[scraper].append(error)
            
            for scraper, errors in scraper_groups.items():
                if len(errors) >= 2:
                    confidence = min(len(errors) / 5.0, 1.0)
                    
                    timestamps = [e.timestamp for e in errors]
                    first_seen = min(timestamps)
                    last_seen = max(timestamps)
                    
                    pattern = FailurePattern(
                        pattern_type='WEBSITE_STRUCTURE_CHANGE',
                        scraper_name=scraper,
                        error_type='PARSING_SELECTOR_ERROR',
                        error_message=f"Multiple selector/parsing errors detected ({len(errors)} occurrences)",
                        frequency=len(errors),
                        first_seen=first_seen,
                        last_seen=last_seen,
                        confidence=confidence,
                        suggested_fix="Website HTML structure may have changed. Consider updating CSS selectors or XPath expressions."
                    )
                    
                    patterns.append(pattern)
        
        return patterns
    
    def _detect_rate_limiting(self, failures: List[ScraperExecution]) -> List[FailurePattern]:
        """Detect rate limiting patterns."""
        patterns = []
        
        rate_limit_errors = [
            f for f in failures 
            if f.error_type == 'HTTP_429_RATE_LIMIT'
        ]
        
        if len(rate_limit_errors) >= 2:
            # Group by scraper
            scraper_groups: Dict[str, List[ScraperExecution]] = {}
            for error in rate_limit_errors:
                scraper = error.scraper_name
                if scraper not in scraper_groups:
                    scraper_groups[scraper] = []
                scraper_groups[scraper].append(error)
            
            for scraper, errors in scraper_groups.items():
                if len(errors) >= 2:
                    confidence = min(len(errors) / 5.0, 1.0)
                    
                    timestamps = [e.timestamp for e in errors]
                    first_seen = min(timestamps)
                    last_seen = max(timestamps)
                    
                    pattern = FailurePattern(
                        pattern_type='RATE_LIMITING',
                        scraper_name=scraper,
                        error_type='HTTP_429_RATE_LIMIT',
                        error_message=f"Rate limiting detected ({len(errors)} occurrences)",
                        frequency=len(errors),
                        first_seen=first_seen,
                        last_seen=last_seen,
                        confidence=confidence,
                        suggested_fix="Increase retry delays and implement exponential backoff. Consider reducing request frequency."
                    )
                    
                    patterns.append(pattern)
        
        return patterns
    
    def _detect_time_patterns(self, failures: List[ScraperExecution]) -> List[FailurePattern]:
        """Detect time-based patterns (e.g., errors at specific times)."""
        patterns = []
        
        # Group failures by hour of day
        hour_groups: Dict[int, List[ScraperExecution]] = {}
        for failure in failures:
            hour = failure.timestamp.hour
            if hour not in hour_groups:
                hour_groups[hour] = []
            hour_groups[hour].append(failure)
        
        # Find hours with significantly more failures
        if hour_groups:
            avg_failures_per_hour = len(failures) / len(hour_groups)
            threshold = avg_failures_per_hour * 2  # 2x average
            
            for hour, hour_failures in hour_groups.items():
                if len(hour_failures) >= threshold and len(hour_failures) >= 3:
                    # Group by scraper
                    scraper_groups: Dict[str, List[ScraperExecution]] = {}
                    for error in hour_failures:
                        scraper = error.scraper_name
                        if scraper not in scraper_groups:
                            scraper_groups[scraper] = []
                        scraper_groups[scraper].append(error)
                    
                    for scraper, errors in scraper_groups.items():
                        if len(errors) >= 3:
                            confidence = min(len(errors) / 10.0, 0.8)  # Cap at 0.8 for time patterns
                            
                            timestamps = [e.timestamp for e in errors]
                            first_seen = min(timestamps)
                            last_seen = max(timestamps)
                            
                            pattern = FailurePattern(
                                pattern_type='TIME_BASED_PATTERN',
                                scraper_name=scraper,
                                error_type='TIME_CORRELATED',
                                error_message=f"Errors clustered around hour {hour:02d}:00 ({len(errors)} occurrences)",
                                frequency=len(errors),
                                first_seen=first_seen,
                                last_seen=last_seen,
                                confidence=confidence,
                                suggested_fix=f"Errors occur frequently around {hour:02d}:00. May be related to scheduled maintenance or traffic patterns."
                            )
                            
                            patterns.append(pattern)
        
        return patterns
    
    def _suggest_fix_for_error(self, error_type: str, error_message: str) -> str:
        """Generate a suggested fix based on error type."""
        suggestions = {
            'HTTP_404_NOT_FOUND': "The requested URL or endpoint may have been removed. Check if the website structure changed or find alternative data source.",
            'HTTP_403_FORBIDDEN': "Access forbidden. May need to update headers, add authentication, or check if IP is blocked.",
            'HTTP_429_RATE_LIMIT': "Rate limiting detected. Increase delays between requests and implement exponential backoff.",
            'TIMEOUT': "Request timed out. Increase timeout duration or check network connectivity.",
            'CONNECTION_ERROR': "Connection failed. Check network connectivity or if the service is down.",
            'PARSING_SELECTOR_ERROR': "CSS selector or XPath not found. Website HTML structure may have changed. Inspect current HTML and update selectors.",
            'PARSING_ERROR': "Failed to parse response. Check if response format changed or if data is malformed.",
            'EMPTY_DATA': "No data returned. Check if the source still provides data or if query parameters need updating.",
            'VALIDATION_ERROR': "Data validation failed. Check if data format or schema changed.",
        }
        
        return suggestions.get(error_type, "Review error message and check scraper implementation.")
    
    def get_pattern_summary(self, patterns: List[FailurePattern]) -> Dict[str, Any]:
        """Get a summary of detected patterns."""
        if not patterns:
            return {
                'total_patterns': 0,
                'by_type': {},
                'by_scraper': {},
                'highest_confidence': None
            }
        
        by_type = Counter(p.pattern_type for p in patterns)
        by_scraper = Counter(p.scraper_name for p in patterns)
        
        highest_confidence = max(patterns, key=lambda p: p.confidence)
        
        return {
            'total_patterns': len(patterns),
            'by_type': dict(by_type),
            'by_scraper': dict(by_scraper),
            'highest_confidence': {
                'pattern_type': highest_confidence.pattern_type,
                'scraper': highest_confidence.scraper_name,
                'confidence': highest_confidence.confidence,
                'frequency': highest_confidence.frequency
            }
        }

