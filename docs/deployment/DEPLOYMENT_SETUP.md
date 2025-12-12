# 🚀 Boom-Bust Sentinel - Deployment Setup Guide

## Current Status: 64/100 Ready ⚠️

Your system is mostly ready but needs AWS permissions to deploy.

## 🔧 Step 1: Add AWS Permissions (Critical)

### Option A: Attach Custom Policy (Recommended)
1. Go to AWS Console → IAM → Users
2. Click on your user: `aiProjects`
3. Click "Add permissions" → "Attach policies directly"
4. Click "Create policy"
5. Click "JSON" tab
6. Copy and paste the content from `aws-permissions-policy.json`
7. Name it: `BoomBustSentinelDeployment`
8. Create and attach the policy

### Option B: Use AWS Managed Policies (Easier but broader permissions)
Attach these managed policies to your `aiProjects` user:
- `AWSLambdaFullAccess`
- `AmazonDynamoDBFullAccess`
- `AmazonSNSFullAccess`
- `IAMFullAccess`
- `AWSCloudFormationFullAccess`
- `SecretsManagerReadWrite`

## 🔧 Step 2: Install Missing Tools

### Install Terraform (Optional)
```bash
# macOS
brew install terraform

# Or skip if you prefer Serverless Framework only
```

## 🔧 Step 3: Fix Database Configuration

The scraper is trying to use "file" database provider but the system expects "dynamodb". Let's fix this:

```bash
# Update .env file
sed -i '' 's/DATABASE_PROVIDER=file/DATABASE_PROVIDER=dynamodb/' .env
```

## 🔧 Step 4: Test Deployment Readiness

After adding AWS permissions, run the readiness check again:

```bash
python scripts/deployment_readiness_check.py
```

**Target: 80+ readiness score**

## 🚀 Step 5: Deploy to AWS

### Option A: Serverless Framework (Recommended)
```bash
# Deploy to development
serverless deploy --stage dev

# Deploy to production
serverless deploy --stage prod
```

### Option B: Terraform
```bash
cd terraform
terraform init
terraform plan
terraform apply
```

## 🔧 Step 6: Verify Deployment

### Test Lambda Functions
```bash
# Test bond issuance scraper
aws lambda invoke --function-name boom-bust-sentinel-dev-bond-issuance response.json
cat response.json
```

### Check DynamoDB Tables
```bash
aws dynamodb list-tables
aws dynamodb describe-table --table-name boom-bust-sentinel-dev-state
```

### Test SNS Topics
```bash
aws sns list-topics
```

## 🔧 Step 7: Set Up Production Database

### Create DynamoDB Table Manually (if needed)
```bash
aws dynamodb create-table \
    --table-name boom-bust-sentinel-prod-state \
    --attribute-definitions \
        AttributeName=pk,AttributeType=S \
        AttributeName=sk,AttributeType=S \
    --key-schema \
        AttributeName=pk,KeyType=HASH \
        AttributeName=sk,KeyType=RANGE \
    --billing-mode PAY_PER_REQUEST
```

## 🔧 Step 8: Configure Production Environment

Create production environment variables:

```bash
# Add to your deployment environment
export ENVIRONMENT=production
export DATABASE_PROVIDER=dynamodb
export DATABASE_TABLE_NAME=boom-bust-sentinel-prod-state
export AWS_REGION=us-east-1
```

## 📊 Monitoring Setup

### CloudWatch Dashboards
Your deployment will automatically create:
- Lambda function metrics
- DynamoDB metrics
- SNS topic metrics
- Custom application metrics

### Grafana Integration (Optional)
If you set up Grafana earlier:
1. Metrics will automatically flow to Grafana Cloud
2. Import the dashboard from `config/grafana_dashboard.json`
3. Set up alerts for threshold breaches

## 🧪 Testing Production Deployment

### Run Integration Tests
```bash
# Test all scrapers in production
python scripts/test_deployment.py --stage prod

# Test specific scraper
python -c "
from scrapers.bond_issuance_scraper import BondIssuanceScraper
scraper = BondIssuanceScraper()
result = scraper.execute()
print(f'Success: {result.success}')
print(f'Data: {result.data}')
"
```

### Verify Data Flow
1. Check DynamoDB for new data
2. Verify SNS notifications
3. Check CloudWatch logs
4. Test alert configurations

## 🚨 Troubleshooting

### Common Issues

**"Access Denied" errors**
- Verify AWS permissions are attached
- Check IAM policy is correct
- Ensure user has necessary roles

**"Table does not exist"**
- Run: `aws dynamodb list-tables`
- Create table manually if needed
- Check table name in environment variables

**Lambda timeout errors**
- Increase timeout in `serverless.yml`
- Check function memory allocation
- Review CloudWatch logs

**No data in dashboard**
- Verify scrapers are running
- Check DynamoDB for data
- Verify API endpoints are working

## 📋 Success Checklist

- [ ] AWS permissions added (80+ readiness score)
- [ ] Serverless deployment successful
- [ ] DynamoDB tables created and accessible
- [ ] Lambda functions deployed and working
- [ ] SNS topics created for notifications
- [ ] CloudWatch logging working
- [ ] Scrapers executing successfully
- [ ] Data flowing to database
- [ ] Dashboard showing real data
- [ ] Alerts configured and working

## 🎯 Next Steps After Deployment

1. **Set up monitoring alerts** in CloudWatch
2. **Configure notification channels** (email, Slack, etc.)
3. **Set up automated testing** with GitHub Actions
4. **Configure backup and disaster recovery**
5. **Set up cost monitoring** and budgets
6. **Document operational procedures**

---

**Need help?** Run the deployment readiness check to see current status:
```bash
python scripts/deployment_readiness_check.py
```