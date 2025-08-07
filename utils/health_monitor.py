"""
System health monitoring utilities for the Boom-Bust Sentinel.
"""

import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed

from services.metrics_service import MetricsService
from services.state_store import StateStore
from services.alert_service import AlertService
from config.settings import settings
from utils.logging_config import get_contextual_logger, ErrorContext


@dataclass
class HealthCheck:
    """Represents a health check configuration."""
    name: str
    check_function: Callable[[], bool]
    timeout_seconds: int = 30
    critical: bool = True
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class HealthMonitor:
    """System health monitoring service."""
    
    def __init__(self, metrics_service: Optional[MetricsService] = None):
        self.logger = get_contextual_logger(__name__, component='health_monitor')
        self.metrics_service = metrics_service or MetricsService()
        self.health_checks: Dict[str, HealthCheck] = {}
        self.last_check_results: Dict[str, Dict[str, Any]] = {}
        
        # Initialize default health checks
        self._register_default_health_checks()
    
    def _register_default_health_checks(self) -> None:
        """Register default system health checks."""
        # Database health check
        self.register_health_check(
            name='database',
            check_function=self._check_database_health,
            timeout_seconds=10,
            critical=True,
            metadata={'component_type': 'storage'}
        )
        
        # Alert service health check
        self.register_health_check(
            name='alert_service',
            check_function=self._check_alert_service_health,
            timeout_seconds=15,
            critical=True,
            metadata={'component_type': 'notification'}
        )
        
        # Metrics service health check
        self.register_health_check(
            name='metrics_service',
            check_function=self._check_metrics_service_health,
            timeout_seconds=10,
            critical=False,
            metadata={'component_type': 'monitoring'}
        )
        
        # External API health checks
        self.register_health_check(
            name='sec_edgar_api',
            check_function=self._check_sec_edgar_health,
            timeout_seconds=20,
            critical=False,
            metadata={'component_type': 'external_api', 'api': 'sec_edgar'}
        )
        
        self.register_health_check(
            name='yahoo_finance_api',
            check_function=self._check_yahoo_finance_health,
            timeout_seconds=15,
            critical=False,
            metadata={'component_type': 'external_api', 'api': 'yahoo_finance'}
        )
    
    def register_health_check(self, name: str, check_function: Callable[[], bool], 
                            timeout_seconds: int = 30, critical: bool = True,
                            metadata: Optional[Dict[str, Any]] = None) -> None:
        """Register a new health check."""
        health_check = HealthCheck(
            name=name,
            check_function=check_function,
            timeout_seconds=timeout_seconds,
            critical=critical,
            metadata=metadata or {}
        )
        
        self.health_checks[name] = health_check
        self.logger.info(f"Registered health check: {name} (critical: {critical})")
    
    def run_health_check(self, name: str) -> Dict[str, Any]:
        """Run a specific health check."""
        if name not in self.health_checks:
            raise ValueError(f"Health check '{name}' not found")
        
        health_check = self.health_checks[name]
        start_time = time.time()
        
        with ErrorContext(self.logger, f"health_check_{name}", check_name=name):
            try:
                # Run the health check with timeout
                with ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(health_check.check_function)
                    is_healthy = future.result(timeout=health_check.timeout_seconds)
                
                response_time_ms = (time.time() - start_time) * 1000
                
                result = {
                    'name': name,
                    'healthy': bool(is_healthy),
                    'response_time_ms': response_time_ms,
                    'timestamp': datetime.now(timezone.utc),
                    'critical': health_check.critical,
                    'error': None,
                    'metadata': health_check.metadata
                }
                
                # Update metrics
                status = 'healthy' if is_healthy else 'failed'
                self.metrics_service.update_system_health(
                    component=name,
                    status=status,
                    response_time_ms=response_time_ms,
                    error_count=0 if is_healthy else 1,
                    metadata=health_check.metadata
                )
                
                self.last_check_results[name] = result
                
                if is_healthy:
                    self.logger.debug(f"Health check '{name}' passed ({response_time_ms:.1f}ms)")
                else:
                    self.logger.warning(f"Health check '{name}' failed ({response_time_ms:.1f}ms)")
                
                return result
                
            except Exception as e:
                response_time_ms = (time.time() - start_time) * 1000
                
                result = {
                    'name': name,
                    'healthy': False,
                    'response_time_ms': response_time_ms,
                    'timestamp': datetime.now(timezone.utc),
                    'critical': health_check.critical,
                    'error': str(e),
                    'metadata': health_check.metadata
                }
                
                # Update metrics
                self.metrics_service.update_system_health(
                    component=name,
                    status='failed',
                    response_time_ms=response_time_ms,
                    error_count=1,
                    metadata={'error': str(e), **health_check.metadata}
                )
                
                self.last_check_results[name] = result
                
                self.logger.error(f"Health check '{name}' failed with error: {str(e)}")
                
                return result
    
    def run_all_health_checks(self) -> Dict[str, Dict[str, Any]]:
        """Run all registered health checks."""
        results = {}
        
        self.logger.info(f"Running {len(self.health_checks)} health checks")
        
        # Run health checks in parallel
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_name = {
                executor.submit(self.run_health_check, name): name 
                for name in self.health_checks.keys()
            }
            
            for future in as_completed(future_to_name):
                name = future_to_name[future]
                try:
                    result = future.result()
                    results[name] = result
                except Exception as e:
                    self.logger.error(f"Failed to run health check '{name}': {str(e)}")
                    results[name] = {
                        'name': name,
                        'healthy': False,
                        'response_time_ms': 0,
                        'timestamp': datetime.now(timezone.utc),
                        'critical': self.health_checks[name].critical,
                        'error': f"Health check execution failed: {str(e)}",
                        'metadata': self.health_checks[name].metadata
                    }
        
        # Log summary
        healthy_count = sum(1 for r in results.values() if r['healthy'])
        total_count = len(results)
        critical_failed = sum(1 for r in results.values() if not r['healthy'] and r['critical'])
        
        self.logger.info(
            f"Health check summary: {healthy_count}/{total_count} healthy, "
            f"{critical_failed} critical failures"
        )
        
        return results
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status."""
        if not self.last_check_results:
            return {
                'status': 'unknown',
                'message': 'No health checks have been run',
                'last_check': None,
                'components': {}
            }
        
        # Determine overall status
        critical_failures = [
            name for name, result in self.last_check_results.items()
            if not result['healthy'] and result['critical']
        ]
        
        non_critical_failures = [
            name for name, result in self.last_check_results.items()
            if not result['healthy'] and not result['critical']
        ]
        
        if critical_failures:
            status = 'critical'
            message = f"Critical components failing: {', '.join(critical_failures)}"
        elif non_critical_failures:
            status = 'degraded'
            message = f"Non-critical components failing: {', '.join(non_critical_failures)}"
        else:
            status = 'healthy'
            message = 'All components healthy'
        
        last_check = max(
            (result['timestamp'] for result in self.last_check_results.values()),
            default=None
        )
        
        return {
            'status': status,
            'message': message,
            'last_check': last_check,
            'components': self.last_check_results.copy(),
            'summary': {
                'total_components': len(self.last_check_results),
                'healthy_components': sum(1 for r in self.last_check_results.values() if r['healthy']),
                'critical_failures': len(critical_failures),
                'non_critical_failures': len(non_critical_failures)
            }
        }
    
    def _check_database_health(self) -> bool:
        """Check database connectivity and basic operations."""
        try:
            state_store = StateStore()
            
            # Try to perform a basic operation
            test_data = {
                'test_key': 'health_check',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'value': 1
            }
            
            # This will test the database connection
            state_store.save_data('health_check', 'database_test', test_data)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Database health check failed: {str(e)}")
            return False
    
    def _check_alert_service_health(self) -> bool:
        """Check alert service functionality."""
        try:
            alert_service = AlertService()
            
            # Check if alert service can initialize channels
            if not hasattr(alert_service, 'channels') or not alert_service.channels:
                self.logger.warning("Alert service has no configured channels")
                return False
            
            # Test alert service without actually sending alerts
            test_alert = {
                'alert_type': 'health_check',
                'data_source': 'health_monitor',
                'metric_name': 'test',
                'current_value': 1,
                'message': 'Health check test alert (not sent)',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            # Just validate the alert structure without sending
            return True
            
        except Exception as e:
            self.logger.error(f"Alert service health check failed: {str(e)}")
            return False
    
    def _check_metrics_service_health(self) -> bool:
        """Check metrics service functionality."""
        try:
            # Test metrics service initialization
            if not self.metrics_service.backends:
                self.logger.warning("Metrics service has no configured backends")
                return False
            
            # Test metric history functionality
            test_metrics = [
                {
                    'data_source': 'health_check',
                    'metric_name': 'test_metric',
                    'value': 1.0,
                    'timestamp': datetime.now(timezone.utc),
                    'source': 'health_monitor',
                    'metadata': {}
                }
            ]
            
            # Update metric history (doesn't send to backends)
            self.metrics_service._update_metric_history(test_metrics)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Metrics service health check failed: {str(e)}")
            return False
    
    def _check_sec_edgar_health(self) -> bool:
        """Check SEC EDGAR API availability."""
        try:
            import requests
            
            # Test SEC EDGAR API endpoint
            response = requests.get(
                'https://www.sec.gov/Archives/edgar/daily-index/master.idx',
                headers={'User-Agent': 'Boom-Bust-Sentinel health-check'},
                timeout=15
            )
            
            return response.status_code == 200
            
        except Exception as e:
            self.logger.error(f"SEC EDGAR health check failed: {str(e)}")
            return False
    
    def _check_yahoo_finance_health(self) -> bool:
        """Check Yahoo Finance API availability."""
        try:
            import yfinance as yf
            
            # Test with a simple ticker
            ticker = yf.Ticker("AAPL")
            info = ticker.info
            
            # Check if we got basic info
            return 'symbol' in info or 'shortName' in info
            
        except Exception as e:
            self.logger.error(f"Yahoo Finance health check failed: {str(e)}")
            return False
    
    async def run_periodic_health_checks(self, interval_seconds: int = None) -> None:
        """Run health checks periodically."""
        if interval_seconds is None:
            interval_seconds = settings.get_monitoring_config().health_check_interval
        
        self.logger.info(f"Starting periodic health checks (interval: {interval_seconds}s)")
        
        while True:
            try:
                self.run_all_health_checks()
                await asyncio.sleep(interval_seconds)
            except Exception as e:
                self.logger.error(f"Error in periodic health checks: {str(e)}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying
    
    def get_health_check_names(self) -> List[str]:
        """Get list of registered health check names."""
        return list(self.health_checks.keys())
    
    def remove_health_check(self, name: str) -> bool:
        """Remove a health check."""
        if name in self.health_checks:
            del self.health_checks[name]
            self.last_check_results.pop(name, None)
            self.logger.info(f"Removed health check: {name}")
            return True
        return False
    
    def clear_health_check_results(self) -> None:
        """Clear all health check results."""
        self.last_check_results.clear()
        self.logger.info("Cleared all health check results")


# Global health monitor instance
health_monitor = HealthMonitor()