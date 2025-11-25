"""
Correlation Engine - Cross-validates anomalies across related metrics.

This agent helps distinguish between:
- Systemic anomalies (affecting multiple related metrics)
- Isolated anomalies (affecting single metrics)

Systemic anomalies are more likely to be real market events.
Isolated anomalies are more likely to be data quality issues.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

import numpy as np
from scipy.stats import pearsonr

from agents.data_quality.enhanced_anomaly_detector import AnomalyResult


@dataclass
class CorrelationResult:
    """Result of correlation analysis."""
    metric_name: str
    is_systemic: bool  # True if correlated with other anomalies
    correlation_score: float  # 0.0 to 1.0
    correlated_metrics: List[str]
    confidence_adjustment: float  # Multiplier for confidence
    explanation: str


class CorrelationEngine:
    """
    Analyzes correlations between anomalies across metrics.
    
    Usage:
        engine = CorrelationEngine()
        correlation = engine.analyze_correlation(anomaly_results)
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Define metric relationships
        # Metrics that typically move together
        self.related_groups = {
            'credit_stress': ['bdc_discount', 'credit_fund', 'bank_provision'],
            'market_volatility': ['bond_issuance', 'bdc_discount'],
            'financial_stress': ['bank_provision', 'credit_fund']
        }
        
        # Individual metric relationships
        self.metric_relationships = {
            'bdc_discount': ['credit_fund', 'bank_provision'],
            'credit_fund': ['bdc_discount', 'bank_provision'],
            'bank_provision': ['bdc_discount', 'credit_fund'],
            'bond_issuance': ['bdc_discount']  # Less correlated
        }
    
    def analyze_correlation(self, anomaly_results: List[AnomalyResult]) -> Dict[str, CorrelationResult]:
        """
        Analyze correlations between anomalies.
        
        Args:
            anomaly_results: List of AnomalyResult objects
            
        Returns:
            Dictionary mapping metric names to CorrelationResult objects
        """
        results = {}
        
        # Filter to only anomalies
        anomalies = [r for r in anomaly_results if r.is_anomaly]
        
        if len(anomalies) < 2:
            # Not enough anomalies for correlation
            for result in anomaly_results:
                results[result.metric_name] = CorrelationResult(
                    metric_name=result.metric_name,
                    is_systemic=False,
                    correlation_score=0.0,
                    correlated_metrics=[],
                    confidence_adjustment=0.9,  # Slightly reduce confidence for isolated
                    explanation="Isolated anomaly - no correlation with other metrics"
                )
            return results
        
        # Check correlations
        for anomaly in anomalies:
            correlation = self._analyze_metric_correlation(anomaly, anomalies)
            results[anomaly.metric_name] = correlation
        
        # Add results for non-anomalies
        non_anomalies = [r for r in anomaly_results if not r.is_anomaly]
        for result in non_anomalies:
            results[result.metric_name] = CorrelationResult(
                metric_name=result.metric_name,
                is_systemic=False,
                correlation_score=0.0,
                correlated_metrics=[],
                confidence_adjustment=1.0,
                explanation="No anomaly detected"
            )
        
        return results
    
    def _analyze_metric_correlation(self, anomaly: AnomalyResult,
                                   all_anomalies: List[AnomalyResult]) -> CorrelationResult:
        """Analyze correlation for a single metric."""
        related_metrics = self.metric_relationships.get(anomaly.metric_name, [])
        
        # Find related anomalies
        related_anomalies = [
            a for a in all_anomalies
            if a.metric_name in related_metrics and a.metric_name != anomaly.metric_name
        ]
        
        if not related_anomalies:
            # Isolated anomaly
            return CorrelationResult(
                metric_name=anomaly.metric_name,
                is_systemic=False,
                correlation_score=0.0,
                correlated_metrics=[],
                confidence_adjustment=0.9,  # Reduce confidence slightly
                explanation="Isolated anomaly - no correlation with related metrics"
            )
        
        # Calculate correlation score
        # Simple heuristic: more related anomalies = higher correlation
        correlation_score = min(1.0, len(related_anomalies) / len(related_metrics))
        
        # Check if part of a systemic group
        is_systemic = self._is_systemic_anomaly(anomaly.metric_name, all_anomalies)
        
        if is_systemic:
            confidence_adjustment = 1.2  # Increase confidence for systemic
            explanation = f"Systemic anomaly - correlated with {len(related_anomalies)} related metric(s): {', '.join([a.metric_name for a in related_anomalies])}"
        else:
            confidence_adjustment = 1.0
            explanation = f"Partial correlation - {len(related_anomalies)} related metric(s) also show anomalies"
        
        return CorrelationResult(
            metric_name=anomaly.metric_name,
            is_systemic=is_systemic,
            correlation_score=correlation_score,
            correlated_metrics=[a.metric_name for a in related_anomalies],
            confidence_adjustment=confidence_adjustment,
            explanation=explanation
        )
    
    def _is_systemic_anomaly(self, metric_name: str, all_anomalies: List[AnomalyResult]) -> bool:
        """Check if anomaly is part of a systemic pattern."""
        # Check if metric is in a related group and multiple group members have anomalies
        for group_name, group_metrics in self.related_groups.items():
            if metric_name in group_metrics:
                # Count anomalies in this group
                group_anomalies = [
                    a for a in all_anomalies
                    if a.metric_name in group_metrics
                ]
                
                # If 2+ metrics in group have anomalies, it's systemic
                if len(group_anomalies) >= 2:
                    return True
        
        return False
    
    def calculate_metric_correlation(self, metric1_values: List[float],
                                   metric2_values: List[float]) -> Tuple[float, float]:
        """
        Calculate correlation coefficient between two metrics.
        
        Args:
            metric1_values: Historical values for metric 1
            metric2_values: Historical values for metric 2
            
        Returns:
            Tuple of (correlation_coefficient, p_value)
        """
        if len(metric1_values) != len(metric2_values):
            return 0.0, 1.0
        
        if len(metric1_values) < 3:
            return 0.0, 1.0
        
        try:
            correlation, p_value = pearsonr(metric1_values, metric2_values)
            return correlation, p_value
        except Exception as e:
            self.logger.warning(f"Error calculating correlation: {e}")
            return 0.0, 1.0
    
    def get_systemic_anomalies(self, anomaly_results: List[AnomalyResult]) -> List[str]:
        """
        Identify which anomalies are systemic (affecting multiple metrics).
        
        Returns:
            List of metric names with systemic anomalies
        """
        correlations = self.analyze_correlation(anomaly_results)
        
        systemic = [
            metric_name
            for metric_name, result in correlations.items()
            if result.is_systemic
        ]
        
        return systemic

