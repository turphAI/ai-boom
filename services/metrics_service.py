"""
Metrics service for sending observability data to monitoring systems.
Supports Grafana Cloud free tier and system health monitoring.
"""

import json
import logging
import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Union
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
import statistics

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from config.settings import settings
from models.core import MetricValue, ScraperResult


@dataclass
class SystemHealthMetric:
    """Represents a system health metric."""
    component: str
    status: str  # 'healthy', 'degraded', 'failed'
    last_check: datetime
    response_time_ms: Optional[float] = None
    error_count: int = 0
    success_rate: float = 1.0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class AnomalyDetection:
    """Represents an anomaly detection result."""
    metric_name: str
    current_value: float
    expected_range: tuple  # (min, max)
    is_anomaly: bool
    confidence: float
    detection_method: str
    timestamp: datetime


class MetricsBackend(ABC):
    """Abstract base class for metrics backends."""
    
    @abstractmethod
    def send_metrics(self, metrics: List[Dict[str, Any]]) -> bool:
        """Send metrics to the backend."""
        pass
    
    @abstractmethod
    def get_backend_name(self) -> str:
        """Get the name of this metrics backend."""
        pass


class GrafanaCloudBackend(MetricsBackend):
    """Grafana Cloud metrics backend using the free tier."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.api_key = settings.GRAFANA_API_KEY
        self.grafana_url = settings.GRAFANA_URL
        
        # Grafana Cloud free tier endpoint
        if self.grafana_url and not self.grafana_url.endswith('/'):
            self.grafana_url += '/'
        
        self.metrics_url = f"{self.grafana_url}api/v1/series" if self.grafana_url else None
        
        # Session for connection pooling
        self.session = requests.Session()
        if self.api_key:
            self.session.headers.update({
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            })
    
    def get_backend_name(self) -> str:
        return "Grafana Cloud"
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def send_metrics(self, metrics: List[Dict[str, Any]]) -> bool:
        """Send metrics to Grafana Cloud using PUT /api/v1/series."""
        if not self.metrics_url or not self.api_key:
            self.logger.warning("Grafana Cloud not configured, skipping metrics submission")
            return False
        
        if not metrics:
            return True
        
        try:
            # Format metrics for Grafana Cloud API
            grafana_metrics = self._format_for_grafana(metrics)
            
            # Send to Grafana Cloud
            response = self.session.put(
                self.metrics_url,
                json={'series': grafana_metrics},
                timeout=30
            )
            
            response.raise_for_status()
            
            self.logger.info(f"Successfully sent {len(metrics)} metrics to Grafana Cloud")
            return True
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to send metrics to Grafana Cloud: {e}")
            if hasattr(e, 'response') and e.response is not None:
                self.logger.error(f"Response status: {e.response.status_code}")
                self.logger.error(f"Response body: {e.response.text}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error sending metrics to Grafana Cloud: {e}")
            return False
    
    def _format_for_grafana(self, metrics: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format metrics for Grafana Cloud API."""
        grafana_series = []
        
        for metric in metrics:
            # Convert timestamp to Unix timestamp
            timestamp = metric.get('timestamp')
            if isinstance(timestamp, datetime):
                unix_timestamp = int(timestamp.timestamp())
            elif isinstance(timestamp, str):
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                unix_timestamp = int(dt.timestamp())
            else:
                unix_timestamp = int(time.time())
            
            # Create Grafana series format
            series = {
                'metric': f"boom_bust_sentinel.{metric['metric_name']}",
                'points': [[unix_timestamp, metric['value']]],
                'tags': {
                    'data_source': metric.get('data_source', 'unknown'),
                    'environment': settings.ENVIRONMENT,
                    'source': metric.get('source', 'boom_bust_sentinel')
                }
            }
            
            # Add metadata as tags
            metadata = metric.get('metadata', {})
            for key, value in metadata.items():
                if isinstance(value, (str, int, float, bool)):
                    series['tags'][f"meta_{key}"] = str(value)
            
            grafana_series.append(series)
        
        return grafana_series


