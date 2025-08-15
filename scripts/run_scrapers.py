#!/usr/bin/env python3
"""
Run all scrapers to generate real data for the dashboard.
"""

import sys
import os
import time
import logging
from datetime import datetime, timezone

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.bond_issuance_scraper import BondIssuanceScraper
from scrapers.bdc_discount_scraper import BDCDiscountScraper
from scrapers.credit_fund_scraper import CreditFundScraper
from scrapers.bank_provision_scraper import BankProvisionScraper
from services.state_store import StateStore
from utils.logging_config import setup_logging

def main():
    """Run all scrapers and generate real data."""
    setup_logging("INFO")
    logger = logging.getLogger(__name__)
    
    logger.info("🚀 Starting Boom-Bust Sentinel scrapers...")
    
    # Initialize state store
    state_store = StateStore()
    
    # Define scrapers
    scrapers = {
        'bond_issuance': BondIssuanceScraper(),
        'bdc_discount': BDCDiscountScraper(),
        'credit_fund': CreditFundScraper(),
        'bank_provision': BankProvisionScraper()
    }
    
    results = {}
    
    # Run each scraper
    for name, scraper in scrapers.items():
        logger.info(f"📊 Running {name} scraper...")
        
        try:
            start_time = time.time()
            result = scraper.execute()
            execution_time = time.time() - start_time
            
            results[name] = {
                'success': result.success,
                'execution_time': execution_time,
                'data': result.data,
                'error': result.error
            }
            
            if result.success:
                logger.info(f"✅ {name} scraper completed successfully in {execution_time:.2f}s")
                if result.data:
                    logger.info(f"   Data: {result.data.get('value', 'N/A')}")
            else:
                logger.warning(f"⚠️ {name} scraper failed: {result.error}")
                
        except Exception as e:
            logger.error(f"❌ {name} scraper error: {e}")
            results[name] = {
                'success': False,
                'execution_time': 0,
                'data': None,
                'error': str(e)
            }
    
    # Summary
    successful = sum(1 for r in results.values() if r['success'])
    total = len(results)
    
    logger.info(f"\n📋 Scraper Summary:")
    logger.info(f"   Successful: {successful}/{total}")
    logger.info(f"   Failed: {total - successful}/{total}")
    
    for name, result in results.items():
        status = "✅" if result['success'] else "❌"
        logger.info(f"   {status} {name}: {result['execution_time']:.2f}s")
    
    logger.info("\n🎉 Scrapers completed! Dashboard should now show real data.")
    logger.info("   Start the dashboard: npm run dev")
    logger.info("   Then visit: http://localhost:3000")

if __name__ == "__main__":
    main()
