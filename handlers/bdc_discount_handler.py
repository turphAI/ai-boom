"""
AWS Lambda handler for BDC Discount Scraper.

This handler provides the AWS Lambda entry point for the BDC discount-to-NAV monitoring scraper.
It includes timeout handling, error logging, and CloudWatch integration.
"""

import json
import logging
import sys
from typing import Dict, Any, Optional

from handlers.base_handler import (
    BaseLambdaHandler,
    MockContext,
    create_lambda_handler,
    create_chunked_handler
)

logger = logging.getLogger(__name__)

# Import scraper after logging setup
try:
    from scrapers.bdc_discount_scraper import BDCDiscountScraper
except ImportError as e:
    logger.error(f"Failed to import BDCDiscountScraper: {e}")
    BDCDiscountScraper = None


class BDCDiscountHandler(BaseLambdaHandler):
    """Handler for BDC discount scraper Lambda function."""
    
    def __init__(self):
        super().__init__(BDCDiscountScraper, "BDC discount")
    
    def get_data_summary(self, result_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract BDC discount specific summary data."""
        return {
            'average_discount': result_data.get('value', 0),
            'average_discount_percentage': result_data.get('average_discount_percentage', 0),
            'bdc_count': result_data.get('bdc_count', 0),
            'symbols_processed': result_data.get('metadata', {}).get('symbols_processed', [])
        }
    
    def get_chunk_config(self) -> Optional[Dict[str, Any]]:
        """Configuration for chunked BDC processing."""
        return {
            'items_attr': 'BDC_CONFIG',
            'default_chunk_size': 2,
            'item_name': 'bdc'
        }


# Create handler instance
_handler = BDCDiscountHandler()

# Lambda entry points
lambda_handler = create_lambda_handler(_handler)
chunked_execution_handler = create_chunked_handler(_handler)


# For local testing
if __name__ == "__main__":
    test_event = {
        "source": "aws.events",
        "detail-type": "Scheduled Event",
        "detail": {}
    }
    
    result = lambda_handler(test_event, MockContext())
    print(json.dumps(result, indent=2, default=str))
