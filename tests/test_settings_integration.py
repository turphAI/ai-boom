"""
Tests for settings integration with secrets management and configuration loading.
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock

from config.settings import Settings
from config.config_loader import AlertThresholds, DatabaseConfig, NotificationConfig


class TestSettingsIntegration:
    """Test Settings class integration with configuration system."""
    
    @patch('config.settings.config_loader')
    def test_settings_initialization(self, mock_config_loader):
        """Test settings initialization with configuration loader."""
        # Setup mock configurations
        mock_config_loader.get_alert_thresholds.return_value = AlertThresholds(
            bond_issuance=3000000000,
            bdc_discount=0.04
        )
        mock_config_loader.get_database_config.return_value = DatabaseConfig(
            provider='firestore',
            table_name='test_table',
            region='eu-west-1'
        )
        mock_config_loader.get_notification_config.return_value = NotificationConfig(
            telegram_bot_token='test_token',
            sns_topic_arn='test_arn'
        )
        mock_config_loader.get_monitoring_config.return_value = Mock(
            grafana_api_key='test_grafana_key',
            grafana_url='https://grafana.test.com'
        )
        mock_config_loader.get_scraping_config.return_value = Mock(
            bdc_symbols=['ARCC', 'OCSL'],
            tech_company_ciks={'MSFT': '0000789019'},
            max_retries=2,
            timeout_seconds=15
        )
        
        with patch.dict(os.environ, {'ENVIRONMENT': 'testing'}):
            settings = Settings()
            
            # Test environment
            assert settings.ENVIRONMENT == 'testing'
            
            # Test alert thresholds
            assert settings.BOND_ISSUANCE_THRESHOLD == 3000000000
            assert settings.BDC_DISCOUNT_THRESHOLD == 0.04
            
            # Test database config
            assert settings.DATABASE_PROVIDER == 'firestore'
            assert settings.DATABASE_TABLE_NAME == 'test_table'
            assert settings.DATABASE_REGION == 'eu-west-1'
            
            # Test notification config
            assert settings.TELEGRAM_BOT_TOKEN == 'test_token'
            assert settings.SNS_TOPIC_ARN == 'test_arn'
            
            # Test monitoring config
            assert settings.GRAFANA_API_KEY == 'test_grafana_key'
            assert settings.GRAFANA_URL == 'https://grafana.test.com'
            
            # Test scraping config
            assert settings.BDC_SYMBOLS == ['ARCC', 'OCSL']
            assert settings.TECH_COMPANY_CIKS == {'MSFT': '0000789019'}
            assert settings.SCRAPING_MAX_RETRIES == 2
            assert settings.SCRAPING_TIMEOUT == 15
    
    @patch('config.settings.config_loader')
    def test_settings_properties_with_none_values(self, mock_config_loader):
        """Test settings properties when configuration returns None values."""
        # Setup mock configurations with None values
        mock_config_loader.get_alert_thresholds.return_value = AlertThresholds()
        mock_config_loader.get_database_config.return_value = DatabaseConfig()
        mock_config_loader.get_notification_config.return_value = NotificationConfig(
            telegram_bot_token=None,
            sns_topic_arn=None,
            slack_webhook_url=None
        )
        mock_config_loader.get_monitoring_config.return_value = Mock(
            grafana_api_key=None,
            grafana_url=None,
            datadog_api_key=None
        )
        mock_config_loader.get_scraping_config.return_value = Mock(
            bdc_symbols=['ARCC'],
            tech_company_ciks={'MSFT': '0000789019'},
            max_retries=3,
            timeout_seconds=30
        )
        
        settings = Settings()
        
        # Test that None values are converted to empty strings
        assert settings.TELEGRAM_BOT_TOKEN == ''
        assert settings.SNS_TOPIC_ARN == ''
        assert settings.SLACK_WEBHOOK_URL == ''
        assert settings.GRAFANA_API_KEY == ''
        assert settings.GRAFANA_URL == ''
        assert settings.DATADOG_API_KEY == ''
    
    @patch('config.settings.config_loader')
    def test_get_alert_thresholds_method(self, mock_config_loader):
        """Test get_alert_thresholds method."""
        mock_thresholds = AlertThresholds(
            bond_issuance=4000000000,
            bdc_discount=0.06,
            credit_fund=0.12,
            bank_provision=0.25
        )
        mock_config_loader.get_alert_thresholds.return_value = mock_thresholds
        mock_config_loader.get_database_config.return_value = DatabaseConfig()
        mock_config_loader.get_notification_config.return_value = NotificationConfig()
        mock_config_loader.get_monitoring_config.return_value = Mock()
        mock_config_loader.get_scraping_config.return_value = Mock()
        
        settings = Settings()
        result = settings.get_alert_thresholds()
        
        expected = {
            'bond_issuance': 4000000000,
            'bdc_discount': 0.06,
            'credit_fund': 0.12,
            'bank_provision': 0.25
        }
        
        assert result == expected
    
    @patch('config.settings.config_loader')
    def test_get_api_credential_method(self, mock_config_loader):
        """Test get_api_credential method."""
        mock_config_loader.get_alert_thresholds.return_value = AlertThresholds()
        mock_config_loader.get_database_config.return_value = DatabaseConfig()
        mock_config_loader.get_notification_config.return_value = NotificationConfig()
        mock_config_loader.get_monitoring_config.return_value = Mock()
        mock_config_loader.get_scraping_config.return_value = Mock()
        mock_config_loader.get_api_credential.return_value = 'test_api_key'
        
        settings = Settings()
        result = settings.get_api_credential('some_api_key')
        
        assert result == 'test_api_key'
        mock_config_loader.get_api_credential.assert_called_once_with('some_api_key')
    
    @patch('config.settings.config_loader')
    def test_get_api_credential_method_none_result(self, mock_config_loader):
        """Test get_api_credential method when result is None."""
        mock_config_loader.get_alert_thresholds.return_value = AlertThresholds()
        mock_config_loader.get_database_config.return_value = DatabaseConfig()
        mock_config_loader.get_notification_config.return_value = NotificationConfig()
        mock_config_loader.get_monitoring_config.return_value = Mock()
        mock_config_loader.get_scraping_config.return_value = Mock()
        mock_config_loader.get_api_credential.return_value = None
        
        settings = Settings()
        result = settings.get_api_credential('nonexistent_key')
        
        assert result == ''
    
    @patch('config.settings.config_loader')
    def test_reload_config_method(self, mock_config_loader):
        """Test reload_config method."""
        # Setup initial mock configurations
        initial_thresholds = AlertThresholds(bond_issuance=1000000000)
        updated_thresholds = AlertThresholds(bond_issuance=2000000000)
        
        mock_config_loader.get_alert_thresholds.side_effect = [
            initial_thresholds,  # Initial load
            updated_thresholds   # After reload
        ]
        mock_config_loader.get_database_config.return_value = DatabaseConfig()
        mock_config_loader.get_notification_config.return_value = NotificationConfig()
        mock_config_loader.get_monitoring_config.return_value = Mock()
        mock_config_loader.get_scraping_config.return_value = Mock()
        
        settings = Settings()
        
        # Check initial value
        assert settings.BOND_ISSUANCE_THRESHOLD == 1000000000
        
        # Reload configuration
        settings.reload_config()
        
        # Check updated value
        assert settings.BOND_ISSUANCE_THRESHOLD == 2000000000
        
        # Verify reload was called
        mock_config_loader.reload_config.assert_called_once()
    
    @patch('config.settings.config_loader')
    def test_reload_config_method_error(self, mock_config_loader):
        """Test reload_config method with error."""
        mock_config_loader.get_alert_thresholds.return_value = AlertThresholds()
        mock_config_loader.get_database_config.return_value = DatabaseConfig()
        mock_config_loader.get_notification_config.return_value = NotificationConfig()
        mock_config_loader.get_monitoring_config.return_value = Mock()
        mock_config_loader.get_scraping_config.return_value = Mock()
        mock_config_loader.reload_config.side_effect = Exception("Reload error")
        
        settings = Settings()
        
        with pytest.raises(Exception, match="Reload error"):
            settings.reload_config()
    
    @patch('config.settings.config_loader')
    def test_aws_environment_variables(self, mock_config_loader):
        """Test AWS environment variable access."""
        mock_config_loader.get_alert_thresholds.return_value = AlertThresholds()
        mock_config_loader.get_database_config.return_value = DatabaseConfig()
        mock_config_loader.get_notification_config.return_value = NotificationConfig()
        mock_config_loader.get_monitoring_config.return_value = Mock()
        mock_config_loader.get_scraping_config.return_value = Mock()
        
        env_vars = {
            'AWS_ACCESS_KEY_ID': 'test_access_key',
            'AWS_SECRET_ACCESS_KEY': 'test_secret_key'
        }
        
        with patch.dict(os.environ, env_vars):
            settings = Settings()
            
            assert settings.AWS_ACCESS_KEY_ID == 'test_access_key'
            assert settings.AWS_SECRET_ACCESS_KEY == 'test_secret_key'
    
    @patch('config.settings.config_loader')
    def test_dashboard_alert_limit_environment_variable(self, mock_config_loader):
        """Test dashboard alert limit from environment variable."""
        mock_config_loader.get_alert_thresholds.return_value = AlertThresholds()
        mock_config_loader.get_database_config.return_value = DatabaseConfig()
        mock_config_loader.get_notification_config.return_value = NotificationConfig()
        mock_config_loader.get_monitoring_config.return_value = Mock()
        mock_config_loader.get_scraping_config.return_value = Mock()
        
        with patch.dict(os.environ, {'DASHBOARD_ALERT_LIMIT': '250'}):
            settings = Settings()
            
            assert settings.DASHBOARD_ALERT_LIMIT == 250
    
    @patch('config.settings.config_loader')
    def test_backward_compatibility_properties(self, mock_config_loader):
        """Test backward compatibility with existing property names."""
        mock_config_loader.get_alert_thresholds.return_value = AlertThresholds()
        mock_config_loader.get_database_config.return_value = DatabaseConfig(
            region='eu-central-1'
        )
        mock_config_loader.get_notification_config.return_value = NotificationConfig()
        mock_config_loader.get_monitoring_config.return_value = Mock()
        mock_config_loader.get_scraping_config.return_value = Mock()
        
        settings = Settings()
        
        # Test that AWS_REGION maps to database region for backward compatibility
        assert settings.AWS_REGION == 'eu-central-1'
        assert settings.DATABASE_REGION == 'eu-central-1'


class TestSettingsGlobalInstance:
    """Test the global settings instance."""
    
    @patch('config.settings.config_loader')
    def test_global_settings_instance(self, mock_config_loader):
        """Test that global settings instance is properly initialized."""
        from config.settings import settings
        
        # Setup minimal mock configuration
        mock_config_loader.get_alert_thresholds.return_value = AlertThresholds()
        mock_config_loader.get_database_config.return_value = DatabaseConfig()
        mock_config_loader.get_notification_config.return_value = NotificationConfig()
        mock_config_loader.get_monitoring_config.return_value = Mock()
        mock_config_loader.get_scraping_config.return_value = Mock()
        
        # Test that settings is an instance of Settings
        assert isinstance(settings, Settings)
        
        # Test that we can access properties
        assert hasattr(settings, 'ENVIRONMENT')
        assert hasattr(settings, 'BOND_ISSUANCE_THRESHOLD')
        assert hasattr(settings, 'DATABASE_PROVIDER')


@pytest.fixture
def mock_full_config():
    """Fixture providing a complete mock configuration."""
    return {
        'alert_thresholds': AlertThresholds(
            bond_issuance=5000000000,
            bdc_discount=0.05,
            credit_fund=0.10,
            bank_provision=0.20
        ),
        'database_config': DatabaseConfig(
            provider='dynamodb',
            table_name='boom_bust_metrics',
            region='us-east-1',
            ttl_days=730
        ),
        'notification_config': NotificationConfig(
            enabled_channels=['sns', 'telegram'],
            telegram_bot_token='mock_token',
            sns_topic_arn='mock_arn',
            max_retries=3,
            retry_delay=1.0
        ),
        'monitoring_config': Mock(
            provider='grafana',
            grafana_api_key='mock_grafana_key',
            grafana_url='https://grafana.mock.com',
            metrics_enabled=True
        ),
        'scraping_config': Mock(
            bdc_symbols=['ARCC', 'OCSL', 'MAIN'],
            tech_company_ciks={'MSFT': '0000789019', 'META': '0001326801'},
            max_retries=3,
            timeout_seconds=30,
            rate_limit_delay=1.0
        )
    }


class TestSettingsWithFullConfiguration:
    """Test Settings with complete configuration."""
    
    @patch('config.settings.config_loader')
    def test_settings_with_full_configuration(self, mock_config_loader, mock_full_config):
        """Test Settings with complete configuration setup."""
        # Setup mock config loader
        mock_config_loader.get_alert_thresholds.return_value = mock_full_config['alert_thresholds']
        mock_config_loader.get_database_config.return_value = mock_full_config['database_config']
        mock_config_loader.get_notification_config.return_value = mock_full_config['notification_config']
        mock_config_loader.get_monitoring_config.return_value = mock_full_config['monitoring_config']
        mock_config_loader.get_scraping_config.return_value = mock_full_config['scraping_config']
        mock_config_loader.get_api_credential.return_value = 'mock_api_key'
        
        settings = Settings()
        
        # Test all major configuration categories
        assert settings.BOND_ISSUANCE_THRESHOLD == 5000000000
        assert settings.DATABASE_PROVIDER == 'dynamodb'
        assert settings.TELEGRAM_BOT_TOKEN == 'mock_token'
        assert settings.GRAFANA_API_KEY == 'mock_grafana_key'
        assert settings.BDC_SYMBOLS == ['ARCC', 'OCSL', 'MAIN']
        
        # Test method calls
        thresholds = settings.get_alert_thresholds()
        assert thresholds['bond_issuance'] == 5000000000
        
        api_key = settings.get_api_credential('test_key')
        assert api_key == 'mock_api_key'