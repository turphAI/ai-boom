"""
Tests for the health monitoring system.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, patch, MagicMock
import asyncio

from utils.health_monitor import HealthMonitor, HealthCheck
from services.metrics_service import MetricsService


class TestHealthCheck:
    """Test cases for HealthCheck dataclass."""
    
    def test_creation(self):
        """Test HealthCheck creation."""
        def dummy_check():
            return True
        
        check = HealthCheck(
            name='test_check',
            check_function=dummy_check,
            timeout_seconds=30,
            critical=True,
            metadata={'key': 'value'}
        )
        
        assert check.name == 'test_check'
        assert check.check_function == dummy_check
        assert check.timeout_seconds == 30
        assert check.critical is True
        assert check.metadata == {'key': 'value'}
    
    def test_creation_with_defaults(self):
        """Test HealthCheck creation with default values."""
        def dummy_check():
            return True
        
        check = HealthCheck(
            name='test_check',
            check_function=dummy_check
        )
        
        assert check.timeout_seconds == 30
        assert check.critical is True
        assert check.metadata == {}


class TestHealthMonitor:
    """Test cases for HealthMonitor class."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.mock_metrics_service = Mock(spec=MetricsService)
        self.health_monitor = HealthMonitor(metrics_service=self.mock_metrics_service)
    
    def test_initialization(self):
        """Test health monitor initialization."""
        assert self.health_monitor.metrics_service == self.mock_metrics_service
        assert len(self.health_monitor.health_checks) > 0
        assert len(self.health_monitor.last_check_results) == 0
        
        # Check that default health checks are registered
        expected_checks = ['database', 'alert_service', 'metrics_service', 'sec_edgar_api', 'yahoo_finance_api']
        for check_name in expected_checks:
            assert check_name in self.health_monitor.health_checks
    
    def test_register_health_check(self):
        """Test registering a custom health check."""
        def custom_check():
            return True
        
        self.health_monitor.register_health_check(
            name='custom_check',
            check_function=custom_check,
            timeout_seconds=15,
            critical=False,
            metadata={'type': 'custom'}
        )
        
        assert 'custom_check' in self.health_monitor.health_checks
        check = self.health_monitor.health_checks['custom_check']
        
        assert check.name == 'custom_check'
        assert check.check_function == custom_check
        assert check.timeout_seconds == 15
        assert check.critical is False
        assert check.metadata == {'type': 'custom'}
    
    def test_run_health_check_success(self):
        """Test running a successful health check."""
        def successful_check():
            return True
        
        self.health_monitor.register_health_check(
            name='test_check',
            check_function=successful_check,
            timeout_seconds=5
        )
        
        result = self.health_monitor.run_health_check('test_check')
        
        assert result['name'] == 'test_check'
        assert result['healthy'] is True
        assert result['response_time_ms'] > 0
        assert result['error'] is None
        assert isinstance(result['timestamp'], datetime)
        
        # Verify metrics were updated
        self.mock_metrics_service.update_system_health.assert_called_once()
        call_args = self.mock_metrics_service.update_system_health.call_args
        assert call_args[1]['component'] == 'test_check'
        assert call_args[1]['status'] == 'healthy'
    
    def test_run_health_check_failure(self):
        """Test running a failing health check."""
        def failing_check():
            return False
        
        self.health_monitor.register_health_check(
            name='test_check',
            check_function=failing_check,
            timeout_seconds=5
        )
        
        result = self.health_monitor.run_health_check('test_check')
        
        assert result['name'] == 'test_check'
        assert result['healthy'] is False
        assert result['response_time_ms'] > 0
        assert result['error'] is None
        
        # Verify metrics were updated
        self.mock_metrics_service.update_system_health.assert_called_once()
        call_args = self.mock_metrics_service.update_system_health.call_args
        assert call_args[1]['component'] == 'test_check'
        assert call_args[1]['status'] == 'failed'
    
    def test_run_health_check_exception(self):
        """Test running a health check that raises an exception."""
        def exception_check():
            raise ValueError("Test exception")
        
        self.health_monitor.register_health_check(
            name='test_check',
            check_function=exception_check,
            timeout_seconds=5
        )
        
        result = self.health_monitor.run_health_check('test_check')
        
        assert result['name'] == 'test_check'
        assert result['healthy'] is False
        assert result['response_time_ms'] > 0
        assert 'Test exception' in result['error']
        
        # Verify metrics were updated
        self.mock_metrics_service.update_system_health.assert_called_once()
        call_args = self.mock_metrics_service.update_system_health.call_args
        assert call_args[1]['component'] == 'test_check'
        assert call_args[1]['status'] == 'failed'
    
    def test_run_health_check_not_found(self):
        """Test running a non-existent health check."""
        with pytest.raises(ValueError, match="Health check 'nonexistent' not found"):
            self.health_monitor.run_health_check('nonexistent')
    
    def test_run_all_health_checks(self):
        """Test running all health checks."""
        # Mock the default health check functions to avoid external dependencies
        with patch.object(self.health_monitor, '_check_database_health', return_value=True), \
             patch.object(self.health_monitor, '_check_alert_service_health', return_value=True), \
             patch.object(self.health_monitor, '_check_metrics_service_health', return_value=True), \
             patch.object(self.health_monitor, '_check_sec_edgar_health', return_value=False), \
             patch.object(self.health_monitor, '_check_yahoo_finance_health', return_value=True):
            
            results = self.health_monitor.run_all_health_checks()
            
            assert len(results) == 5
            assert all(isinstance(result, dict) for result in results.values())
            assert all('healthy' in result for result in results.values())
            
            # Check specific results
            assert results['database']['healthy'] is True
            assert results['sec_edgar_api']['healthy'] is False
    
    def test_get_system_status_healthy(self):
        """Test getting system status when all components are healthy."""
        # Set up mock results
        self.health_monitor.last_check_results = {
            'component1': {
                'name': 'component1',
                'healthy': True,
                'critical': True,
                'timestamp': datetime.now(timezone.utc)
            },
            'component2': {
                'name': 'component2',
                'healthy': True,
                'critical': False,
                'timestamp': datetime.now(timezone.utc)
            }
        }
        
        status = self.health_monitor.get_system_status()
        
        assert status['status'] == 'healthy'
        assert 'All components healthy' in status['message']
        assert status['summary']['total_components'] == 2
        assert status['summary']['healthy_components'] == 2
        assert status['summary']['critical_failures'] == 0
    
    def test_get_system_status_critical(self):
        """Test getting system status with critical failures."""
        self.health_monitor.last_check_results = {
            'critical_component': {
                'name': 'critical_component',
                'healthy': False,
                'critical': True,
                'timestamp': datetime.now(timezone.utc)
            },
            'non_critical_component': {
                'name': 'non_critical_component',
                'healthy': False,
                'critical': False,
                'timestamp': datetime.now(timezone.utc)
            }
        }
        
        status = self.health_monitor.get_system_status()
        
        assert status['status'] == 'critical'
        assert 'critical_component' in status['message']
        assert status['summary']['critical_failures'] == 1
        assert status['summary']['non_critical_failures'] == 1
    
    def test_get_system_status_degraded(self):
        """Test getting system status with only non-critical failures."""
        self.health_monitor.last_check_results = {
            'critical_component': {
                'name': 'critical_component',
                'healthy': True,
                'critical': True,
                'timestamp': datetime.now(timezone.utc)
            },
            'non_critical_component': {
                'name': 'non_critical_component',
                'healthy': False,
                'critical': False,
                'timestamp': datetime.now(timezone.utc)
            }
        }
        
        status = self.health_monitor.get_system_status()
        
        assert status['status'] == 'degraded'
        assert 'non_critical_component' in status['message']
        assert status['summary']['critical_failures'] == 0
        assert status['summary']['non_critical_failures'] == 1
    
    def test_get_system_status_no_checks(self):
        """Test getting system status when no checks have been run."""
        status = self.health_monitor.get_system_status()
        
        assert status['status'] == 'unknown'
        assert 'No health checks have been run' in status['message']
        assert status['last_check'] is None
    
    @patch('utils.health_monitor.StateStore')
    def test_check_database_health_success(self, mock_state_store_class):
        """Test database health check success."""
        mock_state_store = Mock()
        mock_state_store.save_data.return_value = None
        mock_state_store_class.return_value = mock_state_store
        
        result = self.health_monitor._check_database_health()
        
        assert result is True
        mock_state_store.save_data.assert_called_once()
    
    @patch('utils.health_monitor.StateStore')
    def test_check_database_health_failure(self, mock_state_store_class):
        """Test database health check failure."""
        mock_state_store = Mock()
        mock_state_store.save_data.side_effect = Exception("Database connection failed")
        mock_state_store_class.return_value = mock_state_store
        
        result = self.health_monitor._check_database_health()
        
        assert result is False
    
    @patch('utils.health_monitor.AlertService')
    def test_check_alert_service_health_success(self, mock_alert_service_class):
        """Test alert service health check success."""
        mock_alert_service = Mock()
        mock_alert_service.channels = ['mock_channel']
        mock_alert_service_class.return_value = mock_alert_service
        
        result = self.health_monitor._check_alert_service_health()
        
        assert result is True
    
    @patch('utils.health_monitor.AlertService')
    def test_check_alert_service_health_no_channels(self, mock_alert_service_class):
        """Test alert service health check with no channels."""
        mock_alert_service = Mock()
        mock_alert_service.channels = []
        mock_alert_service_class.return_value = mock_alert_service
        
        result = self.health_monitor._check_alert_service_health()
        
        assert result is False
    
    def test_check_metrics_service_health_success(self):
        """Test metrics service health check success."""
        self.mock_metrics_service.backends = ['mock_backend']
        self.mock_metrics_service._update_metric_history.return_value = None
        
        result = self.health_monitor._check_metrics_service_health()
        
        assert result is True
        self.mock_metrics_service._update_metric_history.assert_called_once()
    
    def test_check_metrics_service_health_no_backends(self):
        """Test metrics service health check with no backends."""
        self.mock_metrics_service.backends = []
        
        result = self.health_monitor._check_metrics_service_health()
        
        assert result is False
    
    @patch('requests.get')
    def test_check_sec_edgar_health_success(self, mock_get):
        """Test SEC EDGAR health check success."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        result = self.health_monitor._check_sec_edgar_health()
        
        assert result is True
        mock_get.assert_called_once()
    
    @patch('requests.get')
    def test_check_sec_edgar_health_failure(self, mock_get):
        """Test SEC EDGAR health check failure."""
        mock_get.side_effect = Exception("Connection failed")
        
        result = self.health_monitor._check_sec_edgar_health()
        
        assert result is False
    
    @patch('yfinance.Ticker')
    def test_check_yahoo_finance_health_success(self, mock_ticker_class):
        """Test Yahoo Finance health check success."""
        mock_ticker = Mock()
        mock_ticker.info = {'symbol': 'AAPL', 'shortName': 'Apple Inc.'}
        mock_ticker_class.return_value = mock_ticker
        
        result = self.health_monitor._check_yahoo_finance_health()
        
        assert result is True
    
    @patch('yfinance.Ticker')
    def test_check_yahoo_finance_health_failure(self, mock_ticker_class):
        """Test Yahoo Finance health check failure."""
        mock_ticker_class.side_effect = Exception("API error")
        
        result = self.health_monitor._check_yahoo_finance_health()
        
        assert result is False
    
    def test_get_health_check_names(self):
        """Test getting health check names."""
        names = self.health_monitor.get_health_check_names()
        
        assert isinstance(names, list)
        assert len(names) > 0
        assert 'database' in names
        assert 'alert_service' in names
    
    def test_remove_health_check(self):
        """Test removing a health check."""
        def dummy_check():
            return True
        
        self.health_monitor.register_health_check('temp_check', dummy_check)
        assert 'temp_check' in self.health_monitor.health_checks
        
        result = self.health_monitor.remove_health_check('temp_check')
        
        assert result is True
        assert 'temp_check' not in self.health_monitor.health_checks
    
    def test_remove_nonexistent_health_check(self):
        """Test removing a non-existent health check."""
        result = self.health_monitor.remove_health_check('nonexistent')
        
        assert result is False
    
    def test_clear_health_check_results(self):
        """Test clearing health check results."""
        # Add some mock results
        self.health_monitor.last_check_results = {
            'test1': {'healthy': True},
            'test2': {'healthy': False}
        }
        
        self.health_monitor.clear_health_check_results()
        
        assert len(self.health_monitor.last_check_results) == 0
    
    def test_run_periodic_health_checks_setup(self):
        """Test periodic health checks setup (without actually running async)."""
        # Just test that the method exists and can be called
        assert hasattr(self.health_monitor, 'run_periodic_health_checks')
        assert callable(self.health_monitor.run_periodic_health_checks)


@pytest.fixture
def health_monitor():
    """Health monitor fixture for testing."""
    mock_metrics_service = Mock(spec=MetricsService)
    return HealthMonitor(metrics_service=mock_metrics_service)


@pytest.fixture
def sample_health_check():
    """Sample health check for testing."""
    def sample_check():
        return True
    
    return HealthCheck(
        name='sample_check',
        check_function=sample_check,
        timeout_seconds=10,
        critical=True,
        metadata={'type': 'test'}
    )