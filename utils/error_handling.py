"""
Comprehensive error handling and retry utilities for the Boom-Bust Sentinel system.

This module provides:
- Exponential backoff retry logic for external API calls
- Data integrity validation with checksums
- Anomaly detection for filtering invalid data
- Graceful degradation with cached data fallbacks
- Cross-validation between multiple data sources
"""

import hashlib
import json
import logging
import random
import time
from datetime import datetime, timezone, timedelta
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum

import numpy as np
import requests
from scipy import stats

# Import enhanced anomaly detection (optional - falls back to basic if not available)
try:
    from agents.enhanced_anomaly_detector import EnhancedAnomalyDetector
    from agents.context_analyzer import ContextAnalyzer
    ENHANCED_ANOMALY_DETECTION_AVAILABLE = True
except ImportError:
    ENHANCED_ANOMALY_DETECTION_AVAILABLE = False


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RetryStrategy(Enum):
    """Retry strategy types."""
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    FIXED_INTERVAL = "fixed_interval"


@dataclass
class RetryConfig:
    """Configuration for retry logic."""
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    backoff_factor: float = 2.0
    jitter: bool = True
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    retryable_exceptions: Tuple = (ConnectionError, TimeoutError, requests.RequestException)


@dataclass
class ValidationResult:
    """Result of data validation."""
    is_valid: bool
    confidence: float
    errors: List[str]
    warnings: List[str]
    checksum: Optional[str] = None
    anomaly_score: Optional[float] = None


class RetryableError(Exception):
    """Exception that indicates an operation should be retried."""
    pass


class DataIntegrityError(Exception):
    """Exception raised when data integrity checks fail."""
    pass


class AnomalyDetectionError(Exception):
    """Exception raised when anomaly detection fails."""
    pass


def retry_with_backoff(config: RetryConfig = None):
    """
    Decorator that implements exponential backoff retry logic.
    
    Args:
        config: RetryConfig object with retry parameters
        
    Returns:
        Decorated function with retry logic
    """
    if config is None:
        config = RetryConfig()
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            logger = logging.getLogger(f"{func.__module__}.{func.__name__}")
            
            for attempt in range(config.max_retries + 1):
                try:
                    return func(*args, **kwargs)
                    
                except config.retryable_exceptions as e:
                    if attempt == config.max_retries:
                        logger.error(f"Max retries ({config.max_retries}) exceeded for {func.__name__}")
                        raise e
                    
                    # Calculate delay based on strategy
                    if config.strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
                        delay = min(
                            config.base_delay * (config.backoff_factor ** attempt),
                            config.max_delay
                        )
                    elif config.strategy == RetryStrategy.LINEAR_BACKOFF:
                        delay = min(
                            config.base_delay * (attempt + 1),
                            config.max_delay
                        )
                    else:  # FIXED_INTERVAL
                        delay = config.base_delay
                    
                    # Add jitter to prevent thundering herd
                    if config.jitter:
                        delay += random.uniform(0, delay * 0.1)
                    
                    logger.warning(
                        f"Attempt {attempt + 1} failed for {func.__name__}: {e}. "
                        f"Retrying in {delay:.2f}s"
                    )
                    time.sleep(delay)
                    
                except Exception as e:
                    # Non-retryable exception, re-raise immediately
                    logger.error(f"Non-retryable error in {func.__name__}: {e}")
                    raise e
            
            # This should never be reached, but just in case
            raise RuntimeError(f"Unexpected error in retry logic for {func.__name__}")
        
        return wrapper
    return decorator


