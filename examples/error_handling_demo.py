#!/usr/bin/env python3
"""
Demonstration of comprehensive error handling and data validation features.

This script demonstrates:
1. Exponential backoff retry logic
2. Data integrity validation with checksums
3. Anomaly detection
4. Graceful degradation with cached data
5. Cross-validation between multiple sources

Run this script to see all error handling features in action.
"""

import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List

from utils.error_handling import (
    DataValidator, CachedDataManager, CrossValidator,
    retry_with_backoff, graceful_degradation, RetryConfig,
    ValidationResult
)


def demo_retry_logic():
    """Demonstrate exponential backoff retry logic."""
    print("=" * 60)
    print("DEMO 1: Exponential Backoff Retry Logic")
    print("=" * 60)
    
    call_count = 0
    
    @retry_with_backoff(RetryConfig(max_retries=3, base_delay=0.1, jitter=False))
    def unreliable_api_call():
        nonlocal call_count
        call_count += 1
        print(f"  API call attempt #{call_count}")
        
        if call_count < 3:
            raise ConnectionError(f"Simulated failure #{call_count}")
        
        return {"data": "success", "attempt": call_count}
    
    try:
        start_time = time.time()
        result = unreliable_api_call()
        end_time = time.time()
        
        print(f"✅ Success after {call_count} attempts")
        print(f"   Result: {result}")
        print(f"   Total time: {end_time - start_time:.2f}s")
    except Exception as e:
        print(f"❌ Failed after {call_count} attempts: {e}")
    
    print()


def demo_data_validation():
    """Demonstrate comprehensive data validation."""
    print("=" * 60)
    print("DEMO 2: Data Validation with Anomaly Detection")
    print("=" * 60)
    
    validator = DataValidator()
    
    # Define schema
    schema = {
        'required': ['value', 'timestamp'],
        'types': {'value': (int, float), 'timestamp': str},
        'ranges': {'value': (0, 10000000)}
    }
    
    # Create historical data for anomaly detection
    historical_data = []
    for i in range(10):
        historical_data.append({
            'value': 1000000 + (i * 10000),  # Values around 1M
            'timestamp': (datetime.utcnow() - timedelta(days=i)).isoformat()
        })
    
    # Test cases
    test_cases = [
        {
            'name': 'Valid data',
            'data': {
                'value': 1050000,
                'timestamp': datetime.utcnow().isoformat(),
                'confidence': 0.95
            }
        },
        {
            'name': 'Missing required field',
            'data': {
                'timestamp': datetime.utcnow().isoformat(),
                'confidence': 0.95
            }
        },
        {
            'name': 'Anomalous value',
            'data': {
                'value': 5000000,  # Much higher than historical
                'timestamp': datetime.utcnow().isoformat(),
                'confidence': 0.95
            }
        },
        {
            'name': 'Out of range value',
            'data': {
                'value': -500000,  # Negative value
                'timestamp': datetime.utcnow().isoformat(),
                'confidence': 0.95
            }
        }
    ]
    
    for test_case in test_cases:
        print(f"Testing: {test_case['name']}")
        result = validator.validate_data(
            test_case['data'], 
            schema, 
            historical_data
        )
        
        status = "✅ VALID" if result.is_valid else "❌ INVALID"
        print(f"  {status} (confidence: {result.confidence:.2f})")
        
        if result.errors:
            print(f"  Errors: {', '.join(result.errors)}")
        
        if result.warnings:
            print(f"  Warnings: {', '.join(result.warnings)}")
        
        if result.anomaly_score is not None:
            print(f"  Anomaly score: {result.anomaly_score:.3f}")
        
        if result.checksum:
            print(f"  Checksum: {result.checksum[:8]}...")
        
        print()


def demo_cross_validation():
    """Demonstrate cross-validation between multiple sources."""
    print("=" * 60)
    print("DEMO 3: Cross-Validation Between Data Sources")
    print("=" * 60)
    
    cross_validator = CrossValidator()
    
    # Test scenarios
    scenarios = [
        {
            'name': 'Agreeing sources',
            'primary': {'value': 1000, 'source': 'primary'},
            'secondary': [
                {'value': 1010, 'source': 'secondary1'},
                {'value': 990, 'source': 'secondary2'},
                {'value': 1005, 'source': 'secondary3'}
            ]
        },
        {
            'name': 'Disagreeing sources',
            'primary': {'value': 1000, 'source': 'primary'},
            'secondary': [
                {'value': 1500, 'source': 'secondary1'},  # 50% difference
                {'value': 500, 'source': 'secondary2'},   # 50% difference
                {'value': 1000, 'source': 'secondary3'}   # Exact match
            ]
        },
        {
            'name': 'No secondary sources',
            'primary': {'value': 1000, 'source': 'primary'},
            'secondary': []
        }
    ]
    
    for scenario in scenarios:
        print(f"Testing: {scenario['name']}")
        result = cross_validator.cross_validate(
            scenario['primary'],
            scenario['secondary'],
            tolerance=0.1  # 10% tolerance
        )
        
        status = "✅ VALIDATED" if result['validated'] else "⚠️  DISCREPANCIES"
        print(f"  {status} (confidence: {result['confidence']:.2f})")
        print(f"  Consensus value: {result['consensus_value']}")
        
        if result['discrepancies']:
            print(f"  Discrepancies:")
            for discrepancy in result['discrepancies']:
                print(f"    - {discrepancy}")
        
        print()


