#!/usr/bin/env python3
"""
Script to run the credit fund scraper and save data to the correct file.
This ensures the health monitoring system can detect recent data updates.
"""

import sys
import os
import json
from datetime import datetime, timezone

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.credit_fund_scraper import CreditFundScraper

def main():
    """Run the credit fund scraper and save data."""
    print("Starting credit fund scraper...")
    start_time = datetime.now(timezone.utc)
    
    try:
        # Initialize scraper
        scraper = CreditFundScraper()
        
        # Execute scraper
        result = scraper.execute()
        
        if result.success:
            print(f"✅ Credit fund scraper completed successfully")
            print(f"   Average gross assets: ${result.data['value']:,.0f}")
            print(f"   Total gross assets: ${result.data['total_gross_assets']:,.0f}")
            print(f"   Funds processed: {result.data['funds_processed']}")
            
            # Store data in PlanetScale database
            try:
                from services.planetscale_data_service import PlanetScaleDataService
                db_service = PlanetScaleDataService()
                
                # Store metric data
                success = db_service.store_metric_data(
                    result.data_source,
                    result.metric_name,
                    result.data
                )
                
                # Store scraper health
                db_service.store_scraper_health(
                    'credit_fund',
                    'healthy',
                    int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)
                )
                
                if success:
                    print("✅ Data stored in PlanetScale database")
                else:
                    print("⚠️  Warning: Failed to store data in PlanetScale")
                    
            except ImportError as e:
                print(f"⚠️  Warning: Could not import PlanetScale service: {e}")
                print("   Falling back to local file storage")
                
                # Fallback to local file storage
                data_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'credit_fund_data.json')
                
                # Read existing data or create new array
                if os.path.exists(data_file):
                    with open(data_file, 'r') as f:
                        existing_data = json.load(f)
                else:
                    existing_data = []
                
                # Add new data point at the beginning
                new_entry = {
                    "data_source": result.data_source,
                    "metric_name": result.metric_name,
                    "timestamp": result.timestamp.isoformat(),
                    "data": result.data
                }
                
                existing_data.insert(0, new_entry)
                
                # Keep only the last 100 entries to prevent file from growing too large
                if len(existing_data) > 100:
                    existing_data = existing_data[:100]
                
                # Write updated data
                with open(data_file, 'w') as f:
                    json.dump(existing_data, f, indent=2)
                
                print(f"✅ Data saved to {data_file}")
                
            except Exception as e:
                print(f"❌ Error storing data: {e}")
                return 1
            
        else:
            print(f"❌ Credit fund scraper failed: {result.error}")
            return 1
            
    except Exception as e:
        print(f"❌ Error running credit fund scraper: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
