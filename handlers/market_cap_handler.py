"""
AWS Lambda handler for Market Cap Scraper.

This handler provides the AWS Lambda entry point for the market cap monitoring scraper.
It fetches current market capitalization data for all tracked AI datacenter companies.
"""

import json
import logging
from typing import Dict, Any

from handlers.base_handler import (
    BaseLambdaHandler,
    MockContext,
    create_lambda_handler
)

logger = logging.getLogger(__name__)

# Import scraper after logging setup
try:
    from scrapers.market_cap_scraper import MarketCapScraper
    logger.info("Successfully imported MarketCapScraper")
except ImportError as e:
    logger.error(f"Failed to import MarketCapScraper: {e}")
    MarketCapScraper = None


class MarketCapHandler(BaseLambdaHandler):
    """Handler for market cap scraper Lambda function."""
    
    def __init__(self):
        super().__init__(MarketCapScraper, "market cap")
    
    def get_data_summary(self, result_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract market cap specific summary data."""
        return {
            'total_market_cap': result_data.get('total_market_cap_formatted', ''),
            'ticker_count': result_data.get('ticker_count', 0),
            'category_totals': result_data.get('category_totals', {}),
            'data_quality': result_data.get('metadata', {}).get('data_quality', 'unknown')
        }


# Create handler instance
_handler = MarketCapHandler()

# Lambda entry points
lambda_handler = create_lambda_handler(_handler)


# For local testing
if __name__ == "__main__":
    test_event = {
        "source": "aws.events",
        "detail-type": "Scheduled Event",
        "detail": {}
    }
    
    result = lambda_handler(test_event, MockContext())
    print(json.dumps(result, indent=2, default=str))