class DatadogBackend(MetricsBackend):
    """Datadog metrics backend as fallback option."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.api_key = settings.DATADOG_API_KEY
        self.api_url = "https://api.datadoghq.com/api/v1/series"
        
        # Session for connection pooling
        self.session = requests.Session()
        if self.api_key:
            self.session.headers.update({
                'DD-API-KEY': self.api_key,
                'Content-Type': 'application/json'
            })
    
    def get_backend_name(self) -> str:
        return "Datadog"
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def send_metrics(self, metrics: List[Dict[str, Any]]) -> bool:
        """Send metrics to Datadog."""
        if not self.api_key:
            self.logger.warning("Datadog not configured, skipping metrics submission")
            return False
        
        if not metrics:
            return True
        
        try:
            # Format metrics for Datadog API
            datadog_metrics = self._format_for_datadog(metrics)
            
            # Send to Datadog
            response = self.session.post(
                self.api_url,
                json={'series': datadog_metrics},
                timeout=30
            )
            
            response.raise_for_status()
            
            self.logger.info(f"Successfully sent {len(metrics)} metrics to Datadog")
            return True
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to send metrics to Datadog: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error sending metrics to Datadog: {e}")
            return False
    
    def _format_for_datadog(self, metrics: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format metrics for Datadog API."""
        datadog_series = []
        
        for metric in metrics:
            # Convert timestamp to Unix timestamp
            timestamp = metric.get('timestamp')
            if isinstance(timestamp, datetime):
                unix_timestamp = int(timestamp.timestamp())
            elif isinstance(timestamp, str):
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                unix_timestamp = int(dt.timestamp())
            else:
                unix_timestamp = int(time.time())
            
            # Create Datadog series format
            series = {
                'metric': f"boom_bust_sentinel.{metric['metric_name']}",
                'points': [[unix_timestamp, metric['value']]],
                'tags': [
                    f"data_source:{metric.get('data_source', 'unknown')}",
                    f"environment:{settings.ENVIRONMENT}",
                    f"source:{metric.get('source', 'boom_bust_sentinel')}"
                ]
            }
            
            # Add metadata as tags
            metadata = metric.get('metadata', {})
            for key, value in metadata.items():
                if isinstance(value, (str, int, float, bool)):
                    series['tags'].append(f"meta_{key}:{value}")
            
            datadog_series.append(series)
        
        return datadog_series


