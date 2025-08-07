#!/usr/bin/env python3
"""
Infrastructure health check script for Boom-Bust Sentinel
This script monitors the health of all system components and reports issues.
"""

import os
import sys
import json
import time
import requests
import boto3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

class HealthChecker:
    def __init__(self, environment: str = "prod"):
        self.environment = environment
        self.aws_region = os.getenv("AWS_REGION", "us-east-1")
        self.dashboard_url = os.getenv("DASHBOARD_URL", "")
        self.grafana_api_url = os.getenv("GRAFANA_API_URL", "")
        self.grafana_api_key = os.getenv("GRAFANA_API_KEY", "")
        
        # AWS clients
        self.lambda_client = boto3.client('lambda', region_name=self.aws_region)
        self.dynamodb_client = boto3.client('dynamodb', region_name=self.aws_region)
        self.cloudwatch_client = boto3.client('cloudwatch', region_name=self.aws_region)
        self.sns_client = boto3.client('sns', region_name=self.aws_region)
        
        self.health_results = []
        
    def check_lambda_functions(self) -> Dict[str, Any]:
        """Check the health of all Lambda functions."""
        print("🔍 Checking Lambda functions...")
        
        function_names = [
            f"boom-bust-sentinel-{self.environment}-bond-issuance",
            f"boom-bust-sentinel-{self.environment}-bdc-discount",
            f"boom-bust-sentinel-{self.environment}-credit-fund",
            f"boom-bust-sentinel-{self.environment}-bank-provision"
        ]
        
        results = {}
        
        for function_name in function_names:
            try:
                # Get function configuration
                response = self.lambda_client.get_function(FunctionName=function_name)
                
                # Check if function is active
                state = response['Configuration']['State']
                last_modified = response['Configuration']['LastModified']
                
                # Get recent invocation metrics
                end_time = datetime.utcnow()
                start_time = end_time - timedelta(hours=24)
                
                metrics = self.cloudwatch_client.get_metric_statistics(
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
                
                # Get error metrics
                error_metrics = self.cloudwatch_client.get_metric_statistics(
                    Namespace='AWS/Lambda',
                    MetricName='Errors',
                    Dimensions=[
                        {'Name': 'FunctionName', 'Value': function_name}
                    ],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=3600,
                    Statistics=['Sum']
                )
                
                total_invocations = sum(point['Sum'] for point in metrics['Datapoints'])
                total_errors = sum(point['Sum'] for point in error_metrics['Datapoints'])
                error_rate = (total_errors / total_invocations * 100) if total_invocations > 0 else 0
                
                results[function_name] = {
                    'status': 'healthy' if state == 'Active' and error_rate < 5 else 'unhealthy',
                    'state': state,
                    'last_modified': last_modified,
                    'invocations_24h': total_invocations,
                    'errors_24h': total_errors,
                    'error_rate': error_rate
                }
                
                if results[function_name]['status'] == 'healthy':
                    print(f"  ✅ {function_name}: Healthy")
                else:
                    print(f"  ❌ {function_name}: Unhealthy (Error rate: {error_rate:.1f}%)")
                    
            except Exception as e:
                results[function_name] = {
                    'status': 'error',
                    'error': str(e)
                }
                print(f"  ❌ {function_name}: Error - {e}")
        
        return results
    
    def check_dynamodb_table(self) -> Dict[str, Any]:
        """Check DynamoDB table health."""
        print("🔍 Checking DynamoDB table...")
        
        table_name = f"boom-bust-sentinel-{self.environment}-state"
        
        try:
            response = self.dynamodb_client.describe_table(TableName=table_name)
            table_status = response['Table']['TableStatus']
            item_count = response['Table']['ItemCount']
            table_size = response['Table']['TableSizeBytes']
            
            # Check recent read/write activity
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=1)
            
            read_metrics = self.cloudwatch_client.get_metric_statistics(
                Namespace='AWS/DynamoDB',
                MetricName='ConsumedReadCapacityUnits',
                Dimensions=[
                    {'Name': 'TableName', 'Value': table_name}
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=300,
                Statistics=['Sum']
            )
            
            write_metrics = self.cloudwatch_client.get_metric_statistics(
                Namespace='AWS/DynamoDB',
                MetricName='ConsumedWriteCapacityUnits',
                Dimensions=[
                    {'Name': 'TableName', 'Value': table_name}
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=300,
                Statistics=['Sum']
            )
            
            recent_reads = sum(point['Sum'] for point in read_metrics['Datapoints'])
            recent_writes = sum(point['Sum'] for point in write_metrics['Datapoints'])
            
            result = {
                'status': 'healthy' if table_status == 'ACTIVE' else 'unhealthy',
                'table_status': table_status,
                'item_count': item_count,
                'table_size_bytes': table_size,
                'recent_reads': recent_reads,
                'recent_writes': recent_writes
            }
            
            if result['status'] == 'healthy':
                print(f"  ✅ {table_name}: Healthy ({item_count} items, {table_size} bytes)")
            else:
                print(f"  ❌ {table_name}: Unhealthy (Status: {table_status})")
            
            return result
            
        except Exception as e:
            result = {
                'status': 'error',
                'error': str(e)
            }
            print(f"  ❌ {table_name}: Error - {e}")
            return result
    
    def check_dashboard_health(self) -> Dict[str, Any]:
        """Check web dashboard health."""
        print("🔍 Checking web dashboard...")
        
        if not self.dashboard_url:
            return {
                'status': 'skipped',
                'reason': 'Dashboard URL not configured'
            }
        
        try:
            # Check main dashboard
            response = requests.get(f"{self.dashboard_url}/health", timeout=10)
            
            if response.status_code == 200:
                health_data = response.json()
                
                # Check API endpoints
                api_checks = {}
                api_endpoints = [
                    "/api/metrics/current",
                    "/api/system/health",
                    "/api/alerts/config"
                ]
                
                for endpoint in api_endpoints:
                    try:
                        api_response = requests.get(f"{self.dashboard_url}{endpoint}", timeout=5)
                        api_checks[endpoint] = {
                            'status': 'healthy' if api_response.status_code == 200 else 'unhealthy',
                            'status_code': api_response.status_code,
                            'response_time': api_response.elapsed.total_seconds()
                        }
                    except Exception as e:
                        api_checks[endpoint] = {
                            'status': 'error',
                            'error': str(e)
                        }
                
                result = {
                    'status': 'healthy',
                    'response_time': response.elapsed.total_seconds(),
                    'api_checks': api_checks,
                    'health_data': health_data
                }
                
                print(f"  ✅ Dashboard: Healthy (Response time: {result['response_time']:.2f}s)")
                
            else:
                result = {
                    'status': 'unhealthy',
                    'status_code': response.status_code,
                    'response_time': response.elapsed.total_seconds()
                }
                print(f"  ❌ Dashboard: Unhealthy (Status: {response.status_code})")
            
            return result
            
        except Exception as e:
            result = {
                'status': 'error',
                'error': str(e)
            }
            print(f"  ❌ Dashboard: Error - {e}")
            return result
    
    def check_grafana_integration(self) -> Dict[str, Any]:
        """Check Grafana Cloud integration."""
        print("🔍 Checking Grafana integration...")
        
        if not self.grafana_api_url or not self.grafana_api_key:
            return {
                'status': 'skipped',
                'reason': 'Grafana credentials not configured'
            }
        
        try:
            headers = {
                'Authorization': f'Bearer {self.grafana_api_key}',
                'Content-Type': 'application/json'
            }
            
            # Check API connectivity
            response = requests.get(
                f"{self.grafana_api_url}/org",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                org_data = response.json()
                
                # Check if dashboard exists
                dashboard_response = requests.get(
                    f"{self.grafana_api_url}/search?query=boom-bust-sentinel",
                    headers=headers,
                    timeout=10
                )
                
                dashboards = dashboard_response.json() if dashboard_response.status_code == 200 else []
                
                result = {
                    'status': 'healthy',
                    'org_name': org_data.get('name', 'Unknown'),
                    'dashboards_found': len(dashboards),
                    'response_time': response.elapsed.total_seconds()
                }
                
                print(f"  ✅ Grafana: Healthy ({len(dashboards)} dashboards found)")
                
            else:
                result = {
                    'status': 'unhealthy',
                    'status_code': response.status_code
                }
                print(f"  ❌ Grafana: Unhealthy (Status: {response.status_code})")
            
            return result
            
        except Exception as e:
            result = {
                'status': 'error',
                'error': str(e)
            }
            print(f"  ❌ Grafana: Error - {e}")
            return result
    
    def check_sns_topics(self) -> Dict[str, Any]:
        """Check SNS topics for alerting."""
        print("🔍 Checking SNS topics...")
        
        topic_names = [
            f"boom-bust-sentinel-{self.environment}-alerts",
            f"boom-bust-sentinel-{self.environment}-critical-alerts"
        ]
        
        results = {}
        
        for topic_name in topic_names:
            try:
                # List topics and find ours
                topics = self.sns_client.list_topics()
                topic_arn = None
                
                for topic in topics['Topics']:
                    if topic_name in topic['TopicArn']:
                        topic_arn = topic['TopicArn']
                        break
                
                if topic_arn:
                    # Get topic attributes
                    attributes = self.sns_client.get_topic_attributes(TopicArn=topic_arn)
                    subscription_count = int(attributes['Attributes'].get('SubscriptionsConfirmed', 0))
                    
                    results[topic_name] = {
                        'status': 'healthy',
                        'topic_arn': topic_arn,
                        'subscriptions': subscription_count
                    }
                    
                    print(f"  ✅ {topic_name}: Healthy ({subscription_count} subscriptions)")
                    
                else:
                    results[topic_name] = {
                        'status': 'not_found',
                        'error': 'Topic not found'
                    }
                    print(f"  ❌ {topic_name}: Not found")
                    
            except Exception as e:
                results[topic_name] = {
                    'status': 'error',
                    'error': str(e)
                }
                print(f"  ❌ {topic_name}: Error - {e}")
        
        return results
    
    def run_health_check(self) -> Dict[str, Any]:
        """Run complete health check."""
        print(f"🏥 Running health check for environment: {self.environment}")
        print(f"   Region: {self.aws_region}")
        print(f"   Timestamp: {datetime.utcnow().isoformat()}Z")
        print()
        
        results = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'environment': self.environment,
            'region': self.aws_region,
            'checks': {}
        }
        
        # Run all health checks
        results['checks']['lambda_functions'] = self.check_lambda_functions()
        results['checks']['dynamodb'] = self.check_dynamodb_table()
        results['checks']['dashboard'] = self.check_dashboard_health()
        results['checks']['grafana'] = self.check_grafana_integration()
        results['checks']['sns_topics'] = self.check_sns_topics()
        
        # Calculate overall health
        all_statuses = []
        for check_category in results['checks'].values():
            if isinstance(check_category, dict):
                if 'status' in check_category:
                    all_statuses.append(check_category['status'])
                else:
                    # Handle nested results (like lambda functions)
                    for item in check_category.values():
                        if isinstance(item, dict) and 'status' in item:
                            all_statuses.append(item['status'])
        
        healthy_count = all_statuses.count('healthy')
        total_count = len([s for s in all_statuses if s != 'skipped'])
        
        if total_count == 0:
            overall_status = 'unknown'
        elif healthy_count == total_count:
            overall_status = 'healthy'
        elif healthy_count >= total_count * 0.8:  # 80% healthy threshold
            overall_status = 'degraded'
        else:
            overall_status = 'unhealthy'
        
        results['overall_status'] = overall_status
        results['health_score'] = (healthy_count / total_count * 100) if total_count > 0 else 0
        
        print()
        print(f"📊 Health Check Summary:")
        print(f"   Overall Status: {overall_status.upper()}")
        print(f"   Health Score: {results['health_score']:.1f}%")
        print(f"   Healthy Components: {healthy_count}/{total_count}")
        
        return results

def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Boom-Bust Sentinel Health Check')
    parser.add_argument('--environment', '-e', default='prod', 
                       choices=['dev', 'staging', 'prod'],
                       help='Environment to check (default: prod)')
    parser.add_argument('--output', '-o', help='Output file for results (JSON)')
    parser.add_argument('--fail-on-unhealthy', action='store_true',
                       help='Exit with error code if system is unhealthy')
    
    args = parser.parse_args()
    
    # Run health check
    checker = HealthChecker(environment=args.environment)
    results = checker.run_health_check()
    
    # Save results if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n💾 Results saved to: {args.output}")
    
    # Exit with appropriate code
    if args.fail_on_unhealthy and results['overall_status'] in ['unhealthy', 'degraded']:
        print(f"\n❌ Health check failed: System is {results['overall_status']}")
        sys.exit(1)
    else:
        print(f"\n✅ Health check completed")
        sys.exit(0)

if __name__ == '__main__':
    main()