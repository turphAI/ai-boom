# Boom-Bust Sentinel - TODO & Credentials Setup

## 🔧 Backend Issues to Fix (Priority Order)

### 1. State Store Implementation Issues ✅ FIXED
- ~~**DynamoDBStateStore** is abstract and missing concrete implementations~~ ✅ Implemented
- ~~**FirestoreStateStore** has incorrect inheritance (using DynamoDB methods)~~ ✅ Fixed
- ~~**File-based state store** has date filtering issues~~ ✅ Fixed timezone imports
- ~~**Timestamp sorting issues with mixed string/datetime objects**~~ ✅ Fixed
- **Status**: ✅ Resolved - all state stores now working

### 2. Lambda Handler Error Handling
- Connection errors returning 500 instead of 503
- Timeout handling not working correctly
- Chunked processing logic has incorrect assertions
- **Status**: High - affects production reliability

### 3. Deprecated DateTime Usage ✅ FIXED
- ~~Multiple files using `datetime.utcnow()` (deprecated in Python 3.12+)~~ ✅ Fixed
- ~~Should use `datetime.now(timezone.utc)` instead~~ ✅ Implemented
- **Status**: ✅ Resolved - all 36 files updated to use timezone-aware datetime

### 4. Test Infrastructure Issues
- Some integration tests failing due to mock setup
- GCP Secret Manager tests failing (missing google.cloud module)
- **Status**: Medium - affects development workflow

## 🔑 Required Credentials & Services

### AWS Services (Primary Infrastructure)
```bash
# Required Environment Variables
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=us-east-1  # or your preferred region

# DynamoDB Table
DATABASE_TABLE_NAME=boom-bust-metrics
DATABASE_PROVIDER=dynamodb

# SNS for Notifications
SNS_TOPIC_ARN=arn:aws:sns:us-east-1:123456789012:boom-bust-alerts

# Lambda Configuration
LAMBDA_TIMEOUT=900  # 15 minutes
LAMBDA_MEMORY=512   # MB
```

### Monitoring & Observability
```bash
# Grafana Cloud (Recommended - Free Tier Available)
GRAFANA_URL=https://your-instance.grafana.net
GRAFANA_API_KEY=your-grafana-api-key

# Alternative: Datadog
DATADOG_API_KEY=your-datadog-api-key

# Monitoring Settings
MONITORING_PROVIDER=grafana
METRICS_ENABLED=true
HEALTH_CHECK_INTERVAL=300
```

### Notification Channels
```bash
# Telegram Bot (Optional)
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_CHAT_ID=your-chat-id

# Slack Webhook (Optional)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/your/webhook/url
```

### External APIs
```bash
# SEC EDGAR API (No key required, but rate limited)
# User-Agent header required: "Your-App-Name your-email@domain.com"

# Yahoo Finance (via yfinance library)
# No API key required for basic usage

# Alpha Vantage (Optional, for enhanced financial data)
ALPHA_VANTAGE_API_KEY=your-alpha-vantage-key
```

## 📋 Service Setup Checklist

### AWS Setup
- [ ] Create AWS account and configure CLI
- [ ] Create DynamoDB table with proper schema
- [ ] Set up SNS topic for notifications
- [ ] Configure IAM roles for Lambda functions
- [ ] Set up CloudWatch for logging
- [ ] Configure AWS Secrets Manager (optional)

### Monitoring Setup
- [ ] Sign up for Grafana Cloud free account
- [ ] Create API key with MetricsPublisher role
- [ ] Import dashboard from `config/grafana_dashboard.json`
- [ ] Set up alerts for critical metrics
- [ ] Test metric submission

### Notification Setup
- [ ] Create Telegram bot (optional)
- [ ] Set up Slack webhook (optional)
- [ ] Test notification channels
- [ ] Configure alert thresholds

### Development Environment
- [ ] Install required Python packages
- [ ] Set up environment variables
- [ ] Configure local testing database
- [ ] Run test suite to verify setup

## 🚀 Deployment Preparation

