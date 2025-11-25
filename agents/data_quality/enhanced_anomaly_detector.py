"""
Enhanced Anomaly Detector - Context-aware anomaly detection with multi-source correlation.

This agent enhances existing anomaly detection by:
- Using market context to adjust thresholds
- Correlating anomalies across related metrics
- Reducing false positives
- Providing confidence scores
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

import numpy as np
from scipy import stats

from agents.data_quality.context_analyzer import ContextAnalyzer


@dataclass
class AnomalyResult:
    """Result of enhanced anomaly detection."""
    metric_name: str
    current_value: float
    is_anomaly: bool
    confidence: float  # 0.0 to 1.0
    detection_method: str
    context_adjusted: bool
    threshold_adjustment: float
    related_anomalies: List[str]  # Names of related metrics with anomalies
    explanation: str
    timestamp: datetime


class EnhancedAnomalyDetector:
    """
    Enhanced anomaly detector with context awareness and correlation.
    
    Usage:
        detector = EnhancedAnomalyDetector()
        result = detector.detect_anomaly(
            metric_name='bdc_discount',
            current_value=0.15,
            historical_values=[0.10, 0.11, 0.12, 0.13, 0.14]
        )
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.context_analyzer = ContextAnalyzer()
        
        # Related metrics for correlation
        self.related_metrics = {
            'bdc_discount': ['credit_fund', 'bank_provision'],
            'credit_fund': ['bdc_discount', 'bank_provision'],
            'bank_provision': ['bdc_discount', 'credit_fund'],
            'bond_issuance': []  # Less correlated
        }
    
    def detect_anomaly(self, metric_name: str, current_value: float,
                      historical_values: List[float],
                      base_threshold: Optional[float] = None,
                      method: str = 'zscore') -> AnomalyResult:
        """
        Detect anomaly with context awareness.
        
        Args:
            metric_name: Name of the metric
            current_value: Current value to check
            historical_values: Historical values for comparison
            base_threshold: Base threshold (if None, calculated from data)
            method: Detection method ('zscore', 'iqr', 'percentile')
            
        Returns:
            AnomalyResult object
        """
        if not historical_values:
            return AnomalyResult(
                metric_name=metric_name,
                current_value=current_value,
                is_anomaly=False,
                confidence=0.0,
                detection_method=method,
                context_adjusted=False,
                threshold_adjustment=1.0,
                related_anomalies=[],
                explanation="Insufficient historical data",
                timestamp=datetime.now(timezone.utc)
            )
        
        # Get market context
        context = self.context_analyzer.get_context()
        threshold_adjustment = context.threshold_adjustment
        
        # Calculate base threshold if not provided
        if base_threshold is None:
            base_threshold = self._calculate_base_threshold(historical_values, method)
        
        # Adjust threshold based on context
        adjusted_threshold = base_threshold * threshold_adjustment
        
        # Detect anomaly
        is_anomaly, confidence, explanation = self._detect_with_method(
            current_value, historical_values, adjusted_threshold, method
        )
        
        # Check for related anomalies
        related_anomalies = self._check_related_anomalies(metric_name, current_value)
        
        # Adjust confidence based on correlation
        if related_anomalies:
            # If related metrics also show anomalies, increase confidence
            confidence = min(1.0, confidence * 1.2)
            explanation += f" Correlated with {len(related_anomalies)} related metric(s)."
        else:
            # If isolated anomaly, slightly reduce confidence
            confidence = max(0.0, confidence * 0.9)
            explanation += " Isolated anomaly (no correlation with related metrics)."
        
        return AnomalyResult(
            metric_name=metric_name,
            current_value=current_value,
            is_anomaly=is_anomaly,
            confidence=confidence,
            detection_method=method,
            context_adjusted=threshold_adjustment != 1.0,
            threshold_adjustment=threshold_adjustment,
            related_anomalies=related_anomalies,
            explanation=explanation,
            timestamp=datetime.now(timezone.utc)
        )
    
    def _calculate_base_threshold(self, historical_values: List[float], method: str) -> float:
        """Calculate base threshold from historical data."""
        if method == 'zscore':
            mean = np.mean(historical_values)
            std = np.std(historical_values)
            if std == 0:
                return 0.0
            # 2 standard deviations = ~95% confidence
            return 2.0 * std
        
        elif method == 'iqr':
            q1 = np.percentile(historical_values, 25)
            q3 = np.percentile(historical_values, 75)
            iqr = q3 - q1
            return 1.5 * iqr
        
        elif method == 'percentile':
            # Use 95th percentile as threshold
            return np.percentile(historical_values, 95) - np.median(historical_values)
        
        else:
            # Default to zscore
            mean = np.mean(historical_values)
            std = np.std(historical_values)
            return 2.0 * std if std > 0 else 0.0
    
    def _detect_with_method(self, current_value: float, historical_values: List[float],
                           threshold: float, method: str) -> Tuple[bool, float, str]:
        """Detect anomaly using specified method."""
        if method == 'zscore':
            mean = np.mean(historical_values)
            std = np.std(historical_values)
            
            if std == 0:
                return False, 0.0, "No variance in historical data"
            
            z_score = abs((current_value - mean) / std)
            is_anomaly = z_score > (threshold / std)
            
            # Confidence based on z-score magnitude
            if z_score > 3:
                confidence = 0.95
            elif z_score > 2.5:
                confidence = 0.85
            elif z_score > 2:
                confidence = 0.75
            else:
                confidence = 0.5
            
            explanation = f"Z-score: {z_score:.2f} (mean: {mean:.2f}, std: {std:.2f})"
            
            return is_anomaly, confidence, explanation
        
        elif method == 'iqr':
            q1 = np.percentile(historical_values, 25)
            q3 = np.percentile(historical_values, 75)
            iqr = q3 - q1
            median = np.median(historical_values)
            
            # Check if outside IQR bounds
            lower_bound = q1 - threshold
            upper_bound = q3 + threshold
            
            is_anomaly = current_value < lower_bound or current_value > upper_bound
            
            # Calculate how far outside bounds
            if current_value < lower_bound:
                distance = (lower_bound - current_value) / iqr if iqr > 0 else 0
            elif current_value > upper_bound:
                distance = (current_value - upper_bound) / iqr if iqr > 0 else 0
            else:
                distance = 0
            
            confidence = min(0.95, 0.5 + distance * 0.2)
            
            explanation = f"IQR method: value {current_value:.2f} vs bounds [{lower_bound:.2f}, {upper_bound:.2f}]"
            
            return is_anomaly, confidence, explanation
        
        else:
            # Default to zscore
            return self._detect_with_method(current_value, historical_values, threshold, 'zscore')
    
    def _check_related_anomalies(self, metric_name: str, current_value: float) -> List[str]:
        """
        Check if related metrics also show anomalies.
        
        This helps distinguish between systemic vs isolated anomalies.
        """
        related_metrics = self.related_metrics.get(metric_name, [])
        related_anomalies = []
        
        # In a real implementation, we'd check recent values of related metrics
        # For now, this is a placeholder that can be enhanced
        # TODO: Fetch recent values from metrics service and check for anomalies
        
        return related_anomalies
    
    def detect_anomalies_batch(self, metrics: Dict[str, Dict[str, Any]]) -> List[AnomalyResult]:
        """
        Detect anomalies for multiple metrics with correlation analysis.
        
        Args:
            metrics: Dictionary mapping metric names to {
                'current_value': float,
                'historical_values': List[float],
                'threshold': Optional[float]
            }
            
        Returns:
            List of AnomalyResult objects
        """
        results = []
        
        # First pass: detect anomalies
        for metric_name, metric_data in metrics.items():
            result = self.detect_anomaly(
                metric_name=metric_name,
                current_value=metric_data['current_value'],
                historical_values=metric_data.get('historical_values', []),
                base_threshold=metric_data.get('threshold')
            )
            results.append(result)
        
        # Second pass: check correlations
        anomaly_metrics = [r.metric_name for r in results if r.is_anomaly]
        
        for result in results:
            if result.is_anomaly:
                # Check if related metrics also have anomalies
                related = self.related_metrics.get(result.metric_name, [])
                correlated = [m for m in related if m in anomaly_metrics]
                
                if correlated:
                    result.related_anomalies = correlated
                    result.confidence = min(1.0, result.confidence * 1.2)
                    result.explanation += f" Correlated with {len(correlated)} related metric(s): {', '.join(correlated)}"
        
        return results

