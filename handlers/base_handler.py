"""
Base AWS Lambda handler for all scrapers.

This module provides a base class that handles common Lambda concerns:
- Timeout handling with signal alarms
- Logging configuration
- Error handling and response formatting
- Chunked execution support for large datasets

Individual scraper handlers should inherit from BaseLambdaHandler and implement
the get_data_summary() method to customize success responses.
"""

import json
import logging
import signal
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Optional, Type

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class LambdaTimeoutError(Exception):
    """Custom timeout exception for Lambda functions."""
    pass


def timeout_handler(signum, frame):
    """Signal handler for function timeout."""
    raise LambdaTimeoutError("Lambda function timeout")


class MockContext:
    """Mock context for local testing."""
    aws_request_id = "test-request-id"
    
    def get_remaining_time_in_millis(self):
        return 900000  # 15 minutes


class BaseLambdaHandler(ABC):
    """
    Base class for AWS Lambda scraper handlers.
    
    Provides common functionality:
    - Timeout handling
    - Logging
    - Error handling
    - Response formatting
    
    Subclasses should:
    1. Set scraper_class and scraper_name in __init__
    2. Implement get_data_summary() to customize success response
    3. Optionally implement get_chunk_config() for chunked processing
    """
    
    def __init__(self, scraper_class: Optional[Type], scraper_name: str):
        """
        Initialize the handler.
        
        Args:
            scraper_class: The scraper class to instantiate (can be None if import failed)
            scraper_name: Human-readable name for logging
        """
        self.scraper_class = scraper_class
        self.scraper_name = scraper_name
        self.logger = logging.getLogger(f"handlers.{scraper_name}")
    
    @abstractmethod
    def get_data_summary(self, result_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract data summary from scraper result for the response.
        
        Args:
            result_data: The data dict from scraper result
            
        Returns:
            Dict with summary fields to include in response
        """
        pass
    
    def get_chunk_config(self) -> Optional[Dict[str, Any]]:
        """
        Get configuration for chunked execution.
        
        Returns:
            Dict with 'items_attr' (scraper attribute name containing items to process),
            'default_chunk_size', and 'item_name' (for logging), or None if chunked
            execution is not supported.
        """
        return None
    
    def handle(self, event: Dict[str, Any], context) -> Dict[str, Any]:
        """
        Main Lambda handler entry point.
        
        Args:
            event: Lambda event data
            context: Lambda context object
            
        Returns:
            Dict containing execution results
        """
        # Set up timeout handling (leave 30 seconds buffer for cleanup)
        timeout_seconds = getattr(context, 'get_remaining_time_in_millis', lambda: 900000)() // 1000 - 30
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(max(1, timeout_seconds))
        
        execution_id = context.aws_request_id if hasattr(context, 'aws_request_id') else 'local'
        start_time = datetime.now(timezone.utc)
        
        self.logger.info(f"Starting {self.scraper_name} scraper execution (ID: {execution_id})")
        self.logger.info(f"Event: {json.dumps(event, default=str)}")
        self.logger.info(f"Timeout set to {timeout_seconds} seconds")
        
        try:
            # Check if scraper is available
            if self.scraper_class is None:
                self.logger.error(f"{self.scraper_name} scraper not available due to import error")
                return {
                    'statusCode': 500,
                    'body': {
                        'error': 'Import error',
                        'message': f'{self.scraper_name} scraper not available'
                    }
                }
            
            # Initialize and execute scraper
            scraper = self.scraper_class()
            result = scraper.execute()
            
            # Cancel timeout alarm
            signal.alarm(0)
            
            execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()
            
            response = {
                'statusCode': 200,
                'body': {
                    'success': result.success,
                    'data_source': result.data_source,
                    'metric_name': result.metric_name,
                    'execution_time': execution_time,
                    'timestamp': result.timestamp.isoformat(),
                    'execution_id': execution_id
                }
            }
            
            if result.success:
                self.logger.info(f"{self.scraper_name} scraper completed successfully in {execution_time:.2f}s")
                response['body']['data_summary'] = self.get_data_summary(result.data)
            else:
                self.logger.error(f"{self.scraper_name} scraper failed: {result.error}")
                response['body']['error'] = result.error
                response['statusCode'] = 500
            
            return response
            
        except LambdaTimeoutError:
            signal.alarm(0)
            error_msg = f"{self.scraper_name} scraper timed out after {timeout_seconds} seconds"
            self.logger.error(error_msg)
            
            return {
                'statusCode': 408,
                'body': {
                    'success': False,
                    'error': error_msg,
                    'execution_id': execution_id,
                    'timeout_seconds': timeout_seconds
                }
            }
            
        except Exception as e:
            signal.alarm(0)
            error_msg = f"Unexpected error in {self.scraper_name} scraper: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            
            return {
                'statusCode': 500,
                'body': {
                    'success': False,
                    'error': error_msg,
                    'execution_id': execution_id,
                    'error_type': type(e).__name__
                }
            }
    
    def handle_chunked(self, event: Dict[str, Any], context) -> Dict[str, Any]:
        """
        Handler for chunked processing of large datasets.
        
        Args:
            event: Lambda event data (should include chunk_size and chunk_index)
            context: Lambda context object
            
        Returns:
            Dict containing chunk execution results
        """
        chunk_config = self.get_chunk_config()
        if chunk_config is None:
            return {
                'statusCode': 400,
                'body': {
                    'success': False,
                    'error': f'Chunked execution not supported for {self.scraper_name}'
                }
            }
        
        execution_id = context.aws_request_id if hasattr(context, 'aws_request_id') else 'local'
        chunk_size = event.get('chunk_size', chunk_config['default_chunk_size'])
        chunk_index = event.get('chunk_index', 0)
        
        self.logger.info(f"Starting chunked {self.scraper_name} execution (ID: {execution_id}, chunk: {chunk_index})")
        
        try:
            if self.scraper_class is None:
                return {
                    'statusCode': 500,
                    'body': {
                        'error': 'Import error',
                        'message': f'{self.scraper_name} scraper not available'
                    }
                }
            
            scraper = self.scraper_class()
            
            # Get items to process
            items_dict = getattr(scraper, chunk_config['items_attr'])
            item_keys = list(items_dict.keys())
            start_idx = chunk_index * chunk_size
            end_idx = min(start_idx + chunk_size, len(item_keys))
            
            if start_idx >= len(item_keys):
                return {
                    'statusCode': 200,
                    'body': {
                        'success': True,
                        'message': 'All chunks processed',
                        'chunk_index': chunk_index,
                        f'total_{chunk_config["item_name"]}s': len(item_keys)
                    }
                }
            
            # Process chunk
            chunk_items = {key: items_dict[key] for key in item_keys[start_idx:end_idx]}
            
            # Temporarily override the items for this chunk
            original_items = getattr(scraper, chunk_config['items_attr'])
            setattr(scraper, chunk_config['items_attr'], chunk_items)
            
            result = scraper.execute()
            
            # Restore original items
            setattr(scraper, chunk_config['items_attr'], original_items)
            
            response = {
                'statusCode': 200,
                'body': {
                    'success': result.success,
                    'chunk_index': chunk_index,
                    f'{chunk_config["item_name"]}s_processed': list(chunk_items.values()),
                    'has_more_chunks': end_idx < len(item_keys),
                    'next_chunk_index': chunk_index + 1 if end_idx < len(item_keys) else None
                }
            }
            
            if result.success:
                response['body']['chunk_data'] = self.get_data_summary(result.data)
            else:
                response['body']['error'] = result.error
                response['statusCode'] = 500
            
            return response
            
        except Exception as e:
            error_msg = f"Error in chunked {self.scraper_name} processing: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            
            return {
                'statusCode': 500,
                'body': {
                    'success': False,
                    'error': error_msg,
                    'chunk_index': chunk_index
                }
            }


def create_lambda_handler(handler_instance: BaseLambdaHandler) -> Callable:
    """
    Create a Lambda-compatible handler function from a handler instance.
    
    Args:
        handler_instance: Instance of BaseLambdaHandler subclass
        
    Returns:
        Lambda handler function
    """
    def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
        return handler_instance.handle(event, context)
    return lambda_handler


def create_chunked_handler(handler_instance: BaseLambdaHandler) -> Callable:
    """
    Create a Lambda-compatible chunked handler function from a handler instance.
    
    Args:
        handler_instance: Instance of BaseLambdaHandler subclass
        
    Returns:
        Lambda chunked handler function
    """
    def chunked_execution_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
        return handler_instance.handle_chunked(event, context)
    return chunked_execution_handler

