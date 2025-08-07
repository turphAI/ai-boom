"""
Production environment configuration for Boom-Bust Sentinel
"""

import os

# Environment
ENVIRONMENT = "production"
DEBUG = False

# AWS Configuration
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
DYNAMODB_TABLE = os.getenv("DYNAMODB_TABLE", "boom-bust-sentinel-prod-state")
SNS_TOPIC_ARN = os.getenv("SNS_TOPIC_ARN", "")
CRITICAL_ALERTS_SNS_TOPIC = os.getenv("CRITICAL_ALERTS_SNS_TOPIC", "")

# Secrets Manager
SECRETS_MANAGER_PREFIX = os.getenv("SECRETS_MANAGER_PREFIX", "boom-bust-sentinel/prod")

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
        "symbols": ["ARCC", "OCSL", "MAIN", "PSEC", "BXSL", "FDUS", "GBDC", "HTGC"]
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
        "banks": ["JPM", "BAC", "WFC", "C", "GS", "MS", "USB", "PNC", "TFC", "COF"]
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
        "webhook_secret": "slack-webhook-prod"
    },
    "telegram": {
        "enabled": True,
        "bot_token_secret": "telegram-bot-token-prod",
        "chat_id_secret": "telegram-chat-id-prod"
    }
}

# Monitoring Configuration
MONITORING = {
    "grafana": {
        "enabled": True,
        "api_url": os.getenv("GRAFANA_API_URL", ""),
        "api_key_secret": "grafana-api-key-prod",
        "dashboard_id": "boom-bust-sentinel-prod"
    },
    "cloudwatch": {
        "enabled": True,
        "namespace": "BoomBustSentinel/Prod",
        "retention_days": 30
    }
}

# Database Configuration
DATABASE = {
    "ttl_days": 730,  # 2 years retention for production
    "backup_enabled": True,
    "point_in_time_recovery": True
}

# Rate Limiting (conservative for production)
RATE_LIMITS = {
    "sec_edgar": {
        "requests_per_second": 2,
        "requests_per_hour": 600
    },
    "yahoo_finance": {
        "requests_per_second": 5,
        "requests_per_hour": 1000
    },
    "finra_trace": {
        "requests_per_second": 1,
        "requests_per_hour": 200
    }
}

# Logging Configuration
LOGGING = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "handlers": ["cloudwatch"],
    "cloudwatch_group": "/aws/lambda/boom-bust-sentinel-prod"
}

# Feature Flags
FEATURE_FLAGS = {
    "chunked_processing": True,
    "cross_validation": True,
    "anomaly_detection": True,
    "fallback_sources": True,
    "enhanced_logging": False
}