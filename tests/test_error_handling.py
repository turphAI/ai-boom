"""
Comprehensive tests for error handling and data validation functionality.
"""

import json
import pytest
import time
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, List

from utils.error_handling import (
    DataValidator, CachedDataManager, CrossValidator,
    retry_with_backoff, graceful_degradation, RetryConfig,
    ValidationResult, ErrorSeverity, RetryStrategy,
    RetryableError, DataIntegrityError, AnomalyDetectionError
)


class TestRetryLogic:
    """Test retry logic and exponential backoff."""
    
    def test_retry_success_on_first_attempt(self):
        """Test successful execution on first attempt."""
        call_count = 0
        
        @retry_with_backoff(RetryConfig(max_retries=3))
        def successful_function():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = successful_function()
        assert result == "success"
        assert call_count == 1
    
    def test_retry_success_after_failures(self):
        """Test successful execution after initial failures."""
        call_count = 0
        
        @retry_with_backoff(RetryConfig(max_retries=3, base_delay=0.01))
        def eventually_successful_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Temporary failure")
            return "success"
        
        result = eventually_successful_function()
        assert result == "success"
        assert call_count == 3
    
    def test_retry_max_attempts_exceeded(self):
        """Test failure when max retry attempts are exceeded."""
        call_count = 0
        
        @retry_with_backoff(RetryConfig(max_retries=2, base_delay=0.01))
        def always_failing_function():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("Persistent failure")
        
        with pytest.raises(ConnectionError):
            always_failing_function()
        
        assert call_count == 3  # Initial attempt + 2 retries
    
    def test_non_retryable_exception(self):
        """Test that non-retryable exceptions are not retried."""
        call_count = 0
        
        @retry_with_backoff(RetryConfig(max_retries=3))
        def function_with_non_retryable_error():
            nonlocal call_count
            call_count += 1
            raise ValueError("Non-retryable error")
        
        with pytest.raises(ValueError):
            function_with_non_retryable_error()
        
        assert call_count == 1  # Should not retry
    
    def test_exponential_backoff_timing(self):
        """Test that exponential backoff timing is correct."""
        call_times = []
        
        @retry_with_backoff(RetryConfig(
            max_retries=3, 
            base_delay=0.1, 
            backoff_factor=2.0,
            jitter=False
        ))
        def timing_test_function():
            call_times.append(time.time())
            raise ConnectionError("Test error")
        
        start_time = time.time()
        with pytest.raises(ConnectionError):
            timing_test_function()
        
        # Check that delays are approximately correct
        assert len(call_times) == 4  # Initial + 3 retries
        
        # First retry should be after ~0.1s
        delay1 = call_times[1] - call_times[0]
        assert 0.08 <= delay1 <= 0.15
        
        # Second retry should be after ~0.2s
        delay2 = call_times[2] - call_times[1]
        assert 0.18 <= delay2 <= 0.25


