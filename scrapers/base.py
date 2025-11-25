"""
Base scraper interface for all data scrapers in the Boom-Bust Sentinel system.
"""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
import logging
import time

from models.core import ScraperResult, MetricValue
from services.state_store import create_state_store
from services.alert_service import AlertService
from services.metrics_service import MetricsService
from utils.error_handling import (
    DataValidator, CachedDataManager, CrossValidator,
    retry_with_backoff, RetryConfig, ValidationResult
)


class BaseScraper(ABC):
    """Base class for all data scrapers."""
    
    def __init__(self, data_source: str, metric_name: str):
        self.data_source = data_source
        self.metric_name = metric_name
        self.state_store = create_state_store()
        self.alert_service = AlertService()
        self.metrics_service = MetricsService()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Enhanced error handling components
        self.data_validator = DataValidator(self.logger)
        self.cache_manager = CachedDataManager(cache_ttl_hours=24)
        self.cross_validator = CrossValidator(self.logger)
        
        # Retry configuration for external API calls
        self.retry_config = RetryConfig(
            max_retries=3,
            base_delay=1.0,
            max_delay=30.0,
            backoff_factor=2.0,
            jitter=True
        )
    
    def execute(self) -> ScraperResult:
        """Main execution flow for the scraper with comprehensive error handling."""
        start_time = time.time()
        timestamp = datetime.now(timezone.utc)
        
        try:
            self.logger.info(f"Starting {self.data_source} scraper execution")
            
            # Fetch data with retry (no fallback - real data only)
            current_data = self._fetch_data_with_retry()
            
            # Comprehensive data validation
            validation_result = self._validate_data_comprehensive(current_data)
            
            if not validation_result.is_valid:
                raise ValueError(f"Data validation failed: {', '.join(validation_result.errors)}")
            
            # Log validation warnings
            for warning in validation_result.warnings:
                self.logger.warning(f"Data validation warning: {warning}")
            
            # Get historical data for comparison and anomaly detection
            historical_data = self.get_historical_data()
            historical_data_list = self._get_historical_data_list()
            
            # Cross-validation with multiple sources if available
            cross_validation_result = self._perform_cross_validation(current_data)
            
            # Update confidence based on cross-validation
            final_confidence = min(
                validation_result.confidence,
                cross_validation_result.get('confidence', 1.0)
            )
            current_data['confidence'] = final_confidence
            current_data['validation_checksum'] = validation_result.checksum
            current_data['anomaly_score'] = validation_result.anomaly_score
            
            # Check if we should alert
            if self.should_alert(current_data, historical_data):
                alert_message = self.generate_alert_message(current_data, historical_data)
                self.alert_service.send_alert(alert_message)
            
            # Save current data
            self.state_store.save_data(self.data_source, self.metric_name, current_data)
            
            # Cache data for performance (not for fallback)
            cache_key = f"{self.data_source}_{self.metric_name}"
            self.cache_manager.cache_data(cache_key, current_data)
            
            # Send metrics
            self.send_metrics(current_data)
            
            execution_time = time.time() - start_time
            self.logger.info(f"Successfully completed {self.data_source} scraper in {execution_time:.2f}s")
            
            return ScraperResult(
                data_source=self.data_source,
                metric_name=self.metric_name,
                success=True,
                data=current_data,
                error=None,
                execution_time=execution_time,
                timestamp=timestamp
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Error in {self.data_source} scraper: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            
            # No fallback - fail cleanly
            self.handle_error(e)
            
            return ScraperResult(
                data_source=self.data_source,
                metric_name=self.metric_name,
                success=False,
                data=None,
                error=error_msg,
                execution_time=execution_time,
                timestamp=timestamp
            )
    
    @abstractmethod
    def fetch_data(self) -> Dict[str, Any]:
        """Fetch data from the external source. Must be implemented by subclasses."""
        pass
    
    def _fetch_data_with_retry(self) -> Dict[str, Any]:
        """Fetch data with retry logic (no fallback - real data only)."""
        # Use retry_with_backoff decorator for transient failures, but no fallback to cached/stale data
        @retry_with_backoff(config=self.retry_config)
        def fetch_with_retry():
            return self.fetch_data()
        
        return fetch_with_retry()
    
    def _validate_data_comprehensive(self, data: Dict[str, Any]) -> ValidationResult:
        """Perform comprehensive data validation."""
        # Get data schema for validation
        schema = self.get_data_schema()
        
        # Get historical data for anomaly detection
        historical_data_list = self._get_historical_data_list()
        
        # Perform validation
        validation_result = self.data_validator.validate_data(
            data=data,
            schema=schema,
            historical_data=historical_data_list
        )
        
        return validation_result
    
    def _perform_cross_validation(self, primary_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform cross-validation with secondary data sources."""
        secondary_data = self.get_secondary_data_sources()
        
        if not secondary_data:
            return {'validated': True, 'confidence': 1.0, 'discrepancies': []}
        
        return self.cross_validator.cross_validate(
            primary_data=primary_data,
            secondary_data=secondary_data,
            tolerance=0.1  # 10% tolerance
        )
    
    def _get_historical_data_list(self) -> List[Dict[str, Any]]:
        """Get historical data as a list for anomaly detection."""
        try:
            historical_data = self.state_store.get_historical_data(
                self.data_source, self.metric_name, days=30
            )
            return historical_data if historical_data else []
        except Exception as e:
            self.logger.warning(f"Failed to get historical data: {e}")
            return []
    
    def validate_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean the fetched data. Can be overridden by subclasses."""
        if not data:
            raise ValueError("No data received from source")
        return data
    
    def get_data_schema(self) -> Dict[str, Any]:
        """
        Get data schema for validation. Can be overridden by subclasses.
        
        Returns:
            Schema dictionary with 'required', 'types', and 'ranges' keys
        """
        return {
            'required': ['value', 'timestamp'],
            'types': {
                'value': (int, float),
                'timestamp': (str, datetime),
                'confidence': (int, float)
            },
            'ranges': {
                'confidence': (0.0, 1.0)
            }
        }
    
    def get_secondary_data_sources(self) -> List[Dict[str, Any]]:
        """
        Get secondary data sources for cross-validation.
        Can be overridden by subclasses.
        
        Returns:
            List of secondary data dictionaries
        """
        return []
    
    def get_historical_data(self) -> Optional[Dict[str, Any]]:
        """Get historical data for comparison."""
        return self.state_store.get_latest_value(self.data_source, self.metric_name)
    
    @abstractmethod
    def should_alert(self, current_data: Dict[str, Any], historical_data: Optional[Dict[str, Any]]) -> bool:
        """Determine if an alert should be triggered. Must be implemented by subclasses."""
        pass
    
    @abstractmethod
    def generate_alert_message(self, current_data: Dict[str, Any], historical_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate alert message. Must be implemented by subclasses."""
        pass
    
    def send_metrics(self, data: Dict[str, Any]) -> None:
        """Send metrics to monitoring service."""
        try:
            metric_value = MetricValue(
                value=data.get('value', 0),
                timestamp=datetime.now(timezone.utc),
                confidence=data.get('confidence', 1.0),
                source=self.data_source,
                metadata=data.get('metadata', {})
            )
            self.metrics_service.send_metric(self.data_source, self.metric_name, metric_value)
        except Exception as e:
            self.logger.warning(f"Failed to send metrics: {e}")
    
    def handle_error(self, error: Exception) -> None:
        """Handle errors that occur during scraping."""
        # Log error details
        self.logger.error(f"Scraper error in {self.data_source}: {error}")
        
        # Send error metric
        try:
            error_metric = MetricValue(
                value=1,
                timestamp=datetime.now(timezone.utc),
                confidence=1.0,
                source=self.data_source,
                metadata={'error': str(error), 'error_type': type(error).__name__}
            )
            self.metrics_service.send_metric(self.data_source, 'errors', error_metric)
        except Exception as metrics_error:
            self.logger.error(f"Failed to send error metric: {metrics_error}")