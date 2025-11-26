"""
Deployment verification tests for Boom-Bust Sentinel
These tests verify that the deployment is working correctly in different environments.
"""

import os
import sys
import json
import time
import pytest
import requests
import boto3
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional

class DeploymentVerifier:
    def __init__(self, environment: str = "staging"):
        self.environment = environment
        self.aws_region = os.getenv("AWS_REGION", "us-east-1")
        
        # Environment-specific configurations
        self.config = self._get_environment_config()
        
        # AWS clients
        self.lambda_client = boto3.client('lambda', region_name=self.aws_region)
        self.dynamodb_client = boto3.client('dynamodb', region_name=self.aws_region)
        self.sns_client = boto3.client('sns', region_name=self.aws_region)
        self.cloudwatch_client = boto3.client('cloudwatch', region_name=self.aws_region)
        
    def _get_environment_config(self) -> Dict[str, Any]:
        """Get environment-specific configuration."""
        configs = {
            "staging": {
                "dashboard_url": "https://staging-dashboard.boom-bust-sentinel.com",
                "expected_functions": 8,  # 4 main + 4 chunked
                "table_name": f"boom-bust-sentinel-staging-state",
                "sns_topics": [
                    f"boom-bust-sentinel-staging-alerts",
                    f"boom-bust-sentinel-staging-critical-alerts"
                ]
            },
            "production": {
                "dashboard_url": "https://dashboard.boom-bust-sentinel.com",
                "expected_functions": 8,
                "table_name": f"boom-bust-sentinel-prod-state",
                "sns_topics": [
                    f"boom-bust-sentinel-prod-alerts",
                    f"boom-bust-sentinel-prod-critical-alerts"
                ]
            },
            "dev": {
                "dashboard_url": "http://localhost:3000",
                "expected_functions": 8,
                "table_name": f"boom-bust-sentinel-dev-state",
                "sns_topics": [
                    f"boom-bust-sentinel-dev-alerts",
                    f"boom-bust-sentinel-dev-critical-alerts"
                ]
            }
        }
        
        return configs.get(self.environment, configs["staging"])

