"""
Tests for configuration loader functionality.
"""

import pytest
import json
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from config.config_loader import (
    ConfigLoader,
    AlertThresholds,
    DatabaseConfig,
    NotificationConfig,
    MonitoringConfig,
    ScrapingConfig
)


class TestAlertThresholds:
    """Test AlertThresholds dataclass."""
    
    def test_default_values(self):
        """Test default threshold values."""
        thresholds = AlertThresholds()
        
        assert thresholds.bond_issuance == 5_000_000_000
        assert thresholds.bdc_discount == 0.05
        assert thresholds.credit_fund == 0.10
        assert thresholds.bank_provision == 0.20
    
    def test_custom_values(self):
        """Test custom threshold values."""
        thresholds = AlertThresholds(
            bond_issuance=1_000_000_000,
            bdc_discount=0.03,
            credit_fund=0.08,
            bank_provision=0.15
        )
        
        assert thresholds.bond_issuance == 1_000_000_000
        assert thresholds.bdc_discount == 0.03
        assert thresholds.credit_fund == 0.08
        assert thresholds.bank_provision == 0.15
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        thresholds = AlertThresholds(
            bond_issuance=2_000_000_000,
            bdc_discount=0.04
        )
        
        result = thresholds.to_dict()
        expected = {
            'bond_issuance': 2_000_000_000,
            'bdc_discount': 0.04,
            'credit_fund': 0.10,
            'bank_provision': 0.20
        }
        
        assert result == expected


class TestDatabaseConfig:
    """Test DatabaseConfig dataclass."""
    
    def test_default_values(self):
        """Test default database configuration."""
        config = DatabaseConfig()
        
        assert config.provider == 'dynamodb'
        assert config.connection_string is None
        assert config.table_name == 'boom_bust_metrics'
        assert config.region == 'us-east-1'
        assert config.ttl_days == 730
    
    def test_custom_values(self):
        """Test custom database configuration."""
        config = DatabaseConfig(
            provider='firestore',
            connection_string='test://connection',
            table_name='custom_table',
            region='eu-west-1',
            ttl_days=365
        )
        
        assert config.provider == 'firestore'
        assert config.connection_string == 'test://connection'
        assert config.table_name == 'custom_table'
        assert config.region == 'eu-west-1'
        assert config.ttl_days == 365
    
    def test_invalid_provider(self):
        """Test validation of invalid provider."""
        with pytest.raises(ValueError, match="Unsupported database provider: invalid"):
            DatabaseConfig(provider='invalid')


class TestNotificationConfig:
    """Test NotificationConfig dataclass."""
    
    def test_default_values(self):
        """Test default notification configuration."""
        config = NotificationConfig()
        
        assert config.enabled_channels == ['sns', 'telegram']
        assert config.sns_topic_arn is None
        assert config.telegram_bot_token is None
        assert config.telegram_chat_id is None
        assert config.slack_webhook_url is None
        assert config.max_retries == 3
        assert config.retry_delay == 1.0
    
    def test_custom_values(self):
        """Test custom notification configuration."""
        config = NotificationConfig(
            enabled_channels=['slack', 'telegram'],
            sns_topic_arn='arn:aws:sns:us-east-1:123456789012:test',
            telegram_bot_token='test_token',
            telegram_chat_id='test_chat',
            slack_webhook_url='https://hooks.slack.com/test',
            max_retries=5,
            retry_delay=2.0
        )
        
        assert config.enabled_channels == ['slack', 'telegram']
        assert config.sns_topic_arn == 'arn:aws:sns:us-east-1:123456789012:test'
        assert config.telegram_bot_token == 'test_token'
        assert config.telegram_chat_id == 'test_chat'
        assert config.slack_webhook_url == 'https://hooks.slack.com/test'
        assert config.max_retries == 5
        assert config.retry_delay == 2.0
    
    def test_invalid_channel(self):
        """Test validation of invalid notification channel."""
        with pytest.raises(ValueError, match="Unsupported notification channel: invalid"):
            NotificationConfig(enabled_channels=['invalid'])


