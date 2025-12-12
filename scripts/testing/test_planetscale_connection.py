#!/usr/bin/env python3
"""
Simple test script to verify PlanetScale connection and data service.
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
    # For testing, use placeholder - real credentials should come from environment
    database_url = 'mysql://username:password@host/database?ssl={"rejectUnauthorized":true}'
    print("⚠️  Using placeholder DATABASE_URL. Set DATABASE_URL environment variable for real testing.")
    
os.environ['DATABASE_URL'] = database_url

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
        
        # Print existing metrics
        for metric in metrics[:5]:  # Show first 5
            logger.info(f"   - {metric.get('dataSource')}.{metric.get('metricName')}: {metric.get('value')} {metric.get('unit')}")
        
        return True
    except Exception as e:
        logger.error(f"❌ PlanetScale connection failed: {e}")
        return False

def test_state_store():
    """Test PlanetScale state store."""
    try:
        from services.state_store import create_state_store
        state_store = create_state_store()
        logger.info(f"✅ State store created: {type(state_store).__name__}")
        return True
    except Exception as e:
        logger.error(f"❌ State store creation failed: {e}")
        return False

def test_data_insertion():
    """Test inserting test data into PlanetScale."""
    try:
        from services.planetscale_data_service import PlanetScaleDataService
        service = PlanetScaleDataService()
        
        # Create test data
        test_data = {
            'value': 1000000,
            'unit': 'currency',
            'confidence': 0.95,
            'metadata': {
                'test': True,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        }
        
        success = service.store_metric_data('test', 'test_metric', test_data)
        if success:
            logger.info("✅ Test data inserted successfully")
            return True
        else:
            logger.error("❌ Test data insertion failed")
            return False
    except Exception as e:
        logger.error(f"❌ Test data insertion crashed: {e}")
        return False

def main():
    """Main function to test PlanetScale integration."""
    logger.info("🧪 Testing PlanetScale Integration")
    logger.info("=" * 50)
    
    tests = [
        ("PlanetScale Connection", test_planetscale_connection),
        ("State Store Creation", test_state_store),
        ("Data Insertion", test_data_insertion)
    ]
    
    success_count = 0
    total_count = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n🔍 Running {test_name} test...")
        if test_func():
            success_count += 1
        logger.info("-" * 30)
    
    # Summary
    logger.info(f"\n📈 Test Results:")
    logger.info(f"   Successful: {success_count}/{total_count}")
    logger.info(f"   Failed: {total_count - success_count}/{total_count}")
    
    if success_count == total_count:
        logger.info("🎉 All PlanetScale tests passed!")
        return True
    else:
        logger.warning("⚠️  Some tests failed. Check logs above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