class TestDataValidator:
    """Test data validation functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.validator = DataValidator()
        self.valid_data = {
            'value': 1000000,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'confidence': 0.95,
            'metadata': {'source': 'test'}
        }
        self.schema = {
            'required': ['value', 'timestamp'],
            'types': {'value': (int, float), 'timestamp': str},
            'ranges': {'value': (0, 10000000)}
        }
    
    def test_valid_data_validation(self):
        """Test validation of valid data."""
        result = self.validator.validate_data(self.valid_data, self.schema)
        
        assert result.is_valid
        assert result.confidence > 0.8
        assert len(result.errors) == 0
        assert result.checksum is not None
    
    def test_missing_required_field(self):
        """Test validation failure for missing required field."""
        invalid_data = self.valid_data.copy()
        del invalid_data['value']
        
        result = self.validator.validate_data(invalid_data, self.schema)
        
        assert not result.is_valid
        assert 'Missing required field: value' in result.errors
    
    def test_wrong_field_type(self):
        """Test validation failure for wrong field type."""
        invalid_data = self.valid_data.copy()
        invalid_data['value'] = "not_a_number"
        
        result = self.validator.validate_data(invalid_data, self.schema)
        
        assert not result.is_valid
        assert any('type' in error.lower() for error in result.errors)
    
    def test_value_out_of_range(self):
        """Test validation failure for value out of range."""
        invalid_data = self.valid_data.copy()
        invalid_data['value'] = 20000000  # Above max range
        
        result = self.validator.validate_data(invalid_data, self.schema)
        
        assert not result.is_valid
        assert any('outside range' in error for error in result.errors)
    
    def test_checksum_calculation(self):
        """Test checksum calculation consistency."""
        result1 = self.validator.validate_data(self.valid_data, self.schema)
        result2 = self.validator.validate_data(self.valid_data, self.schema)
        
        assert result1.checksum == result2.checksum
        
        # Different data should have different checksum
        different_data = self.valid_data.copy()
        different_data['value'] = 2000000
        result3 = self.validator.validate_data(different_data, self.schema)
        
        assert result1.checksum != result3.checksum
    
    def test_anomaly_detection(self):
        """Test anomaly detection with historical data."""
        # Create historical data with consistent values
        historical_data = []
        for i in range(10):
            historical_data.append({
                'value': 1000000 + (i * 10000),  # Values around 1M
                'timestamp': (datetime.now(timezone.utc) - timedelta(days=i)).isoformat()
            })
        
        # Test normal value (should have low anomaly score)
        normal_data = {'value': 1050000, 'timestamp': datetime.now(timezone.utc).isoformat()}
        result = self.validator.validate_data(normal_data, self.schema, historical_data)
        assert result.anomaly_score < 0.3
        
        # Test anomalous value (should have high anomaly score)
        anomalous_data = {'value': 5000000, 'timestamp': datetime.now(timezone.utc).isoformat()}
        result = self.validator.validate_data(anomalous_data, self.schema, historical_data)
        assert result.anomaly_score > 0.5
    
    def test_data_quality_warnings(self):
        """Test data quality warning detection."""
        # Data with null values
        data_with_nulls = self.valid_data.copy()
        data_with_nulls['optional_field'] = None
        data_with_nulls['empty_field'] = ""
        
        result = self.validator.validate_data(data_with_nulls, self.schema)
        assert len(result.warnings) > 0
        assert any('null/empty values' in warning for warning in result.warnings)
        
        # Data with suspiciously round numbers
        round_number_data = self.valid_data.copy()
        round_number_data['value'] = 5000000  # Exact millions
        
        result = self.validator.validate_data(round_number_data, self.schema)
        assert any('round number' in warning for warning in result.warnings)


class TestCachedDataManager:
    """Test cached data management."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.cache_manager = CachedDataManager(cache_ttl_hours=1)
        self.test_data = {'value': 123, 'timestamp': datetime.now(timezone.utc).isoformat()}
    
    def test_cache_and_retrieve(self):
        """Test caching and retrieving data."""
        key = "test_key"
        
        # Cache data
        self.cache_manager.cache_data(key, self.test_data)
        
        # Retrieve data
        cached_data = self.cache_manager.get_cached_data(key)
        assert cached_data == self.test_data
    
    def test_cache_expiration(self):
        """Test cache expiration."""
        key = "test_key"
        
        # Create cache manager with very short TTL
        short_ttl_manager = CachedDataManager(cache_ttl_hours=0.001)  # ~3.6 seconds
        
        # Cache data
        short_ttl_manager.cache_data(key, self.test_data)
        
        # Data should be available immediately
        cached_data = short_ttl_manager.get_cached_data(key)
        assert cached_data == self.test_data
        
        # Wait for expiration and check again
        time.sleep(0.01)  # Wait longer than TTL
        cached_data = short_ttl_manager.get_cached_data(key)
        assert cached_data is None
    
    def test_cache_miss(self):
        """Test cache miss for non-existent key."""
        cached_data = self.cache_manager.get_cached_data("non_existent_key")
        assert cached_data is None
    
    def test_clear_cache(self):
        """Test clearing cache."""
        key = "test_key"
        
        # Cache data
        self.cache_manager.cache_data(key, self.test_data)
        assert self.cache_manager.get_cached_data(key) is not None
        
        # Clear cache
        self.cache_manager.clear_cache()
        assert self.cache_manager.get_cached_data(key) is None


