"""
CloudWatch Events integration for scheduled scraper execution.

This module provides utilities for managing CloudWatch Events rules and targets
for scheduled execution of the Boom-Bust Sentinel scrapers.
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class CloudWatchScheduler:
    """Manages CloudWatch Events rules for scraper scheduling."""
    
    def __init__(self, region_name: str = 'us-east-1'):
        self.events_client = boto3.client('events', region_name=region_name)
        self.lambda_client = boto3.client('lambda', region_name=region_name)
        
    def create_scraper_schedule(self, 
                               scraper_name: str,
                               lambda_function_arn: str,
                               schedule_expression: str,
                               description: str = None) -> bool:
        """
        Create a CloudWatch Events rule to schedule a scraper.
        
        Args:
            scraper_name: Name of the scraper (e.g., 'bond-issuance')
            lambda_function_arn: ARN of the Lambda function to invoke
            schedule_expression: Cron or rate expression (e.g., 'cron(0 6 * * ? *)')
            description: Optional description for the rule
            
        Returns:
            bool: True if successful, False otherwise
        """
        rule_name = f"boom-bust-{scraper_name}-schedule"
        
        try:
            # Create the CloudWatch Events rule
            response = self.events_client.put_rule(
                Name=rule_name,
                ScheduleExpression=schedule_expression,
                Description=description or f"Scheduled execution for {scraper_name} scraper",
                State='ENABLED'
            )
            
            rule_arn = response['RuleArn']
            logger.info(f"Created CloudWatch Events rule: {rule_name}")
            
            # Add the Lambda function as a target
            self.events_client.put_targets(
                Rule=rule_name,
                Targets=[
                    {
                        'Id': '1',
                        'Arn': lambda_function_arn,
                        'Input': json.dumps({
                            'source': 'aws.events',
                            'detail-type': 'Scheduled Event',
                            'detail': {
                                'scraper_name': scraper_name,
                                'scheduled_time': datetime.utcnow().isoformat()
                            }
                        })
                    }
                ]
            )
            
            logger.info(f"Added Lambda target to rule: {rule_name}")
            
            # Add permission for CloudWatch Events to invoke the Lambda function
            try:
                self.lambda_client.add_permission(
                    FunctionName=lambda_function_arn,
                    StatementId=f"allow-cloudwatch-{scraper_name}",
                    Action='lambda:InvokeFunction',
                    Principal='events.amazonaws.com',
                    SourceArn=rule_arn
                )
                logger.info(f"Added CloudWatch Events permission to Lambda function")
            except ClientError as e:
                if e.response['Error']['Code'] == 'ResourceConflictException':
                    logger.info("Permission already exists")
                else:
                    raise
            
            return True
            
        except ClientError as e:
            logger.error(f"Failed to create schedule for {scraper_name}: {e}")
            return False
    
    def update_scraper_schedule(self, 
                               scraper_name: str,
                               schedule_expression: str) -> bool:
        """
        Update the schedule expression for an existing scraper rule.
        
        Args:
            scraper_name: Name of the scraper
            schedule_expression: New cron or rate expression
            
        Returns:
            bool: True if successful, False otherwise
        """
        rule_name = f"boom-bust-{scraper_name}-schedule"
        
        try:
            self.events_client.put_rule(
                Name=rule_name,
                ScheduleExpression=schedule_expression,
                State='ENABLED'
            )
            
            logger.info(f"Updated schedule for {rule_name}: {schedule_expression}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to update schedule for {scraper_name}: {e}")
            return False
    
    def disable_scraper_schedule(self, scraper_name: str) -> bool:
        """
        Disable a scraper schedule without deleting it.
        
        Args:
            scraper_name: Name of the scraper
            
        Returns:
            bool: True if successful, False otherwise
        """
        rule_name = f"boom-bust-{scraper_name}-schedule"
        
        try:
            self.events_client.disable_rule(Name=rule_name)
            logger.info(f"Disabled schedule for {rule_name}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to disable schedule for {scraper_name}: {e}")
            return False
    
    def enable_scraper_schedule(self, scraper_name: str) -> bool:
        """
        Enable a previously disabled scraper schedule.
        
        Args:
            scraper_name: Name of the scraper
            
        Returns:
            bool: True if successful, False otherwise
        """
        rule_name = f"boom-bust-{scraper_name}-schedule"
        
        try:
            self.events_client.enable_rule(Name=rule_name)
            logger.info(f"Enabled schedule for {rule_name}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to enable schedule for {scraper_name}: {e}")
            return False
    
    def delete_scraper_schedule(self, scraper_name: str) -> bool:
        """
        Delete a scraper schedule completely.
        
        Args:
            scraper_name: Name of the scraper
            
        Returns:
            bool: True if successful, False otherwise
        """
        rule_name = f"boom-bust-{scraper_name}-schedule"
        
        try:
            # Remove all targets first
            targets_response = self.events_client.list_targets_by_rule(Rule=rule_name)
            if targets_response['Targets']:
                target_ids = [target['Id'] for target in targets_response['Targets']]
                self.events_client.remove_targets(
                    Rule=rule_name,
                    Ids=target_ids
                )
                logger.info(f"Removed targets from {rule_name}")
            
            # Delete the rule
            self.events_client.delete_rule(Name=rule_name)
            logger.info(f"Deleted schedule rule: {rule_name}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to delete schedule for {scraper_name}: {e}")
            return False
    
    def list_scraper_schedules(self) -> List[Dict[str, Any]]:
        """
        List all boom-bust scraper schedules.
        
        Returns:
            List of schedule information dictionaries
        """
        try:
            response = self.events_client.list_rules(
                NamePrefix='boom-bust-',
                Limit=50
            )
            
            schedules = []
            for rule in response['Rules']:
                rule_info = {
                    'name': rule['Name'],
                    'schedule_expression': rule.get('ScheduleExpression', ''),
                    'state': rule['State'],
                    'description': rule.get('Description', ''),
                    'arn': rule['Arn']
                }
                
                # Get targets for this rule
                targets_response = self.events_client.list_targets_by_rule(Rule=rule['Name'])
                rule_info['targets'] = targets_response['Targets']
                
                schedules.append(rule_info)
            
            return schedules
            
        except ClientError as e:
            logger.error(f"Failed to list scraper schedules: {e}")
            return []
    
    def get_scraper_schedule_status(self, scraper_name: str) -> Optional[Dict[str, Any]]:
        """
        Get the status of a specific scraper schedule.
        
        Args:
            scraper_name: Name of the scraper
            
        Returns:
            Dict with schedule status information, or None if not found
        """
        rule_name = f"boom-bust-{scraper_name}-schedule"
        
        try:
            response = self.events_client.describe_rule(Name=rule_name)
            
            # Get targets
            targets_response = self.events_client.list_targets_by_rule(Rule=rule_name)
            
            return {
                'name': response['Name'],
                'schedule_expression': response.get('ScheduleExpression', ''),
                'state': response['State'],
                'description': response.get('Description', ''),
                'arn': response['Arn'],
                'targets': targets_response['Targets']
            }
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                logger.info(f"Schedule not found for {scraper_name}")
                return None
            else:
                logger.error(f"Failed to get schedule status for {scraper_name}: {e}")
                return None


def setup_default_schedules(scheduler: CloudWatchScheduler, 
                           lambda_function_arns: Dict[str, str]) -> Dict[str, bool]:
    """
    Set up default schedules for all scrapers.
    
    Args:
        scheduler: CloudWatchScheduler instance
        lambda_function_arns: Dict mapping scraper names to Lambda function ARNs
        
    Returns:
        Dict mapping scraper names to success status
    """
    # Default schedule configurations
    default_schedules = {
        'bond-issuance': {
            'schedule': 'cron(0 8 ? * MON *)',  # Monday 8 AM UTC (weekly)
            'description': 'Weekly bond issuance monitoring'
        },
        'bdc-discount': {
            'schedule': 'cron(0 6 * * ? *)',  # Daily 6 AM UTC
            'description': 'Daily BDC discount-to-NAV monitoring'
        },
        'credit-fund': {
            'schedule': 'cron(0 7 1 * ? *)',  # First day of month, 7 AM UTC
            'description': 'Monthly private credit fund monitoring'
        },
        'bank-provision': {
            'schedule': 'cron(0 9 1 1,4,7,10 ? *)',  # Quarterly, 9 AM UTC
            'description': 'Quarterly bank provision monitoring'
        }
    }
    
    results = {}
    
    for scraper_name, config in default_schedules.items():
        if scraper_name in lambda_function_arns:
            success = scheduler.create_scraper_schedule(
                scraper_name=scraper_name,
                lambda_function_arn=lambda_function_arns[scraper_name],
                schedule_expression=config['schedule'],
                description=config['description']
            )
            results[scraper_name] = success
        else:
            logger.warning(f"No Lambda function ARN provided for {scraper_name}")
            results[scraper_name] = False
    
    return results


# For testing and manual execution
if __name__ == "__main__":
    # Example usage
    scheduler = CloudWatchScheduler()
    
    # Example Lambda function ARNs (replace with actual ARNs)
    lambda_arns = {
        'bond-issuance': 'arn:aws:lambda:us-east-1:123456789012:function:boom-bust-bond-issuance',
        'bdc-discount': 'arn:aws:lambda:us-east-1:123456789012:function:boom-bust-bdc-discount',
        'credit-fund': 'arn:aws:lambda:us-east-1:123456789012:function:boom-bust-credit-fund',
        'bank-provision': 'arn:aws:lambda:us-east-1:123456789012:function:boom-bust-bank-provision'
    }
    
    # Set up default schedules
    results = setup_default_schedules(scheduler, lambda_arns)
    print("Schedule setup results:", results)
    
    # List all schedules
    schedules = scheduler.list_scraper_schedules()
    print(f"Found {len(schedules)} schedules:")
    for schedule in schedules:
        print(f"  {schedule['name']}: {schedule['schedule_expression']} ({schedule['state']})")