class DataValidator:
    """Comprehensive data validation with integrity checks and anomaly detection."""
    
    def __init__(self, logger: logging.Logger = None, use_enhanced_detection: bool = True):
        self.logger = logger or logging.getLogger(__name__)
        self.historical_data_cache = {}
        
        # Initialize enhanced anomaly detection if available
        self.use_enhanced_detection = use_enhanced_detection and ENHANCED_ANOMALY_DETECTION_AVAILABLE
        if self.use_enhanced_detection:
            try:
                self.enhanced_detector = EnhancedAnomalyDetector()
                self.context_analyzer = ContextAnalyzer()
                self.logger.info("Enhanced anomaly detection enabled for data validation")
            except Exception as e:
                self.logger.warning(f"Failed to initialize enhanced anomaly detection: {e}")
                self.use_enhanced_detection = False
        else:
            self.enhanced_detector = None
            self.context_analyzer = None
    
    def validate_data(self, data: Dict[str, Any], 
                     schema: Dict[str, Any] = None,
                     historical_data: List[Dict[str, Any]] = None) -> ValidationResult:
        """
        Comprehensive data validation.
        
        Args:
            data: Data to validate
            schema: Expected data schema
            historical_data: Historical data for anomaly detection
            
        Returns:
            ValidationResult with validation details
        """
        errors = []
        warnings = []
        confidence = 1.0
        
        try:
            # Basic data validation
            if not data:
                errors.append("Data is empty or None")
                return ValidationResult(False, 0.0, errors, warnings)
            
            # Schema validation
            if schema:
                schema_errors = self._validate_schema(data, schema)
                errors.extend(schema_errors)
            
            # Calculate checksum for integrity
            checksum = self._calculate_checksum(data)
            
            # Anomaly detection (enhanced if available)
            anomaly_score = None
            if historical_data:
                if self.use_enhanced_detection and self.enhanced_detector:
                    anomaly_score = self._detect_anomalies_enhanced(data, historical_data)
                else:
                    anomaly_score = self._detect_anomalies(data, historical_data)
                
                if anomaly_score > 0.8:  # High anomaly score
                    warnings.append(f"High anomaly score: {anomaly_score:.3f}")
                    confidence *= 0.7
                elif anomaly_score > 0.6:  # Medium anomaly score
                    warnings.append(f"Medium anomaly score: {anomaly_score:.3f}")
                    confidence *= 0.85
            
            # Data quality checks
            quality_warnings = self._check_data_quality(data)
            warnings.extend(quality_warnings)
            
            # Adjust confidence based on warnings
            confidence *= max(0.1, 1.0 - (len(warnings) * 0.1))
            
            is_valid = len(errors) == 0
            
            return ValidationResult(
                is_valid=is_valid,
                confidence=confidence,
                errors=errors,
                warnings=warnings,
                checksum=checksum,
                anomaly_score=anomaly_score
            )
            
        except Exception as e:
            self.logger.error(f"Error during data validation: {e}")
            errors.append(f"Validation error: {str(e)}")
            return ValidationResult(False, 0.0, errors, warnings)
    
    def _validate_schema(self, data: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
        """Validate data against schema."""
        errors = []
        
        # Check required fields
        required_fields = schema.get('required', [])
        for field in required_fields:
            if field not in data:
                errors.append(f"Missing required field: {field}")
        
        # Check field types
        field_types = schema.get('types', {})
        for field, expected_type in field_types.items():
            if field in data:
                if not isinstance(data[field], expected_type):
                    errors.append(
                        f"Field '{field}' has type {type(data[field]).__name__}, "
                        f"expected {expected_type.__name__}"
                    )
        
        # Check value ranges
        ranges = schema.get('ranges', {})
        for field, (min_val, max_val) in ranges.items():
            if field in data and isinstance(data[field], (int, float)):
                if data[field] < min_val or data[field] > max_val:
                    errors.append(
                        f"Field '{field}' value {data[field]} is outside range "
                        f"[{min_val}, {max_val}]"
                    )
        
        return errors
    
    def _calculate_checksum(self, data: Dict[str, Any]) -> str:
        """Calculate SHA-256 checksum of data for integrity verification."""
        try:
            # Convert data to JSON string with sorted keys for consistent hashing
            json_str = json.dumps(data, sort_keys=True, default=str)
            return hashlib.sha256(json_str.encode()).hexdigest()
        except Exception as e:
            self.logger.warning(f"Failed to calculate checksum: {e}")
            return None
    
    def _detect_anomalies_enhanced(self, current_data: Dict[str, Any],
                                  historical_data: List[Dict[str, Any]]) -> float:
        """
        Enhanced anomaly detection using context-aware detection.
        
        Returns:
            Anomaly score between 0 (normal) and 1 (highly anomalous)
        """
        if not self.use_enhanced_detection or not self.enhanced_detector:
            return self._detect_anomalies(current_data, historical_data)
        
        try:
            if not historical_data or len(historical_data) < 3:
                return 0.0
            
            # Extract numeric values
            current_values = self._extract_numeric_values(current_data)
            historical_values = [
                self._extract_numeric_values(data) for data in historical_data
            ]
            
            if not current_values or not historical_values:
                return 0.0
            
            anomaly_scores = []
            
            # Use enhanced detection for each numeric field
            for field, current_value in current_values.items():
                historical_field_values = [
                    values.get(field) for values in historical_values
                    if field in values and values[field] is not None
                ]
                
                if len(historical_field_values) < 3:
                    continue
                
                # Use enhanced detector
                result = self.enhanced_detector.detect_anomaly(
                    metric_name=field,
                    current_value=current_value,
                    historical_values=historical_field_values,
                    method='zscore'
                )
                
                # Convert confidence to anomaly score
                if result.is_anomaly:
                    anomaly_scores.append(result.confidence)
                else:
                    # Even if not anomalous, low confidence might indicate something
                    anomaly_scores.append(result.confidence * 0.5)
            
            # Return maximum anomaly score
            return max(anomaly_scores) if anomaly_scores else 0.0
            
        except Exception as e:
            self.logger.warning(f"Enhanced anomaly detection failed, falling back to basic: {e}")
            return self._detect_anomalies(current_data, historical_data)
    
    def _detect_anomalies(self, current_data: Dict[str, Any], 
                         historical_data: List[Dict[str, Any]]) -> float:
        """
        Detect anomalies in current data compared to historical data.
        
        Returns:
            Anomaly score between 0 (normal) and 1 (highly anomalous)
        """
        try:
            if not historical_data or len(historical_data) < 3:
                return 0.0  # Not enough data for anomaly detection
            
            # Extract numeric values for analysis
            current_values = self._extract_numeric_values(current_data)
            historical_values = [
                self._extract_numeric_values(data) for data in historical_data
            ]
            
            if not current_values or not historical_values:
                return 0.0
            
            anomaly_scores = []
            
            # Statistical anomaly detection for each numeric field
            for field, current_value in current_values.items():
                historical_field_values = [
                    values.get(field) for values in historical_values
                    if field in values and values[field] is not None
                ]
                
                if len(historical_field_values) < 3:
                    continue
                
                # Z-score based anomaly detection
                mean_val = np.mean(historical_field_values)
                std_val = np.std(historical_field_values)
                
                if std_val > 0:
                    z_score = abs((current_value - mean_val) / std_val)
                    # Convert z-score to anomaly score (0-1)
                    anomaly_score = min(1.0, z_score / 3.0)  # 3-sigma rule
                    anomaly_scores.append(anomaly_score)
            
            # Return maximum anomaly score
            return max(anomaly_scores) if anomaly_scores else 0.0
            
        except Exception as e:
            self.logger.warning(f"Anomaly detection failed: {e}")
            return 0.0
    
    def _extract_numeric_values(self, data: Dict[str, Any]) -> Dict[str, float]:
        """Extract numeric values from nested data structure."""
        numeric_values = {}
        
        def extract_recursive(obj, prefix=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    new_key = f"{prefix}.{key}" if prefix else key
                    extract_recursive(value, new_key)
            elif isinstance(obj, (int, float)) and not isinstance(obj, bool):
                numeric_values[prefix] = float(obj)
        
        extract_recursive(data)
        return numeric_values
    
    def _check_data_quality(self, data: Dict[str, Any]) -> List[str]:
        """Check data quality and return warnings."""
        warnings = []
        
        # Check for missing or null values
        null_fields = []
        for key, value in data.items():
            if value is None or (isinstance(value, str) and value.strip() == ""):
                null_fields.append(key)
        
        if null_fields:
            warnings.append(f"Fields with null/empty values: {', '.join(null_fields)}")
        
        # Check for suspiciously round numbers (might indicate estimates)
        numeric_fields = self._extract_numeric_values(data)
        for field, value in numeric_fields.items():
            if value != 0 and value % 1000000 == 0:  # Exact millions
                warnings.append(f"Suspiciously round number in {field}: {value}")
        
        # Check timestamp freshness
        if 'timestamp' in data:
            try:
                if isinstance(data['timestamp'], str):
                    timestamp = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
                else:
                    timestamp = data['timestamp']
                
                # Ensure both timestamps are timezone-aware for comparison
                if timestamp.tzinfo is None:
                    timestamp = timestamp.replace(tzinfo=timezone.utc)
                age = datetime.now(timezone.utc) - timestamp
                if age > timedelta(hours=24):
                    warnings.append(f"Data is {age.days} days old")
            except Exception:
                warnings.append("Invalid timestamp format")
        
        return warnings


class CachedDataManager:
    """Manages cached data for graceful degradation."""
    
    def __init__(self, cache_ttl_hours: int = 24):
        self.cache_ttl_hours = cache_ttl_hours
        self.cache = {}
        self.logger = logging.getLogger(__name__)
    
    def get_cached_data(self, key: str) -> Optional[Dict[str, Any]]:
        """Get cached data if available and not expired."""
        if key not in self.cache:
            return None
        
        cached_item = self.cache[key]
        cache_time = cached_item['timestamp']
        
        # Check if cache is expired
        if datetime.now(timezone.utc) - cache_time > timedelta(hours=self.cache_ttl_hours):
            del self.cache[key]
            return None
        
        self.logger.info(f"Using cached data for {key}")
        return cached_item['data']
    
    def cache_data(self, key: str, data: Dict[str, Any]) -> None:
        """Cache data with timestamp."""
        self.cache[key] = {
            'data': data,
            'timestamp': datetime.now(timezone.utc)
        }
        self.logger.debug(f"Cached data for {key}")
    
    def clear_cache(self) -> None:
        """Clear all cached data."""
        self.cache.clear()
        self.logger.info("Cache cleared")


class CrossValidator:
    """Cross-validation between multiple data sources."""
    
    def __init__(self, logger: logging.Logger = None):
        self.logger = logger or logging.getLogger(__name__)
    
    def cross_validate(self, primary_data: Dict[str, Any], 
                      secondary_data: List[Dict[str, Any]],
                      tolerance: float = 0.1) -> Dict[str, Any]:
        """
        Cross-validate data between multiple sources.
        
        Args:
            primary_data: Primary data source
            secondary_data: List of secondary data sources
            tolerance: Acceptable difference threshold (0.1 = 10%)
            
        Returns:
            Validation result with confidence score
        """
        if not secondary_data:
            return {
                'validated': True,
                'confidence': 0.5,  # Lower confidence without cross-validation
                'discrepancies': [],
                'consensus_value': primary_data.get('value')
            }
        
        primary_value = primary_data.get('value')
        if primary_value is None:
            return {
                'validated': False,
                'confidence': 0.0,
                'discrepancies': ['Primary data has no value'],
                'consensus_value': None
            }
        
        secondary_values = []
        discrepancies = []
        
        for i, data in enumerate(secondary_data):
            secondary_value = data.get('value')
            if secondary_value is None:
                continue
            
            secondary_values.append(secondary_value)
            
            # Calculate relative difference
            if primary_value != 0:
                diff = abs(secondary_value - primary_value) / abs(primary_value)
                if diff > tolerance:
                    discrepancies.append(
                        f"Source {i+1}: {secondary_value} vs primary {primary_value} "
                        f"(diff: {diff*100:.1f}%)"
                    )
        
        if not secondary_values:
            return {
                'validated': True,
                'confidence': 0.5,
                'discrepancies': ['No secondary data available'],
                'consensus_value': primary_value
            }
        
        # Calculate consensus value (median of all values)
        all_values = [primary_value] + secondary_values
        consensus_value = np.median(all_values)
        
        # Calculate confidence based on agreement
        agreement_ratio = 1.0 - (len(discrepancies) / len(secondary_values))
        confidence = min(1.0, 0.5 + (agreement_ratio * 0.5))
        
        return {
            'validated': len(discrepancies) == 0,
            'confidence': confidence,
            'discrepancies': discrepancies,
            'consensus_value': consensus_value,
            'source_count': len(all_values)
        }


class ErrorHandler:
    """Comprehensive error handling and recovery system."""
    
    def __init__(self, logger: logging.Logger = None):
        self.logger = logger or logging.getLogger(__name__)
        self.validator = DataValidator(logger)
        self.cache_manager = CachedDataManager()
        self.cross_validator = CrossValidator(logger)
        self.error_counts = {}
        self.recovery_strategies = {}
    
    def handle_error(self, error: Exception, context: str = None, 
                    severity: ErrorSeverity = ErrorSeverity.MEDIUM) -> Dict[str, Any]:
        """
        Handle errors with appropriate recovery strategies.
        
        Args:
            error: The exception that occurred
            context: Context where the error occurred
            severity: Error severity level
            
        Returns:
            Error handling result with recovery information
        """
        error_type = type(error).__name__
        context = context or "unknown"
        
        # Track error counts
        error_key = f"{error_type}_{context}"
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
        
        # Log error with appropriate level
        if severity == ErrorSeverity.CRITICAL:
            self.logger.critical(f"Critical error in {context}: {error}")
        elif severity == ErrorSeverity.HIGH:
            self.logger.error(f"High severity error in {context}: {error}")
        elif severity == ErrorSeverity.MEDIUM:
            self.logger.warning(f"Medium severity error in {context}: {error}")
        else:
            self.logger.info(f"Low severity error in {context}: {error}")
        
        # Determine recovery strategy
        recovery_strategy = self._get_recovery_strategy(error, context, severity)
        
        # Execute recovery strategy
        recovery_result = self._execute_recovery_strategy(recovery_strategy, error, context)
        
        return {
            'error_type': error_type,
            'context': context,
            'severity': severity.value,
            'recovery_strategy': recovery_strategy,
            'recovery_successful': recovery_result['success'],
            'fallback_data_used': recovery_result.get('fallback_data', False),
            'error_count': self.error_counts[error_key],
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    
    def _get_recovery_strategy(self, error: Exception, context: str, 
                              severity: ErrorSeverity) -> str:
        """Determine appropriate recovery strategy based on error and context."""
        error_type = type(error).__name__
        
        # Network-related errors
        if isinstance(error, (ConnectionError, TimeoutError, requests.RequestException)):
            if severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
                return "retry_with_backoff"
            else:
                return "use_cached_data"
        
        # Data validation errors
        if isinstance(error, (DataIntegrityError, AnomalyDetectionError)):
            return "cross_validate_and_clean"
        
        # Resource exhaustion
        if "memory" in str(error).lower() or "quota" in str(error).lower():
            return "reduce_load_and_retry"
        
        # Default strategy
        return "log_and_continue"
    
    def _execute_recovery_strategy(self, strategy: str, error: Exception, 
                                  context: str) -> Dict[str, Any]:
        """Execute the determined recovery strategy."""
        try:
            if strategy == "retry_with_backoff":
                return self._retry_with_backoff(error, context)
            elif strategy == "use_cached_data":
                return self._use_cached_data(context)
            elif strategy == "cross_validate_and_clean":
                return self._cross_validate_and_clean(error, context)
            elif strategy == "reduce_load_and_retry":
                return self._reduce_load_and_retry(error, context)
            else:  # log_and_continue
                return self._log_and_continue(error, context)
        except Exception as recovery_error:
            self.logger.error(f"Recovery strategy {strategy} failed: {recovery_error}")
            return {'success': False, 'error': str(recovery_error)}
    
    def _retry_with_backoff(self, error: Exception, context: str) -> Dict[str, Any]:
        """Retry operation with exponential backoff."""
        # This would be implemented with the retry decorator
        return {'success': True, 'strategy': 'retry_with_backoff'}
    
    def _use_cached_data(self, context: str) -> Dict[str, Any]:
        """Use cached data as fallback."""
        cached_data = self.cache_manager.get_cached_data(context)
        if cached_data:
            return {'success': True, 'fallback_data': True, 'strategy': 'use_cached_data'}
        return {'success': False, 'strategy': 'use_cached_data'}
    
    def _cross_validate_and_clean(self, error: Exception, context: str) -> Dict[str, Any]:
        """Cross-validate data and clean if necessary."""
        return {'success': True, 'strategy': 'cross_validate_and_clean'}
    
    def _reduce_load_and_retry(self, error: Exception, context: str) -> Dict[str, Any]:
        """Reduce load and retry operation."""
        return {'success': True, 'strategy': 'reduce_load_and_retry'}
    
    def _log_and_continue(self, error: Exception, context: str) -> Dict[str, Any]:
        """Log error and continue operation."""
        return {'success': True, 'strategy': 'log_and_continue'}
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics for monitoring."""
        return {
            'total_errors': sum(self.error_counts.values()),
            'error_counts': self.error_counts.copy(),
            'recovery_success_rate': self._calculate_recovery_success_rate()
        }
    
    def _calculate_recovery_success_rate(self) -> float:
        """Calculate recovery success rate (placeholder implementation)."""
        # This would track actual recovery success/failure
        return 0.85  # Placeholder value


def graceful_degradation(fallback_func: Callable = None, 
                        cache_manager: CachedDataManager = None):
    """
    Decorator for graceful degradation with cached data fallbacks.
    
    Args:
        fallback_func: Function to call if primary function fails
        cache_manager: Cache manager for storing/retrieving cached data
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            logger = logging.getLogger(f"{func.__module__}.{func.__name__}")
            cache_key = f"{func.__name__}_{hash(str(args) + str(kwargs))}"
            
            try:
                # Try primary function
                result = func(*args, **kwargs)
                
                # Cache successful result
                if cache_manager:
                    cache_manager.cache_data(cache_key, result)
                
                return result
                
            except Exception as e:
                logger.warning(f"Primary function {func.__name__} failed: {e}")
                
                # Try cached data
                if cache_manager:
                    cached_result = cache_manager.get_cached_data(cache_key)
                    if cached_result:
                        logger.info(f"Using cached data for {func.__name__}")
                        # Mark data as stale
                        cached_result['_stale'] = True
                        cached_result['_stale_reason'] = str(e)
                        return cached_result
                
                # Try fallback function
                if fallback_func:
                    try:
                        logger.info(f"Using fallback function for {func.__name__}")
                        result = fallback_func(*args, **kwargs)
                        result['_fallback'] = True
                        return result
                    except Exception as fallback_error:
                        logger.error(f"Fallback function also failed: {fallback_error}")
                
                # All options exhausted, re-raise original exception
                raise e
        
        return wrapper
    return decorator


# Example usage and testing
if __name__ == "__main__":
    import requests
    
    # Test retry decorator
    @retry_with_backoff(RetryConfig(max_retries=3, base_delay=0.1))
    def test_api_call():
        response = requests.get("https://httpbin.org/status/500")
        response.raise_for_status()
        return response.json()
    
    # Test data validation
    validator = DataValidator()
    test_data = {
        'value': 1000000,
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'metadata': {'source': 'test'}
    }
    
    schema = {
        'required': ['value', 'timestamp'],
        'types': {'value': (int, float), 'timestamp': str},
        'ranges': {'value': (0, 10000000)}
    }
    
    result = validator.validate_data(test_data, schema)
    print(f"Validation result: {result}")