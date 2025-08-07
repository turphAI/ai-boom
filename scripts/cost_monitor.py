#!/usr/bin/env python3
"""
AWS cost monitoring script for Boom-Bust Sentinel
This script monitors AWS costs and alerts when thresholds are exceeded.
"""

import os
import sys
import json
import boto3
from datetime import datetime, timedelta
from typing import Dict, List, Any

class CostMonitor:
    def __init__(self):
        self.aws_region = os.getenv("AWS_REGION", "us-east-1")
        self.cost_threshold = float(os.getenv("COST_THRESHOLD", "100"))  # Default $100
        
        # AWS clients
        self.ce_client = boto3.client('ce', region_name='us-east-1')  # Cost Explorer is only in us-east-1
        self.cloudwatch_client = boto3.client('cloudwatch', region_name=self.aws_region)
        
    def get_current_month_costs(self) -> Dict[str, Any]:
        """Get current month's costs."""
        # Get current month date range
        now = datetime.utcnow()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        try:
            response = self.ce_client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_of_month.strftime('%Y-%m-%d'),
                    'End': now.strftime('%Y-%m-%d')
                },
                Granularity='MONTHLY',
                Metrics=['BlendedCost'],
                GroupBy=[
                    {
                        'Type': 'DIMENSION',
                        'Key': 'SERVICE'
                    }
                ]
            )
            
            results = response['ResultsByTime']
            if not results:
                return {'total_cost': 0, 'services': {}}
            
            # Parse results
            total_cost = 0
            services = {}
            
            for group in results[0]['Groups']:
                service_name = group['Keys'][0]
                cost = float(group['Metrics']['BlendedCost']['Amount'])
                
                if cost > 0:  # Only include services with actual costs
                    services[service_name] = cost
                    total_cost += cost
            
            return {
                'total_cost': total_cost,
                'services': services,
                'period': {
                    'start': start_of_month.strftime('%Y-%m-%d'),
                    'end': now.strftime('%Y-%m-%d')
                }
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'total_cost': 0,
                'services': {}
            }
    
    def get_last_month_costs(self) -> Dict[str, Any]:
        """Get last month's costs for comparison."""
        now = datetime.utcnow()
        
        # Calculate last month's date range
        first_day_current_month = now.replace(day=1)
        last_day_last_month = first_day_current_month - timedelta(days=1)
        first_day_last_month = last_day_last_month.replace(day=1)
        
        try:
            response = self.ce_client.get_cost_and_usage(
                TimePeriod={
                    'Start': first_day_last_month.strftime('%Y-%m-%d'),
                    'End': first_day_current_month.strftime('%Y-%m-%d')
                },
                Granularity='MONTHLY',
                Metrics=['BlendedCost'],
                GroupBy=[
                    {
                        'Type': 'DIMENSION',
                        'Key': 'SERVICE'
                    }
                ]
            )
            
            results = response['ResultsByTime']
            if not results:
                return {'total_cost': 0, 'services': {}}
            
            # Parse results
            total_cost = 0
            services = {}
            
            for group in results[0]['Groups']:
                service_name = group['Keys'][0]
                cost = float(group['Metrics']['BlendedCost']['Amount'])
                
                if cost > 0:
                    services[service_name] = cost
                    total_cost += cost
            
            return {
                'total_cost': total_cost,
                'services': services,
                'period': {
                    'start': first_day_last_month.strftime('%Y-%m-%d'),
                    'end': first_day_current_month.strftime('%Y-%m-%d')
                }
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'total_cost': 0,
                'services': {}
            }
    
    def get_daily_costs(self, days: int = 7) -> Dict[str, Any]:
        """Get daily costs for the last N days."""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        try:
            response = self.ce_client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                Granularity='DAILY',
                Metrics=['BlendedCost']
            )
            
            daily_costs = []
            for result in response['ResultsByTime']:
                date = result['TimePeriod']['Start']
                cost = float(result['Total']['BlendedCost']['Amount'])
                daily_costs.append({
                    'date': date,
                    'cost': cost
                })
            
            return {
                'daily_costs': daily_costs,
                'average_daily_cost': sum(item['cost'] for item in daily_costs) / len(daily_costs) if daily_costs else 0,
                'total_cost': sum(item['cost'] for item in daily_costs)
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'daily_costs': [],
                'average_daily_cost': 0,
                'total_cost': 0
            }
    
    def get_boom_bust_sentinel_costs(self) -> Dict[str, Any]:
        """Get costs specifically for Boom-Bust Sentinel resources."""
        now = datetime.utcnow()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        try:
            # Get costs filtered by resource tags
            response = self.ce_client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_of_month.strftime('%Y-%m-%d'),
                    'End': now.strftime('%Y-%m-%d')
                },
                Granularity='MONTHLY',
                Metrics=['BlendedCost'],
                GroupBy=[
                    {
                        'Type': 'DIMENSION',
                        'Key': 'SERVICE'
                    }
                ],
                Filter={
                    'Or': [
                        {
                            'Dimensions': {
                                'Key': 'RESOURCE_ID',
                                'Values': ['boom-bust-sentinel*']
                            }
                        },
                        {
                            'Tags': {
                                'Key': 'Project',
                                'Values': ['boom-bust-sentinel']
                            }
                        }
                    ]
                }
            )
            
            results = response['ResultsByTime']
            if not results:
                return {'total_cost': 0, 'services': {}}
            
            # Parse results
            total_cost = 0
            services = {}
            
            for group in results[0]['Groups']:
                service_name = group['Keys'][0]
                cost = float(group['Metrics']['BlendedCost']['Amount'])
                
                if cost > 0:
                    services[service_name] = cost
                    total_cost += cost
            
            return {
                'total_cost': total_cost,
                'services': services,
                'period': {
                    'start': start_of_month.strftime('%Y-%m-%d'),
                    'end': now.strftime('%Y-%m-%d')
                }
            }
            
        except Exception as e:
            # Fallback: estimate based on known resource patterns
            return self._estimate_project_costs()
    
    def _estimate_project_costs(self) -> Dict[str, Any]:
        """Estimate project costs based on service usage patterns."""
        # This is a fallback method when tag-based filtering doesn't work
        current_month = self.get_current_month_costs()
        
        # Estimate based on typical serverless application patterns
        estimated_services = {}
        estimated_total = 0
        
        # Lambda costs (typically small)
        if 'AWS Lambda' in current_month['services']:
            lambda_cost = current_month['services']['AWS Lambda']
            # Assume our project is a small portion of total Lambda usage
            estimated_lambda = min(lambda_cost * 0.1, 10.0)  # Max $10 for Lambda
            estimated_services['AWS Lambda'] = estimated_lambda
            estimated_total += estimated_lambda
        
        # DynamoDB costs
        if 'Amazon DynamoDB' in current_month['services']:
            dynamodb_cost = current_month['services']['Amazon DynamoDB']
            estimated_dynamodb = min(dynamodb_cost * 0.2, 20.0)  # Max $20 for DynamoDB
            estimated_services['Amazon DynamoDB'] = estimated_dynamodb
            estimated_total += estimated_dynamodb
        
        # SNS costs (typically very small)
        if 'Amazon Simple Notification Service' in current_month['services']:
            sns_cost = current_month['services']['Amazon Simple Notification Service']
            estimated_sns = min(sns_cost * 0.1, 2.0)  # Max $2 for SNS
            estimated_services['Amazon Simple Notification Service'] = estimated_sns
            estimated_total += estimated_sns
        
        # CloudWatch costs
        if 'Amazon CloudWatch' in current_month['services']:
            cloudwatch_cost = current_month['services']['Amazon CloudWatch']
            estimated_cloudwatch = min(cloudwatch_cost * 0.1, 5.0)  # Max $5 for CloudWatch
            estimated_services['Amazon CloudWatch'] = estimated_cloudwatch
            estimated_total += estimated_cloudwatch
        
        return {
            'total_cost': estimated_total,
            'services': estimated_services,
            'estimated': True,
            'period': current_month.get('period', {})
        }
    
    def send_cost_metric(self, cost_data: Dict[str, Any]) -> None:
        """Send cost metrics to CloudWatch."""
        try:
            # Send total cost metric
            self.cloudwatch_client.put_metric_data(
                Namespace='BoomBustSentinel/Costs',
                MetricData=[
                    {
                        'MetricName': 'TotalMonthlyCost',
                        'Value': cost_data['total_cost'],
                        'Unit': 'None',
                        'Timestamp': datetime.utcnow()
                    }
                ]
            )
            
            # Send per-service metrics
            for service, cost in cost_data.get('services', {}).items():
                # Clean service name for metric name
                metric_name = service.replace(' ', '').replace('-', '')
                
                self.cloudwatch_client.put_metric_data(
                    Namespace='BoomBustSentinel/Costs',
                    MetricData=[
                        {
                            'MetricName': f'{metric_name}Cost',
                            'Value': cost,
                            'Unit': 'None',
                            'Timestamp': datetime.utcnow()
                        }
                    ]
                )
                
        except Exception as e:
            print(f"⚠️  Failed to send cost metrics: {e}")
    
    def run_cost_monitoring(self) -> Dict[str, Any]:
        """Run comprehensive cost monitoring."""
        print(f"💰 Running cost monitoring")
        print(f"   Threshold: ${self.cost_threshold}")
        print(f"   Timestamp: {datetime.utcnow().isoformat()}Z")
        print()
        
        # Get cost data
        current_month = self.get_current_month_costs()
        last_month = self.get_last_month_costs()
        daily_costs = self.get_daily_costs()
        project_costs = self.get_boom_bust_sentinel_costs()
        
        # Calculate projections
        days_in_month = datetime.utcnow().day
        days_remaining = 31 - days_in_month  # Rough estimate
        
        if daily_costs['average_daily_cost'] > 0:
            projected_monthly_cost = current_month['total_cost'] + (daily_costs['average_daily_cost'] * days_remaining)
        else:
            projected_monthly_cost = current_month['total_cost']
        
        # Calculate month-over-month change
        if last_month['total_cost'] > 0:
            mom_change = ((current_month['total_cost'] - last_month['total_cost']) / last_month['total_cost']) * 100
        else:
            mom_change = 0
        
        results = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'threshold': self.cost_threshold,
            'current_month': current_month,
            'last_month': last_month,
            'daily_costs': daily_costs,
            'project_costs': project_costs,
            'projected_monthly_cost': projected_monthly_cost,
            'month_over_month_change': mom_change,
            'alerts': []
        }
        
        # Check for alerts
        if current_month['total_cost'] > self.cost_threshold:
            results['alerts'].append({
                'type': 'threshold_exceeded',
                'message': f"Current month costs (${current_month['total_cost']:.2f}) exceed threshold (${self.cost_threshold})",
                'severity': 'high'
            })
        
        if projected_monthly_cost > self.cost_threshold:
            results['alerts'].append({
                'type': 'projected_threshold_exceeded',
                'message': f"Projected monthly costs (${projected_monthly_cost:.2f}) will exceed threshold (${self.cost_threshold})",
                'severity': 'medium'
            })
        
        if mom_change > 50:  # 50% increase
            results['alerts'].append({
                'type': 'high_growth',
                'message': f"Costs increased by {mom_change:.1f}% compared to last month",
                'severity': 'medium'
            })
        
        if daily_costs['average_daily_cost'] > self.cost_threshold / 10:  # More than 10% of monthly threshold per day
            results['alerts'].append({
                'type': 'high_daily_cost',
                'message': f"Average daily cost (${daily_costs['average_daily_cost']:.2f}) is unusually high",
                'severity': 'low'
            })
        
        # Send metrics to CloudWatch
        self.send_cost_metric(current_month)
        
        # Print summary
        print(f"📊 Cost Summary:")
        print(f"   Current Month: ${current_month['total_cost']:.2f}")
        print(f"   Last Month: ${last_month['total_cost']:.2f}")
        print(f"   Month-over-Month: {mom_change:+.1f}%")
        print(f"   Projected Monthly: ${projected_monthly_cost:.2f}")
        print(f"   Average Daily: ${daily_costs['average_daily_cost']:.2f}")
        
        if project_costs.get('total_cost', 0) > 0:
            print(f"   Project Costs: ${project_costs['total_cost']:.2f}")
        
        # Print top services
        if current_month['services']:
            print(f"\n🏆 Top Services:")
            sorted_services = sorted(current_month['services'].items(), key=lambda x: x[1], reverse=True)
            for service, cost in sorted_services[:5]:
                print(f"   {service}: ${cost:.2f}")
        
        # Print alerts
        if results['alerts']:
            print(f"\n🚨 Alerts:")
            for alert in results['alerts']:
                severity_emoji = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}
                print(f"   {severity_emoji.get(alert['severity'], '⚪')} {alert['message']}")
        else:
            print(f"\n✅ No cost alerts")
        
        return results

def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Boom-Bust Sentinel Cost Monitor')
    parser.add_argument('--threshold', '-t', type=float, 
                       help='Cost threshold in USD (overrides COST_THRESHOLD env var)')
    parser.add_argument('--output', '-o', help='Output file for results (JSON)')
    parser.add_argument('--fail-on-threshold', action='store_true',
                       help='Exit with error code if threshold is exceeded')
    
    args = parser.parse_args()
    
    # Override threshold if provided
    if args.threshold:
        os.environ['COST_THRESHOLD'] = str(args.threshold)
    
    # Run cost monitoring
    monitor = CostMonitor()
    results = monitor.run_cost_monitoring()
    
    # Save results if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n💾 Results saved to: {args.output}")
    
    # Exit with appropriate code
    if args.fail_on_threshold:
        high_severity_alerts = [alert for alert in results['alerts'] if alert['severity'] == 'high']
        
        if high_severity_alerts:
            print(f"\n❌ Cost monitoring failed: {len(high_severity_alerts)} high-severity alerts")
            sys.exit(1)
    
    print(f"\n✅ Cost monitoring completed")
    sys.exit(0)

if __name__ == '__main__':
    main()