class MetricsService:
    """Service for sending metrics to monitoring systems and health monitoring."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.backends: List[MetricsBackend] = []
        self.health_metrics: Dict[str, SystemHealthMetric] = {}
        self.metric_history: Dict[str, List[float]] = {}
        self.max_history_size = 100
        
        # Initialize backends
        self._initialize_backends()
    
    def _initialize_backends(self) -> None:
        """Initialize all configured metrics backends."""
        # Add Grafana Cloud if configured
        if settings.GRAFANA_API_KEY and settings.GRAFANA_URL:
            self.backends.append(GrafanaCloudBackend())
        
        # Add Datadog if configured
        if settings.DATADOG_API_KEY:
            self.backends.append(DatadogBackend())
        
        if not self.backends:
            self.logger.warning("No metrics backends configured")
        else:
            backend_names = [b.get_backend_name() for b in self.backends]
            self.logger.info(f"Initialized metrics backends: {', '.join(backend_names)}")
    
    def send_metric(self, data_source: str, metric_name: str, metric_value: MetricValue) -> bool:
        """Send a single metric to all configured backends."""
        metric_data = {
            'data_source': data_source,
            'metric_name': metric_name,
            'value': metric_value.value,
            'timestamp': metric_value.timestamp,
            'source': metric_value.source,
            'confidence': metric_value.confidence,
            'metadata': metric_value.metadata
        }
        
        return self.send_metrics([metric_data])
    
    def send_metrics(self, metrics: List[Dict[str, Any]]) -> bool:
        """Send multiple metrics to all configured backends."""
        if not metrics:
            return True
        
        if not self.backends:
            self.logger.warning("No metrics backends available")
            return False
        
        # Update metric history for anomaly detection
        self._update_metric_history(metrics)
        
        # Send to all backends
        results = {}
        for backend in self.backends:
            try:
                success = backend.send_metrics(metrics)
                results[backend.get_backend_name()] = success
            except Exception as e:
                self.logger.error(f"Error sending metrics to {backend.get_backend_name()}: {e}")
                results[backend.get_backend_name()] = False
        
        # Return True if at least one backend succeeded
        success = any(results.values())
        
        if success:
            successful_backends = [name for name, result in results.items() if result]
            self.logger.info(f"Metrics sent successfully to: {', '.join(successful_backends)}")
        else:
            self.logger.error("Failed to send metrics to any backend")
        
        return success
    
    def send_scraper_metrics(self, scraper_result: ScraperResult) -> bool:
        """Send metrics from a scraper result."""
        metrics = []
        
        # Execution time metric
        metrics.append({
            'data_source': scraper_result.data_source,
            'metric_name': f"{scraper_result.metric_name}_execution_time",
            'value': scraper_result.execution_time,
            'timestamp': scraper_result.timestamp,
            'source': 'scraper_execution',
            'metadata': {
                'success': scraper_result.success,
                'has_error': scraper_result.error is not None
            }
        })
        
        # Success/failure metric
        metrics.append({
            'data_source': scraper_result.data_source,
            'metric_name': f"{scraper_result.metric_name}_success",
            'value': 1 if scraper_result.success else 0,
            'timestamp': scraper_result.timestamp,
            'source': 'scraper_execution',
            'metadata': {
                'error': scraper_result.error if scraper_result.error else None
            }
        })
        
        # Data metrics if available
        if scraper_result.success and scraper_result.data:
            for key, value in scraper_result.data.items():
                if isinstance(value, (int, float)):
                    metrics.append({
                        'data_source': scraper_result.data_source,
                        'metric_name': f"{scraper_result.metric_name}_{key}",
                        'value': value,
                        'timestamp': scraper_result.timestamp,
                        'source': 'scraper_data',
                        'metadata': {}
                    })
        
        return self.send_metrics(metrics)
    
    def update_system_health(self, component: str, status: str, response_time_ms: Optional[float] = None, 
                           error_count: int = 0, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Update system health metrics for a component."""
        health_metric = SystemHealthMetric(
            component=component,
            status=status,
            last_check=datetime.now(timezone.utc),
            response_time_ms=response_time_ms,
            error_count=error_count,
            metadata=metadata or {}
        )
        
        # Calculate success rate if we have previous data
        if component in self.health_metrics:
            previous = self.health_metrics[component]
            total_checks = previous.metadata.get('total_checks', 1) + 1
            successful_checks = previous.metadata.get('successful_checks', 1)
            
            if status == 'healthy':
                successful_checks += 1
            
            health_metric.success_rate = successful_checks / total_checks
            health_metric.metadata.update({
                'total_checks': total_checks,
                'successful_checks': successful_checks
            })
        else:
            health_metric.success_rate = 1.0 if status == 'healthy' else 0.0
            health_metric.metadata.update({
                'total_checks': 1,
                'successful_checks': 1 if status == 'healthy' else 0
            })
        
        self.health_metrics[component] = health_metric
        
        # Send health metrics
        health_metrics = [
            {
                'data_source': 'system_health',
                'metric_name': f"{component}_status",
                'value': 1 if status == 'healthy' else 0,
                'timestamp': health_metric.last_check,
                'source': 'health_monitor',
                'metadata': {
                    'component': component,
                    'status': status,
                    'success_rate': health_metric.success_rate
                }
            }
        ]
        
        if response_time_ms is not None:
            health_metrics.append({
                'data_source': 'system_health',
                'metric_name': f"{component}_response_time",
                'value': response_time_ms,
                'timestamp': health_metric.last_check,
                'source': 'health_monitor',
                'metadata': {'component': component}
            })
        
        if error_count > 0:
            health_metrics.append({
                'data_source': 'system_health',
                'metric_name': f"{component}_error_count",
                'value': error_count,
                'timestamp': health_metric.last_check,
                'source': 'health_monitor',
                'metadata': {'component': component}
            })
        
        self.send_metrics(health_metrics)
    
    def get_system_health(self) -> Dict[str, SystemHealthMetric]:
        """Get current system health status."""
        return self.health_metrics.copy()
    
    def detect_anomalies(self, metric_name: str, current_value: float, 
                        detection_method: str = 'statistical') -> Optional[AnomalyDetection]:
        """Detect anomalies in metric values using statistical methods."""
        if metric_name not in self.metric_history:
            return None
        
        history = self.metric_history[metric_name]
        if len(history) < 10:  # Need at least 10 data points
            return None
        
        try:
            if detection_method == 'statistical':
                return self._statistical_anomaly_detection(metric_name, current_value, history)
            elif detection_method == 'iqr':
                return self._iqr_anomaly_detection(metric_name, current_value, history)
            else:
                self.logger.warning(f"Unknown anomaly detection method: {detection_method}")
                return None
        except Exception as e:
            self.logger.error(f"Error in anomaly detection for {metric_name}: {e}")
            return None
    
    def _statistical_anomaly_detection(self, metric_name: str, current_value: float, 
                                     history: List[float]) -> AnomalyDetection:
        """Statistical anomaly detection using standard deviation."""
        mean = statistics.mean(history)
        stdev = statistics.stdev(history) if len(history) > 1 else 0
        
        # Consider values beyond 2 standard deviations as anomalies
        threshold = 2.0
        lower_bound = mean - (threshold * stdev)
        upper_bound = mean + (threshold * stdev)
        
        is_anomaly = current_value < lower_bound or current_value > upper_bound
        
        # Calculate confidence based on how far from the mean
        if stdev > 0:
            z_score = abs(current_value - mean) / stdev
            confidence = min(z_score / threshold, 1.0)
        else:
            confidence = 1.0 if is_anomaly else 0.0
        
        return AnomalyDetection(
            metric_name=metric_name,
            current_value=current_value,
            expected_range=(lower_bound, upper_bound),
            is_anomaly=is_anomaly,
            confidence=confidence,
            detection_method='statistical',
            timestamp=datetime.now(timezone.utc)
        )
    
    def _iqr_anomaly_detection(self, metric_name: str, current_value: float, 
                              history: List[float]) -> AnomalyDetection:
        """Anomaly detection using Interquartile Range (IQR)."""
        sorted_history = sorted(history)
        n = len(sorted_history)
        
        q1_idx = n // 4
        q3_idx = 3 * n // 4
        
        q1 = sorted_history[q1_idx]
        q3 = sorted_history[q3_idx]
        iqr = q3 - q1
        
        # IQR method: values beyond 1.5 * IQR from Q1/Q3 are outliers
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        is_anomaly = current_value < lower_bound or current_value > upper_bound
        
        # Calculate confidence based on distance from bounds
        if is_anomaly:
            if current_value < lower_bound:
                distance = lower_bound - current_value
            else:
                distance = current_value - upper_bound
            
            confidence = min(distance / (iqr * 0.5), 1.0)
        else:
            confidence = 0.0
        
        return AnomalyDetection(
            metric_name=metric_name,
            current_value=current_value,
            expected_range=(lower_bound, upper_bound),
            is_anomaly=is_anomaly,
            confidence=confidence,
            detection_method='iqr',
            timestamp=datetime.now(timezone.utc)
        )
    
    def _update_metric_history(self, metrics: List[Dict[str, Any]]) -> None:
        """Update metric history for anomaly detection."""
        for metric in metrics:
            metric_name = metric.get('metric_name')
            value = metric.get('value')
            
            if metric_name and isinstance(value, (int, float)):
                if metric_name not in self.metric_history:
                    self.metric_history[metric_name] = []
                
                self.metric_history[metric_name].append(float(value))
                
                # Keep only the most recent values
                if len(self.metric_history[metric_name]) > self.max_history_size:
                    self.metric_history[metric_name] = self.metric_history[metric_name][-self.max_history_size:]
    
    def get_metric_history(self, metric_name: str) -> List[float]:
        """Get metric history for a specific metric."""
        return self.metric_history.get(metric_name, []).copy()
    
    def clear_metric_history(self, metric_name: Optional[str] = None) -> None:
        """Clear metric history for a specific metric or all metrics."""
        if metric_name:
            self.metric_history.pop(metric_name, None)
        else:
            self.metric_history.clear()
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get a summary of metrics and system health."""
        return {
            'backends_configured': len(self.backends),
            'backend_names': [b.get_backend_name() for b in self.backends],
            'health_components': len(self.health_metrics),
            'healthy_components': sum(1 for h in self.health_metrics.values() if h.status == 'healthy'),
            'metrics_tracked': len(self.metric_history),
            'total_metric_points': sum(len(history) for history in self.metric_history.values()),
            'last_health_check': max(
                (h.last_check for h in self.health_metrics.values()),
                default=None
            )
        }