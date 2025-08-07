"""
Tests for the MetricsService class and monitoring functionality.
"""

import json
import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, patch, MagicMock
import requests

from services.metrics_service import (
    MetricsService, GrafanaCloudBackend, DatadogBackend, 
    SystemHealthMetric, AnomalyDetection
)
from models.core import MetricValue, ScraperResult


class TestGrafanaCloudBackend:
    """Test cases for Grafana Cloud backend."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.backend = GrafanaCloudBackend()
    
    @patch('services.metrics_service.settings')
    def test_initialization_with_config(self, mock_settings):
        """Test backend initialization with proper configuration."""
        mock_settings.GRAFANA_API_KEY = 'test-api-key'
        mock_settings.GRAFANA_URL = 'https://test.grafana.net'
        
        backend = GrafanaCloudBackend()
        
        assert backend.api_key == 'test-api-key'
        assert backend.grafana_url == 'https://test.grafana.net/'
        assert backend.metrics_url == 'https://test.grafana.net/api/v1/series'
    
    @patch('services.metrics_service.settings')
    def test_initialization_without_config(self, mock_settings):
        """Test backend initialization without configuration."""
        mock_settings.GRAFANA_API_KEY = ''
        mock_settings.GRAFANA_URL = ''
        
        backend = GrafanaCloudBackend()
        
        assert backend.api_key == ''
        assert backend.metrics_url is None
    
    def test_get_backend_name(self):
        """Test backend name retrieval."""
        assert self.backend.get_backend_name() == "Grafana Cloud"
    
    @patch('services.metrics_service.settings')
    @patch('requests.Session.put')
    def test_send_metrics_success(self, mock_put, mock_settings):
        """Test successful metrics submission to Grafana Cloud."""
        mock_settings.GRAFANA_API_KEY = 'test-key'
        mock_settings.GRAFANA_URL = 'https://test.grafana.net'
        mock_settings.ENVIRONMENT = 'test'
        
        # Mock successful response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_put.return_value = mock_response
        
        backend = GrafanaCloudBackend()
        
        metrics = [
            {
                'data_source': 'test_source',
                'metric_name': 'test_metric',
                'value': 42.0,
                'timestamp': datetime.now(timezone.utc),
                'source': 'test',
                'metadata': {'key': 'value'}
            }
        ]
        
        result = backend.send_metrics(metrics)
        
        assert result is True
        mock_put.assert_called_once()
        
        # Verify the request payload
        call_args = mock_put.call_args
        assert 'json' in call_args.kwargs
        payload = call_args.kwargs['json']
        assert 'series' in payload
        assert len(payload['series']) == 1
        
        series = payload['series'][0]
        assert series['metric'] == 'boom_bust_sentinel.test_metric'
        assert 'points' in series
        assert 'tags' in series
        assert series['tags']['data_source'] == 'test_source'
        assert series['tags']['environment'] == 'test'
    
    @patch('services.metrics_service.settings')
    def test_send_metrics_no_config(self, mock_settings):
        """Test metrics submission without configuration."""
        mock_settings.GRAFANA_API_KEY = ''
        mock_settings.GRAFANA_URL = ''
        
        backend = GrafanaCloudBackend()
        
        result = backend.send_metrics([{'test': 'data'}])
        
        assert result is False
    
    @patch('services.metrics_service.settings')
    @patch('requests.Session.put')
    def test_send_metrics_http_error(self, mock_put, mock_settings):
        """Test metrics submission with HTTP error."""
        mock_settings.GRAFANA_API_KEY = 'test-key'
        mock_settings.GRAFANA_URL = 'https://test.grafana.net'
        
        # Mock HTTP error
        mock_put.side_effect = requests.exceptions.HTTPError("HTTP 500 Error")
        
        backend = GrafanaCloudBackend()
        
        metrics = [{'metric_name': 'test', 'value': 1, 'timestamp': datetime.now()}]
        result = backend.send_metrics(metrics)
        
        assert result is False
    
    def test_format_for_grafana(self):
        """Test metric formatting for Grafana API."""
        with patch('services.metrics_service.settings') as mock_settings:
            mock_settings.ENVIRONMENT = 'test'
            
            backend = GrafanaCloudBackend()
            
            metrics = [
                {
                    'data_source': 'bond_issuance',
                    'metric_name': 'weekly_total',
                    'value': 1500000000,
                    'timestamp': datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
                    'source': 'scraper',
                    'metadata': {
                        'companies': 'MSFT,META',
                        'avg_coupon': 4.25
                    }
                }
            ]
            
            formatted = backend._format_for_grafana(metrics)
            
            assert len(formatted) == 1
            series = formatted[0]
            
            assert series['metric'] == 'boom_bust_sentinel.weekly_total'
            assert len(series['points']) == 1
            assert series['points'][0][1] == 1500000000
            assert series['tags']['data_source'] == 'bond_issuance'
            assert series['tags']['environment'] == 'test'
            assert series['tags']['meta_companies'] == 'MSFT,META'
            assert series['tags']['meta_avg_coupon'] == '4.25'


class TestDatadogBackend:
    """Test cases for Datadog backend."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.backend = DatadogBackend()
    
    def test_get_backend_name(self):
        """Test backend name retrieval."""
        assert self.backend.get_backend_name() == "Datadog"
    
    @patch('services.metrics_service.settings')
    @patch('requests.Session.post')
    def test_send_metrics_success(self, mock_post, mock_settings):
        """Test successful metrics submission to Datadog."""
        mock_settings.DATADOG_API_KEY = 'test-key'
        mock_settings.ENVIRONMENT = 'test'
        
        # Mock successful response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        backend = DatadogBackend()
        
        metrics = [
            {
                'data_source': 'test_source',
                'metric_name': 'test_metric',
                'value': 42.0,
                'timestamp': datetime.now(timezone.utc),
                'source': 'test',
                'metadata': {'key': 'value'}
            }
        ]
        
        result = backend.send_metrics(metrics)
        
        assert result is True
        mock_post.assert_called_once()
    
    def test_format_for_datadog(self):
        """Test metric formatting for Datadog API."""
        with patch('services.metrics_service.settings') as mock_settings:
            mock_settings.ENVIRONMENT = 'test'
            
            backend = DatadogBackend()
            
            metrics = [
                {
                    'data_source': 'bond_issuance',
                    'metric_name': 'weekly_total',
                    'value': 1500000000,
                    'timestamp': datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
                    'source': 'scraper',
                    'metadata': {
                        'companies': 'MSFT,META',
                        'avg_coupon': 4.25
                    }
                }
            ]
            
            formatted = backend._format_for_datadog(metrics)
            
            assert len(formatted) == 1
            series = formatted[0]
            
            assert series['metric'] == 'boom_bust_sentinel.weekly_total'
            assert len(series['points']) == 1
            assert series['points'][0][1] == 1500000000
            assert 'data_source:bond_issuance' in series['tags']
            assert 'environment:test' in series['tags']
            assert 'meta_companies:MSFT,META' in series['tags']