class TestInfrastructureDeployment:
    """Test infrastructure deployment."""
    
    @pytest.fixture(scope="class")
    def verifier(self, request):
        environment = "staging" if request.config.getoption("--staging") else "production"
        return DeploymentVerifier(environment)
    
    def test_lambda_functions_exist(self, verifier):
        """Test that all Lambda functions are deployed and active."""
        expected_functions = [
            f"boom-bust-sentinel-{verifier.environment}-bond-issuance",
            f"boom-bust-sentinel-{verifier.environment}-bdc-discount",
            f"boom-bust-sentinel-{verifier.environment}-credit-fund",
            f"boom-bust-sentinel-{verifier.environment}-bank-provision",
            f"boom-bust-sentinel-{verifier.environment}-bond-issuance-chunked",
            f"boom-bust-sentinel-{verifier.environment}-bdc-discount-chunked",
            f"boom-bust-sentinel-{verifier.environment}-credit-fund-chunked",
            f"boom-bust-sentinel-{verifier.environment}-bank-provision-chunked"
        ]
        
        for function_name in expected_functions:
            try:
                response = verifier.lambda_client.get_function(FunctionName=function_name)
                assert response['Configuration']['State'] == 'Active', f"Function {function_name} is not active"
                assert response['Configuration']['Runtime'].startswith('python'), f"Function {function_name} has wrong runtime"
                
                # Check environment variables
                env_vars = response['Configuration'].get('Environment', {}).get('Variables', {})
                assert 'STAGE' in env_vars, f"Function {function_name} missing STAGE environment variable"
                assert env_vars['STAGE'] == verifier.environment, f"Function {function_name} has wrong STAGE"
                
            except Exception as e:
                pytest.fail(f"Function {function_name} not found or not accessible: {e}")
    
    def test_dynamodb_table_exists(self, verifier):
        """Test that DynamoDB table is created and configured correctly."""
        table_name = verifier.config['table_name']
        
        try:
            response = verifier.dynamodb_client.describe_table(TableName=table_name)
            table = response['Table']
            
            # Check table status
            assert table['TableStatus'] == 'ACTIVE', f"Table {table_name} is not active"
            
            # Check key schema
            key_schema = {item['AttributeName']: item['KeyType'] for item in table['KeySchema']}
            assert key_schema.get('pk') == 'HASH', "Table missing hash key 'pk'"
            assert key_schema.get('sk') == 'RANGE', "Table missing range key 'sk'"
            
            # Check TTL configuration
            ttl_response = verifier.dynamodb_client.describe_time_to_live(TableName=table_name)
            assert ttl_response['TimeToLiveDescription']['TimeToLiveStatus'] == 'ENABLED', "TTL not enabled"
            
            # Check GSI
            gsi_names = [gsi['IndexName'] for gsi in table.get('GlobalSecondaryIndexes', [])]
            assert 'DataSourceIndex' in gsi_names, "DataSourceIndex GSI not found"
            
        except Exception as e:
            pytest.fail(f"DynamoDB table {table_name} verification failed: {e}")
    
    def test_sns_topics_exist(self, verifier):
        """Test that SNS topics are created."""
        try:
            topics_response = verifier.sns_client.list_topics()
            topic_arns = [topic['TopicArn'] for topic in topics_response['Topics']]
            
            for expected_topic in verifier.config['sns_topics']:
                matching_topics = [arn for arn in topic_arns if expected_topic in arn]
                assert len(matching_topics) > 0, f"SNS topic {expected_topic} not found"
                
                # Check topic attributes
                topic_arn = matching_topics[0]
                attributes = verifier.sns_client.get_topic_attributes(TopicArn=topic_arn)
                assert 'DisplayName' in attributes['Attributes'], f"Topic {expected_topic} missing display name"
                
        except Exception as e:
            pytest.fail(f"SNS topics verification failed: {e}")
    
    def test_cloudwatch_log_groups_exist(self, verifier):
        """Test that CloudWatch log groups are created."""
        expected_log_groups = [
            f"/aws/lambda/boom-bust-sentinel-{verifier.environment}-bond-issuance",
            f"/aws/lambda/boom-bust-sentinel-{verifier.environment}-bdc-discount",
            f"/aws/lambda/boom-bust-sentinel-{verifier.environment}-credit-fund",
            f"/aws/lambda/boom-bust-sentinel-{verifier.environment}-bank-provision"
        ]
        
        try:
            logs_client = boto3.client('logs', region_name=verifier.aws_region)
            
            for log_group_name in expected_log_groups:
                response = logs_client.describe_log_groups(logGroupNamePrefix=log_group_name)
                matching_groups = [lg for lg in response['logGroups'] if lg['logGroupName'] == log_group_name]
                assert len(matching_groups) > 0, f"Log group {log_group_name} not found"
                
                # Check retention policy
                log_group = matching_groups[0]
                assert 'retentionInDays' in log_group, f"Log group {log_group_name} missing retention policy"
                
        except Exception as e:
            pytest.fail(f"CloudWatch log groups verification failed: {e}")