class TestConfigLoader:
    """Test ConfigLoader class."""
    
    @patch('config.config_loader.SecretManager')
    def test_init_default_environment(self, mock_secret_manager):
        """Test initialization with default environment."""
        with patch.dict(os.environ, {}, clear=True):
            loader = ConfigLoader()
            
            assert loader.environment == 'development'
            assert 'development.json' in loader.config_path
    
    @patch('config.config_loader.SecretManager')
    def test_init_custom_environment(self, mock_secret_manager):
        """Test initialization with custom environment."""
        with patch.dict(os.environ, {'ENVIRONMENT': 'production'}):
            loader = ConfigLoader()
            
            assert loader.environment == 'production'
            assert 'production.json' in loader.config_path
    
    @patch('config.config_loader.SecretManager')
    def test_init_custom_config_path(self, mock_secret_manager):
        """Test initialization with custom config path."""
        custom_path = '/custom/path/config.json'
        loader = ConfigLoader(config_path=custom_path)
        
        assert loader.config_path == custom_path
    
    @patch('config.config_loader.SecretManager')
    def test_load_file_config_success(self, mock_secret_manager):
        """Test successful file configuration loading."""
        config_data = {
            'database': {'provider': 'firestore'},
            'alert_thresholds': {'bond_issuance': 1000000000}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name
        
        try:
            loader = ConfigLoader(config_path=temp_path)
            result = loader._load_file_config()
            
            assert result == config_data
        finally:
            os.unlink(temp_path)
    
    @patch('config.config_loader.SecretManager')
    def test_load_file_config_not_found(self, mock_secret_manager):
        """Test file configuration loading when file doesn't exist."""
        loader = ConfigLoader(config_path='/nonexistent/path.json')
        result = loader._load_file_config()
        
        assert result == {}
    
    @patch('config.config_loader.SecretManager')
    def test_load_file_config_invalid_json(self, mock_secret_manager):
        """Test file configuration loading with invalid JSON."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('invalid json content')
            temp_path = f.name
        
        try:
            loader = ConfigLoader(config_path=temp_path)
            result = loader._load_file_config()
            
            assert result == {}
        finally:
            os.unlink(temp_path)
    
    @patch('config.config_loader.SecretManager')
    def test_load_environment_config(self, mock_secret_manager):
        """Test environment configuration loading."""
        env_vars = {
            'DATABASE_PROVIDER': 'firestore',
            'AWS_REGION': 'eu-west-1',
            'BOND_ISSUANCE_THRESHOLD': '2000000000',
            'BDC_DISCOUNT_THRESHOLD': '0.03',
            'NOTIFICATION_CHANNELS': 'slack,telegram',
            'ALERT_MAX_RETRIES': '5',
            'MONITORING_PROVIDER': 'datadog',
            'METRICS_ENABLED': 'false',
            'SCRAPING_MAX_RETRIES': '2'
        }
        
        with patch.dict(os.environ, env_vars):
            loader = ConfigLoader()
            result = loader._load_environment_config()
            
            assert result['database']['provider'] == 'firestore'
            assert result['database']['region'] == 'eu-west-1'
            assert result['alert_thresholds']['bond_issuance'] == 2000000000
            assert result['alert_thresholds']['bdc_discount'] == 0.03
            assert result['notifications']['enabled_channels'] == ['slack', 'telegram']
            assert result['notifications']['max_retries'] == 5
            assert result['monitoring']['provider'] == 'datadog'
            assert result['monitoring']['metrics_enabled'] is False
            assert result['scraping']['max_retries'] == 2
    
    @patch('config.config_loader.SecretManager')
    def test_merge_configs(self, mock_secret_manager):
        """Test configuration merging."""
        loader = ConfigLoader()
        
        config1 = {
            'database': {'provider': 'dynamodb', 'region': 'us-east-1'},
            'alerts': {'enabled': True}
        }
        
        config2 = {
            'database': {'region': 'eu-west-1', 'table_name': 'custom'},
            'monitoring': {'provider': 'grafana'}
        }
        
        result = loader._merge_configs(config1, config2)
        
        expected = {
            'database': {
                'provider': 'dynamodb',
                'region': 'eu-west-1',
                'table_name': 'custom'
            },
            'alerts': {'enabled': True},
            'monitoring': {'provider': 'grafana'}
        }
        
        assert result == expected
    
    @patch('config.config_loader.SecretManager')
    def test_load_secrets_config_success(self, mock_secret_manager_class):
        """Test successful secrets configuration loading."""
        mock_manager = Mock()
        mock_manager.get_api_credentials.return_value = {'grafana_api_key': 'test_key'}
        mock_manager.get_database_config.return_value = {'connection_string': 'test://db'}
        mock_manager.get_notification_config.return_value = {'sns_topic_arn': 'test_arn'}
        mock_secret_manager_class.return_value = mock_manager
        
        loader = ConfigLoader()
        result = loader._load_secrets_config()
        
        assert result['api_credentials']['grafana_api_key'] == 'test_key'
        assert result['database']['connection_string'] == 'test://db'
        assert result['notifications']['sns_topic_arn'] == 'test_arn'
        assert result['monitoring']['grafana_api_key'] == 'test_key'
    
    @patch('config.config_loader.SecretManager')
    def test_load_secrets_config_error(self, mock_secret_manager_class):
        """Test secrets configuration loading with error."""
        mock_manager = Mock()
        mock_manager.get_api_credentials.side_effect = Exception("Secrets error")
        mock_secret_manager_class.return_value = mock_manager
        
        loader = ConfigLoader()
        result = loader._load_secrets_config()
        
        assert result == {}
    
    @patch('config.config_loader.SecretManager')
    def test_get_alert_thresholds(self, mock_secret_manager):
        """Test alert thresholds retrieval."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_data = {
                'alert_thresholds': {
                    'bond_issuance': 3000000000,
                    'bdc_discount': 0.04
                }
            }
            json.dump(config_data, f)
            temp_path = f.name
        
        try:
            loader = ConfigLoader(config_path=temp_path)
            thresholds = loader.get_alert_thresholds()
            
            assert thresholds.bond_issuance == 3000000000
            assert thresholds.bdc_discount == 0.04
            assert thresholds.credit_fund == 0.10  # default value
            assert thresholds.bank_provision == 0.20  # default value
        finally:
            os.unlink(temp_path)
    
    @patch('config.config_loader.SecretManager')
    def test_get_database_config(self, mock_secret_manager):
        """Test database configuration retrieval."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_data = {
                'database': {
                    'provider': 'firestore',
                    'table_name': 'custom_table',
                    'ttl_days': 365
                }
            }
            json.dump(config_data, f)
            temp_path = f.name
        
        try:
            loader = ConfigLoader(config_path=temp_path)
            db_config = loader.get_database_config()
            
            assert db_config.provider == 'firestore'
            assert db_config.table_name == 'custom_table'
            assert db_config.ttl_days == 365
            assert db_config.region == 'us-east-1'  # default value
        finally:
            os.unlink(temp_path)
    
    @patch('config.config_loader.SecretManager')
    def test_reload_config(self, mock_secret_manager):
        """Test configuration reloading."""
        loader = ConfigLoader()
        
        # Load config to populate cache
        loader.load_config()
        assert 'full_config' in loader._config_cache
        
        # Reload config
        loader.reload_config()
        assert loader._config_cache == {}
    
    @patch('config.config_loader.SecretManager')
    def test_config_caching(self, mock_secret_manager):
        """Test configuration caching behavior."""
        loader = ConfigLoader()
        
        # First load should populate cache
        config1 = loader.load_config(use_cache=True)
        assert 'full_config' in loader._config_cache
        
        # Second load should use cache
        config2 = loader.load_config(use_cache=True)
        assert config1 is config2  # Same object reference
        
        # Load without cache should return new object
        config3 = loader.load_config(use_cache=False)
        assert config1 is not config3  # Different object reference


class TestConfigLoaderIntegration:
    """Integration tests for ConfigLoader."""
    
    @patch('config.config_loader.SecretManager')
    def test_full_configuration_loading(self, mock_secret_manager_class):
        """Test complete configuration loading workflow."""
        # Setup mock secret manager
        mock_manager = Mock()
        mock_manager.get_api_credentials.return_value = {
            'telegram_bot_token': 'secret_token',
            'grafana_api_key': 'secret_grafana_key'
        }
        mock_manager.get_database_config.return_value = {
            'connection_string': 'secret://connection'
        }
        mock_manager.get_notification_config.return_value = {
            'sns_topic_arn': 'secret_arn',
            'telegram_chat_id': 'secret_chat_id'
        }
        mock_secret_manager_class.return_value = mock_manager
        
        # Create temporary config file
        config_data = {
            'database': {
                'provider': 'firestore',
                'table_name': 'test_table'
            },
            'alert_thresholds': {
                'bond_issuance': 2000000000
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name
        
        try:
            # Set environment variables
            env_vars = {
                'DATABASE_TTL_DAYS': '365',
                'BDC_DISCOUNT_THRESHOLD': '0.03'
            }
            
            with patch.dict(os.environ, env_vars):
                loader = ConfigLoader(config_path=temp_path)
                
                # Test alert thresholds
                thresholds = loader.get_alert_thresholds()
                assert thresholds.bond_issuance == 2000000000  # from file
                assert thresholds.bdc_discount == 0.03  # from env
                
                # Test database config
                db_config = loader.get_database_config()
                assert db_config.provider == 'firestore'  # from file
                assert db_config.table_name == 'test_table'  # from file
                assert db_config.ttl_days == 365  # from env
                assert db_config.connection_string == 'secret://connection'  # from secrets
                
                # Test notification config
                notif_config = loader.get_notification_config()
                assert notif_config.telegram_bot_token == 'secret_token'  # from secrets
                assert notif_config.telegram_chat_id == 'secret_chat_id'  # from secrets
                assert notif_config.sns_topic_arn == 'secret_arn'  # from secrets
                
                # Test API credential retrieval
                grafana_key = loader.get_api_credential('grafana_api_key')
                assert grafana_key == 'secret_grafana_key'
                
        finally:
            os.unlink(temp_path)