"""
Scraper Monitor - Watches scraper executions and collects error data.

This is Phase 1: Basic monitoring without auto-fixing.
It collects data about scraper runs, failures, and errors for analysis.
"""

import json
import logging
import os
import traceback
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class ScraperExecution:
    """Represents a single scraper execution attempt."""
    scraper_name: str
    data_source: str
    metric_name: str
    success: bool
    execution_time: float
    timestamp: datetime
    error_message: Optional[str] = None
    error_type: Optional[str] = None
    stack_trace: Optional[str] = None
    data_quality: Optional[Dict[str, Any]] = None
    http_status_codes: Optional[List[int]] = None
    html_structure_hash: Optional[str] = None  # Hash of HTML structure for change detection
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        # Convert datetime to ISO string
        data['timestamp'] = self.timestamp.isoformat()
        return data


class ScraperMonitor:
    """
    Monitors scraper executions and collects detailed error information.
    
    This is the foundation of the agent system - it watches what happens
    and collects data for analysis.
    
    Usage:
        monitor = ScraperMonitor()
        
        # Wrap scraper execution
        result = monitor.monitor_execution(
            scraper_name='bdc_discount',
            scraper_instance=scraper,
            execute_func=lambda: scraper.execute()
        )
    """
    
    def __init__(self, log_dir: str = "logs/agent"):
        """
        Initialize the scraper monitor.
        
        Args:
            log_dir: Directory to store execution logs
        """
        self.logger = logging.getLogger(__name__)
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Storage for execution history
        self.execution_history: List[ScraperExecution] = []
        self.max_history_size = 1000  # Keep last 1000 executions
        
        # Statistics
        self.stats = {
            'total_executions': 0,
            'successful': 0,
            'failed': 0,
            'error_types': {},
            'scraper_stats': {}
        }
    
    def monitor_execution(self, scraper_name: str, scraper_instance, 
                         execute_func) -> ScraperExecution:
        """
        Monitor a scraper execution and collect detailed information.
        
        Args:
            scraper_name: Name of the scraper (e.g., 'bdc_discount')
            scraper_instance: The scraper instance being executed
            execute_func: Function that executes the scraper (lambda: scraper.execute())
            
        Returns:
            ScraperExecution object with all collected data
        """
        start_time = datetime.now(timezone.utc)
        execution_start = start_time.timestamp()
        
        execution = ScraperExecution(
            scraper_name=scraper_name,
            data_source=getattr(scraper_instance, 'data_source', 'unknown'),
            metric_name=getattr(scraper_instance, 'metric_name', 'unknown'),
            success=False,
            execution_time=0.0,
            timestamp=start_time
        )
        
        try:
            self.logger.info(f"🔍 Monitoring scraper execution: {scraper_name}")
            
            # Execute the scraper
            result = execute_func()
            
            # Calculate execution time
            execution_time = datetime.now(timezone.utc).timestamp() - execution_start
            
            # Extract information from result
            if hasattr(result, 'success'):
                execution.success = result.success
                execution.execution_time = execution_time
                
                if result.success:
                    execution.data_quality = self._extract_data_quality(result)
                    self.stats['successful'] += 1
                    self.logger.info(f"✅ {scraper_name} succeeded in {execution_time:.2f}s")
                else:
                    execution.error_message = getattr(result, 'error', 'Unknown error')
                    execution.error_type = self._classify_error(execution.error_message)
                    self.stats['failed'] += 1
                    self.logger.warning(f"❌ {scraper_name} failed: {execution.error_message}")
            else:
                # Result doesn't have expected structure
                execution.success = True  # Assume success if no error raised
                execution.execution_time = execution_time
                self.stats['successful'] += 1
                
        except Exception as e:
            # Exception occurred during execution
            execution_time = datetime.now(timezone.utc).timestamp() - execution_start
            execution.success = False
            execution.execution_time = execution_time
            execution.error_message = str(e)
            execution.error_type = type(e).__name__
            execution.stack_trace = traceback.format_exc()
            
            self.stats['failed'] += 1
            self.logger.error(f"❌ {scraper_name} raised exception: {e}")
            self.logger.debug(traceback.format_exc())
        
        # Update statistics
        self._update_stats(execution)
        
        # Store execution
        self._store_execution(execution)
        
        return execution
    
    def _extract_data_quality(self, result) -> Dict[str, Any]:
        """Extract data quality metrics from successful result."""
        quality = {}
        
        if hasattr(result, 'data') and result.data:
            data = result.data
            quality['has_value'] = 'value' in data
            quality['has_timestamp'] = 'timestamp' in data
            quality['confidence'] = data.get('confidence', None)
            quality['anomaly_score'] = data.get('anomaly_score', None)
            quality['validation_checksum'] = data.get('validation_checksum', None)
        
        return quality
    
    def _classify_error(self, error_message: str) -> str:
        """
        Classify error type based on error message.
        
        This helps identify patterns in failures.
        """
        error_lower = error_message.lower()
        
        # HTTP errors
        if '404' in error_message or 'not found' in error_lower:
            return 'HTTP_404_NOT_FOUND'
        elif '403' in error_message or 'forbidden' in error_lower:
            return 'HTTP_403_FORBIDDEN'
        elif '429' in error_message or 'rate limit' in error_lower:
            return 'HTTP_429_RATE_LIMIT'
        elif '500' in error_message or '502' in error_message or '503' in error_message:
            return 'HTTP_5XX_SERVER_ERROR'
        elif 'timeout' in error_lower:
            return 'TIMEOUT'
        elif 'connection' in error_lower:
            return 'CONNECTION_ERROR'
        
        # Parsing errors
        elif 'selector' in error_lower or 'css' in error_lower or 'xpath' in error_lower:
            return 'PARSING_SELECTOR_ERROR'
        elif 'parse' in error_lower or 'parsing' in error_lower:
            return 'PARSING_ERROR'
        elif 'empty' in error_lower or 'no data' in error_lower:
            return 'EMPTY_DATA'
        
        # Validation errors
        elif 'validation' in error_lower or 'invalid' in error_lower:
            return 'VALIDATION_ERROR'
        
        # Generic
        else:
            return 'UNKNOWN_ERROR'
    
    def _update_stats(self, execution: ScraperExecution):
        """Update statistics based on execution result."""
        self.stats['total_executions'] += 1
        
        # Track error types
        if execution.error_type:
            self.stats['error_types'][execution.error_type] = \
                self.stats['error_types'].get(execution.error_type, 0) + 1
        
        # Track scraper-specific stats
        if execution.scraper_name not in self.stats['scraper_stats']:
            self.stats['scraper_stats'][execution.scraper_name] = {
                'total': 0,
                'successful': 0,
                'failed': 0
            }
        
        scraper_stat = self.stats['scraper_stats'][execution.scraper_name]
        scraper_stat['total'] += 1
        if execution.success:
            scraper_stat['successful'] += 1
        else:
            scraper_stat['failed'] += 1
    
    def _store_execution(self, execution: ScraperExecution):
        """Store execution in history and log file."""
        # Add to history
        self.execution_history.append(execution)
        
        # Keep history size manageable
        if len(self.execution_history) > self.max_history_size:
            self.execution_history = self.execution_history[-self.max_history_size:]
        
        # Write to log file (append mode)
        log_file = self.log_dir / f"{execution.scraper_name}_executions.jsonl"
        with open(log_file, 'a') as f:
            f.write(json.dumps(execution.to_dict()) + '\n')
    
    def get_recent_failures(self, scraper_name: Optional[str] = None, 
                           limit: int = 10) -> List[ScraperExecution]:
        """
        Get recent failed executions.
        
        Args:
            scraper_name: Filter by scraper name (None for all)
            limit: Maximum number of failures to return
            
        Returns:
            List of failed ScraperExecution objects
        """
        failures = [
            ex for ex in self.execution_history 
            if not ex.success and (scraper_name is None or ex.scraper_name == scraper_name)
        ]
        
        # Sort by timestamp (most recent first)
        failures.sort(key=lambda x: x.timestamp, reverse=True)
        
        return failures[:limit]
    
    def get_error_patterns(self, scraper_name: Optional[str] = None) -> Dict[str, int]:
        """
        Get error pattern counts.
        
        Args:
            scraper_name: Filter by scraper name (None for all)
            
        Returns:
            Dictionary mapping error types to counts
        """
        if scraper_name:
            failures = [ex for ex in self.execution_history 
                       if not ex.success and ex.scraper_name == scraper_name]
        else:
            failures = [ex for ex in self.execution_history if not ex.success]
        
        patterns = {}
        for failure in failures:
            error_type = failure.error_type or 'UNKNOWN_ERROR'
            patterns[error_type] = patterns.get(error_type, 0) + 1
        
        return patterns
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get overall statistics."""
        return {
            **self.stats,
            'success_rate': (
                self.stats['successful'] / self.stats['total_executions'] 
                if self.stats['total_executions'] > 0 else 0.0
            ),
            'total_history_size': len(self.execution_history)
        }
    
    def export_history(self, filepath: str):
        """Export execution history to JSON file."""
        history_data = [ex.to_dict() for ex in self.execution_history]
        
        with open(filepath, 'w') as f:
            json.dump({
                'exported_at': datetime.now(timezone.utc).isoformat(),
                'total_executions': len(history_data),
                'executions': history_data,
                'statistics': self.get_statistics()
            }, f, indent=2)
        
        self.logger.info(f"Exported {len(history_data)} executions to {filepath}")

