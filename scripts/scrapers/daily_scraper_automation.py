#!/usr/bin/env python3
"""
Daily Scraper Automation for Boom-Bust Sentinel
This script runs all scrapers once per day to collect fresh data.
"""

import sys
import os
import time
import logging
import json
from datetime import datetime, timezone, date

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.bond_issuance_scraper import BondIssuanceScraper
from scrapers.bdc_discount_scraper import BDCDiscountScraper
from scrapers.credit_fund_scraper import CreditFundScraper
from scrapers.bank_provision_scraper import BankProvisionScraper
from services.state_store import StateStore
from utils.logging_config import setup_logging

def setup_daily_logging():
    """Set up logging for daily automation."""
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = f"{log_dir}/daily_scraper_{datetime.now().strftime('%Y%m%d')}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger(__name__)

def run_daily_scrapers():
    """Run all scrapers for daily data collection."""
    logger = setup_daily_logging()
    
    logger.info("🚀 Starting Daily Boom-Bust Sentinel Scrapers")
    logger.info(f"   Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("   This will collect fresh data from all sources")
    logger.info("")
    
    # Initialize state store
    state_store = StateStore()
    
    # Define all scrapers
    scrapers = {
        'bond_issuance': BondIssuanceScraper(),
        'bdc_discount': BDCDiscountScraper(),
        'credit_fund': CreditFundScraper(),
        'bank_provision': BankProvisionScraper()
    }
    
    results = {}
    start_time = time.time()
    
    # Run each scraper
    for name, scraper in scrapers.items():
        logger.info(f"📊 Running {name} scraper...")
        
        try:
            scraper_start = time.time()
            result = scraper.execute()
            scraper_time = time.time() - scraper_start
            
            results[name] = {
                'success': result.success,
                'execution_time': scraper_time,
                'data': result.data,
                'error': result.error,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            if result.success:
                logger.info(f"✅ {name} scraper completed successfully in {scraper_time:.2f}s")
                if result.data:
                    value = result.data.get('value', 'N/A')
                    if isinstance(value, (int, float)):
                        logger.info(f"   Data: {value:,.2f}")
                    else:
                        logger.info(f"   Data: {value}")
            else:
                logger.warning(f"⚠️ {name} scraper failed: {result.error}")
                
        except Exception as e:
            logger.error(f"❌ {name} scraper error: {e}")
            results[name] = {
                'success': False,
                'execution_time': 0,
                'data': None,
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
    
    # Calculate summary
    total_time = time.time() - start_time
    successful = sum(1 for r in results.values() if r['success'])
    total = len(results)
    
    # Log summary
    logger.info(f"\n📋 Daily Scraper Summary:")
    logger.info(f"   Total execution time: {total_time:.2f}s")
    logger.info(f"   Successful: {successful}/{total}")
    logger.info(f"   Failed: {total - successful}/{total}")
    logger.info("")
    
    for name, result in results.items():
        status = "✅" if result['success'] else "❌"
        logger.info(f"   {status} {name}: {result['execution_time']:.2f}s")
    
    # Save results to JSON for monitoring
    results_file = f"logs/daily_results_{datetime.now().strftime('%Y%m%d')}.json"
    
    # Convert datetime objects to strings for JSON serialization
    def convert_datetime_to_string(obj):
        if isinstance(obj, dict):
            return {k: convert_datetime_to_string(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_datetime_to_string(item) for item in obj]
        elif isinstance(obj, (datetime, date)):
            return obj.isoformat()
        else:
            return obj
    
    serializable_results = convert_datetime_to_string(results)
    
    with open(results_file, 'w') as f:
        json.dump({
            'date': datetime.now().isoformat(),
            'total_execution_time': total_time,
            'successful_scrapers': successful,
            'total_scrapers': total,
            'results': serializable_results
        }, f, indent=2)
    
    logger.info(f"\n🎉 Daily scraping completed!")
    logger.info(f"   Results saved to: {results_file}")
    logger.info(f"   Dashboard will now show fresh data")
    
    return successful == total

if __name__ == "__main__":
    success = run_daily_scrapers()
    sys.exit(0 if success else 1)
