"""
Learning System - Tracks feedback and optimizes thresholds over time.

This agent learns from user feedback to improve anomaly detection:
- Tracks which alerts were acknowledged/ignored
- Adjusts thresholds based on feedback
- Improves detection accuracy over time
"""

import json
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict

from agents.data_quality.enhanced_anomaly_detector import AnomalyResult


@dataclass
class FeedbackRecord:
    """Record of user feedback on an anomaly."""
    metric_name: str
    anomaly_timestamp: datetime
    feedback_timestamp: datetime
    was_relevant: bool  # True if user acknowledged, False if ignored
    confidence_at_detection: float
    threshold_adjustment: float
    notes: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['anomaly_timestamp'] = self.anomaly_timestamp.isoformat()
        data['feedback_timestamp'] = self.feedback_timestamp.isoformat()
        return data


class LearningSystem:
    """
    Learning system that improves anomaly detection based on feedback.
    
    Usage:
        learner = LearningSystem()
        learner.record_feedback(metric_name='bdc_discount', was_relevant=True)
        optimized_threshold = learner.get_optimized_threshold('bdc_discount')
    """
    
    def __init__(self, storage_dir: str = "logs/data_quality"):
        self.logger = logging.getLogger(__name__)
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.feedback_file = self.storage_dir / "feedback_history.jsonl"
        self.thresholds_file = self.storage_dir / "optimized_thresholds.json"
        
        # Load optimized thresholds
        self.optimized_thresholds: Dict[str, float] = self._load_optimized_thresholds()
    
    def record_feedback(self, metric_name: str, was_relevant: bool,
                       anomaly_result: Optional[AnomalyResult] = None,
                       notes: Optional[str] = None) -> bool:
        """
        Record user feedback on an anomaly.
        
        Args:
            metric_name: Name of the metric
            was_relevant: True if alert was relevant/acknowledged, False if ignored
            anomaly_result: Original anomaly result (optional)
            notes: Additional notes (optional)
            
        Returns:
            True if recorded successfully
        """
        try:
            feedback = FeedbackRecord(
                metric_name=metric_name,
                anomaly_timestamp=anomaly_result.timestamp if anomaly_result else datetime.now(timezone.utc),
                feedback_timestamp=datetime.now(timezone.utc),
                was_relevant=was_relevant,
                confidence_at_detection=anomaly_result.confidence if anomaly_result else 0.0,
                threshold_adjustment=anomaly_result.threshold_adjustment if anomaly_result else 1.0,
                notes=notes
            )
            
            # Append to feedback history
            with open(self.feedback_file, 'a') as f:
                f.write(json.dumps(feedback.to_dict()) + '\n')
            
            # Update optimized thresholds
            self._update_thresholds(metric_name, was_relevant, anomaly_result)
            
            self.logger.info(f"✅ Recorded feedback for {metric_name}: {'relevant' if was_relevant else 'ignored'}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to record feedback: {e}")
            return False
    
    def _update_thresholds(self, metric_name: str, was_relevant: bool,
                          anomaly_result: Optional[AnomalyResult]) -> None:
        """Update optimized thresholds based on feedback."""
        # Get recent feedback for this metric
        recent_feedback = self.get_recent_feedback(metric_name, days=30)
        
        if len(recent_feedback) < 5:
            # Not enough feedback yet
            return
        
        # Calculate relevance rate
        relevant_count = sum(1 for f in recent_feedback if f.was_relevant)
        relevance_rate = relevant_count / len(recent_feedback)
        
        # Adjust threshold based on relevance rate
        current_threshold = self.optimized_thresholds.get(metric_name, 1.0)
        
        if relevance_rate < 0.3:
            # Too many false positives - increase threshold (less sensitive)
            new_threshold = current_threshold * 1.1
            self.logger.info(f"📈 Increasing threshold for {metric_name}: {current_threshold:.2f} -> {new_threshold:.2f} (low relevance: {relevance_rate:.2%})")
        elif relevance_rate > 0.7:
            # High relevance - can decrease threshold slightly (more sensitive)
            new_threshold = current_threshold * 0.95
            self.logger.info(f"📉 Decreasing threshold for {metric_name}: {current_threshold:.2f} -> {new_threshold:.2f} (high relevance: {relevance_rate:.2%})")
        else:
            # Good balance - keep current threshold
            return
        
        # Update optimized threshold
        self.optimized_thresholds[metric_name] = new_threshold
        self._save_optimized_thresholds()
    
    def get_optimized_threshold(self, metric_name: str, base_threshold: float) -> float:
        """
        Get optimized threshold for a metric.
        
        Args:
            metric_name: Name of the metric
            base_threshold: Base threshold from historical data
            
        Returns:
            Optimized threshold (adjusted based on learning)
        """
        adjustment = self.optimized_thresholds.get(metric_name, 1.0)
        return base_threshold * adjustment
    
    def get_recent_feedback(self, metric_name: Optional[str] = None,
                           days: int = 30) -> List[FeedbackRecord]:
        """
        Get recent feedback records.
        
        Args:
            metric_name: Filter by metric name (optional)
            days: Number of days to look back
            
        Returns:
            List of FeedbackRecord objects
        """
        if not self.feedback_file.exists():
            return []
        
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        feedback_records = []
        
        try:
            with open(self.feedback_file, 'r') as f:
                for line in f:
                    if not line.strip():
                        continue
                    
                    data = json.loads(line)
                    
                    # Filter by date
                    feedback_time = datetime.fromisoformat(data['feedback_timestamp'])
                    if feedback_time < cutoff_date:
                        continue
                    
                    # Filter by metric if specified
                    if metric_name and data['metric_name'] != metric_name:
                        continue
                    
                    feedback = FeedbackRecord(
                        metric_name=data['metric_name'],
                        anomaly_timestamp=datetime.fromisoformat(data['anomaly_timestamp']),
                        feedback_timestamp=feedback_time,
                        was_relevant=data['was_relevant'],
                        confidence_at_detection=data['confidence_at_detection'],
                        threshold_adjustment=data['threshold_adjustment'],
                        notes=data.get('notes')
                    )
                    
                    feedback_records.append(feedback)
            
            # Sort by timestamp (newest first)
            feedback_records.sort(key=lambda x: x.feedback_timestamp, reverse=True)
            
        except Exception as e:
            self.logger.error(f"Failed to read feedback history: {e}")
        
        return feedback_records
    
    def get_feedback_stats(self, metric_name: Optional[str] = None,
                          days: int = 30) -> Dict[str, Any]:
        """
        Get statistics about feedback.
        
        Args:
            metric_name: Filter by metric name (optional)
            days: Number of days to analyze
            
        Returns:
            Dictionary with statistics
        """
        feedback = self.get_recent_feedback(metric_name, days)
        
        if not feedback:
            return {
                'total_feedback': 0,
                'relevance_rate': 0.0,
                'avg_confidence': 0.0
            }
        
        relevant_count = sum(1 for f in feedback if f.was_relevant)
        avg_confidence = sum(f.confidence_at_detection for f in feedback) / len(feedback)
        
        return {
            'total_feedback': len(feedback),
            'relevance_rate': relevant_count / len(feedback),
            'avg_confidence': avg_confidence,
            'relevant_count': relevant_count,
            'ignored_count': len(feedback) - relevant_count
        }
    
    def _load_optimized_thresholds(self) -> Dict[str, float]:
        """Load optimized thresholds from disk."""
        if not self.thresholds_file.exists():
            return {}
        
        try:
            with open(self.thresholds_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            self.logger.warning(f"Failed to load optimized thresholds: {e}")
            return {}
    
    def _save_optimized_thresholds(self) -> None:
        """Save optimized thresholds to disk."""
        try:
            with open(self.thresholds_file, 'w') as f:
                json.dump(self.optimized_thresholds, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save optimized thresholds: {e}")

