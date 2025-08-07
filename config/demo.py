#!/usr/bin/env python3
"""
Demonstration script for the secrets management and configuration system.
"""

import os
from config.secrets import SecretManager
from config.config_loader import ConfigLoader
from config.settings import Settings


def demo_secrets_management():
    """Demonstrate secrets management functionality."""
    print("=== Secrets Management Demo ===")
    
    # Use mock provider for demonstration
    os.environ['SECRET_PROVIDER'] = 'mock'
    
    # Initialize SecretManager
    secret_manager = SecretManager()
    print(f"Secret provider: {secret_manager.provider}")
    
    # Get API credentials
    api_creds = secret_manager.get_api_credentials()
    print(f"API credentials: {list(api_creds.keys())}")
    
    # Get specific credential
    telegram_token = secret_manager.get_secret_value('boom-bust-sentinel/api-keys', 'telegram_bot_token')
    print(f"Telegram token: {telegram_token[:10]}..." if telegram_token else "None")
    
    # Get database config
    db_config = secret_manager.get_database_config()
    print(f"Database config: {list(db_config.keys())}")
    
    print()


def demo_configuration_loading():
    """Demonstrate configuration loading functionality."""
    print("=== Configuration Loading Demo ===")
    
    # Test different environments
    for env in ['development', 'production', 'testing']:
        print(f"\n--- {env.upper()} Environment ---")
        
        config_loader = ConfigLoader(environment=env)
        
        # Get alert thresholds
        thresholds = config_loader.get_alert_thresholds()
        print(f"Bond issuance threshold: ${thresholds.bond_issuance:,.0f}")
        print(f"BDC discount threshold: {thresholds.bdc_discount:.1%}")
        
        # Get database config
        db_config = config_loader.get_database_config()
        print(f"Database: {db_config.provider} ({db_config.table_name})")
        print(f"TTL: {db_config.ttl_days} days")
        
        # Get scraping config
        scraping_config = config_loader.get_scraping_config()
        print(f"BDC symbols: {scraping_config.bdc_symbols}")
        print(f"Max retries: {scraping_config.max_retries}")
    
    print()


def demo_settings_integration():
    """Demonstrate Settings class integration."""
    print("=== Settings Integration Demo ===")
    
    # Set environment for testing
    os.environ['ENVIRONMENT'] = 'development'
    os.environ['SECRET_PROVIDER'] = 'mock'
    
    # Initialize Settings
    settings = Settings()
    
    print(f"Environment: {settings.ENVIRONMENT}")
    print(f"Database provider: {settings.DATABASE_PROVIDER}")
    print(f"Database table: {settings.DATABASE_TABLE_NAME}")
    print(f"AWS region: {settings.AWS_REGION}")
    
    print("\nAlert Thresholds:")
    print(f"  Bond issuance: ${settings.BOND_ISSUANCE_THRESHOLD:,.0f}")
    print(f"  BDC discount: {settings.BDC_DISCOUNT_THRESHOLD:.1%}")
    print(f"  Credit fund: {settings.CREDIT_FUND_THRESHOLD:.1%}")
    print(f"  Bank provision: {settings.BANK_PROVISION_THRESHOLD:.1%}")
    
    print("\nNotification Settings:")
    print(f"  Max retries: {settings.ALERT_MAX_RETRIES}")
    print(f"  Retry delay: {settings.ALERT_RETRY_DELAY}s")
    print(f"  Telegram token: {'***' if settings.TELEGRAM_BOT_TOKEN else 'Not set'}")
    
    print("\nData Sources:")
    print(f"  BDC symbols: {settings.BDC_SYMBOLS}")
    print(f"  Tech CIKs: {list(settings.TECH_COMPANY_CIKS.keys())}")
    
    # Test method calls
    all_thresholds = settings.get_alert_thresholds()
    print(f"\nAll thresholds: {all_thresholds}")
    
    # Test API credential retrieval
    grafana_key = settings.get_api_credential('grafana_api_key')
    print(f"Grafana API key: {'***' if grafana_key else 'Not set'}")
    
    print()


def demo_environment_switching():
    """Demonstrate environment-based configuration switching."""
    print("=== Environment Switching Demo ===")
    
    # Test environment variable override
    original_env = os.environ.get('ENVIRONMENT', 'development')
    
    for env in ['development', 'production', 'testing']:
        os.environ['ENVIRONMENT'] = env
        os.environ['SECRET_PROVIDER'] = 'mock'
        
        # Create new settings instance for each environment
        settings = Settings()
        
        print(f"\n{env.upper()} Environment:")
        print(f"  Bond threshold: ${settings.BOND_ISSUANCE_THRESHOLD:,.0f}")
        print(f"  Database table: {settings.DATABASE_TABLE_NAME}")
        print(f"  TTL days: {settings.DATABASE_TTL_DAYS}")
        print(f"  BDC symbols: {len(settings.BDC_SYMBOLS)} symbols")
        print(f"  Max retries: {settings.ALERT_MAX_RETRIES}")
    
    # Restore original environment
    os.environ['ENVIRONMENT'] = original_env
    print()


def demo_configuration_reload():
    """Demonstrate configuration reloading."""
    print("=== Configuration Reload Demo ===")
    
    os.environ['ENVIRONMENT'] = 'development'
    os.environ['SECRET_PROVIDER'] = 'mock'
    
    settings = Settings()
    
    print(f"Initial bond threshold: ${settings.BOND_ISSUANCE_THRESHOLD:,.0f}")
    
    # Simulate configuration change by setting environment variable
    os.environ['BOND_ISSUANCE_THRESHOLD'] = '2000000000'
    
    print("Setting BOND_ISSUANCE_THRESHOLD=2000000000...")
    
    # Reload configuration
    settings.reload_config()
    
    print(f"After reload bond threshold: ${settings.BOND_ISSUANCE_THRESHOLD:,.0f}")
    
    # Clean up
    if 'BOND_ISSUANCE_THRESHOLD' in os.environ:
        del os.environ['BOND_ISSUANCE_THRESHOLD']
    
    print()


def main():
    """Run all demonstrations."""
    print("Boom-Bust Sentinel Configuration System Demo")
    print("=" * 50)
    
    try:
        demo_secrets_management()
        demo_configuration_loading()
        demo_settings_integration()
        demo_environment_switching()
        demo_configuration_reload()
        
        print("✅ All demonstrations completed successfully!")
        
    except Exception as e:
        print(f"❌ Demo failed with error: {str(e)}")
        raise


if __name__ == "__main__":
    main()