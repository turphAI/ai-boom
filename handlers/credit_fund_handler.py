"""
AWS Lambda handler for Credit Fund Scraper.

This handler provides the AWS Lambda entry point for the private credit fund monitoring scraper.
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
    from scrapers.credit_fund_scraper import CreditFundScraper
except ImportError as e:
    logger.error(f"Failed to import CreditFundScraper: {e}")
    sys.exit(1)


class TimeoutError(Exception):
    """Custom timeout exception."""
    pass


def timeout_handler(signum, frame):
    """Signal handler for function timeout."""
    raise TimeoutError("Lambda function timeout")


def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    AWS Lambda handler for credit fund scraper.
    
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
    
    logger.info(f"Starting credit fund scraper execution (ID: {execution_id})")
    logger.info(f"Event: {json.dumps(event, default=str)}")
    logger.info(f"Timeout set to {timeout_seconds} seconds")
    
    try:
        # Initialize scraper
        scraper = CreditFundScraper()
        
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
            logger.info(f"Credit fund scraper completed successfully in {execution_time:.2f}s")
            response['body']['data_summary'] = {
                'average_gross_assets': result.data.get('value', 0),
                'total_gross_assets': result.data.get('total_gross_assets', 0),
                'funds_processed': result.data.get('funds_processed', 0),
                'confidence': result.data.get('confidence', 0)
            }
        else:
            logger.error(f"Credit fund scraper failed: {result.error}")
            response['body']['error'] = result.error
            response['statusCode'] = 500
        
        return response
        
    except TimeoutError:
        signal.alarm(0)
        error_msg = f"Credit fund scraper timed out after {timeout_seconds} seconds"
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
        error_msg = f"Unexpected error in credit fund scraper: {str(e)}"
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
    Handler for chunked processing of credit fund data.
    
    This handler can be used when the regular handler times out due to large Form PF files
    or network issues when downloading SEC data.
    """
    execution_id = context.aws_request_id if hasattr(context, 'aws_request_id') else 'local'
    chunk_size = event.get('chunk_size', 2)  # Number of funds to process per chunk
    chunk_index = event.get('chunk_index', 0)
    
    logger.info(f"Starting chunked credit fund execution (ID: {execution_id}, chunk: {chunk_index})")
    
    try:
        scraper = CreditFundScraper()
        
        # Get list of credit funds to process
        fund_ciks = list(scraper.CREDIT_FUND_CIKS.keys())
        start_idx = chunk_index * chunk_size
        end_idx = min(start_idx + chunk_size, len(fund_ciks))
        
        if start_idx >= len(fund_ciks):
            return {
                'statusCode': 200,
                'body': {
                    'success': True,
                    'message': 'All chunks processed',
                    'chunk_index': chunk_index,
                    'total_funds': len(fund_ciks)
                }
            }
        
        # Process chunk of funds
        chunk_funds = {cik: scraper.CREDIT_FUND_CIKS[cik] 
                      for cik in fund_ciks[start_idx:end_idx]}
        
        # Temporarily override the fund list for this chunk
        original_funds = scraper.CREDIT_FUND_CIKS
        scraper.CREDIT_FUND_CIKS = chunk_funds
        
        result = scraper.execute()
        
        # Restore original fund list
        scraper.CREDIT_FUND_CIKS = original_funds
        
        response = {
            'statusCode': 200,
            'body': {
                'success': result.success,
                'chunk_index': chunk_index,
                'funds_processed': list(chunk_funds.values()),
                'has_more_chunks': end_idx < len(fund_ciks),
                'next_chunk_index': chunk_index + 1 if end_idx < len(fund_ciks) else None
            }
        }
        
        if result.success:
            response['body']['chunk_data'] = {
                'chunk_average_assets': result.data.get('value', 0),
                'funds_count': result.data.get('funds_processed', 0)
            }
        else:
            response['body']['error'] = result.error
            response['statusCode'] = 500
        
        return response
        
    except Exception as e:
        error_msg = f"Error in chunked credit fund processing: {str(e)}"
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