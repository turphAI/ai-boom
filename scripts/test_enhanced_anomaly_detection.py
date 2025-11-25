#!/usr/bin/env python3
"""
Test Enhanced Anomaly Detection - Demo script for data quality agent.

Usage:
    python scripts/test_enhanced_anomaly_detection.py
"""

import sys
import os
import logging
from datetime import datetime, timezone

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.context_analyzer import ContextAnalyzer
from agents.enhanced_anomaly_detector import EnhancedAnomalyDetector
from agents.correlation_engine import CorrelationEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_context_analyzer():
    """Test context analyzer."""
    print("\n" + "="*60)
    print("1️⃣  Testing Context Analyzer")
    print("="*60)
    
    analyzer = ContextAnalyzer()
    
    # Test current date
    context = analyzer.get_context()
    print(f"\n📅 Current Market Context:")
    print(f"   Date: {context.date.strftime('%Y-%m-%d')}")
    print(f"   Types: {', '.join([t.value for t in context.context_types])}")
    print(f"   Description: {context.description}")
    print(f"   Expected Volatility: {context.expected_volatility}")
    print(f"   Threshold Adjustment: {context.threshold_adjustment:.2f}x")
    
    # Test specific dates
    test_dates = [
        datetime(2025, 1, 1, tzinfo=timezone.utc),  # New Year's Day
        datetime(2025, 7, 4, tzinfo=timezone.utc),  # Independence Day
        datetime(2025, 1, 31, tzinfo=timezone.utc),  # Near FOMC meeting
        datetime(2025, 4, 20, tzinfo=timezone.utc),  # Earnings season
    ]
    
    print(f"\n📊 Testing Specific Dates:")
    for date in test_dates:
        context = analyzer.get_context(date)
        print(f"   {date.strftime('%Y-%m-%d')}: {context.description}")
        print(f"      Threshold Adjustment: {context.threshold_adjustment:.2f}x")


def test_anomaly_detection():
    """Test enhanced anomaly detection."""
    print("\n" + "="*60)
    print("2️⃣  Testing Enhanced Anomaly Detection")
    print("="*60)
    
    detector = EnhancedAnomalyDetector()
    
    # Test case 1: Normal value
    print(f"\n📊 Test Case 1: Normal Value")
    historical = [0.10, 0.11, 0.12, 0.13, 0.14, 0.12, 0.11]
    result = detector.detect_anomaly(
        metric_name='bdc_discount',
        current_value=0.12,
        historical_values=historical
    )
    print(f"   Current Value: {result.current_value}")
    print(f"   Is Anomaly: {result.is_anomaly}")
    print(f"   Confidence: {result.confidence:.2f}")
    print(f"   Explanation: {result.explanation}")
    print(f"   Context Adjusted: {result.context_adjusted}")
    
    # Test case 2: Anomalous value
    print(f"\n📊 Test Case 2: Anomalous Value")
    result = detector.detect_anomaly(
        metric_name='bdc_discount',
        current_value=0.25,  # Much higher than historical
        historical_values=historical
    )
    print(f"   Current Value: {result.current_value}")
    print(f"   Is Anomaly: {result.is_anomaly}")
    print(f"   Confidence: {result.confidence:.2f}")
    print(f"   Explanation: {result.explanation}")
    print(f"   Threshold Adjustment: {result.threshold_adjustment:.2f}x")
    
    # Test case 3: Batch detection
    print(f"\n📊 Test Case 3: Batch Detection")
    metrics = {
        'bdc_discount': {
            'current_value': 0.15,
            'historical_values': [0.10, 0.11, 0.12, 0.13, 0.14]
        },
        'credit_fund': {
            'current_value': 0.20,
            'historical_values': [0.15, 0.16, 0.17, 0.18, 0.19]
        }
    }
    
    results = detector.detect_anomalies_batch(metrics)
    for result in results:
        print(f"   {result.metric_name}: Anomaly={result.is_anomaly}, Confidence={result.confidence:.2f}")


def test_correlation_engine():
    """Test correlation engine."""
    print("\n" + "="*60)
    print("3️⃣  Testing Correlation Engine")
    print("="*60)
    
    from agents.enhanced_anomaly_detector import AnomalyResult
    
    # Create mock anomaly results
    anomalies = [
        AnomalyResult(
            metric_name='bdc_discount',
            current_value=0.20,
            is_anomaly=True,
            confidence=0.85,
            detection_method='zscore',
            context_adjusted=True,
            threshold_adjustment=1.0,
            related_anomalies=[],
            explanation="High z-score",
            timestamp=datetime.now(timezone.utc)
        ),
        AnomalyResult(
            metric_name='credit_fund',
            current_value=0.25,
            is_anomaly=True,
            confidence=0.80,
            detection_method='zscore',
            context_adjusted=True,
            threshold_adjustment=1.0,
            related_anomalies=[],
            explanation="High z-score",
            timestamp=datetime.now(timezone.utc)
        ),
        AnomalyResult(
            metric_name='bond_issuance',
            current_value=1000000,
            is_anomaly=False,
            confidence=0.0,
            detection_method='zscore',
            context_adjusted=False,
            threshold_adjustment=1.0,
            related_anomalies=[],
            explanation="Normal",
            timestamp=datetime.now(timezone.utc)
        )
    ]
    
    engine = CorrelationEngine()
    correlations = engine.analyze_correlation(anomalies)
    
    print(f"\n📊 Correlation Analysis:")
    for metric_name, correlation in correlations.items():
        print(f"   {metric_name}:")
        print(f"      Systemic: {correlation.is_systemic}")
        print(f"      Correlation Score: {correlation.correlation_score:.2f}")
        print(f"      Correlated Metrics: {', '.join(correlation.correlated_metrics) if correlation.correlated_metrics else 'None'}")
        print(f"      Confidence Adjustment: {correlation.confidence_adjustment:.2f}x")
        print(f"      Explanation: {correlation.explanation}")
    
    systemic = engine.get_systemic_anomalies(anomalies)
    print(f"\n🔍 Systemic Anomalies: {', '.join(systemic) if systemic else 'None'}")


def main():
    """Main entry point."""
    print("\n" + "="*60)
    print("🧪 Enhanced Anomaly Detection - Test Suite")
    print("="*60)
    
    try:
        test_context_analyzer()
        test_anomaly_detection()
        test_correlation_engine()
        
        print("\n" + "="*60)
        print("✅ All tests completed!")
        print("="*60)
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())

