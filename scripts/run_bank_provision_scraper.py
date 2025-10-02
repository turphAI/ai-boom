#!/usr/bin/env python3
"""
Script to run the bank provision scraper and save data to the correct file.
This ensures the health monitoring system can detect recent data updates.
"""

import sys
import os
import json
from datetime import datetime, timezone

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.bank_provision_scraper import BankProvisionScraper

def main():
    """Run the bank provision scraper and save data."""
    print("Starting bank provision scraper...")
    
    try:
        # Initialize scraper
        scraper = BankProvisionScraper()
        
        # Execute scraper
        result = scraper.execute()
        
        if result.success:
            print(f"✅ Bank provision scraper completed successfully")
            print(f"   Total provisions: ${result.data['value']:,.0f}")
            print(f"   Banks processed: {result.data['bank_count']}")
            print(f"   Quarter: {result.data['metadata']['quarter']}")
            
            # Save data to the health monitoring file
            data_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'bank_provision_data.json')
            
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
            
        else:
            print(f"❌ Bank provision scraper failed: {result.error}")
            return 1
            
    except Exception as e:
        print(f"❌ Error running bank provision scraper: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
