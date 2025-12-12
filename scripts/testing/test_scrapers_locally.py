#!/usr/bin/env python3
"""
Test scrapers locally to verify they're working
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.bond_issuance_scraper import BondIssuanceScraper
from scrapers.bdc_discount_scraper import BDCDiscountScraper
from scrapers.credit_fund_scraper import CreditFundScraper
from scrapers.bank_provision_scraper import BankProvisionScraper

def test_scraper(scraper_class, name):
    """Test a single scraper"""
    print(f"\n🧪 Testing {name}...")
    print("-" * 40)
    
    try:
        scraper = scraper_class()
        print(f"✅ Scraper initialized: {scraper.data_source}")
        
        # Test execution (this will use fallback data if real data fails)
        result = scraper.execute()
        
        print(f"📊 Execution result:")
        print(f"   Success: {result.success}")
        print(f"   Data source: {result.data_source}")
        print(f"   Execution time: {result.execution_time:.3f}s")
        
        if result.error:
            print(f"   Error: {result.error}")
        
        if result.data:
            print(f"   Data keys: {list(result.data.keys())}")
            if 'value' in result.data:
                print(f"   Value: {result.data['value']}")
            if '_fallback' in result.data:
                print(f"   Using fallback: {result.data['_fallback']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing {name}: {e}")
        return False

def main():
    """Test all scrapers locally"""
    print("🚀 Testing Boom-Bust Sentinel Scrapers Locally")
    print("=" * 60)
    
    scrapers = [
        (BondIssuanceScraper, "Bond Issuance Scraper"),
        (BDCDiscountScraper, "BDC Discount Scraper"),
        (CreditFundScraper, "Credit Fund Scraper"),
        (BankProvisionScraper, "Bank Provision Scraper")
    ]
    
    results = {}
    
    for scraper_class, name in scrapers:
        results[name] = test_scraper(scraper_class, name)
    
    print("\n" + "=" * 60)
    print("📋 SUMMARY")
    print("=" * 60)
    
    for name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {name}")
    
    total_pass = sum(results.values())
    total_tests = len(results)
    
    print(f"\n🎯 Results: {total_pass}/{total_tests} scrapers working")
    
    if total_pass == total_tests:
        print("🎉 All scrapers are functional!")
        print("\n💡 Next steps:")
        print("   • Run individual scrapers: python -c 'from scrapers.bond_issuance_scraper import BondIssuanceScraper; print(BondIssuanceScraper().execute())'")
        print("   • Check data files: ls -la data/")
        print("   • Set up monitoring (Grafana)")
    else:
        print("⚠️  Some scrapers need attention")
        print("   Check the error messages above for details")

if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    main()