"""
AWS Lambda handler for Credit Fund Scraper.

This handler provides the AWS Lambda entry point for the private credit fund monitoring scraper.
It includes timeout handling, error logging, and CloudWatch integration.
"""

import json
import logging
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
    from scrapers.credit_fund_scraper import CreditFundScraper
except ImportError as e:
    logger.error(f"Failed to import CreditFundScraper: {e}")
    CreditFundScraper = None


class CreditFundHandler(BaseLambdaHandler):
    """Handler for credit fund scraper Lambda function."""
    
    def __init__(self):
        super().__init__(CreditFundScraper, "credit fund")
    
    def get_data_summary(self, result_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract credit fund specific summary data."""
        return {
            'average_gross_assets': result_data.get('value', 0),
            'total_gross_assets': result_data.get('total_gross_assets', 0),
            'funds_processed': result_data.get('funds_processed', 0),
            'confidence': result_data.get('confidence', 0)
        }
    
    def get_chunk_config(self) -> Optional[Dict[str, Any]]:
        """Configuration for chunked credit fund processing."""
        return {
            'items_attr': 'CREDIT_FUND_CIKS',
            'default_chunk_size': 2,
            'item_name': 'fund'
        }


# Create handler instance
_handler = CreditFundHandler()

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
