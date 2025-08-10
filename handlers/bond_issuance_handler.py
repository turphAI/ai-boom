"""
AWS Lambda handler for Bond Issuance Scraper.

This handler provides the AWS Lambda entry point for the bond issuance monitoring scraper.
It includes timeout handling, error logging, and CloudWatch integration.
"""

import json
import logging
import os
import signal
import sys
from datetime import datetime, timezone
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import scraper after logging setup
try:
    from scrapers.bond_issuance_scraper import BondIssuanceScraper
    logger.info("Successfully imported BondIssuanceScraper")
except ImportError as e:
    logger.error(f"Failed to import BondIssuanceScraper: {e}")
    # Don't exit, just log the error for now
    BondIssuanceScraper = None


class TimeoutError(Exception):
    """Custom timeout exception."""
    pass


def timeout_handler(signum, frame):
    """Signal handler for function timeout."""
    raise TimeoutError("Lambda function timeout")


def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    AWS Lambda handler for bond issuance scraper.
    
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
    start_time = datetime.now(timezone.utc)
    
    logger.info(f"Starting bond issuance scraper execution (ID: {execution_id})")
    logger.info(f"Event: {json.dumps(event, default=str)}")
    logger.info(f"Timeout set to {timeout_seconds} seconds")
    
    try:
        # Test if scraper is available
        if BondIssuanceScraper is None:
            logger.error("BondIssuanceScraper not available due to import error")
            return {
                'statusCode': 500,
                'body': {'error': 'Import error', 'message': 'BondIssuanceScraper not available'}
            }
        
        # Initialize scraper
        scraper = BondIssuanceScraper()
        
        # Execute scraper
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
            logger.info(f"Bond issuance scraper completed successfully in {execution_time:.2f}s")
            response['body']['data_summary'] = {
                'total_issuance': result.data.get('value', 0),
                'companies_count': len(result.data.get('metadata', {}).get('companies', [])),
                'bond_count': result.data.get('metadata', {}).get('bond_count', 0),
                'confidence': result.data.get('confidence', 0)
            }
        else:
            logger.error(f"Bond issuance scraper failed: {result.error}")
            response['body']['error'] = result.error
            response['statusCode'] = 500
        
        return response
        
    except TimeoutError:
        signal.alarm(0)
        error_msg = f"Bond issuance scraper timed out after {timeout_seconds} seconds"
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
        error_msg = f"Unexpected error in bond issuance scraper: {str(e)}"
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
    Handler for chunked processing of large datasets.
    
    This handler can be used when the regular handler times out due to large data volumes.
    It processes data in chunks and can be invoked multiple times.
    """
    execution_id = context.aws_request_id if hasattr(context, 'aws_request_id') else 'local'
    chunk_size = event.get('chunk_size', 10)  # Number of companies to process per chunk
    chunk_index = event.get('chunk_index', 0)
    
    logger.info(f"Starting chunked bond issuance execution (ID: {execution_id}, chunk: {chunk_index})")
    
    try:
        scraper = BondIssuanceScraper()
        
        # Get list of companies to process
        companies = list(scraper.TECH_COMPANY_CIKS.keys())
        start_idx = chunk_index * chunk_size
        end_idx = min(start_idx + chunk_size, len(companies))
        
        if start_idx >= len(companies):
            return {
                'statusCode': 200,
                'body': {
                    'success': True,
                    'message': 'All chunks processed',
                    'chunk_index': chunk_index,
                    'total_companies': len(companies)
                }
            }
        
        # Process chunk of companies
        chunk_companies = {cik: scraper.TECH_COMPANY_CIKS[cik] 
                          for cik in companies[start_idx:end_idx]}
        
        # Temporarily override the company list for this chunk
        original_companies = scraper.TECH_COMPANY_CIKS
        scraper.TECH_COMPANY_CIKS = chunk_companies
        
        result = scraper.execute()
        
        # Restore original company list
        scraper.TECH_COMPANY_CIKS = original_companies
        
        response = {
            'statusCode': 200,
            'body': {
                'success': result.success,
                'chunk_index': chunk_index,
                'companies_processed': list(chunk_companies.values()),
                'has_more_chunks': end_idx < len(companies),
                'next_chunk_index': chunk_index + 1 if end_idx < len(companies) else None
            }
        }
        
        if result.success:
            response['body']['chunk_data'] = {
                'total_issuance': result.data.get('value', 0),
                'bond_count': result.data.get('metadata', {}).get('bond_count', 0)
            }
        else:
            response['body']['error'] = result.error
            response['statusCode'] = 500
        
        return response
        
    except Exception as e:
        error_msg = f"Error in chunked bond issuance processing: {str(e)}"
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