class TestCrossValidator:
    """Test cross-validation functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.cross_validator = CrossValidator()
        self.primary_data = {'value': 1000, 'source': 'primary'}
    
    def test_cross_validation_agreement(self):
        """Test cross-validation with agreeing sources."""
        secondary_data = [
            {'value': 1010, 'source': 'secondary1'},
            {'value': 990, 'source': 'secondary2'},
            {'value': 1005, 'source': 'secondary3'}
        ]
        
        result = self.cross_validator.cross_validate(
            self.primary_data, secondary_data, tolerance=0.05
        )
        
        assert result['validated']
        assert result['confidence'] > 0.8
        assert len(result['discrepancies']) == 0
        assert result['consensus_value'] == 1005  # Median value
    
    def test_cross_validation_disagreement(self):
        """Test cross-validation with disagreeing sources."""
        secondary_data = [
            {'value': 1500, 'source': 'secondary1'},  # 50% difference
            {'value': 500, 'source': 'secondary2'},   # 50% difference
            {'value': 1000, 'source': 'secondary3'}   # Exact match
        ]
        
        result = self.cross_validator.cross_validate(
            self.primary_data, secondary_data, tolerance=0.1
        )
        
        assert not result['validated']
        assert result['confidence'] < 0.8
        assert len(result['discrepancies']) == 2  # Two disagreeing sources
    
    def test_cross_validation_no_secondary_data(self):
        """Test cross-validation with no secondary data."""
        result = self.cross_validator.cross_validate(
            self.primary_data, [], tolerance=0.1
        )
        
        assert result['validated']
        assert result['confidence'] == 0.5  # Lower confidence without validation
        assert result['consensus_value'] == 1000
    
    def test_cross_validation_missing_values(self):
        """Test cross-validation with missing values in secondary data."""
        secondary_data = [
            {'source': 'secondary1'},  # Missing value
            {'value': 1010, 'source': 'secondary2'},
            {'value': None, 'source': 'secondary3'}  # Null value
        ]
        
        result = self.cross_validator.cross_validate(
            self.primary_data, secondary_data, tolerance=0.05
        )
        
        assert result['validated']
        assert result['source_count'] == 2  # Only primary and one secondary


class TestGracefulDegradation:
    """Test graceful degradation functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.cache_manager = CachedDataManager()
        self.fallback_data = {'value': 999, 'fallback': True}
    
    def test_graceful_degradation_success(self):
        """Test graceful degradation when primary function succeeds."""
        @graceful_degradation(cache_manager=self.cache_manager)
        def successful_function():
            return {'value': 123, 'success': True}
        
        result = successful_function()
        assert result['value'] == 123
        assert result['success']
        assert '_fallback' not in result
    
    def test_graceful_degradation_with_cache(self):
        """Test graceful degradation using cached data."""
        cache_key = f"failing_function_{hash('')}"
        self.cache_manager.cache_data(cache_key, {'value': 456, 'cached': True})
        
        @graceful_degradation(cache_manager=self.cache_manager)
        def failing_function():
            raise ConnectionError("Primary function failed")
        
        result = failing_function()
        assert result['value'] == 456
        assert result['cached']
        assert result['_stale']
    
    def test_graceful_degradation_with_fallback(self):
        """Test graceful degradation using fallback function."""
        def fallback_function():
            return self.fallback_data
        
        @graceful_degradation(fallback_func=fallback_function)
        def failing_function():
            raise ConnectionError("Primary function failed")
        
        result = failing_function()
        assert result['value'] == 999
        assert result['_fallback']
    
    def test_graceful_degradation_all_fail(self):
        """Test graceful degradation when all options fail."""
        def failing_fallback():
            raise ValueError("Fallback also failed")
        
        @graceful_degradation(fallback_func=failing_fallback)
        def failing_function():
            raise ConnectionError("Primary function failed")
        
        with pytest.raises(ConnectionError):
            failing_function()


class TestIntegrationScenarios:
    """Test integration scenarios combining multiple error handling features."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.validator = DataValidator()
        self.cache_manager = CachedDataManager()
        self.cross_validator = CrossValidator()
    
    def test_complete_error_handling_pipeline(self):
        """Test complete error handling pipeline."""
        # Mock external API that fails initially then succeeds
        call_count = 0
        
        @retry_with_backoff(RetryConfig(max_retries=2, base_delay=0.01))
        @graceful_degradation(cache_manager=self.cache_manager)
        def fetch_data_with_full_error_handling():
            nonlocal call_count
            call_count += 1
            
            if call_count < 2:
                raise ConnectionError("Temporary API failure")
            
            return {
                'value': 1000000,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'confidence': 0.95,
                'source': 'api'
            }
        
        # Execute function
        result = fetch_data_with_full_error_handling()
        
        # Validate result
        schema = {
            'required': ['value', 'timestamp'],
            'types': {'value': (int, float), 'timestamp': str},
            'ranges': {'value': (0, 10000000)}
        }
        
        validation_result = self.validator.validate_data(result, schema)
        
        assert validation_result.is_valid
        assert result['value'] == 1000000
        assert call_count == 2  # Should have retried once
    
    def test_data_integrity_with_cross_validation(self):
        """Test data integrity checking with cross-validation."""
        primary_data = {
            'value': 1000000,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'source': 'primary'
        }
        
        secondary_data = [
            {'value': 1010000, 'source': 'secondary1'},
            {'value': 990000, 'source': 'secondary2'}
        ]
        
        # Validate primary data
        schema = {
            'required': ['value', 'timestamp'],
            'types': {'value': (int, float)},
            'ranges': {'value': (0, 10000000)}
        }
        
        validation_result = self.validator.validate_data(primary_data, schema)
        assert validation_result.is_valid
        
        # Cross-validate
        cross_validation_result = self.cross_validator.cross_validate(
            primary_data, secondary_data, tolerance=0.05
        )
        
        assert cross_validation_result['validated']
        assert cross_validation_result['confidence'] > 0.8
        
        # Calculate final confidence
        final_confidence = min(
            validation_result.confidence,
            cross_validation_result['confidence']
        )
        
        assert final_confidence > 0.8


if __name__ == "__main__":
    pytest.main([__file__, "-v"])