class TestMetricsService:
    """Test cases for the main MetricsService class."""
    
    def setup_method(self):
        """Setup test fixtures."""
        with patch('services.metrics_service.settings') as mock_settings:
            mock_settings.GRAFANA_API_KEY = ''
            mock_settings.GRAFANA_URL = ''
            mock_settings.DATADOG_API_KEY = ''
            
            self.service = MetricsService()
    
    def test_initialization_no_backends(self):
        """Test service initialization without configured backends."""
        assert len(self.service.backends) == 0
        assert len(self.service.health_metrics) == 0
        assert len(self.service.metric_history) == 0
    
    @patch('services.metrics_service.settings')
    def test_initialization_with_backends(self, mock_settings):
        """Test service initialization with configured backends."""
        mock_settings.GRAFANA_API_KEY = 'test-key'
        mock_settings.GRAFANA_URL = 'https://test.grafana.net'
        mock_settings.DATADOG_API_KEY = 'test-key'
        
        service = MetricsService()
        
        assert len(service.backends) == 2
        backend_names = [b.get_backend_name() for b in service.backends]
        assert 'Grafana Cloud' in backend_names
        assert 'Datadog' in backend_names
    
    def test_send_metric_no_backends(self):
        """Test sending single metric without backends."""
        metric_value = MetricValue(
            value=42.0,
            timestamp=datetime.now(timezone.utc),
            confidence=0.95,
            source='test',
            metadata={'test': 'data'}
        )
        
        result = self.service.send_metric('test_source', 'test_metric', metric_value)
        
        assert result is False
    
    def test_send_metrics_empty_list(self):
        """Test sending empty metrics list."""
        result = self.service.send_metrics([])
        
        assert result is True
    
    @patch('services.metrics_service.GrafanaCloudBackend')
    def test_send_metrics_with_backend(self, mock_backend_class):
        """Test sending metrics with configured backend."""
        # Setup mock backend
        mock_backend = Mock()
        mock_backend.get_backend_name.return_value = 'Test Backend'
        mock_backend.send_metrics.return_value = True
        mock_backend_class.return_value = mock_backend
        
        with patch('services.metrics_service.settings') as mock_settings:
            mock_settings.GRAFANA_API_KEY = 'test-key'
            mock_settings.GRAFANA_URL = 'https://test.grafana.net'
            mock_settings.DATADOG_API_KEY = ''
            
            service = MetricsService()
        
        metrics = [
            {
                'data_source': 'test',
                'metric_name': 'test_metric',
                'value': 42.0,
                'timestamp': datetime.now(timezone.utc),
                'source': 'test',
                'metadata': {}
            }
        ]
        
        result = service.send_metrics(metrics)
        
        assert result is True
        mock_backend.send_metrics.assert_called_once_with(metrics)
    
    def test_send_scraper_metrics(self):
        """Test sending metrics from scraper result."""
        scraper_result = ScraperResult(
            data_source='bond_issuance',
            metric_name='weekly',
            success=True,
            data={'total_amount': 1500000000, 'count': 5},
            error=None,
            execution_time=2.5,
            timestamp=datetime.now(timezone.utc)
        )
        
        with patch.object(self.service, 'send_metrics') as mock_send:
            mock_send.return_value = True
            
            result = self.service.send_scraper_metrics(scraper_result)
            
            assert result is True
            mock_send.assert_called_once()
            
            # Verify metrics were created correctly
            metrics = mock_send.call_args[0][0]
            assert len(metrics) == 4  # execution_time, success, total_amount, count
            
            metric_names = [m['metric_name'] for m in metrics]
            assert 'weekly_execution_time' in metric_names
            assert 'weekly_success' in metric_names
            assert 'weekly_total_amount' in metric_names
            assert 'weekly_count' in metric_names
    
    def test_update_system_health(self):
        """Test system health metric updates."""
        with patch.object(self.service, 'send_metrics') as mock_send:
            mock_send.return_value = True
            
            self.service.update_system_health(
                component='database',
                status='healthy',
                response_time_ms=50.0,
                error_count=0,
                metadata={'connection_pool': 'active'}
            )
            
            # Verify health metric was stored
            assert 'database' in self.service.health_metrics
            health_metric = self.service.health_metrics['database']
            
            assert health_metric.component == 'database'
            assert health_metric.status == 'healthy'
            assert health_metric.response_time_ms == 50.0
            assert health_metric.error_count == 0
            assert health_metric.success_rate == 1.0
            
            # Verify metrics were sent
            mock_send.assert_called_once()
            metrics = mock_send.call_args[0][0]
            assert len(metrics) == 2  # status and response_time
    
    def test_get_system_health(self):
        """Test system health retrieval."""
        # Add some health metrics
        self.service.health_metrics['component1'] = SystemHealthMetric(
            component='component1',
            status='healthy',
            last_check=datetime.now(timezone.utc)
        )
        
        health = self.service.get_system_health()
        
        assert len(health) == 1
        assert 'component1' in health
        assert health['component1'].status == 'healthy'
    
    def test_detect_anomalies_insufficient_data(self):
        """Test anomaly detection with insufficient historical data."""
        result = self.service.detect_anomalies('test_metric', 42.0)
        
        assert result is None
    
    def test_detect_anomalies_statistical(self):
        """Test statistical anomaly detection."""
        # Add historical data
        metric_name = 'test_metric'
        self.service.metric_history[metric_name] = [10, 12, 11, 13, 10, 12, 11, 14, 10, 13]
        
        # Test normal value
        result = self.service.detect_anomalies(metric_name, 12.0, 'statistical')
        
        assert result is not None
        assert result.metric_name == metric_name
        assert result.current_value == 12.0
        assert result.is_anomaly is False
        assert result.detection_method == 'statistical'
        
        # Test anomalous value
        result = self.service.detect_anomalies(metric_name, 50.0, 'statistical')
        
        assert result is not None
        assert result.is_anomaly is True
        assert result.confidence > 0.5
    
    def test_detect_anomalies_iqr(self):
        """Test IQR-based anomaly detection."""
        # Add historical data with some outliers
        metric_name = 'test_metric'
        self.service.metric_history[metric_name] = [10, 12, 11, 13, 10, 12, 11, 14, 10, 13, 15, 9]
        
        # Test normal value
        result = self.service.detect_anomalies(metric_name, 12.0, 'iqr')
        
        assert result is not None
        assert result.metric_name == metric_name
        assert result.current_value == 12.0
        assert result.detection_method == 'iqr'
        
        # Test anomalous value
        result = self.service.detect_anomalies(metric_name, 100.0, 'iqr')
        
        assert result is not None
        assert result.is_anomaly is True
    
    def test_update_metric_history(self):
        """Test metric history updates."""
        metrics = [
            {
                'metric_name': 'test_metric_1',
                'value': 42.0
            },
            {
                'metric_name': 'test_metric_2',
                'value': 'string_value'  # Should be ignored
            },
            {
                'metric_name': 'test_metric_1',
                'value': 43.0
            }
        ]
        
        self.service._update_metric_history(metrics)
        
        assert 'test_metric_1' in self.service.metric_history
        assert 'test_metric_2' not in self.service.metric_history
        assert len(self.service.metric_history['test_metric_1']) == 2
        assert self.service.metric_history['test_metric_1'] == [42.0, 43.0]
    
    def test_get_metric_history(self):
        """Test metric history retrieval."""
        self.service.metric_history['test_metric'] = [1.0, 2.0, 3.0]
        
        history = self.service.get_metric_history('test_metric')
        
        assert history == [1.0, 2.0, 3.0]
        
        # Verify it returns a copy
        history.append(4.0)
        assert len(self.service.metric_history['test_metric']) == 3
    
    def test_clear_metric_history(self):
        """Test metric history clearing."""
        self.service.metric_history['metric1'] = [1.0, 2.0]
        self.service.metric_history['metric2'] = [3.0, 4.0]
        
        # Clear specific metric
        self.service.clear_metric_history('metric1')
        
        assert 'metric1' not in self.service.metric_history
        assert 'metric2' in self.service.metric_history
        
        # Clear all metrics
        self.service.clear_metric_history()
        
        assert len(self.service.metric_history) == 0
    
    def test_get_metrics_summary(self):
        """Test metrics summary generation."""
        # Add some test data
        self.service.health_metrics['component1'] = SystemHealthMetric(
            component='component1',
            status='healthy',
            last_check=datetime.now(timezone.utc)
        )
        self.service.health_metrics['component2'] = SystemHealthMetric(
            component='component2',
            status='failed',
            last_check=datetime.now(timezone.utc)
        )
        self.service.metric_history['metric1'] = [1.0, 2.0, 3.0]
        self.service.metric_history['metric2'] = [4.0, 5.0]
        
        summary = self.service.get_metrics_summary()
        
        assert summary['backends_configured'] == 0
        assert summary['health_components'] == 2
        assert summary['healthy_components'] == 1
        assert summary['metrics_tracked'] == 2
        assert summary['total_metric_points'] == 5
        assert summary['last_health_check'] is not None


