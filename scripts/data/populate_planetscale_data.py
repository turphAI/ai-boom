#!/usr/bin/env python3
"""
Script to populate PlanetScale database with sample data for testing.
This will add some metrics data so the production system health shows data.
"""

import os
import sys
import logging
from datetime import datetime, timezone

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set environment to production to use PlanetScale
os.environ['ENVIRONMENT'] = 'production'

# Get DATABASE_URL from environment or use placeholder
database_url = os.getenv('DATABASE_URL')
if not database_url:
    print("❌ DATABASE_URL environment variable not set. Cannot populate database.")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def populate_sample_data():
    """Populate PlanetScale with sample metrics data."""
    try:
        from services.planetscale_data_service import PlanetScaleDataService
        service = PlanetScaleDataService()
        
        # Sample data for each scraper
        sample_data = [
            {
                'data_source': 'bond_issuance',
                'metric_name': 'weekly_issuance',
                'data': {
                    'value': 3500000000,  # $3.5B
                    'unit': 'currency',
                    'confidence': 0.85,
                    'metadata': {
                        'companies': ['MSFT', 'META'],
                        'bond_count': 2,
                        'avg_coupon': 4.35,
                        'source': 'sec_edgar',
                        'success_rate': 1.0
                    }
                }
            },
            {
                'data_source': 'bdc_discount',
                'metric_name': 'discount_to_nav',
                'data': {
                    'value': 0.08,  # 8%
                    'unit': 'percentage',
                    'confidence': 0.90,
                    'metadata': {
                        'symbols': ['ARCC', 'OCSL', 'MAIN', 'PSEC', 'BXSL'],
                        'avg_discount': 0.08,
                        'source': 'market_data',
                        'success_rate': 1.0
                    }
                }
            },
            {
                'data_source': 'credit_fund',
                'metric_name': 'gross_asset_value',
                'data': {
                    'value': 12500000000,  # $12.5B
                    'unit': 'currency',
                    'confidence': 0.75,
                    'metadata': {
                        'fund_count': 15,
                        'avg_size': 833000000,
                        'source': 'sec_filings',
                        'success_rate': 0.8
                    }
                }
            },
            {
                'data_source': 'bank_provision',
                'metric_name': 'non_bank_financial_provisions',
                'data': {
                    'value': 850000000,  # $850M
                    'unit': 'currency',
                    'confidence': 0.88,
                    'metadata': {
                        'banks': ['JPM', 'BAC', 'WFC', 'C', 'GS', 'MS'],
                        'provision_count': 6,
                        'avg_provision': 141666667,
                        'source': 'sec_filings',
                        'success_rate': 1.0
                    }
                }
            }
        ]
        
        success_count = 0
        total_count = len(sample_data)
        
        for item in sample_data:
            logger.info(f"📊 Adding {item['data_source']}.{item['metric_name']} data...")
            success = service.store_metric_data(
                item['data_source'],
                item['metric_name'],
                item['data']
            )
            
            if success:
                success_count += 1
                logger.info(f"✅ Successfully added {item['data_source']}.{item['metric_name']}")
            else:
                logger.error(f"❌ Failed to add {item['data_source']}.{item['metric_name']}")
        
        logger.info(f"\n📈 Population Results:")
        logger.info(f"   Successful: {success_count}/{total_count}")
        logger.info(f"   Failed: {total_count - success_count}/{total_count}")
        
        if success_count == total_count:
            logger.info("🎉 All sample data added successfully!")
            return True
        else:
            logger.warning("⚠️  Some data failed to be added.")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error populating sample data: {e}")
        return False

def verify_data():
    """Verify that data was added successfully."""
    try:
        from services.planetscale_data_service import PlanetScaleDataService
        service = PlanetScaleDataService()
        
        metrics = service.get_latest_metrics()
        logger.info(f"📊 Found {len(metrics)} metrics in database")
        
        for metric in metrics:
            logger.info(f"   - {metric.get('dataSource')}.{metric.get('metricName')}: {metric.get('value')} {metric.get('unit')}")
        
        return len(metrics) > 0
        
    except Exception as e:
        logger.error(f"❌ Error verifying data: {e}")
        return False

def main():
    """Main function to populate PlanetScale database."""
    logger.info("🚀 Populating PlanetScale Database with Sample Data")
    logger.info("=" * 60)
    
    # Populate sample data
    if populate_sample_data():
        logger.info("\n🔍 Verifying data...")
        if verify_data():
            logger.info("✅ Database population completed successfully!")
            logger.info("🎯 Production system health should now show data.")
            return True
        else:
            logger.error("❌ Data verification failed.")
            return False
    else:
        logger.error("❌ Database population failed.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)






