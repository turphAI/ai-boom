"""
AWS Lambda handler for Market Cap Scraper.

This handler provides the AWS Lambda entry point for the market cap monitoring scraper.
It fetches current market capitalization data for all tracked AI datacenter companies.
"""

import json
import logging
import signal
from datetime import datetime, timezone
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import scraper after logging setup
try:
    from scrapers.market_cap_scraper import MarketCapScraper
    logger.info("Successfully imported MarketCapScraper")
except ImportError as e:
    logger.error(f"Failed to import MarketCapScraper: {e}")
    MarketCapScraper = None


class TimeoutError(Exception):
    """Custom timeout exception."""
    pass


def timeout_handler(signum, frame):
    """Signal handler for function timeout."""
    raise TimeoutError("Lambda function timeout")


def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    AWS Lambda handler for market cap scraper.
    
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
    
    logger.info(f"Starting market cap scraper execution (ID: {execution_id})")
    logger.info(f"Event: {json.dumps(event, default=str)}")
    logger.info(f"Timeout set to {timeout_seconds} seconds")
    
    try:
        # Test if scraper is available
        if MarketCapScraper is None:
            logger.error("MarketCapScraper not available due to import error")
            return {
                'statusCode': 500,
                'body': {'error': 'Import error', 'message': 'MarketCapScraper not available'}
            }
        
        # Initialize scraper
        scraper = MarketCapScraper()
        
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
            logger.info(f"Market cap scraper completed successfully in {execution_time:.2f}s")
            response['body']['data_summary'] = {
                'total_market_cap': result.data.get('total_market_cap_formatted', ''),
                'ticker_count': result.data.get('ticker_count', 0),
                'category_totals': result.data.get('category_totals', {}),
                'data_quality': result.data.get('metadata', {}).get('data_quality', 'unknown')
            }
        else:
            logger.error(f"Market cap scraper failed: {result.error}")
            response['body']['error'] = result.error
            response['statusCode'] = 500
        
        return response
        
    except TimeoutError:
        signal.alarm(0)
        error_msg = f"Market cap scraper timed out after {timeout_seconds} seconds"
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
        error_msg = f"Unexpected error in market cap scraper: {str(e)}"
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

