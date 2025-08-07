#!/usr/bin/env python3
"""
Lambda-specific health check script for Boom-Bust Sentinel
This script performs detailed health checks on Lambda functions.
"""

import os
import sys
import json
import boto3
from datetime import datetime, timedelta
from typing import Dict, List, Any

class LambdaHealthChecker:
    def __init__(self, environment: str = "prod"):
        self.environment = environment
        self.aws_region = os.getenv("AWS_REGION", "us-east-1")
        
        # AWS clients
        self.lambda_client = boto3.client('lambda', region_name=self.aws_region)
        self.cloudwatch_client = boto3.client('cloudwatch', region_name=self.aws_region)
        self.logs_client = boto3.client('logs', region_name=self.aws_region)
        
    def get_function_names(self) -> List[str]:
        """Get all Lambda function names for this environment."""
        return [
            f"boom-bust-sentinel-{self.environment}-bond-issuance",
            f"boom-bust-sentinel-{self.environment}-bdc-discount",
            f"boom-bust-sentinel-{self.environment}-credit-fund",
            f"boom-bust-sentinel-{self.environment}-bank-provision",
            f"boom-bust-sentinel-{self.environment}-bond-issuance-chunked",
            f"boom-bust-sentinel-{self.environment}-bdc-discount-chunked",
            f"boom-bust-sentinel-{self.environment}-credit-fund-chunked",
            f"boom-bust-sentinel-{self.environment}-bank-provision-chunked"
        ]
    
    def check_function_configuration(self, function_name: str) -> Dict[str, Any]:
        """Check Lambda function configuration."""
        try:
            response = self.lambda_client.get_function(FunctionName=function_name)
            config = response['Configuration']
            
            return {
                'status': 'healthy' if config['State'] == 'Active' else 'unhealthy',
                'state': config['State'],
                'runtime': config['Runtime'],
                'memory_size': config['MemorySize'],
                'timeout': config['Timeout'],
                'last_modified': config['LastModified'],
                'code_size': config['CodeSize'],
                'environment_variables': len(config.get('Environment', {}).get('Variables', {}))
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def get_function_metrics(self, function_name: str, hours: int = 24) -> Dict[str, Any]:
        """Get CloudWatch metrics for a Lambda function."""
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        
        metrics_to_check = [
            'Invocations',
            'Errors',
            'Duration',
            'Throttles',
            'ConcurrentExecutions'
        ]
        
        results = {}
        
        for metric_name in metrics_to_check:
            try:
                response = self.cloudwatch_client.get_metric_statistics(
                    Namespace='AWS/Lambda',
                    MetricName=metric_name,
                    Dimensions=[
                        {'Name': 'FunctionName', 'Value': function_name}
                    ],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=3600,  # 1 hour periods
                    Statistics=['Sum', 'Average', 'Maximum'] if metric_name == 'Duration' else ['Sum']
                )
                
                datapoints = response['Datapoints']
                if datapoints:
                    if metric_name == 'Duration':
                        results[metric_name] = {
                            'average': sum(point['Average'] for point in datapoints) / len(datapoints),
                            'maximum': max(point['Maximum'] for point in datapoints),
                            'datapoints': len(datapoints)
                        }
                    else:
                        results[metric_name] = {
                            'total': sum(point['Sum'] for point in datapoints),
                            'datapoints': len(datapoints)
                        }
                else:
                    results[metric_name] = {
                        'total': 0,
                        'datapoints': 0
                    }
                    
            except Exception as e:
                results[metric_name] = {
                    'error': str(e)
                }
        
        return results
    
    def check_recent_logs(self, function_name: str, hours: int = 1) -> Dict[str, Any]:
        """Check recent logs for errors and warnings."""
        log_group_name = f"/aws/lambda/{function_name}"
        
        try:
            end_time = int(datetime.utcnow().timestamp() * 1000)
            start_time = int((datetime.utcnow() - timedelta(hours=hours)).timestamp() * 1000)
            
            # Get recent log events
            response = self.logs_client.filter_log_events(
                logGroupName=log_group_name,
                startTime=start_time,
                endTime=end_time,
                limit=100
            )
            
            events = response.get('events', [])
            
            # Analyze log events
            error_count = 0
            warning_count = 0
            timeout_count = 0
            memory_errors = 0
            
            for event in events:
                message = event['message'].lower()
                
                if 'error' in message or 'exception' in message or 'traceback' in message:
                    error_count += 1
                elif 'warning' in message or 'warn' in message:
                    warning_count += 1
                elif 'task timed out' in message:
                    timeout_count += 1
                elif 'memory' in message and ('limit' in message or 'exceeded' in message):
                    memory_errors += 1
            
            return {
                'status': 'healthy' if error_count == 0 and timeout_count == 0 else 'unhealthy',
                'total_events': len(events),
                'error_count': error_count,
                'warning_count': warning_count,
                'timeout_count': timeout_count,
                'memory_errors': memory_errors,
                'recent_events': [
                    {
                        'timestamp': datetime.fromtimestamp(event['timestamp'] / 1000).isoformat(),
                        'message': event['message'][:200] + '...' if len(event['message']) > 200 else event['message']
                    }
                    for event in events[-5:]  # Last 5 events
                ]
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def test_function_invocation(self, function_name: str) -> Dict[str, Any]:
        """Test function invocation with a health check payload."""
        try:
            # Create a test payload
            test_payload = {
                'source': 'health-check',
                'detail-type': 'Health Check',
                'detail': {
                    'test': True,
                    'timestamp': datetime.utcnow().isoformat()
                }
            }
            
            # Invoke function
            response = self.lambda_client.invoke(
                FunctionName=function_name,
                InvocationType='RequestResponse',
                Payload=json.dumps(test_payload)
            )
            
            # Parse response
            status_code = response['StatusCode']
            payload = json.loads(response['Payload'].read())
            
            return {
                'status': 'healthy' if status_code == 200 and not response.get('FunctionError') else 'unhealthy',
                'status_code': status_code,
                'execution_duration': response.get('ExecutedVersion', 'Unknown'),
                'function_error': response.get('FunctionError'),
                'response_payload': payload if isinstance(payload, dict) else str(payload)[:200]
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def analyze_function_health(self, function_name: str) -> Dict[str, Any]:
        """Perform comprehensive health analysis for a function."""
        print(f"  🔍 Analyzing {function_name}...")
        
        # Get configuration
        config_check = self.check_function_configuration(function_name)
        
        # Get metrics
        metrics = self.get_function_metrics(function_name)
        
        # Check logs
        log_check = self.check_recent_logs(function_name)
        
        # Test invocation (skip for chunked functions to avoid unnecessary executions)
        if 'chunked' not in function_name:
            invocation_test = self.test_function_invocation(function_name)
        else:
            invocation_test = {'status': 'skipped', 'reason': 'Chunked function - skipping test invocation'}
        
        # Calculate health score
        health_factors = []
        
        # Configuration health
        if config_check['status'] == 'healthy':
            health_factors.append(1.0)
        else:
            health_factors.append(0.0)
        
        # Metrics health
        if 'Errors' in metrics and 'Invocations' in metrics:
            total_invocations = metrics['Invocations'].get('total', 0)
            total_errors = metrics['Errors'].get('total', 0)
            
            if total_invocations > 0:
                error_rate = total_errors / total_invocations
                health_factors.append(1.0 - min(error_rate * 10, 1.0))  # Penalize high error rates
            else:
                health_factors.append(0.5)  # Neutral if no invocations
        
        # Log health
        if log_check['status'] == 'healthy':
            health_factors.append(1.0)
        elif log_check['status'] == 'error':
            health_factors.append(0.0)
        else:
            # Partial health based on error count
            error_count = log_check.get('error_count', 0)
            health_factors.append(max(0.0, 1.0 - error_count * 0.1))
        
        # Invocation test health
        if invocation_test['status'] == 'healthy':
            health_factors.append(1.0)
        elif invocation_test['status'] == 'skipped':
            health_factors.append(0.8)  # Neutral but slightly lower
        else:
            health_factors.append(0.0)
        
        overall_health_score = sum(health_factors) / len(health_factors) * 100
        
        # Determine overall status
        if overall_health_score >= 90:
            overall_status = 'healthy'
        elif overall_health_score >= 70:
            overall_status = 'degraded'
        else:
            overall_status = 'unhealthy'
        
        result = {
            'overall_status': overall_status,
            'health_score': overall_health_score,
            'configuration': config_check,
            'metrics': metrics,
            'logs': log_check,
            'invocation_test': invocation_test
        }
        
        # Print summary
        status_emoji = {
            'healthy': '✅',
            'degraded': '⚠️',
            'unhealthy': '❌',
            'error': '💥'
        }
        
        print(f"    {status_emoji.get(overall_status, '❓')} Status: {overall_status.upper()} (Score: {overall_health_score:.1f}%)")
        
        if metrics.get('Invocations', {}).get('total', 0) > 0:
            invocations = metrics['Invocations']['total']
            errors = metrics.get('Errors', {}).get('total', 0)
            error_rate = (errors / invocations * 100) if invocations > 0 else 0
            print(f"    📊 Invocations: {invocations}, Errors: {errors} ({error_rate:.1f}%)")
        
        if 'Duration' in metrics:
            avg_duration = metrics['Duration'].get('average', 0)
            max_duration = metrics['Duration'].get('maximum', 0)
            print(f"    ⏱️  Duration: Avg {avg_duration:.0f}ms, Max {max_duration:.0f}ms")
        
        return result
    
    def run_lambda_health_check(self) -> Dict[str, Any]:
        """Run comprehensive Lambda health check."""
        print(f"🔧 Running Lambda health check for environment: {self.environment}")
        print(f"   Region: {self.aws_region}")
        print(f"   Timestamp: {datetime.utcnow().isoformat()}Z")
        print()
        
        function_names = self.get_function_names()
        results = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'environment': self.environment,
            'region': self.aws_region,
            'functions': {}
        }
        
        # Check each function
        for function_name in function_names:
            results['functions'][function_name] = self.analyze_function_health(function_name)
        
        # Calculate overall Lambda health
        all_scores = [func['health_score'] for func in results['functions'].values()]
        overall_score = sum(all_scores) / len(all_scores) if all_scores else 0
        
        healthy_functions = sum(1 for func in results['functions'].values() if func['overall_status'] == 'healthy')
        total_functions = len(results['functions'])
        
        if overall_score >= 90:
            overall_status = 'healthy'
        elif overall_score >= 70:
            overall_status = 'degraded'
        else:
            overall_status = 'unhealthy'
        
        results['overall_status'] = overall_status
        results['overall_score'] = overall_score
        results['healthy_functions'] = healthy_functions
        results['total_functions'] = total_functions
        
        print()
        print(f"📊 Lambda Health Summary:")
        print(f"   Overall Status: {overall_status.upper()}")
        print(f"   Overall Score: {overall_score:.1f}%")
        print(f"   Healthy Functions: {healthy_functions}/{total_functions}")
        
        return results

def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Boom-Bust Sentinel Lambda Health Check')
    parser.add_argument('--environment', '-e', default='prod', 
                       choices=['dev', 'staging', 'prod'],
                       help='Environment to check (default: prod)')
    parser.add_argument('--function', '-f', help='Check specific function only')
    parser.add_argument('--output', '-o', help='Output file for results (JSON)')
    parser.add_argument('--fail-on-unhealthy', action='store_true',
                       help='Exit with error code if any function is unhealthy')
    
    args = parser.parse_args()
    
    # Run health check
    checker = LambdaHealthChecker(environment=args.environment)
    
    if args.function:
        # Check single function
        result = checker.analyze_function_health(args.function)
        results = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'environment': args.environment,
            'region': checker.aws_region,
            'functions': {args.function: result}
        }
    else:
        # Check all functions
        results = checker.run_lambda_health_check()
    
    # Save results if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n💾 Results saved to: {args.output}")
    
    # Exit with appropriate code
    if args.fail_on_unhealthy:
        unhealthy_functions = [
            name for name, func in results['functions'].items() 
            if func['overall_status'] in ['unhealthy', 'error']
        ]
        
        if unhealthy_functions:
            print(f"\n❌ Health check failed: {len(unhealthy_functions)} unhealthy functions")
            for func_name in unhealthy_functions:
                print(f"   - {func_name}")
            sys.exit(1)
    
    print(f"\n✅ Lambda health check completed")
    sys.exit(0)

if __name__ == '__main__':
    main()