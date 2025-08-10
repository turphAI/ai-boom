"""
Configuration loader with environment-based switching and secrets integration.
"""

import os
import json
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path
import logging

from .secrets import SecretManager

logger = logging.getLogger(__name__)


@dataclass
class AlertThresholds:
    """Alert threshold configuration."""
    bond_issuance: float = 5_000_000_000  # $5B
    bdc_discount: float = 0.05  # 5%
    credit_fund: float = 0.10  # 10%
    bank_provision: float = 0.20  # 20%
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary."""
        return {
            'bond_issuance': self.bond_issuance,
            'bdc_discount': self.bdc_discount,
            'credit_fund': self.credit_fund,
            'bank_provision': self.bank_provision
        }


@dataclass
class DatabaseConfig:
    """Database configuration."""
    provider: str = 'dynamodb'  # 'dynamodb' or 'firestore'
    connection_string: Optional[str] = None
    table_name: str = 'boom_bust_metrics'
    region: str = 'us-east-1'
    ttl_days: int = 730  # 2 years
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.provider not in ['dynamodb', 'firestore']:
            raise ValueError(f"Unsupported database provider: {self.provider}")


@dataclass
class NotificationConfig:
    """Notification configuration."""
    enabled_channels: list = field(default_factory=lambda: ['sns', 'telegram'])
    sns_topic_arn: Optional[str] = None
    telegram_bot_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    slack_webhook_url: Optional[str] = None
    max_retries: int = 3
    retry_delay: float = 1.0
    
    def __post_init__(self):
        """Validate notification configuration."""
        valid_channels = ['sns', 'telegram', 'slack']
        for channel in self.enabled_channels:
            if channel not in valid_channels:
                raise ValueError(f"Unsupported notification channel: {channel}")


@dataclass
class MonitoringConfig:
    """Monitoring and observability configuration."""
    provider: str = 'grafana'  # 'grafana' or 'datadog'
    grafana_url: Optional[str] = None
    grafana_token: Optional[str] = None
    datadog_api_key: Optional[str] = None
    metrics_enabled: bool = True
    health_check_interval: int = 300  # 5 minutes


@dataclass
class ScrapingConfig:
    """Data scraping configuration."""
    bdc_symbols: list = field(default_factory=lambda: ['ARCC', 'OCSL', 'MAIN', 'PSEC', 'BXSL', 'TCPC'])
    tech_company_ciks: Dict[str, str] = field(default_factory=lambda: {
        'MSFT': '0000789019',
        'META': '0001326801', 
        'AMZN': '0001018724',
        'GOOGL': '0001652044'
    })
    max_retries: int = 3
    timeout_seconds: int = 30
    rate_limit_delay: float = 1.0


class ConfigLoader:
    """Configuration loader with environment-based switching and secrets integration."""
    
    def __init__(self, environment: str = None, config_path: str = None):
        self.environment = environment or os.getenv('ENVIRONMENT', 'development')
        self.config_path = config_path or self._get_default_config_path()
        self.secret_manager = SecretManager()
        self._config_cache = {}
        
        logger.info(f"Initializing ConfigLoader for environment: {self.environment}")
    
    def _get_default_config_path(self) -> str:
        """Get the default configuration file path."""
        base_path = Path(__file__).parent
        return str(base_path / f"environments/{self.environment}.json")
    
    def _load_file_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        if not os.path.exists(self.config_path):
            logger.warning(f"Configuration file not found: {self.config_path}")
            return {}
        
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Error loading configuration file {self.config_path}: {str(e)}")
            return {}
    
    def _load_environment_config(self) -> Dict[str, Any]:
        """Load configuration from environment variables."""
        config = {}
        
        # Only add database config if environment variables are set
        database_config = {}
        if 'DATABASE_PROVIDER' in os.environ:
            database_config['provider'] = os.getenv('DATABASE_PROVIDER')
        if 'AWS_REGION' in os.environ:
            database_config['region'] = os.getenv('AWS_REGION')
        if 'DATABASE_TABLE_NAME' in os.environ:
            database_config['table_name'] = os.getenv('DATABASE_TABLE_NAME')
        if 'DATABASE_TTL_DAYS' in os.environ:
            database_config['ttl_days'] = int(os.getenv('DATABASE_TTL_DAYS'))
        if database_config:
            config['database'] = database_config
        
        # Only add alert thresholds if environment variables are set
        alert_thresholds = {}
        if 'BOND_ISSUANCE_THRESHOLD' in os.environ:
            alert_thresholds['bond_issuance'] = float(os.getenv('BOND_ISSUANCE_THRESHOLD'))
        if 'BDC_DISCOUNT_THRESHOLD' in os.environ:
            alert_thresholds['bdc_discount'] = float(os.getenv('BDC_DISCOUNT_THRESHOLD'))
        if 'CREDIT_FUND_THRESHOLD' in os.environ:
            alert_thresholds['credit_fund'] = float(os.getenv('CREDIT_FUND_THRESHOLD'))
        if 'BANK_PROVISION_THRESHOLD' in os.environ:
            alert_thresholds['bank_provision'] = float(os.getenv('BANK_PROVISION_THRESHOLD'))
        if alert_thresholds:
            config['alert_thresholds'] = alert_thresholds
        
        # Only add notification config if environment variables are set
        notifications = {}
        if 'NOTIFICATION_CHANNELS' in os.environ:
            notifications['enabled_channels'] = os.getenv('NOTIFICATION_CHANNELS').split(',')
        if 'ALERT_MAX_RETRIES' in os.environ:
            notifications['max_retries'] = int(os.getenv('ALERT_MAX_RETRIES'))
        if 'ALERT_RETRY_DELAY' in os.environ:
            notifications['retry_delay'] = float(os.getenv('ALERT_RETRY_DELAY'))
        if notifications:
            config['notifications'] = notifications
        
        # Only add monitoring config if environment variables are set
        monitoring = {}
        if 'MONITORING_PROVIDER' in os.environ:
            monitoring['provider'] = os.getenv('MONITORING_PROVIDER')
        if 'METRICS_ENABLED' in os.environ:
            monitoring['metrics_enabled'] = os.getenv('METRICS_ENABLED').lower() == 'true'
        if 'HEALTH_CHECK_INTERVAL' in os.environ:
            monitoring['health_check_interval'] = int(os.getenv('HEALTH_CHECK_INTERVAL'))
        if monitoring:
            config['monitoring'] = monitoring
        
        # Only add scraping config if environment variables are set
        scraping = {}
        if 'SCRAPING_MAX_RETRIES' in os.environ:
            scraping['max_retries'] = int(os.getenv('SCRAPING_MAX_RETRIES'))
        if 'SCRAPING_TIMEOUT' in os.environ:
            scraping['timeout_seconds'] = int(os.getenv('SCRAPING_TIMEOUT'))
        if 'SCRAPING_RATE_LIMIT' in os.environ:
            scraping['rate_limit_delay'] = float(os.getenv('SCRAPING_RATE_LIMIT'))
        if scraping:
            config['scraping'] = scraping
        
        return config
    
    def _merge_configs(self, *configs: Dict[str, Any]) -> Dict[str, Any]:
        """Merge multiple configuration dictionaries."""
        merged = {}
        for config in configs:
            for key, value in config.items():
                if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                    merged[key] = self._merge_configs(merged[key], value)
                else:
                    merged[key] = value
        return merged
    
    def _load_secrets_config(self) -> Dict[str, Any]:
        """Load configuration from secrets manager."""
        try:
            api_credentials = self.secret_manager.get_api_credentials()
            database_config = self.secret_manager.get_database_config()
            notification_config = self.secret_manager.get_notification_config()
            
            return {
                'api_credentials': api_credentials,
                'database': {
                    'connection_string': database_config.get('connection_string'),
                    'username': database_config.get('username'),
                    'password': database_config.get('password')
                },
                'notifications': {
                    'sns_topic_arn': notification_config.get('sns_topic_arn'),
                    'telegram_bot_token': notification_config.get('telegram_bot_token'),
                    'telegram_chat_id': notification_config.get('telegram_chat_id'),
                    'slack_webhook_url': notification_config.get('slack_webhook_url')
                },
                'monitoring': {
                    'grafana_token': api_credentials.get('grafana_token'),
                    'datadog_api_key': api_credentials.get('datadog_api_key')
                }
            }
        except Exception as e:
            logger.error(f"Error loading secrets configuration: {str(e)}")
            return {}
    
    def load_config(self, use_cache: bool = True) -> Dict[str, Any]:
        """Load complete configuration from all sources."""
        if use_cache and 'full_config' in self._config_cache:
            return self._config_cache['full_config']
        
        # Load from different sources in order of precedence
        file_config = self._load_file_config()
        env_config = self._load_environment_config()
        secrets_config = self._load_secrets_config()
        
        # Merge configurations (later sources override earlier ones)
        full_config = self._merge_configs(file_config, env_config, secrets_config)
        
        if use_cache:
            self._config_cache['full_config'] = full_config
        
        return full_config
    
    def get_alert_thresholds(self) -> AlertThresholds:
        """Get alert threshold configuration."""
        config = self.load_config()
        thresholds_config = config.get('alert_thresholds', {})
        
        return AlertThresholds(
            bond_issuance=thresholds_config.get('bond_issuance', 5_000_000_000),
            bdc_discount=thresholds_config.get('bdc_discount', 0.05),
            credit_fund=thresholds_config.get('credit_fund', 0.10),
            bank_provision=thresholds_config.get('bank_provision', 0.20)
        )
    
    def get_database_config(self) -> DatabaseConfig:
        """Get database configuration."""
        config = self.load_config()
        db_config = config.get('database', {})
        
        return DatabaseConfig(
            provider=db_config.get('provider', 'dynamodb'),
            connection_string=db_config.get('connection_string'),
            table_name=db_config.get('table_name', 'boom_bust_metrics'),
            region=db_config.get('region', 'us-east-1'),
            ttl_days=db_config.get('ttl_days', 730)
        )
    
    def get_notification_config(self) -> NotificationConfig:
        """Get notification configuration."""
        config = self.load_config()
        notif_config = config.get('notifications', {})
        
        return NotificationConfig(
            enabled_channels=notif_config.get('enabled_channels', ['sns', 'telegram']),
            sns_topic_arn=notif_config.get('sns_topic_arn'),
            telegram_bot_token=notif_config.get('telegram_bot_token'),
            telegram_chat_id=notif_config.get('telegram_chat_id'),
            slack_webhook_url=notif_config.get('slack_webhook_url'),
            max_retries=notif_config.get('max_retries', 3),
            retry_delay=notif_config.get('retry_delay', 1.0)
        )
    
    def get_monitoring_config(self) -> MonitoringConfig:
        """Get monitoring configuration."""
        config = self.load_config()
        monitor_config = config.get('monitoring', {})
        
        return MonitoringConfig(
            provider=monitor_config.get('provider', 'grafana'),
            grafana_url=monitor_config.get('grafana_url'),
            grafana_token=monitor_config.get('grafana_token'),
            datadog_api_key=monitor_config.get('datadog_api_key'),
            metrics_enabled=monitor_config.get('metrics_enabled', True),
            health_check_interval=monitor_config.get('health_check_interval', 300)
        )
    
    def get_scraping_config(self) -> ScrapingConfig:
        """Get scraping configuration."""
        config = self.load_config()
        scraping_config = config.get('scraping', {})
        
        return ScrapingConfig(
            bdc_symbols=scraping_config.get('bdc_symbols', ['ARCC', 'OCSL', 'MAIN', 'PSEC', 'BXSL', 'TCPC']),
            tech_company_ciks=scraping_config.get('tech_company_ciks', {
                'MSFT': '0000789019',
                'META': '0001326801', 
                'AMZN': '0001018724',
                'GOOGL': '0001652044'
            }),
            max_retries=scraping_config.get('max_retries', 3),
            timeout_seconds=scraping_config.get('timeout_seconds', 30),
            rate_limit_delay=scraping_config.get('rate_limit_delay', 1.0)
        )
    
    def get_api_credential(self, key: str) -> Optional[str]:
        """Get a specific API credential."""
        config = self.load_config()
        api_credentials = config.get('api_credentials', {})
        return api_credentials.get(key)
    
    def reload_config(self):
        """Clear cache and reload configuration."""
        self._config_cache.clear()
        logger.info("Configuration cache cleared and reloaded")


# Global configuration loader instance
config_loader = ConfigLoader()