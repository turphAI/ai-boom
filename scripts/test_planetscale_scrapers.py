#!/usr/bin/env python3
"""
Test script to run scrapers and populate PlanetScale database.
This script will run all scrapers and save data to PlanetScale instead of local files.
"""

import os
import sys
import logging
from datetime import datetime, timezone

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set environment to production to use PlanetScale
os.environ['ENVIRONMENT'] = 'production'
# DATABASE_URL should be set from environment variable, not hardcoded
# For testing, set it via: export DATABASE_URL="mysql://user:pass@host/db?sslaccept=strict"
database_url = os.getenv('DATABASE_URL')
if not database_url:
    raise ValueError("DATABASE_URL environment variable must be set for testing")
os.environ['DATABASE_URL'] = database_url

from scrapers.bond_issuance_scraper import BondIssuanceScraper
from scrapers.bdc_discount_scraper import BDCDiscountScraper
from scrapers.credit_fund_scraper import CreditFundScraper
from scrapers.bank_provision_scraper import BankProvisionScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_planetscale_connection():
    """Test PlanetScale connection."""
    try:
        from services.planetscale_data_service import PlanetScaleDataService
        service = PlanetScaleDataService()
        metrics = service.get_latest_metrics()
        logger.info(f"✅ PlanetScale connection successful. Found {len(metrics)} existing metrics.")
        return True
    except Exception as e:
        logger.error(f"❌ PlanetScale connection failed: {e}")
        return False

def run_scraper(scraper_class, scraper_name):
    """Run a single scraper and log results."""
    try:
        logger.info(f"🚀 Starting {scraper_name} scraper...")
        scraper = scraper_class()
        result = scraper.execute()
        
        if result.success:
            logger.info(f"✅ {scraper_name} scraper completed successfully")
            logger.info(f"   Data: {result.data}")
            logger.info(f"   Execution time: {result.execution_time:.2f}s")
        else:
            logger.error(f"❌ {scraper_name} scraper failed: {result.error}")
        
        return result.success
    except Exception as e:
        logger.error(f"❌ {scraper_name} scraper crashed: {e}")
        return False

def main():
    """Main function to test PlanetScale scrapers."""
    logger.info("🧪 Testing PlanetScale scraper integration")
    logger.info("=" * 50)
    
    # Test PlanetScale connection first
    if not test_planetscale_connection():
        logger.error("❌ Cannot proceed without PlanetScale connection")
        return False
    
    # Define scrapers to test
    scrapers = [
        (BondIssuanceScraper, "Bond Issuance"),
        (BDCDiscountScraper, "BDC Discount"),
        (CreditFundScraper, "Credit Fund"),
        (BankProvisionScraper, "Bank Provision")
    ]
    
    success_count = 0
    total_count = len(scrapers)
    
    # Run each scraper
    for scraper_class, scraper_name in scrapers:
        logger.info(f"\n📊 Testing {scraper_name} scraper...")
        if run_scraper(scraper_class, scraper_name):
            success_count += 1
        logger.info("-" * 30)
    
    # Summary
    logger.info(f"\n📈 Test Results:")
    logger.info(f"   Successful: {success_count}/{total_count}")
    logger.info(f"   Failed: {total_count - success_count}/{total_count}")
    
    if success_count == total_count:
        logger.info("🎉 All scrapers working with PlanetScale!")
        return True
    else:
        logger.warning("⚠️  Some scrapers failed. Check logs above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)