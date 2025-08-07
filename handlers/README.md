# Boom-Bust Sentinel Lambda Handlers

This directory contains AWS Lambda handler functions for the Boom-Bust Sentinel scrapers. Each handler provides a serverless entry point for the corresponding scraper with comprehensive error handling, timeout management, and monitoring capabilities.

## Handler Functions

### 1. Bond Issuance Handler (`bond_issuance_handler.py`)

Monitors weekly investment-grade tech bond issuance from SEC filings.

**Schedule**: Weekly (Monday 8 AM UTC)
**Timeout**: 15 minutes
**Memory**: 1024 MB

**Features**:
- Processes SEC Rule 424B prospectuses
- Extracts notional amounts and coupon rates
- Supports chunked processing for large datasets
- Comprehensive error logging and metrics

### 2. BDC Discount Handler (`bdc_discount_handler.py`)

Tracks Business Development Company discount-to-NAV ratios.

**Schedule**: Daily (6 AM UTC)
**Timeout**: 15 minutes
**Memory**: 1024 MB

**Features**:
- Fetches stock prices from Yahoo Finance
- Parses NAV data from RSS feeds
- Calculates discount ratios
- Handles network timeouts gracefully

### 3. Credit Fund Handler (`credit_fund_handler.py`)

Monitors private credit fund asset marks from Form PF filings.

**Schedule**: Monthly (1st day, 7 AM UTC)
**Timeout**: 15 minutes
**Memory**: 1024 MB

**Features**:
- Downloads and parses Form PF XML files
- Extracts gross asset values
- Detects quarter-over-quarter declines
- Handles large XML file processing

### 4. Bank Provision Handler (`bank_provision_handler.py`)

Tracks bank provisioning for non-bank financial exposures.

**Schedule**: Quarterly (1st day of Q1,Q2,Q3,Q4, 9 AM UTC)
**Timeout**: 15 minutes
**Memory**: 1024 MB

**Features**:
- Parses XBRL data from 10-Q filings
- Fallback to earnings call transcript analysis
- Extracts provision amounts
- Multi-source data validation

## Common Features

All handlers include:

### Error Handling
- Comprehensive exception catching and logging
- Structured error responses with context
- CloudWatch metrics for error tracking
- Critical alert notifications for severe failures

### Timeout Management
- Configurable timeout handling with signal-based interruption
- Graceful cleanup on timeout
- Buffer time for proper shutdown
- Chunked processing fallback for large datasets

### Monitoring & Observability
- Structured logging with execution context
- CloudWatch metrics for performance tracking
- Execution time and success rate monitoring
- Business metrics specific to each scraper

### Chunked Processing
- Automatic fallback for timeout scenarios
- Configurable chunk sizes
- State management across chunks
- Progress tracking and resumption

## Deployment

### Using Serverless Framework

```bash
# Deploy all functions
./deploy.sh serverless

# Deploy to specific stage and region
./deploy.sh -s prod -r us-west-2 serverless
```

### Using Terraform

```bash
# Deploy infrastructure
./deploy.sh terraform

# Deploy to specific environment
./deploy.sh -s production -r us-west-2 terraform
```

## Configuration

### Environment Variables

All handlers use these environment variables:

- `STAGE`: Deployment stage (dev, staging, prod)
- `REGION`: AWS region
- `DYNAMODB_TABLE`: State storage table name
- `SNS_TOPIC_ARN`: Alert notifications topic
- `CRITICAL_ALERTS_SNS_TOPIC`: Critical alert topic
- `SECRETS_MANAGER_PREFIX`: Prefix for secrets
- `SCRAPER_NAME`: Specific scraper identifier

### AWS Secrets Manager

Handlers retrieve sensitive configuration from AWS Secrets Manager:

- `{prefix}/api-keys`: External API keys
- `{prefix}/webhook-urls`: Notification webhook URLs
- `{prefix}/database-config`: Database connection strings

## CloudWatch Events Integration

### Scheduled Execution

Each handler is triggered by CloudWatch Events rules:

```json
{
  "source": "aws.events",
  "detail-type": "Scheduled Event",
  "detail": {
    "scraper_name": "bond-issuance"
  }
}
```

### Manual Invocation

Handlers can be invoked manually with custom events:

```bash
aws lambda invoke \
  --function-name boom-bust-sentinel-dev-bond-issuance \
  --payload '{"source":"manual","detail":{"test":true}}' \
  response.json
```

## Chunked Processing

When regular execution times out, handlers support chunked processing:

### Invoking Chunked Handler

