"""
AWS Lambda handler for Bond Issuance Scraper.

This handler provides the AWS Lambda entry point for the bond issuance monitoring scraper.
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
    from scrapers.bond_issuance_scraper import BondIssuanceScraper
    logger.info("Successfully imported BondIssuanceScraper")
except ImportError as e:
    logger.error(f"Failed to import BondIssuanceScraper: {e}")
    BondIssuanceScraper = None


class BondIssuanceHandler(BaseLambdaHandler):
    """Handler for bond issuance scraper Lambda function."""
    
    def __init__(self):
        super().__init__(BondIssuanceScraper, "bond issuance")
    
    def get_data_summary(self, result_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract bond issuance specific summary data."""
        return {
            'total_issuance': result_data.get('value', 0),
            'companies_count': len(result_data.get('metadata', {}).get('companies', [])),
            'bond_count': result_data.get('metadata', {}).get('bond_count', 0),
            'confidence': result_data.get('confidence', 0)
        }
    
    def get_chunk_config(self) -> Optional[Dict[str, Any]]:
        """Configuration for chunked bond processing."""
        return {
            'items_attr': 'TECH_COMPANY_CIKS',
            'default_chunk_size': 10,
            'item_name': 'company'
        }


# Create handler instance
_handler = BondIssuanceHandler()

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
