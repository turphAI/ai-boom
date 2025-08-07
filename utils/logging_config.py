"""
Enhanced logging configuration with contextual information for CloudWatch/Cloud Logging.
"""

import json
import logging
import logging.config
import os
import sys
import traceback
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from functools import wraps

from config.settings import settings


class ContextualFormatter(logging.Formatter):
    """Custom formatter that adds contextual information to log records."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.environment = settings.ENVIRONMENT
    
    def format(self, record):
        # Add contextual information
        record.environment = self.environment
        record.service = 'boom-bust-sentinel'
        record.timestamp_iso = datetime.now(timezone.utc).isoformat()
        
        # Add request ID if available (for Lambda)
        if hasattr(record, 'aws_request_id'):
            record.request_id = record.aws_request_id
        
        # Add function name and line number for better debugging
        if hasattr(record, 'funcName'):
            record.function = record.funcName
        
        # Format the message
        formatted = super().format(record)
        
        return formatted


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging in cloud environments."""
    
    def __init__(self):
        super().__init__()
        self.environment = settings.ENVIRONMENT
    
    def format(self, record):
        log_entry = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'service': 'boom-bust-sentinel',
            'environment': self.environment,
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'thread': record.thread,
            'process': record.process
        }
        
        # Add exception information if present
        if record.exc_info:
            log_entry['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                          'filename', 'module', 'lineno', 'funcName', 'created', 
                          'msecs', 'relativeCreated', 'thread', 'threadName', 
                          'processName', 'process', 'getMessage', 'exc_info', 
                          'exc_text', 'stack_info']:
                log_entry[key] = value
        
        return json.dumps(log_entry, default=str)


class CloudWatchHandler(logging.Handler):
    """Custom handler for AWS CloudWatch Logs."""
    
    def __init__(self, log_group: str, log_stream: str):
        super().__init__()
        self.log_group = log_group
        self.log_stream = log_stream
        self.client = None
        
        # Initialize CloudWatch client if in AWS environment
        if os.getenv('AWS_LAMBDA_FUNCTION_NAME'):
            try:
                import boto3
                self.client = boto3.client('logs', region_name=settings.AWS_REGION)
            except ImportError:
                pass
    
    def emit(self, record):
        if not self.client:
            return
        
        try:
            log_event = {
                'timestamp': int(record.created * 1000),
                'message': self.format(record)
            }
            
            # Send to CloudWatch (simplified - in production would batch these)
            self.client.put_log_events(
                logGroupName=self.log_group,
                logStreamName=self.log_stream,
                logEvents=[log_event]
            )
        except Exception:
            # Don't let logging errors break the application
            pass


def setup_logging(log_level: str = None, use_json: bool = None) -> None:
    """Setup logging configuration based on environment."""
    if log_level is None:
        log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    
    if use_json is None:
        # Use JSON logging in production or cloud environments
        use_json = (
            settings.ENVIRONMENT == 'production' or 
            os.getenv('AWS_LAMBDA_FUNCTION_NAME') or
            os.getenv('GOOGLE_CLOUD_PROJECT')
        )
    
    # Base configuration
    config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                '()': ContextualFormatter,
                'format': '%(timestamp_iso)s - %(environment)s - %(service)s - %(name)s - %(levelname)s - %(function)s:%(lineno)d - %(message)s'
            },
            'json': {
                '()': JSONFormatter
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': log_level,
                'formatter': 'json' if use_json else 'standard',
                'stream': sys.stdout
            }
        },
        'loggers': {
            'boom_bust_sentinel': {
                'level': log_level,
                'handlers': ['console'],
                'propagate': False
            },
            'scrapers': {
                'level': log_level,
                'handlers': ['console'],
                'propagate': False
            },
            'services': {
                'level': log_level,
                'handlers': ['console'],
                'propagate': False
            },
            'handlers': {
                'level': log_level,
                'handlers': ['console'],
                'propagate': False
            }
        },
        'root': {
            'level': log_level,
            'handlers': ['console']
        }
    }
    
    # Add CloudWatch handler if in AWS Lambda
    if os.getenv('AWS_LAMBDA_FUNCTION_NAME'):
        function_name = os.getenv('AWS_LAMBDA_FUNCTION_NAME')
        config['handlers']['cloudwatch'] = {
            '()': CloudWatchHandler,
            'log_group': f'/aws/lambda/{function_name}',
            'log_stream': f'{datetime.now().strftime("%Y/%m/%d")}/[LATEST]',
            'level': log_level,
            'formatter': 'json'
        }
        
        # Add CloudWatch handler to all loggers
        for logger_config in config['loggers'].values():
            logger_config['handlers'].append('cloudwatch')
        config['root']['handlers'].append('cloudwatch')
    
    logging.config.dictConfig(config)


