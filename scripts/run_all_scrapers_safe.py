#!/usr/bin/env python3
"""
Safe Scraper Runner - Ensures data scraping and storage without data loss.

This script runs all scrapers in a safe manner with:
- Data validation before storage
- Backup of existing data before updates
- Proper error handling and recovery
- Integration with both local files and PlanetScale database
"""

import sys
import os
import json
import shutil
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import traceback

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not available, skip

from scrapers.bond_issuance_scraper import BondIssuanceScraper
from scrapers.bdc_discount_scraper import BDCDiscountScraper
from scrapers.credit_fund_scraper import CreditFundScraper
from scrapers.bank_provision_scraper import BankProvisionScraper
from scrapers.market_cap_scraper import MarketCapScraper
from scrapers.ai_investment_scraper import AIInvestmentScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/scraper_safe_run.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SafeScraperRunner:
    """Safe scraper runner with data validation and backup."""
    
    def __init__(self):
        self.data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
        self.backup_dir = os.path.join(self.data_dir, 'backups')
        self.scrapers = {
            'bond_issuance': BondIssuanceScraper(),
            'bdc_discount': BDCDiscountScraper(),
            'credit_fund': CreditFundScraper(),
            'bank_provision': BankProvisionScraper(),
            'market_cap': MarketCapScraper(),
            'ai_investment': AIInvestmentScraper()
        }
        
        # Ensure directories exist
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.backup_dir, exist_ok=True)
        os.makedirs('logs', exist_ok=True)
    
    def backup_existing_data(self, scraper_name: str) -> str:
        """Backup existing data before scraping."""
        data_file = os.path.join(self.data_dir, f'{scraper_name}_data.json')
        
        if os.path.exists(data_file):
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = os.path.join(self.backup_dir, f'{scraper_name}_backup_{timestamp}.json')
            shutil.copy2(data_file, backup_file)
            logger.info(f"✅ Backed up existing data to {backup_file}")
            return backup_file
        return None
    
    def validate_data(self, data: Any, scraper_name: str) -> bool:
        """Validate scraped data before storage."""
        try:
            # Basic validation checks
            if not isinstance(data, dict):
                logger.error(f"❌ Invalid data type for {scraper_name}: expected dict, got {type(data)}")
                return False
            
            # Check required fields
            required_fields = ['value', 'confidence']
            for field in required_fields:
                if field not in data:
                    logger.error(f"❌ Missing required field '{field}' in {scraper_name} data")
                    return False
            
            # Validate value is numeric (handle string numbers)
            value = data['value']
            if isinstance(value, str):
                try:
                    value = float(value)
                except ValueError:
                    logger.error(f"❌ Invalid value type for {scraper_name}: cannot convert '{value}' to number")
                    return False
            elif not isinstance(value, (int, float)):
                logger.error(f"❌ Invalid value type for {scraper_name}: expected numeric, got {type(value)}")
                return False
            
            # Validate confidence is between 0 and 1 (handle string numbers)
            confidence = data.get('confidence', 0)
            if isinstance(confidence, str):
                try:
                    confidence = float(confidence)
                except ValueError:
                    logger.error(f"❌ Invalid confidence type for {scraper_name}: cannot convert '{confidence}' to number")
                    return False
            
            if not isinstance(confidence, (int, float)):
                logger.error(f"❌ Invalid confidence type for {scraper_name}: expected numeric, got {type(confidence)}")
                return False
                
            if not (0 <= confidence <= 1):
                logger.error(f"❌ Invalid confidence value for {scraper_name}: {confidence} (must be 0-1)")
                return False
            
            # Validate timestamp format (timestamp is optional if not present, we'll add it)
            timestamp = data.get('timestamp')
            if timestamp:
                try:
                    # Handle datetime objects
                    if isinstance(timestamp, datetime):
                        pass  # Already a datetime object, valid
                    elif isinstance(timestamp, str):
                        datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    else:
                        logger.warning(f"⚠️  Unexpected timestamp type for {scraper_name}: {type(timestamp)}")
                except (ValueError, AttributeError) as e:
                    logger.warning(f"⚠️  Invalid timestamp format for {scraper_name}: {timestamp} - {e}")
                    # Don't fail validation, we'll add timestamp if missing
            
            logger.info(f"✅ Data validation passed for {scraper_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Data validation error for {scraper_name}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def store_data_safely(self, scraper_name: str, result_data: Dict[str, Any]) -> bool:
        """Store data safely with validation and backup."""
        try:
            # Validate the data first
            if not self.validate_data(result_data, scraper_name):
                return False
            
            # Backup existing data
            backup_file = self.backup_existing_data(scraper_name)
            
            # Ensure timestamp exists in result_data
            if 'timestamp' not in result_data or not result_data.get('timestamp'):
                result_data['timestamp'] = datetime.now(timezone.utc).isoformat()
            
            # Prepare data entry
            data_entry = {
                "data_source": scraper_name,
                "metric_name": result_data.get('metric_name', 'default'),
                "timestamp": result_data.get('timestamp', datetime.now(timezone.utc).isoformat()),
                "data": result_data
            }
            
            # Read existing data or create new array
            data_file = os.path.join(self.data_dir, f'{scraper_name}_data.json')
            if os.path.exists(data_file):
                with open(data_file, 'r') as f:
                    existing_data = json.load(f)
            else:
                existing_data = []
            
            # Add new data point at the beginning
            existing_data.insert(0, data_entry)
            
            # Keep only the last 100 entries to prevent file from growing too large
            if len(existing_data) > 100:
                existing_data = existing_data[:100]
            
            # In production, prioritize PlanetScale storage
            env = os.getenv('ENVIRONMENT', 'development')
            if env == 'production':
                # Store in PlanetScale first (primary storage)
                planetscale_success = self.store_in_planetscale(scraper_name, result_data)
                if not planetscale_success:
                    logger.error(f"❌ Failed to store in PlanetScale for {scraper_name} - this is critical in production!")
                    return False
                logger.info(f"✅ Data stored successfully in PlanetScale for {scraper_name}")
            else:
                # In development, store locally and optionally try PlanetScale
                with open(data_file, 'w') as f:
                    json.dump(existing_data, f, indent=2)
                logger.info(f"✅ Data stored successfully locally for {scraper_name}")
                
                # Try to store in PlanetScale as well (optional in dev)
                self.store_in_planetscale(scraper_name, result_data)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error storing data for {scraper_name}: {e}")
            
            # Restore from backup if available
            if backup_file and os.path.exists(backup_file):
                try:
                    shutil.copy2(backup_file, data_file)
                    logger.info(f"✅ Restored data from backup for {scraper_name}")
                except Exception as restore_error:
                    logger.error(f"❌ Failed to restore from backup: {restore_error}")
            
            return False
    
    def store_in_planetscale(self, scraper_name: str, result_data: Dict[str, Any]) -> bool:
        """Store data in PlanetScale database."""
        try:
            from services.planetscale_data_service import PlanetScaleDataService
            
            # Ensure result_data is a dict, not a string
            if isinstance(result_data, str):
                try:
                    import json
                    result_data = json.loads(result_data)
                except (json.JSONDecodeError, ValueError):
                    logger.error(f"❌ result_data is a string but not valid JSON: {result_data[:100]}")
                    return False
            
            if not isinstance(result_data, dict):
                logger.error(f"❌ result_data must be a dict, got {type(result_data)}: {result_data}")
                return False
            
            service = PlanetScaleDataService()
            
            # Get metric name from result_data or use default
            metric_name = result_data.get('metric_name', 'default')
            
            # Ensure data has required fields
            if 'value' not in result_data:
                logger.error(f"❌ result_data missing 'value' field: {list(result_data.keys())}")
                return False
            
            # Store metric data (service expects data dict with value, confidence, etc.)
            success = service.store_metric_data(
                scraper_name,
                metric_name,
                result_data  # Pass the full data dict
            )
            
            if success:
                logger.info(f"✅ Data stored in PlanetScale for {scraper_name}.{metric_name}")
            else:
                logger.warning(f"⚠️  Failed to store data in PlanetScale for {scraper_name}")
            
            return success
            
        except ImportError as e:
            logger.warning(f"⚠️  PlanetScale service not available: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ PlanetScale storage error for {scraper_name}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def run_scraper_safely(self, scraper_name: str, scraper_instance) -> Dict[str, Any]:
        """Run a single scraper safely with error handling."""
        logger.info(f"🚀 Starting {scraper_name} scraper...")
        
        try:
            # Execute scraper
            result = scraper_instance.execute()
            
            if result.success:
                logger.info(f"✅ {scraper_name} scraper completed successfully")
                logger.info(f"   Value: {result.data.get('value', 'N/A')}")
                logger.info(f"   Confidence: {result.data.get('confidence', 'N/A')}")
                
                # Store data safely
                if self.store_data_safely(scraper_name, result.data):
                    return {
                        'success': True,
                        'scraper': scraper_name,
                        'value': result.data.get('value'),
                        'confidence': result.data.get('confidence'),
                        'timestamp': result.timestamp.isoformat(),
                        'execution_time': result.execution_time
                    }
                else:
                    return {
                        'success': False,
                        'scraper': scraper_name,
                        'error': 'Data storage failed'
                    }
            else:
                logger.error(f"❌ {scraper_name} scraper failed: {result.error}")
                return {
                    'success': False,
                    'scraper': scraper_name,
                    'error': result.error
                }
                
        except Exception as e:
            logger.error(f"❌ Unexpected error in {scraper_name} scraper: {e}")
            logger.error(traceback.format_exc())
            return {
                'success': False,
                'scraper': scraper_name,
                'error': str(e)
            }
    
    def run_all_scrapers(self) -> Dict[str, Any]:
        """Run all scrapers safely."""
        logger.info("🚀 Starting safe scraper run for all data sources...")
        
        results = {
            'start_time': datetime.now(timezone.utc).isoformat(),
            'scrapers': {},
            'summary': {
                'total': len(self.scrapers),
                'successful': 0,
                'failed': 0
            }
        }
        
        for scraper_name, scraper_instance in self.scrapers.items():
            result = self.run_scraper_safely(scraper_name, scraper_instance)
            results['scrapers'][scraper_name] = result
            
            if result['success']:
                results['summary']['successful'] += 1
            else:
                results['summary']['failed'] += 1
        
        results['end_time'] = datetime.now(timezone.utc).isoformat()
        
        # Save run summary
        summary_file = os.path.join(self.data_dir, 'scraper_run_summary.json')
        with open(summary_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"📊 Scraper run completed:")
        logger.info(f"   Successful: {results['summary']['successful']}/{results['summary']['total']}")
        logger.info(f"   Failed: {results['summary']['failed']}/{results['summary']['total']}")
        
        return results

def main():
    """Main execution function."""
    try:
        runner = SafeScraperRunner()
        results = runner.run_all_scrapers()
        
        # Exit with error code if any scrapers failed
        if results['summary']['failed'] > 0:
            sys.exit(1)
        else:
            sys.exit(0)
            
    except Exception as e:
        logger.error(f"❌ Fatal error in scraper runner: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()
