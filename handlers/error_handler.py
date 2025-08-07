"""
Comprehensive error handling and logging for Lambda functions.

This module provides centralized error handling, logging, and monitoring
for all Boom-Bust Sentinel Lambda functions.
"""

import json
import logging
import traceback
from datetime import datetime
from typing import Dict, Any, Optional, Callable
from functools import wraps

import boto3
from botocore.exceptions import ClientError


class LambdaErrorHandler:
    """Centralized error handling for Lambda functions."""
    
    def __init__(self, function_name: str, region_name: str = 'us-east-1'):
        self.function_name = function_name
        self.cloudwatch = boto3.client('cloudwatch', region_name=region_name)
        self.sns = boto3.client('sns', region_name=region_name)
        self.logger = logging.getLogger(function_name)
        
        # Configure structured logging
        self._setup_logging()
    
    def _setup_logging(self):
        """Set up structured logging for Lambda."""
        # Create custom formatter for structured logs
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - '
            '%(funcName)s:%(lineno)d - %(message)s'
        )
        
        # Configure handler
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        
        # Set up logger
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(handler)
        
        # Prevent duplicate logs
        self.logger.propagate = False
    
    def log_execution_start(self, event: Dict[str, Any], context) -> str:
        """Log the start of Lambda execution."""
        execution_id = getattr(context, 'aws_request_id', 'local')
        
        log_data = {
            'execution_id': execution_id,
            'function_name': self.function_name,
            'event_source': event.get('source', 'unknown'),
            'event_detail_type': event.get('detail-type', 'unknown'),
            'remaining_time_ms': getattr(context, 'get_remaining_time_in_millis', lambda: 0)(),
            'memory_limit_mb': getattr(context, 'memory_limit_in_mb', 0),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        self.logger.info(f"Lambda execution started: {json.dumps(log_data)}")
        return execution_id
    
    def log_execution_end(self, execution_id: str, success: bool, 
                         execution_time: float, result_summary: Dict[str, Any] = None):
        """Log the end of Lambda execution."""
        log_data = {
            'execution_id': execution_id,
            'function_name': self.function_name,
            'success': success,
            'execution_time_seconds': execution_time,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        if result_summary:
            log_data['result_summary'] = result_summary
        
        level = logging.INFO if success else logging.ERROR
        self.logger.log(level, f"Lambda execution completed: {json.dumps(log_data)}")
    
    def handle_error(self, error: Exception, execution_id: str, 
                    context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Handle and log errors with detailed context.
        
        Args:
            error: The exception that occurred
            execution_id: Unique execution identifier
            context: Additional context information
            
        Returns:
            Standardized error response dictionary
        """
        error_type = type(error).__name__
        error_message = str(error)
        stack_trace = traceback.format_exc()
        
        # Create detailed error log
        error_log = {
            'execution_id': execution_id,
            'function_name': self.function_name,
            'error_type': error_type,
            'error_message': error_message,
            'stack_trace': stack_trace,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        if context:
            error_log['context'] = context
        
        # Log the error
        self.logger.error(f"Lambda execution error: {json.dumps(error_log, default=str)}")
        
        # Send CloudWatch metric
        self._send_error_metric(error_type)
        
        # Determine HTTP status code based on error type
        status_code = self._get_status_code_for_error(error)
        
        return {
            'statusCode': status_code,
            'body': {
                'success': False,
                'error': error_message,
                'error_type': error_type,
                'execution_id': execution_id,
                'timestamp': datetime.utcnow().isoformat()
            }
        }
    
    def _send_error_metric(self, error_type: str):
        """Send error metric to CloudWatch."""
        try:
            self.cloudwatch.put_metric_data(
                Namespace='BoomBustSentinel/Lambda',
                MetricData=[
                    {
                        'MetricName': 'Errors',
                        'Dimensions': [
                            {
                                'Name': 'FunctionName',
                                'Value': self.function_name
                            },
                            {
                                'Name': 'ErrorType',
                                'Value': error_type
                            }
                        ],
                        'Value': 1,
                        'Unit': 'Count',
                        'Timestamp': datetime.utcnow()
                    }
                ]
            )
        except Exception as e:
            self.logger.warning(f"Failed to send error metric: {e}")
    
    def _get_status_code_for_error(self, error: Exception) -> int:
        """Determine appropriate HTTP status code for error type."""
        if isinstance(error, TimeoutError):
            return 408  # Request Timeout
        elif isinstance(error, ValueError):
            return 400  # Bad Request
        elif isinstance(error, PermissionError):
            return 403  # Forbidden
        elif isinstance(error, FileNotFoundError):
            return 404  # Not Found
        elif isinstance(error, ConnectionError):
            return 503  # Service Unavailable
        else:
            return 500  # Internal Server Error
    
    def send_critical_alert(self, error: Exception, execution_id: str, 
                           sns_topic_arn: str = None):
        """Send critical error alert via SNS."""
        if not sns_topic_arn:
            # Use environment variable or default
            import os
            sns_topic_arn = os.environ.get('CRITICAL_ALERTS_SNS_TOPIC')
        
        if not sns_topic_arn:
            self.logger.warning("No SNS topic configured for critical alerts")
            return
        
        try:
            message = {
                'function_name': self.function_name,
                'execution_id': execution_id,
                'error_type': type(error).__name__,
                'error_message': str(error),
                'timestamp': datetime.utcnow().isoformat(),
                'severity': 'CRITICAL'
            }
            
            self.sns.publish(
                TopicArn=sns_topic_arn,
                Subject=f"CRITICAL: {self.function_name} Lambda Error",
                Message=json.dumps(message, indent=2)
            )
            
            self.logger.info(f"Critical alert sent for execution {execution_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to send critical alert: {e}")


def lambda_error_handler(function_name: str):
    """
    Decorator for Lambda functions to provide comprehensive error handling.
    
    Args:
        function_name: Name of the Lambda function for logging
        
    Returns:
        Decorated function with error handling
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(event: Dict[str, Any], context) -> Dict[str, Any]:
            error_handler = LambdaErrorHandler(function_name)
            execution_id = error_handler.log_execution_start(event, context)
            start_time = datetime.utcnow()
            
            try:
                # Execute the original function
                result = func(event, context)
                
                # Log successful completion
                execution_time = (datetime.utcnow() - start_time).total_seconds()
                result_summary = result.get('body', {}) if isinstance(result, dict) else {}
                error_handler.log_execution_end(
                    execution_id, True, execution_time, result_summary
                )
                
                return result
                
            except Exception as error:
                # Handle and log the error
                execution_time = (datetime.utcnow() - start_time).total_seconds()
                error_handler.log_execution_end(execution_id, False, execution_time)
                
                # Send critical alert for certain error types
                if isinstance(error, (ConnectionError, TimeoutError)):
                    error_handler.send_critical_alert(error, execution_id)
                
                return error_handler.handle_error(error, execution_id, {
                    'event': event,
                    'execution_time': execution_time
                })
        
        return wrapper
    return decorator


class MetricsCollector:
    """Collect and send custom metrics to CloudWatch."""
    
    def __init__(self, namespace: str = 'BoomBustSentinel/Lambda'):
        self.namespace = namespace
        self.cloudwatch = boto3.client('cloudwatch')
        self.logger = logging.getLogger(__name__)
    
    def send_execution_metrics(self, function_name: str, execution_time: float, 
                              success: bool, data_points: int = 0):
        """Send execution metrics to CloudWatch."""
        try:
            metrics = [
                {
                    'MetricName': 'ExecutionTime',
                    'Dimensions': [{'Name': 'FunctionName', 'Value': function_name}],
                    'Value': execution_time,
                    'Unit': 'Seconds',
                    'Timestamp': datetime.utcnow()
                },
                {
                    'MetricName': 'Executions',
                    'Dimensions': [
                        {'Name': 'FunctionName', 'Value': function_name},
                        {'Name': 'Status', 'Value': 'Success' if success else 'Error'}
                    ],
                    'Value': 1,
                    'Unit': 'Count',
                    'Timestamp': datetime.utcnow()
                }
            ]
            
            if data_points > 0:
                metrics.append({
                    'MetricName': 'DataPointsProcessed',
                    'Dimensions': [{'Name': 'FunctionName', 'Value': function_name}],
                    'Value': data_points,
                    'Unit': 'Count',
                    'Timestamp': datetime.utcnow()
                })
            
            self.cloudwatch.put_metric_data(
                Namespace=self.namespace,
                MetricData=metrics
            )
            
        except Exception as e:
            self.logger.warning(f"Failed to send execution metrics: {e}")
    
    def send_business_metrics(self, function_name: str, metrics: Dict[str, float]):
        """Send business-specific metrics to CloudWatch."""
        try:
            metric_data = []
            
            for metric_name, value in metrics.items():
                metric_data.append({
                    'MetricName': metric_name,
                    'Dimensions': [{'Name': 'FunctionName', 'Value': function_name}],
                    'Value': value,
                    'Unit': 'None',
                    'Timestamp': datetime.utcnow()
                })
            
            if metric_data:
                self.cloudwatch.put_metric_data(
                    Namespace=self.namespace,
                    MetricData=metric_data
                )
                
        except Exception as e:
            self.logger.warning(f"Failed to send business metrics: {e}")


# Example usage and testing
if __name__ == "__main__":
    # Test the error handler
    @lambda_error_handler('test-function')
    def test_lambda_handler(event, context):
        if event.get('cause_error'):
            raise ValueError("Test error")
        return {
            'statusCode': 200,
            'body': {'message': 'Success'}
        }
    
    # Mock context
    class MockContext:
        aws_request_id = "test-123"
        memory_limit_in_mb = 128
        
        def get_remaining_time_in_millis(self):
            return 300000
    
    # Test successful execution
    result = test_lambda_handler({}, MockContext())
    print("Success test:", json.dumps(result, indent=2))
    
    # Test error handling
    result = test_lambda_handler({'cause_error': True}, MockContext())
    print("Error test:", json.dumps(result, indent=2))