```bash
aws lambda invoke \
  --function-name boom-bust-sentinel-dev-bond-issuance-chunked \
  --payload '{"chunk_size":2,"chunk_index":0}' \
  response.json
```

### Chunk Processing Flow

1. Handler determines total items to process
2. Calculates chunk boundaries based on `chunk_size` and `chunk_index`
3. Processes subset of data
4. Returns status indicating if more chunks remain
5. Can be invoked repeatedly until all chunks processed

## Error Handling

### Error Response Format

```json
{
  "statusCode": 500,
  "body": {
    "success": false,
    "error": "Error message",
    "error_type": "ExceptionType",
    "execution_id": "request-id",
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

### HTTP Status Codes

- `200`: Success
- `400`: Bad Request (validation error)
- `403`: Forbidden (permission error)
- `404`: Not Found (resource missing)
- `408`: Request Timeout
- `500`: Internal Server Error
- `503`: Service Unavailable (external service down)

## Monitoring

### CloudWatch Metrics

Custom metrics sent to `BoomBustSentinel/Lambda` namespace:

- `ExecutionTime`: Function execution duration
- `Executions`: Success/error counts
- `DataPointsProcessed`: Number of items processed
- `Errors`: Error counts by type

### CloudWatch Logs

Structured logs include:

- Execution ID for tracing
- Performance metrics
- Error details with stack traces
- Business context (companies processed, data quality, etc.)

### Dashboards

CloudWatch dashboard shows:

- Execution duration trends
- Error rates by function
- Success/failure counts
- Data processing volumes

## Testing

### Unit Tests

```bash
# Run handler tests
python -m pytest tests/test_lambda_handlers.py -v

# Run specific test class
python -m pytest tests/test_lambda_handlers.py::TestBondIssuanceHandler -v
```

### Local Testing

Each handler includes a `__main__` block for local testing:

```bash
# Test bond issuance handler locally
python handlers/bond_issuance_handler.py
```

### Integration Testing

```bash
# Run full integration tests
python -m pytest tests/test_integration.py -v
```

## Performance Optimization

### Memory Configuration

- Standard handlers: 1024 MB
- Chunked handlers: 1024 MB (can be reduced to 512 MB if needed)

### Timeout Configuration

- Standard handlers: 900 seconds (15 minutes)
- Chunked handlers: 300-600 seconds (5-10 minutes)

### Cold Start Optimization

- Minimal imports in handler functions
- Lazy loading of heavy dependencies
- Connection pooling for external services
- Efficient packaging with serverless-python-requirements

## Troubleshooting

### Common Issues

1. **Timeout Errors**
   - Check CloudWatch logs for execution time
   - Consider using chunked processing
   - Optimize scraper performance

2. **Permission Errors**
   - Verify IAM role permissions
   - Check Secrets Manager access
   - Validate DynamoDB permissions

3. **External Service Failures**
   - Check network connectivity
   - Verify API keys in Secrets Manager
   - Review rate limiting settings

4. **Data Quality Issues**
   - Monitor confidence scores in metrics
   - Check data validation logs
   - Review source data availability

### Debug Mode

Enable debug logging by setting environment variable:

```bash
export LOG_LEVEL=DEBUG
```

### Manual Execution

Test individual handlers:

```bash
# Create test event
cat > test_event.json << EOF
{
  "source": "manual",
  "detail-type": "Test Event",
  "detail": {"test": true}
}
EOF

# Invoke function
aws lambda invoke \
  --function-name boom-bust-sentinel-dev-bond-issuance \
  --payload file://test_event.json \
  response.json

# Check response
cat response.json
```

## Security Considerations

### IAM Permissions

Handlers use least-privilege IAM roles with access only to:

- Required DynamoDB tables
- Specific SNS topics
- Relevant Secrets Manager secrets
- CloudWatch Logs and Metrics

### Secrets Management

- All sensitive data stored in AWS Secrets Manager
- Automatic secret rotation where supported
- No hardcoded credentials in code

### Network Security

- Functions run in AWS managed VPC
- No direct internet access for sensitive operations
- All external API calls use HTTPS

### Data Protection

- All data encrypted in transit and at rest
- PII handling follows data protection guidelines
- Audit logging for all data access

## Support

For issues or questions:

1. Check CloudWatch logs for error details
2. Review monitoring dashboards
3. Consult this documentation
4. Contact the development team

## Contributing

When adding new handlers:

1. Follow the existing pattern and structure
2. Include comprehensive error handling
3. Add timeout and chunked processing support
4. Write unit and integration tests
5. Update deployment configurations
6. Document new functionality