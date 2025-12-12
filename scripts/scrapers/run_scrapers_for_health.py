#!/usr/bin/env python3
"""
Script to run both credit_fund and bank_provision scrapers to ensure system health.
This script should be run regularly (e.g., every hour) to keep data fresh.
"""

import sys
import os
import subprocess
from datetime import datetime

def run_scraper(script_path, scraper_name):
    """Run a scraper script and return success status."""
    print(f"\n🔄 Running {scraper_name} scraper...")
    
    try:
        result = subprocess.run([
            sys.executable, script_path
        ], capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(__file__)))
        
        if result.returncode == 0:
            print(f"✅ {scraper_name} scraper completed successfully")
            if result.stdout:
                print(f"   Output: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ {scraper_name} scraper failed")
            if result.stderr:
                print(f"   Error: {result.stderr.strip()}")
            return False
            
    except Exception as e:
        print(f"❌ Error running {scraper_name} scraper: {e}")
        return False

def main():
    """Run all scrapers to maintain system health."""
    print("🚀 Starting scraper health maintenance run...")
    print(f"   Timestamp: {datetime.now().isoformat()}")
    
    # Get script directory
    script_dir = os.path.dirname(__file__)
    
    # Define scrapers to run
    scrapers = [
        {
            'script': os.path.join(script_dir, 'run_credit_fund_scraper.py'),
            'name': 'Credit Fund'
        },
        {
            'script': os.path.join(script_dir, 'run_bank_provision_scraper.py'),
            'name': 'Bank Provision'
        }
    ]
    
    # Track results
    results = {}
    
    # Run each scraper
    for scraper in scrapers:
        success = run_scraper(scraper['script'], scraper['name'])
        results[scraper['name']] = success
    
    # Summary
    print(f"\n📊 Health Maintenance Summary:")
    successful = sum(results.values())
    total = len(results)
    
    for name, success in results.items():
        status = "✅ Healthy" if success else "❌ Failed"
        print(f"   {name}: {status}")
    
    print(f"\n   Overall: {successful}/{total} scrapers healthy")
    
    if successful == total:
        print("🎉 All scrapers are healthy!")
        return 0
    else:
        print("⚠️  Some scrapers failed - check logs for details")
        return 1

if __name__ == "__main__":
    sys.exit(main())
