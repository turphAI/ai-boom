#!/usr/bin/env python3
"""
Sync scraped data from local JSON files to PlanetScale database.
This script reads data from the data/ directory and pushes it to PlanetScale.
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set environment to production to use PlanetScale
os.environ['ENVIRONMENT'] = 'production'

# Get DATABASE_URL from environment
database_url = os.getenv('DATABASE_URL')
if not database_url:
    print("❌ DATABASE_URL environment variable not set. Cannot sync to database.")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def read_json_file(file_path: str):
    """Read and parse a JSON file."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}")
        return None

def sync_data_to_planetscale():
    """Sync scraped data from JSON files to PlanetScale."""
    try:
        from services.planetscale_data_service import PlanetScaleDataService
        service = PlanetScaleDataService()
        
        # Define the data files to sync
        data_dir = Path(__file__).parent.parent / 'data'
        data_files = [
            'bond_issuance_weekly.json',
            'bdc_discount_discount_to_nav.json',
            'credit_fund_gross_asset_value.json',
            'bank_provision_non_bank_financial_provisions.json'
        ]
        
        success_count = 0
        total_count = 0
        
        for filename in data_files:
            file_path = data_dir / filename
            
            if not file_path.exists():
                logger.warning(f"⚠️  File not found: {file_path}")
                continue
            
            logger.info(f"📖 Reading {filename}...")
            data = read_json_file(file_path)
            
            if not data:
                logger.error(f"❌ Failed to read {filename}")
                continue
            
            # Data files contain arrays of data points
            if isinstance(data, list) and len(data) > 0:
                # Process each data point (usually we want the most recent one)
                for data_point in data:
                    total_count += 1
                    
                    data_source = data_point.get('data_source')
                    metric_name = data_point.get('metric_name')
                    metric_data = data_point.get('data', {})
                    
                    if not data_source or not metric_name:
                        logger.warning(f"⚠️  Invalid data point in {filename}, skipping")
                        continue
                    
                    logger.info(f"📊 Syncing {data_source}.{metric_name}...")
                    
                    success = service.store_metric_data(
                        data_source,
                        metric_name,
                        metric_data
                    )
                    
                    if success:
                        success_count += 1
                        value = metric_data.get('value', 'N/A')
                        logger.info(f"✅ Synced {data_source}.{metric_name}: {value}")
                    else:
                        logger.error(f"❌ Failed to sync {data_source}.{metric_name}")
        
        logger.info(f"\n📈 Sync Results:")
        logger.info(f"   Successful: {success_count}/{total_count}")
        logger.info(f"   Failed: {total_count - success_count}/{total_count}")
        
        if success_count > 0:
            logger.info("🎉 Data synced successfully!")
            return True
        else:
            logger.error("❌ No data was synced.")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error syncing data: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_sync():
    """Verify that data was synced successfully."""
    try:
        from services.planetscale_data_service import PlanetScaleDataService
        service = PlanetScaleDataService()
        
        metrics = service.get_latest_metrics()
        logger.info(f"\n🔍 Verification - Found {len(metrics)} metrics in database:")
        
        for metric in metrics:
            data_source = metric.get('dataSource', 'unknown')
            metric_name = metric.get('metricName', 'unknown')
            value = metric.get('value', 'N/A')
            unit = metric.get('unit', '')
            logger.info(f"   - {data_source}.{metric_name}: {value} {unit}")
        
        return len(metrics) > 0
        
    except Exception as e:
        logger.error(f"❌ Error verifying sync: {e}")
        return False

def main():
    """Main function to sync scraped data to PlanetScale."""
    logger.info("🚀 Syncing Scraped Data to PlanetScale Database")
    logger.info("=" * 60)
    
    # Sync data
    if sync_data_to_planetscale():
        logger.info("\n🔍 Verifying sync...")
        if verify_sync():
            logger.info("\n✅ Data sync completed successfully!")
            logger.info("🎯 Production dashboard should now show updated data.")
            return True
        else:
            logger.error("\n❌ Data verification failed.")
            return False
    else:
        logger.error("\n❌ Data sync failed.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)