class TestSystemHealthMetric:
    """Test cases for SystemHealthMetric dataclass."""
    
    def test_creation(self):
        """Test SystemHealthMetric creation."""
        now = datetime.now(timezone.utc)
        
        metric = SystemHealthMetric(
            component='database',
            status='healthy',
            last_check=now,
            response_time_ms=50.0,
            error_count=0,
            success_rate=1.0,
            metadata={'pool_size': 10}
        )
        
        assert metric.component == 'database'
        assert metric.status == 'healthy'
        assert metric.last_check == now
        assert metric.response_time_ms == 50.0
        assert metric.error_count == 0
        assert metric.success_rate == 1.0
        assert metric.metadata == {'pool_size': 10}
    
    def test_creation_with_defaults(self):
        """Test SystemHealthMetric creation with default values."""
        now = datetime.now(timezone.utc)
        
        metric = SystemHealthMetric(
            component='api',
            status='degraded',
            last_check=now
        )
        
        assert metric.response_time_ms is None
        assert metric.error_count == 0
        assert metric.success_rate == 1.0
        assert metric.metadata == {}


class TestAnomalyDetection:
    """Test cases for AnomalyDetection dataclass."""
    
    def test_creation(self):
        """Test AnomalyDetection creation."""
        now = datetime.now(timezone.utc)
        
        anomaly = AnomalyDetection(
            metric_name='test_metric',
            current_value=100.0,
            expected_range=(10.0, 50.0),
            is_anomaly=True,
            confidence=0.95,
            detection_method='statistical',
            timestamp=now
        )
        
        assert anomaly.metric_name == 'test_metric'
        assert anomaly.current_value == 100.0
        assert anomaly.expected_range == (10.0, 50.0)
        assert anomaly.is_anomaly is True
        assert anomaly.confidence == 0.95
        assert anomaly.detection_method == 'statistical'
        assert anomaly.timestamp == now


@pytest.fixture
def sample_metrics():
    """Sample metrics for testing."""
    return [
        {
            'data_source': 'bond_issuance',
            'metric_name': 'weekly_total',
            'value': 1500000000,
            'timestamp': datetime.now(timezone.utc),
            'source': 'scraper',
            'metadata': {'companies': 'MSFT,META'}
        },
        {
            'data_source': 'bdc_discount',
            'metric_name': 'avg_discount',
            'value': -0.15,
            'timestamp': datetime.now(timezone.utc),
            'source': 'scraper',
            'metadata': {'symbols': 'ARCC,OCSL'}
        }
    ]


@pytest.fixture
def sample_scraper_result():
    """Sample scraper result for testing."""
    return ScraperResult(
        data_source='bond_issuance',
        metric_name='weekly',
        success=True,
        data={
            'total_amount': 2500000000,
            'bond_count': 8,
            'avg_coupon': 4.75
        },
        error=None,
        execution_time=3.2,
        timestamp=datetime.now(timezone.utc)
    )