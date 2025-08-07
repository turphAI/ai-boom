"""
Development environment configuration for Boom-Bust Sentinel
"""

import os

# Environment
ENVIRONMENT = "development"
DEBUG = True

# AWS Configuration
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
DYNAMODB_TABLE = os.getenv("DYNAMODB_TABLE", "boom-bust-sentinel-dev-state")
SNS_TOPIC_ARN = os.getenv("SNS_TOPIC_ARN", "")
CRITICAL_ALERTS_SNS_TOPIC = os.getenv("CRITICAL_ALERTS_SNS_TOPIC", "")

# Secrets Manager
SECRETS_MANAGER_PREFIX = os.getenv("SECRETS_MANAGER_PREFIX", "boom-bust-sentinel/dev")

# Data Sources Configuration
DATA_SOURCES = {
    "bond_issuance": {
        "enabled": True,
        "schedule": "0 8 ? * MON *",  # Weekly on Monday 8 AM UTC
        "timeout": 900,
        "memory": 1024,
        "threshold": 5000000000,  # $5B threshold for alerts
        "fallback_enabled": True
    },
    "bdc_discount": {
        "enabled": True,
        "schedule": "0 6 * * ? *",  # Daily at 6 AM UTC
        "timeout": 900,
        "memory": 1024,
        "threshold": 0.05,  # 5% change threshold
        "symbols": ["ARCC", "OCSL", "MAIN", "PSEC", "BXSL"]
    },
    "credit_fund": {
        "enabled": True,
        "schedule": "0 7 1 * ? *",  # Monthly on 1st at 7 AM UTC
        "timeout": 900,
        "memory": 1024,
        "threshold": 0.10,  # 10% decline threshold
        "form_pf_delay_days": 75
    },
    "bank_provision": {
        "enabled": True,
        "schedule": "0 9 1 1,4,7,10 ? *",  # Quarterly
        "timeout": 900,
        "memory": 1024,
        "threshold": 0.20,  # 20% increase threshold
        "banks": ["JPM", "BAC", "WFC", "C", "GS", "MS"]
    }
}

# Alert Configuration
ALERT_CHANNELS = {
    "email": {
        "enabled": True,
        "sns_topic": SNS_TOPIC_ARN
    },
    "slack": {
        "enabled": True,
        "webhook_secret": "slack-webhook-dev"
    },
    "telegram": {
        "enabled": True,
        "bot_token_secret": "telegram-bot-token-dev",
        "chat_id_secret": "telegram-chat-id-dev"
    }
}

# Monitoring Configuration
MONITORING = {
    "grafana": {
        "enabled": True,
        "api_url": os.getenv("GRAFANA_API_URL", ""),
        "api_key_secret": "grafana-api-key-dev",
        "dashboard_id": "boom-bust-sentinel-dev"
    },
    "cloudwatch": {
        "enabled": True,
        "namespace": "BoomBustSentinel/Dev",
        "retention_days": 7
    }
}

# Database Configuration
DATABASE = {
    "ttl_days": 90,  # Shorter retention for dev
    "backup_enabled": False,
    "point_in_time_recovery": False
}

# Rate Limiting (more lenient for dev)
RATE_LIMITS = {
    "sec_edgar": {
        "requests_per_second": 5,
        "requests_per_hour": 1000
    },
    "yahoo_finance": {
        "requests_per_second": 10,
        "requests_per_hour": 2000
    },
    "finra_trace": {
        "requests_per_second": 2,
        "requests_per_hour": 500
    }
}

# Logging Configuration
LOGGING = {
    "level": "DEBUG",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "handlers": ["console", "file"],
    "file_path": "/tmp/boom-bust-sentinel-dev.log"
}

# Feature Flags
FEATURE_FLAGS = {
    "chunked_processing": True,
    "cross_validation": True,
    "anomaly_detection": True,
    "fallback_sources": True,
    "enhanced_logging": True
}