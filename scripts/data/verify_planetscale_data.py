#!/usr/bin/env python3
"""
Verify that scraped data was successfully stored in PlanetScale.
This script checks for recent data and reports on data freshness.
"""

import os
import sys
from datetime import datetime, timezone, timedelta

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def verify_data_storage():
    """Verify that data was stored in PlanetScale."""
    print("=" * 60)
    print("VERIFYING PLANETSCALE DATA STORAGE")
    print("=" * 60)
    print()
    
    # Check environment
    database_url = os.getenv('DATABASE_URL', '')
    if not database_url:
        print("❌ ERROR: DATABASE_URL environment variable not set")
        print("   Cannot verify data storage without database connection")
        sys.exit(1)
    
    env = os.getenv('ENVIRONMENT', 'development')
    print(f"Environment: {env}")
    print()
    
    try:
        from services.planetscale_data_service import PlanetScaleDataService
        service = PlanetScaleDataService()
        
        # Expected scrapers
        expected_scrapers = {
            'bond_issuance': 'weekly',
            'bdc_discount': 'daily',
            'credit_fund': 'monthly',
            'bank_provision': 'quarterly'
        }
        
        print("Checking for recent data from each scraper:")
        print()
        
        all_fresh = True
        now = datetime.now(timezone.utc)
        
        for scraper_name, frequency in expected_scrapers.items():
            # Get latest metrics for this scraper
            metrics = service.get_latest_metrics(scraper_name)
            
            if not metrics:
                print(f"❌ {scraper_name}: No data found")
                all_fresh = False
                continue
            
            # Find the most recent metric
            most_recent = None
            most_recent_time = None
            
            for metric in metrics:
                updated_at = metric.get('updatedAt')
                if updated_at:
                    try:
                        if isinstance(updated_at, str):
                            updated_dt = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                        else:
                            updated_dt = updated_at
                        
                        if updated_dt.tzinfo is None:
                            updated_dt = updated_dt.replace(tzinfo=timezone.utc)
                        
                        if most_recent_time is None or updated_dt > most_recent_time:
                            most_recent_time = updated_dt
                            most_recent = metric
                    except Exception as e:
                        continue
            
            if most_recent and most_recent_time:
                age = now - most_recent_time
                value = most_recent.get('value', 'N/A')
                
                # Determine if data is fresh based on frequency
                if frequency == 'daily':
                    fresh_threshold = timedelta(days=2)
                elif frequency == 'weekly':
                    fresh_threshold = timedelta(days=8)
                elif frequency == 'monthly':
                    fresh_threshold = timedelta(days=35)
                elif frequency == 'quarterly':
                    fresh_threshold = timedelta(days=100)
                else:
                    fresh_threshold = timedelta(days=7)
                
                if age < fresh_threshold:
                    print(f"✅ {scraper_name}: Data is fresh (updated {age.days} days ago, value: {value})")
                else:
                    print(f"⚠️  {scraper_name}: Data is stale (updated {age.days} days ago, value: {value})")
                    all_fresh = False
            else:
                print(f"❌ {scraper_name}: Could not determine data age")
                all_fresh = False
        
        print()
        
        if all_fresh:
            print("✅ All scrapers have fresh data in PlanetScale!")
            return True
        else:
            print("⚠️  Some scrapers have stale or missing data")
            print("   This may indicate scrapers are not running or data storage is failing")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: Failed to verify data storage: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function."""
    success = verify_data_storage()
    
    if success:
        print()
        print("=" * 60)
        print("VERIFICATION PASSED")
        print("=" * 60)
        sys.exit(0)
    else:
        print()
        print("=" * 60)
        print("VERIFICATION FAILED")
        print("=" * 60)
        print()
        print("Troubleshooting steps:")
        print("1. Check GitHub Actions workflow logs")
        print("2. Verify DATABASE_URL secret is configured correctly")
        print("3. Check that scrapers completed successfully")
        print("4. Run diagnostic script: python scripts/diagnose_scraper_status.py")
        sys.exit(1)

if __name__ == "__main__":
    main()

