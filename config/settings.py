"""
Configuration settings for the Boom-Bust Sentinel system.
Enhanced with secrets management and environment-based configuration.
"""

import os
from typing import Dict, Any
import logging

from .config_loader import config_loader

logger = logging.getLogger(__name__)


class Settings:
    """Application settings and configuration with secrets integration."""
    
    def __init__(self):
        """Initialize settings with configuration loader."""
        self._config_loader = config_loader
        self._environment = os.getenv('ENVIRONMENT', 'development')
        
        # Load configurations
        self._alert_thresholds = self._config_loader.get_alert_thresholds()
        self._database_config = self._config_loader.get_database_config()
        self._notification_config = self._config_loader.get_notification_config()
        self._monitoring_config = self._config_loader.get_monitoring_config()
        self._scraping_config = self._config_loader.get_scraping_config()
    
    @property
    def ENVIRONMENT(self) -> str:
        """Get current environment."""
        return self._environment
    
    # Database settings
    @property
    def DATABASE_PROVIDER(self) -> str:
        """Get database provider."""
        return self._database_config.provider
    
    @property
    def DATABASE_TABLE_NAME(self) -> str:
        """Get database table name."""
        return self._database_config.table_name
    
    @property
    def DATABASE_REGION(self) -> str:
        """Get database region."""
        return self._database_config.region
    
    @property
    def DATABASE_TTL_DAYS(self) -> int:
        """Get database TTL in days."""
        return self._database_config.ttl_days
    
    # AWS settings (backward compatibility)
    @property
    def AWS_REGION(self) -> str:
        """Get AWS region."""
        return self._database_config.region
    
    @property
    def AWS_ACCESS_KEY_ID(self) -> str:
        """Get AWS access key ID from environment."""
        return os.getenv('AWS_ACCESS_KEY_ID', '')
    
    @property
    def AWS_SECRET_ACCESS_KEY(self) -> str:
        """Get AWS secret access key from environment."""
        return os.getenv('AWS_SECRET_ACCESS_KEY', '')
    
    # Alert thresholds
    @property
    def BOND_ISSUANCE_THRESHOLD(self) -> float:
        """Get bond issuance threshold."""
        return self._alert_thresholds.bond_issuance
    
    @property
    def BDC_DISCOUNT_THRESHOLD(self) -> float:
        """Get BDC discount threshold."""
        return self._alert_thresholds.bdc_discount
    
    @property
    def CREDIT_FUND_THRESHOLD(self) -> float:
        """Get credit fund threshold."""
        return self._alert_thresholds.credit_fund
    
    @property
    def BANK_PROVISION_THRESHOLD(self) -> float:
        """Get bank provision threshold."""
        return self._alert_thresholds.bank_provision
    
    # Notification settings
    @property
    def TELEGRAM_BOT_TOKEN(self) -> str:
        """Get Telegram bot token."""
        return self._notification_config.telegram_bot_token or ''
    
    @property
    def TELEGRAM_CHAT_ID(self) -> str:
        """Get Telegram chat ID."""
        return self._notification_config.telegram_chat_id or ''
    
    @property
    def SNS_TOPIC_ARN(self) -> str:
        """Get SNS topic ARN."""
        return self._notification_config.sns_topic_arn or ''
    
    @property
    def SLACK_WEBHOOK_URL(self) -> str:
        """Get Slack webhook URL."""
        return self._notification_config.slack_webhook_url or ''
    
    # Alert retry settings
    @property
    def ALERT_MAX_RETRIES(self) -> int:
        """Get maximum alert retries."""
        return self._notification_config.max_retries
    
    @property
    def ALERT_RETRY_DELAY(self) -> float:
        """Get alert retry delay."""
        return self._notification_config.retry_delay
    
    # Dashboard settings
    @property
    def DASHBOARD_ALERT_LIMIT(self) -> int:
        """Get dashboard alert limit."""
        return int(os.getenv('DASHBOARD_ALERT_LIMIT', '100'))
    
    # Monitoring
    @property
    def GRAFANA_API_KEY(self) -> str:
        """Get Grafana API key."""
        return self._monitoring_config.grafana_api_key or ''
    
    @property
    def GRAFANA_URL(self) -> str:
        """Get Grafana URL."""
        return self._monitoring_config.grafana_url or ''
    
    @property
    def DATADOG_API_KEY(self) -> str:
        """Get Datadog API key."""
        return self._monitoring_config.datadog_api_key or ''
    
    # Data source configurations
    @property
    def BDC_SYMBOLS(self) -> list:
        """Get BDC symbols list."""
        return self._scraping_config.bdc_symbols
    
    @property
    def TECH_COMPANY_CIKS(self) -> Dict[str, str]:
        """Get tech company CIKs."""
        return self._scraping_config.tech_company_ciks
    
    # Scraping settings
    @property
    def SCRAPING_MAX_RETRIES(self) -> int:
        """Get scraping max retries."""
        return self._scraping_config.max_retries
    
    @property
    def SCRAPING_TIMEOUT(self) -> int:
        """Get scraping timeout."""
        return self._scraping_config.timeout_seconds
    
    @property
    def SCRAPING_RATE_LIMIT(self) -> float:
        """Get scraping rate limit delay."""
        return self._scraping_config.rate_limit_delay
    
    def get_alert_thresholds(self) -> Dict[str, float]:
        """Get all alert thresholds as a dictionary."""
        return self._alert_thresholds.to_dict()
    
    def get_api_credential(self, key: str) -> str:
        """Get API credential by key."""
        credential = self._config_loader.get_api_credential(key)
        return credential or ''
    
    def reload_config(self):
        """Reload configuration from all sources."""
        try:
            self._config_loader.reload_config()
            
            # Reload all configurations
            self._alert_thresholds = self._config_loader.get_alert_thresholds()
            self._database_config = self._config_loader.get_database_config()
            self._notification_config = self._config_loader.get_notification_config()
            self._monitoring_config = self._config_loader.get_monitoring_config()
            self._scraping_config = self._config_loader.get_scraping_config()
            
            logger.info("Settings configuration reloaded successfully")
        except Exception as e:
            logger.error(f"Error reloading settings configuration: {str(e)}")
            raise


# Global settings instance
settings = Settings()