class TestFunctionality:
    """Test application functionality."""
    
    @pytest.fixture(scope="class")
    def verifier(self, request):
        environment = "staging" if request.config.getoption("--staging") else "production"
        return DeploymentVerifier(environment)
    
    def test_lambda_function_invocation(self, verifier):
        """Test that Lambda functions can be invoked successfully."""
        test_functions = [
            f"boom-bust-sentinel-{verifier.environment}-bond-issuance",
            f"boom-bust-sentinel-{verifier.environment}-bdc-discount"
        ]
        
        for function_name in test_functions:
            try:
                # Create test payload
                test_payload = {
                    'source': 'deployment-test',
                    'detail-type': 'Deployment Verification',
                    'detail': {
                        'test': True,
                        'timestamp': datetime.now(timezone.utc).isoformat()
                    }
                }
                
                # Invoke function
                response = verifier.lambda_client.invoke(
                    FunctionName=function_name,
                    InvocationType='RequestResponse',
                    Payload=json.dumps(test_payload)
                )
                
                # Check response
                assert response['StatusCode'] == 200, f"Function {function_name} returned status {response['StatusCode']}"
                assert 'FunctionError' not in response, f"Function {function_name} returned error: {response.get('FunctionError')}"
                
                # Parse payload
                payload = json.loads(response['Payload'].read())
                assert isinstance(payload, dict), f"Function {function_name} returned invalid payload"
                
            except Exception as e:
                pytest.fail(f"Function {function_name} invocation failed: {e}")
    
    def test_dynamodb_read_write(self, verifier):
        """Test DynamoDB read/write operations."""
        table_name = verifier.config['table_name']
        
        # Test data
        test_item = {
            'pk': {'S': 'test-deployment'},
            'sk': {'S': f'verification-{int(time.time())}'},
            'data_source': {'S': 'deployment-test'},
            'timestamp': {'S': datetime.now(timezone.utc).isoformat()},
            'value': {'N': '123.45'},
            'metadata': {'S': json.dumps({'test': True})},
            'ttl': {'N': str(int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()))}
        }
        
        try:
            # Write test item
            verifier.dynamodb_client.put_item(
                TableName=table_name,
                Item=test_item
            )
            
            # Read test item
            response = verifier.dynamodb_client.get_item(
                TableName=table_name,
                Key={
                    'pk': test_item['pk'],
                    'sk': test_item['sk']
                }
            )
            
            assert 'Item' in response, "Test item not found after write"
            assert response['Item']['value']['N'] == '123.45', "Test item value incorrect"
            
            # Clean up test item
            verifier.dynamodb_client.delete_item(
                TableName=table_name,
                Key={
                    'pk': test_item['pk'],
                    'sk': test_item['sk']
                }
            )
            
        except Exception as e:
            pytest.fail(f"DynamoDB read/write test failed: {e}")
    
    def test_sns_message_publishing(self, verifier):
        """Test SNS message publishing."""
        try:
            # Find alert topic
            topics_response = verifier.sns_client.list_topics()
            alert_topic_arn = None
            
            for topic in topics_response['Topics']:
                if f"boom-bust-sentinel-{verifier.environment}-alerts" in topic['TopicArn']:
                    alert_topic_arn = topic['TopicArn']
                    break
            
            assert alert_topic_arn is not None, "Alert topic not found"
            
            # Publish test message
            test_message = {
                'alert_type': 'deployment_test',
                'message': 'Deployment verification test message',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'environment': verifier.environment
            }
            
            response = verifier.sns_client.publish(
                TopicArn=alert_topic_arn,
                Message=json.dumps(test_message),
                Subject='Deployment Verification Test'
            )
            
            assert 'MessageId' in response, "SNS message publishing failed"
            
        except Exception as e:
            pytest.fail(f"SNS message publishing test failed: {e}")