def get_contextual_logger(name: str, **context) -> logging.Logger:
    """Get a logger with additional context."""
    logger = logging.getLogger(name)
    
    # Add context to all log records
    old_factory = logging.getLogRecordFactory()
    
    def record_factory(*args, **kwargs):
        record = old_factory(*args, **kwargs)
        for key, value in context.items():
            setattr(record, key, value)
        return record
    
    logging.setLogRecordFactory(record_factory)
    
    return logger


def log_execution_time(logger: Optional[logging.Logger] = None):
    """Decorator to log function execution time."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = datetime.now()
            func_logger = logger or logging.getLogger(func.__module__)
            
            try:
                result = func(*args, **kwargs)
                execution_time = (datetime.now() - start_time).total_seconds()
                
                func_logger.info(
                    f"Function {func.__name__} completed successfully",
                    extra={
                        'function_name': func.__name__,
                        'execution_time_seconds': execution_time,
                        'success': True
                    }
                )
                
                return result
                
            except Exception as e:
                execution_time = (datetime.now() - start_time).total_seconds()
                
                func_logger.error(
                    f"Function {func.__name__} failed: {str(e)}",
                    extra={
                        'function_name': func.__name__,
                        'execution_time_seconds': execution_time,
                        'success': False,
                        'error_type': type(e).__name__,
                        'error_message': str(e)
                    },
                    exc_info=True
                )
                
                raise
        
        return wrapper
    return decorator


def log_scraper_execution(data_source: str, metric_name: str):
    """Decorator specifically for scraper execution logging."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = datetime.now()
            logger = logging.getLogger(f"scrapers.{data_source}")
            
            logger.info(
                f"Starting {data_source} scraper for {metric_name}",
                extra={
                    'data_source': data_source,
                    'metric_name': metric_name,
                    'scraper_function': func.__name__,
                    'start_time': start_time.isoformat()
                }
            )
            
            try:
                result = func(*args, **kwargs)
                execution_time = (datetime.now() - start_time).total_seconds()
                
                logger.info(
                    f"Scraper {data_source}.{metric_name} completed successfully",
                    extra={
                        'data_source': data_source,
                        'metric_name': metric_name,
                        'execution_time_seconds': execution_time,
                        'success': True,
                        'result_type': type(result).__name__
                    }
                )
                
                return result
                
            except Exception as e:
                execution_time = (datetime.now() - start_time).total_seconds()
                
                logger.error(
                    f"Scraper {data_source}.{metric_name} failed: {str(e)}",
                    extra={
                        'data_source': data_source,
                        'metric_name': metric_name,
                        'execution_time_seconds': execution_time,
                        'success': False,
                        'error_type': type(e).__name__,
                        'error_message': str(e),
                        'function_name': func.__name__
                    },
                    exc_info=True
                )
                
                raise
        
        return wrapper
    return decorator


class ErrorContext:
    """Context manager for adding error context to logs."""
    
    def __init__(self, logger: logging.Logger, operation: str, **context):
        self.logger = logger
        self.operation = operation
        self.context = context
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.now()
        self.logger.debug(
            f"Starting operation: {self.operation}",
            extra={
                'operation': self.operation,
                'start_time': self.start_time.isoformat(),
                **self.context
            }
        )
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        execution_time = (datetime.now() - self.start_time).total_seconds()
        
        if exc_type is None:
            self.logger.debug(
                f"Operation completed: {self.operation}",
                extra={
                    'operation': self.operation,
                    'execution_time_seconds': execution_time,
                    'success': True,
                    **self.context
                }
            )
        else:
            self.logger.error(
                f"Operation failed: {self.operation} - {str(exc_val)}",
                extra={
                    'operation': self.operation,
                    'execution_time_seconds': execution_time,
                    'success': False,
                    'error_type': exc_type.__name__,
                    'error_message': str(exc_val),
                    **self.context
                },
                exc_info=True
            )
        
        return False  # Don't suppress exceptions


# Initialize logging when module is imported
setup_logging()