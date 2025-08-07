# Monitoring and Observability Setup

This document describes how to set up and use the monitoring and observability system for the Boom-Bust Sentinel.

## Overview

The monitoring system consists of three main components:

1. **MetricsService** - Sends metrics to Grafana Cloud or Datadog
2. **HealthMonitor** - Monitors system component health
3. **Enhanced Logging** - Structured logging with contextual information

## Configuration

### Environment Variables

Set these environment variables to configure monitoring:

```bash
# Grafana Cloud (recommended for free tier)
GRAFANA_URL=https://your-instance.grafana.net
GRAFANA_API_KEY=your-api-key

# Datadog (alternative)
DATADOG_API_KEY=your-datadog-api-key

# Monitoring settings
MONITORING_PROVIDER=grafana  # or 'datadog'
METRICS_ENABLED=true
HEALTH_CHECK_INTERVAL=300  # seconds

# Logging
LOG_LEVEL=INFO
```

### Grafana Cloud Setup

1. Sign up for a free Grafana Cloud account at https://grafana.com/
2. Create a new API key with "MetricsPublisher" role
3. Set the `GRAFANA_URL` and `GRAFANA_API_KEY` environment variables
4. Import the dashboard from `config/grafana_dashboard.json`

### Datadog Setup (Alternative)

1. Sign up for Datadog account
2. Get your API key from the Datadog dashboard
3. Set the `DATADOG_API_KEY` environment variable

## Usage

### Sending Metrics

```python
from services.metrics_service import MetricsService
from models.core import MetricValue
from datetime import datetime, timezone

# Initialize service
metrics_service = MetricsService()

# Send a single metric
metric_value = MetricValue(
    value=1500000000,  # $1.5B
    timestamp=datetime.now(timezone.utc),
    confidence=0.95,
    source='bond_scraper',
    metadata={'companies': 'MSFT,META'}
)

metrics_service.send_metric('bond_issuance', 'weekly_total', metric_value)

# Send multiple metrics
metrics = [
    {
        'data_source': 'bdc_discount',
        'metric_name': 'avg_discount',
        'value': -0.15,
        'timestamp': datetime.now(timezone.utc),
        'source': 'scraper',
        'metadata': {'symbols': 'ARCC,OCSL'}
    }
]

metrics_service.send_metrics(metrics)
```

### Health Monitoring

```python
from utils.health_monitor import HealthMonitor

# Initialize monitor
health_monitor = HealthMonitor()

# Register custom health check
def my_service_check():
    # Your health check logic
    return True  # or False

health_monitor.register_health_check(
    name='my_service',
    check_function=my_service_check,
    timeout_seconds=10,
    critical=True
)

# Run all health checks
results = health_monitor.run_all_health_checks()

# Get system status
status = health_monitor.get_system_status()
print(f"System status: {status['status']}")
```

### Enhanced Logging

```python
from utils.logging_config import get_contextual_logger, ErrorContext

# Get logger with context
logger = get_contextual_logger(__name__, component='my_scraper')

# Log with extra context
logger.info(
    "Processing data",
    extra={
        'data_source': 'bond_issuance',
        'record_count': 100,
        'processing_time': 2.5
    }
)

# Use error context manager
with ErrorContext(logger, 'data_processing', source='bond_scraper'):
    # Your code here
    process_data()
```

### Scraper Integration

```python
from services.metrics_service import MetricsService
from models.core import ScraperResult
from utils.logging_config import log_scraper_execution

metrics_service = MetricsService()

@log_scraper_execution('bond_issuance', 'weekly')
def scrape_bond_data():
    # Your scraping logic
    return data

# Send scraper metrics
scraper_result = ScraperResult(
    data_source='bond_issuance',
    metric_name='weekly',
    success=True,
    data={'total_amount': 2500000000},
    error=None,
    execution_time=3.2,
    timestamp=datetime.now(timezone.utc)
)

metrics_service.send_scraper_metrics(scraper_result)
```

## Anomaly Detection

The metrics service includes built-in anomaly detection:

```python
# Detect anomalies using statistical methods
anomaly = metrics_service.detect_anomalies('bond_issuance_weekly', 5000000000)

if anomaly and anomaly.is_anomaly:
    print(f"Anomaly detected! Confidence: {anomaly.confidence:.2%}")
    print(f"Expected range: {anomaly.expected_range}")
```

## Dashboard Metrics

The following metrics are automatically sent to your monitoring backend:

### System Health Metrics
- `boom_bust_sentinel.{component}_status` - Component health (1=healthy, 0=failed)
- `boom_bust_sentinel.{component}_response_time` - Response time in milliseconds
- `boom_bust_sentinel.{component}_error_count` - Error count

### Scraper Metrics
- `boom_bust_sentinel.{scraper}_execution_time` - Execution time in seconds
- `boom_bust_sentinel.{scraper}_success` - Success rate (1=success, 0=failure)
- `boom_bust_sentinel.{metric_name}` - Actual scraped values

### Business Metrics
- `boom_bust_sentinel.weekly_total` - Bond issuance weekly total
- `boom_bust_sentinel.avg_discount` - BDC average discount to NAV
- `boom_bust_sentinel.asset_value` - Credit fund asset values
- `boom_bust_sentinel.non_bank_provision` - Bank provisions for non-bank financials

## Grafana Dashboard

Import the pre-built dashboard from `config/grafana_dashboard.json` to visualize:

- System health overview
- Scraper execution times and success rates
- Business metric trends
- Error counts and response times

## Alerting

Set up alerts in Grafana or Datadog based on:

- System health status changes
- Scraper failure rates above threshold
- Business metric anomalies
- High error rates or response times

## Troubleshooting

### No Metrics Backends Configured

If you see "No metrics backends configured":
1. Check that `GRAFANA_API_KEY` and `GRAFANA_URL` are set
2. Or set `DATADOG_API_KEY` for Datadog
3. Verify the API keys are valid

### Health Checks Failing

Common health check failures:
- **Database**: Check DynamoDB/Firestore connectivity
- **Alert Service**: Verify notification channels are configured
- **External APIs**: Check internet connectivity and API limits

### Metrics Not Appearing

If metrics don't appear in Grafana/Datadog:
1. Check API key permissions
2. Verify the metrics URL is correct
3. Check logs for HTTP errors
4. Ensure metrics are being sent (check logs)

## Performance Considerations

- Metrics are sent asynchronously with retry logic
- Health checks run in parallel with timeouts
- Metric history is limited to 100 points per metric
- Old health check results are automatically cleaned up

## Security

- API keys are retrieved from environment variables or secrets manager
- No sensitive data is included in metric metadata
- Logs can be configured to exclude sensitive information

## Testing

Run the monitoring demo to test your setup:

```bash
python examples/monitoring_demo.py
```

This will demonstrate all monitoring features and help verify your configuration.