def demo_graceful_degradation():
    """Demonstrate graceful degradation with cached data."""
    print("=" * 60)
    print("DEMO 4: Graceful Degradation with Cached Data")
    print("=" * 60)
    
    cache_manager = CachedDataManager(cache_ttl_hours=1)
    
    # Pre-populate cache
    cached_data = {
        'value': 750000,
        'timestamp': datetime.utcnow().isoformat(),
        'source': 'cached',
        'confidence': 0.8
    }
    cache_manager.cache_data('test_key', cached_data)
    
    @graceful_degradation(cache_manager=cache_manager)
    def failing_api_call():
        raise ConnectionError("Primary API is down")
    
    def fallback_function():
        return {
            'value': 500000,
            'timestamp': datetime.utcnow().isoformat(),
            'source': 'fallback',
            'confidence': 0.6
        }
    
    @graceful_degradation(fallback_func=fallback_function)
    def api_with_fallback():
        raise ConnectionError("Primary API is down")
    
    # Test cached data fallback
    print("Testing cached data fallback:")
    try:
        result = failing_api_call()
        print(f"✅ Used cached data: {result['value']} (stale: {result.get('_stale', False)})")
    except Exception as e:
        print(f"❌ Failed: {e}")
    
    print()
    
    # Test fallback function
    print("Testing fallback function:")
    try:
        result = api_with_fallback()
        print(f"✅ Used fallback: {result['value']} (fallback: {result.get('_fallback', False)})")
    except Exception as e:
        print(f"❌ Failed: {e}")
    
    print()


def demo_integration_scenario():
    """Demonstrate all features working together."""
    print("=" * 60)
    print("DEMO 5: Complete Integration Scenario")
    print("=" * 60)
    
    # Initialize components
    validator = DataValidator()
    cache_manager = CachedDataManager()
    cross_validator = CrossValidator()
    
    # Simulate a complete data processing pipeline
    call_count = 0
    
    @retry_with_backoff(RetryConfig(max_retries=2, base_delay=0.1))
    @graceful_degradation(cache_manager=cache_manager)
    def fetch_financial_data():
        nonlocal call_count
        call_count += 1
        
        if call_count == 1:
            raise ConnectionError("First attempt failed")
        
        return {
            'value': 2500000,
            'timestamp': datetime.utcnow().isoformat(),
            'confidence': 0.95,
            'source': 'primary_api'
        }
    
    def get_secondary_sources():
        return [
            {'value': 2520000, 'source': 'secondary1'},
            {'value': 2480000, 'source': 'secondary2'}
        ]
    
    # Execute pipeline
    print("Executing complete data processing pipeline...")
    
    try:
        # 1. Fetch data with retry and fallback
        print("1. Fetching data with retry logic...")
        primary_data = fetch_financial_data()
        print(f"   ✅ Data fetched: ${primary_data['value']:,}")
        
        # 2. Validate data
        print("2. Validating data integrity...")
        schema = {
            'required': ['value', 'timestamp'],
            'types': {'value': (int, float), 'timestamp': str},
            'ranges': {'value': (0, 10000000)}
        }
        
        validation_result = validator.validate_data(primary_data, schema)
        if validation_result.is_valid:
            print(f"   ✅ Data valid (confidence: {validation_result.confidence:.2f})")
        else:
            print(f"   ❌ Data invalid: {', '.join(validation_result.errors)}")
            return
        
        # 3. Cross-validate with secondary sources
        print("3. Cross-validating with secondary sources...")
        secondary_data = get_secondary_sources()
        cross_validation = cross_validator.cross_validate(
            primary_data, secondary_data, tolerance=0.05
        )
        
        if cross_validation['validated']:
            print(f"   ✅ Cross-validation passed (confidence: {cross_validation['confidence']:.2f})")
        else:
            print(f"   ⚠️  Cross-validation issues: {len(cross_validation['discrepancies'])} discrepancies")
        
        # 4. Calculate final confidence
        final_confidence = min(
            validation_result.confidence,
            cross_validation['confidence']
        )
        
        print(f"4. Final result:")
        print(f"   Value: ${primary_data['value']:,}")
        print(f"   Confidence: {final_confidence:.2f}")
        print(f"   Checksum: {validation_result.checksum[:8]}...")
        print(f"   API calls made: {call_count}")
        
    except Exception as e:
        print(f"❌ Pipeline failed: {e}")
    
    print()


def main():
    """Run all demonstrations."""
    print("🚀 Comprehensive Error Handling and Data Validation Demo")
    print("This demo shows all error handling features in action.\n")
    
    demo_retry_logic()
    demo_data_validation()
    demo_cross_validation()
    demo_graceful_degradation()
    demo_integration_scenario()
    
    print("=" * 60)
    print("✅ All demonstrations completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()