class TestDashboard:
    """Test web dashboard functionality."""
    
    @pytest.fixture(scope="class")
    def verifier(self, request):
        environment = "staging" if request.config.getoption("--staging") else "production"
        return DeploymentVerifier(environment)
    
    def test_dashboard_accessibility(self, verifier):
        """Test that dashboard is accessible."""
        dashboard_url = verifier.config['dashboard_url']
        
        if dashboard_url.startswith('http://localhost'):
            pytest.skip("Skipping localhost dashboard test in deployment verification")
        
        try:
            response = requests.get(dashboard_url, timeout=10)
            assert response.status_code == 200, f"Dashboard returned status {response.status_code}"
            assert 'text/html' in response.headers.get('content-type', ''), "Dashboard not returning HTML"
            
        except requests.exceptions.RequestException as e:
            pytest.fail(f"Dashboard accessibility test failed: {e}")
    
    def test_api_endpoints(self, verifier):
        """Test API endpoints."""
        dashboard_url = verifier.config['dashboard_url']
        
        if dashboard_url.startswith('http://localhost'):
            pytest.skip("Skipping localhost API test in deployment verification")
        
        api_endpoints = [
            '/api/system/health',
            '/api/metrics/current',
            '/health'
        ]
        
        for endpoint in api_endpoints:
            try:
                response = requests.get(f"{dashboard_url}{endpoint}", timeout=10)
                assert response.status_code in [200, 401], f"API endpoint {endpoint} returned status {response.status_code}"
                
                if response.status_code == 200:
                    # Try to parse JSON response
                    try:
                        data = response.json()
                        assert isinstance(data, dict), f"API endpoint {endpoint} not returning valid JSON"
                    except json.JSONDecodeError:
                        # Some endpoints might return plain text
                        pass
                        
            except requests.exceptions.RequestException as e:
                pytest.fail(f"API endpoint {endpoint} test failed: {e}")

class TestMonitoring:
    """Test monitoring and observability."""
    
    @pytest.fixture(scope="class")
    def verifier(self, request):
        environment = "staging" if request.config.getoption("--staging") else "production"
        return DeploymentVerifier(environment)
    
    def test_cloudwatch_metrics(self, verifier):
        """Test that CloudWatch metrics are being generated."""
        # Check for Lambda metrics
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=24)
        
        function_name = f"boom-bust-sentinel-{verifier.environment}-bond-issuance"
        
        try:
            response = verifier.cloudwatch_client.get_metric_statistics(
                Namespace='AWS/Lambda',
                MetricName='Invocations',
                Dimensions=[
                    {'Name': 'FunctionName', 'Value': function_name}
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,
                Statistics=['Sum']
            )
            
            # We don't require metrics to exist (functions might not have been invoked yet)
            # but the API call should succeed
            assert 'Datapoints' in response, "CloudWatch metrics API not responding correctly"
            
        except Exception as e:
            pytest.fail(f"CloudWatch metrics test failed: {e}")
    
    def test_cloudwatch_alarms(self, verifier):
        """Test that CloudWatch alarms are configured."""
        try:
            response = verifier.cloudwatch_client.describe_alarms(
                AlarmNamePrefix=f"boom-bust-sentinel-{verifier.environment}"
            )
            
            alarms = response['MetricAlarms']
            
            # We expect at least some alarms to be configured
            expected_alarm_types = ['error-rate', 'duration']
            found_alarm_types = set()
            
            for alarm in alarms:
                for alarm_type in expected_alarm_types:
                    if alarm_type in alarm['AlarmName']:
                        found_alarm_types.add(alarm_type)
            
            # At least one type of alarm should be configured
            assert len(found_alarm_types) > 0, "No CloudWatch alarms found"
            
        except Exception as e:
            pytest.fail(f"CloudWatch alarms test failed: {e}")

def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--production",
        action="store_true",
        default=False,
        help="Run tests in production environment"
    )
    parser.addoption(
        "--staging",
        action="store_true",
        default=False,
        help="Run tests in staging environment"
    )

def pytest_configure(config):
    """Configure pytest for deployment verification."""
    # Add custom markers
    config.addinivalue_line("markers", "staging: mark test to run only in staging environment")
    config.addinivalue_line("markers", "production: mark test to run only in production environment")

def pytest_collection_modifyitems(config, items):
    """Modify test collection based on environment."""
    if config.getoption("--staging"):
        # Skip production-only tests
        skip_production = pytest.mark.skip(reason="Skipping production test in staging environment")
        for item in items:
            if "production" in item.keywords:
                item.add_marker(skip_production)
    elif config.getoption("--production"):
        # Skip staging-only tests
        skip_staging = pytest.mark.skip(reason="Skipping staging test in production environment")
        for item in items:
            if "staging" in item.keywords:
                item.add_marker(skip_staging)

if __name__ == '__main__':
    # Allow running as script
    pytest.main([__file__] + sys.argv[1:])