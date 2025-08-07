"""
AWS Lambda handler for BDC Discount Scraper.

This handler provides the AWS Lambda entry point for the BDC discount-to-NAV monitoring scraper.
It includes timeout handling, error logging, and CloudWatch integration.
"""

import json
import logging
import os
import signal
import sys
from datetime import datetime
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import scraper after logging setup
try:
    from scrapers.bdc_discount_scraper import BDCDiscountScraper
except ImportError as e:
    logger.error(f"Failed to import BDCDiscountScraper: {e}")
    sys.exit(1)


class TimeoutError(Exception):
    """Custom timeout exception."""
    pass


def timeout_handler(signum, frame):
    """Signal handler for function timeout."""
    raise TimeoutError("Lambda function timeout")


def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    AWS Lambda handler for BDC discount scraper.
    
    Args:
        event: Lambda event data (from CloudWatch Events)
        context: Lambda context object
        
    Returns:
        Dict containing execution results
    """
    # Set up timeout handling (leave 30 seconds buffer for cleanup)
    timeout_seconds = getattr(context, 'get_remaining_time_in_millis', lambda: 900000)() // 1000 - 30
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(max(1, timeout_seconds))
    
    execution_id = context.aws_request_id if hasattr(context, 'aws_request_id') else 'local'
    start_time = datetime.utcnow()
    
    logger.info(f"Starting BDC discount scraper execution (ID: {execution_id})")
    logger.info(f"Event: {json.dumps(event, default=str)}")
    logger.info(f"Timeout set to {timeout_seconds} seconds")
    
    try:
        # Initialize scraper
        scraper = BDCDiscountScraper()
        
        # Execute scraper
        result = scraper.execute()
        
        # Cancel timeout alarm
        signal.alarm(0)
        
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        
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
            logger.info(f"BDC discount scraper completed successfully in {execution_time:.2f}s")
            response['body']['data_summary'] = {
                'average_discount': result.data.get('value', 0),
                'average_discount_percentage': result.data.get('average_discount_percentage', 0),
                'bdc_count': result.data.get('bdc_count', 0),
                'symbols_processed': result.data.get('metadata', {}).get('symbols_processed', [])
            }
        else:
            logger.error(f"BDC discount scraper failed: {result.error}")
            response['body']['error'] = result.error
            response['statusCode'] = 500
        
        return response
        
    except TimeoutError:
        signal.alarm(0)
        error_msg = f"BDC discount scraper timed out after {timeout_seconds} seconds"
        logger.error(error_msg)
        
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
        error_msg = f"Unexpected error in BDC discount scraper: {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        return {
            'statusCode': 500,
            'body': {
                'success': False,
                'error': error_msg,
                'execution_id': execution_id,
                'error_type': type(e).__name__
            }
        }


def chunked_execution_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Handler for chunked processing of BDC data.
    
    This handler can be used when the regular handler times out due to network issues
    or large numbers of BDCs to process.
    """
    execution_id = context.aws_request_id if hasattr(context, 'aws_request_id') else 'local'
    chunk_size = event.get('chunk_size', 2)  # Number of BDCs to process per chunk
    chunk_index = event.get('chunk_index', 0)
    
    logger.info(f"Starting chunked BDC discount execution (ID: {execution_id}, chunk: {chunk_index})")
    
    try:
        scraper = BDCDiscountScraper()
        
        # Get list of BDCs to process
        bdc_symbols = list(scraper.BDC_CONFIG.keys())
        start_idx = chunk_index * chunk_size
        end_idx = min(start_idx + chunk_size, len(bdc_symbols))
        
        if start_idx >= len(bdc_symbols):
            return {
                'statusCode': 200,
                'body': {
                    'success': True,
                    'message': 'All chunks processed',
                    'chunk_index': chunk_index,
                    'total_bdcs': len(bdc_symbols)
                }
            }
        
        # Process chunk of BDCs
        chunk_bdcs = {symbol: scraper.BDC_CONFIG[symbol] 
                     for symbol in bdc_symbols[start_idx:end_idx]}
        
        # Temporarily override the BDC list for this chunk
        original_bdcs = scraper.BDC_CONFIG
        scraper.BDC_CONFIG = chunk_bdcs
        
        result = scraper.execute()
        
        # Restore original BDC list
        scraper.BDC_CONFIG = original_bdcs
        
        response = {
            'statusCode': 200,
            'body': {
                'success': result.success,
                'chunk_index': chunk_index,
                'bdcs_processed': list(chunk_bdcs.keys()),
                'has_more_chunks': end_idx < len(bdc_symbols),
                'next_chunk_index': chunk_index + 1 if end_idx < len(bdc_symbols) else None
            }
        }
        
        if result.success:
            response['body']['chunk_data'] = {
                'chunk_average_discount': result.data.get('value', 0),
                'bdc_count': result.data.get('bdc_count', 0)
            }
        else:
            response['body']['error'] = result.error
            response['statusCode'] = 500
        
        return response
        
    except Exception as e:
        error_msg = f"Error in chunked BDC discount processing: {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        return {
            'statusCode': 500,
            'body': {
                'success': False,
                'error': error_msg,
                'chunk_index': chunk_index
            }
        }


# For local testing
if __name__ == "__main__":
    # Mock context for local testing
    class MockContext:
        aws_request_id = "test-request-id"
        
        def get_remaining_time_in_millis(self):
            return 900000  # 15 minutes
    
    test_event = {
        "source": "aws.events",
        "detail-type": "Scheduled Event",
        "detail": {}
    }
    
    result = lambda_handler(test_event, MockContext())
    print(json.dumps(result, indent=2, default=str))