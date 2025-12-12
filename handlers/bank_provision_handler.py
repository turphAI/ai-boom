"""
AWS Lambda handler for Bank Provision Scraper.

This handler provides the AWS Lambda entry point for the bank provision monitoring scraper.
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
    from scrapers.bank_provision_scraper import BankProvisionScraper
except ImportError as e:
    logger.error(f"Failed to import BankProvisionScraper: {e}")
    BankProvisionScraper = None


class BankProvisionHandler(BaseLambdaHandler):
    """Handler for bank provision scraper Lambda function."""
    
    def __init__(self):
        super().__init__(BankProvisionScraper, "bank provision")
    
    def get_data_summary(self, result_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract bank provision specific summary data."""
        return {
            'total_provisions': result_data.get('value', 0),
            'bank_count': result_data.get('bank_count', 0),
            'quarter': result_data.get('metadata', {}).get('quarter', 'Unknown'),
            'extraction_methods': result_data.get('metadata', {}).get('extraction_methods', {}),
            'confidence': result_data.get('confidence', 0)
        }
    
    def get_chunk_config(self) -> Optional[Dict[str, Any]]:
        """Configuration for chunked bank processing."""
        return {
            'items_attr': 'BANK_CIKS',
            'default_chunk_size': 2,
            'item_name': 'bank'
        }


# Create handler instance
_handler = BankProvisionHandler()

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