### Terraform Infrastructure
```bash
# Initialize Terraform
terraform init
terraform plan
terraform apply
```

### Serverless Framework
```bash
# Deploy Lambda functions
serverless deploy --stage production
```

### Environment-Specific Configs
Create these files:
- `config/environments/development.json`
- `config/environments/staging.json`
- `config/environments/production.json`

## 🔍 Testing & Validation

### Backend Health Check
```bash
# Run core component tests
python -m pytest tests/test_metrics_service.py tests/test_health_monitor.py -v

# Run monitoring demo
python examples/monitoring_demo.py

# Test individual scrapers
python -m pytest tests/test_*_scraper.py -v
```

### Integration Testing
```bash
# Test with real AWS services (requires credentials)
python -m pytest tests/test_*_integration.py -v

# Test Lambda handlers
python -m pytest tests/test_lambda_handlers.py -v
```

## 📊 Monitoring Dashboard Metrics

### System Health Metrics
- Component status (database, scrapers, alerts)
- Response times and error rates
- Success rates and execution times

### Business Metrics
- Bond issuance weekly totals
- BDC discount to NAV averages
- Credit fund asset values
- Bank provision amounts

### Alert Thresholds
```bash
# Default thresholds (configurable)
BOND_ISSUANCE_THRESHOLD=5000000000  # $5B
BDC_DISCOUNT_THRESHOLD=0.05         # 5%
CREDIT_FUND_THRESHOLD=0.10          # 10%
BANK_PROVISION_THRESHOLD=0.20       # 20%
```

## 🔧 Next Steps for Web UI Tasks

### API Endpoints Needed
- `/api/health` - System health status
- `/api/metrics` - Recent metrics data
- `/api/alerts` - Alert history and acknowledgment
- `/api/scrapers` - Scraper status and controls

### Frontend Requirements
- Real-time dashboard with charts
- Alert management interface
- System health monitoring
- Configuration management

### Authentication & Security
- API key authentication
- Rate limiting
- CORS configuration
- Input validation

## 📝 Configuration Files to Create

### 1. Environment Configs
```json
// config/environments/production.json
{
  "database": {
    "provider": "dynamodb",
    "table_name": "boom-bust-metrics-prod",
    "region": "us-east-1"
  },
  "monitoring": {
    "provider": "grafana",
    "metrics_enabled": true
  },
  "alert_thresholds": {
    "bond_issuance": 5000000000,
    "bdc_discount": 0.05
  }
}
```

### 2. Serverless Config Updates
```yaml
# serverless.yml additions
environment:
  GRAFANA_URL: ${env:GRAFANA_URL}
  GRAFANA_API_KEY: ${env:GRAFANA_API_KEY}
  DATABASE_TABLE_NAME: ${self:custom.tableName}
```

### 3. Terraform Variables
```hcl
# terraform/variables.tf
variable "grafana_api_key" {
  description = "Grafana Cloud API key"
  type        = string
  sensitive   = true
}
```

## 🎯 Immediate Action Items

1. ~~**Fix State Store Implementation**~~ ✅ **COMPLETED**
2. ~~**Configure AWS credentials**~~ ✅ **COMPLETED** (Local development working)
3. ~~**Fix deprecated DateTime usage**~~ ✅ **COMPLETED**
4. **Set up Grafana Cloud account** (High)
5. **Add AWS permissions for full deployment** (High)
6. **Test monitoring pipeline** (Medium)
7. **Prepare API endpoints for web UI** (Medium)

## 💡 Cost Optimization Notes

### Free Tier Usage
- **Grafana Cloud**: 10K metrics/month free
- **AWS Lambda**: 1M requests/month free
- **DynamoDB**: 25GB storage free
- **SNS**: 1K notifications/month free

### Estimated Monthly Costs (Beyond Free Tier)
- Lambda executions: ~$5-10
- DynamoDB storage: ~$2-5
- CloudWatch logs: ~$1-3
- **Total**: ~$8-18/month for moderate usage