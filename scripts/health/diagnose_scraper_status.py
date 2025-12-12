#!/usr/bin/env python3
"""
Diagnostic script to check scraper automation and data storage status.
This helps identify why scrapers aren't running or data isn't being stored.
"""

import os
import sys
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def check_environment():
    """Check environment configuration."""
    print("=" * 60)
    print("1. ENVIRONMENT CONFIGURATION")
    print("=" * 60)
    
    env = os.getenv('ENVIRONMENT', 'development')
    print(f"   ENVIRONMENT: {env}")
    
    database_url = os.getenv('DATABASE_URL', '')
    if database_url:
        # Mask password in URL
        if '@' in database_url:
            parts = database_url.split('@')
            if ':' in parts[0]:
                user_pass = parts[0].split(':')
                masked = f"{user_pass[0]}:****@{parts[1]}"
                print(f"   DATABASE_URL: mysql://{masked}")
            else:
                print(f"   DATABASE_URL: {database_url[:50]}...")
        else:
            print(f"   DATABASE_URL: {database_url[:50]}...")
    else:
        print("   ❌ DATABASE_URL: NOT SET")
    
    fred_key = os.getenv('FRED_API_KEY', '')
    if fred_key:
        print(f"   FRED_API_KEY: {'*' * (len(fred_key) - 4)}{fred_key[-4:]}")
    else:
        print("   ⚠️  FRED_API_KEY: NOT SET (optional but recommended)")
    
    print()

def check_github_workflow():
    """Check GitHub Actions workflow status."""
    print("=" * 60)
    print("2. GITHUB ACTIONS WORKFLOW")
    print("=" * 60)
    
    workflow_file = Path(__file__).parent.parent / '.github' / 'workflows' / 'run-scrapers.yml'
    if workflow_file.exists():
        print(f"   ✅ Workflow file exists: {workflow_file}")
        
        # Read workflow to check schedule
        with open(workflow_file, 'r') as f:
            content = f.read()
            if "cron:" in content:
                print("   ✅ Scheduled workflow configured")
            if "workflow_dispatch" in content:
                print("   ✅ Manual trigger enabled")
    else:
        print(f"   ❌ Workflow file not found: {workflow_file}")
    
    print("   ℹ️  Check GitHub Actions tab to see if workflow is running")
    print("   ℹ️  Verify DATABASE_URL secret is configured in GitHub")
    print()

def check_planetscale_connection():
    """Check PlanetScale database connection and recent data."""
    print("=" * 60)
    print("3. PLANETSCALE DATABASE")
    print("=" * 60)
    
    database_url = os.getenv('DATABASE_URL', '')
    if not database_url:
        print("   ❌ DATABASE_URL not set - cannot check database")
        print()
        return
    
    try:
        from services.planetscale_data_service import PlanetScaleDataService
        service = PlanetScaleDataService()
        
        # Get latest metrics
        metrics = service.get_latest_metrics()
        
        if metrics:
            print(f"   ✅ Connected to PlanetScale")
            print(f"   ✅ Found {len(metrics)} metrics in database")
            
            # Check data freshness
            now = datetime.now(timezone.utc)
            recent_count = 0
            stale_count = 0
            
            for metric in metrics[:10]:  # Check first 10
                updated_at = metric.get('updatedAt')
                if updated_at:
                    if isinstance(updated_at, str):
                        try:
                            updated_dt = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                        except:
                            updated_dt = None
                    else:
                        updated_dt = updated_at
                    
                    if updated_dt:
                        age = now - updated_dt.replace(tzinfo=timezone.utc) if updated_dt.tzinfo is None else updated_dt
                        if age < timedelta(days=1):
                            recent_count += 1
                        elif age > timedelta(days=7):
                            stale_count += 1
                        
                        print(f"      - {metric.get('dataSource', 'unknown')}.{metric.get('metricName', 'unknown')}: "
                              f"updated {age.days} days ago")
            
            print()
            if recent_count > 0:
                print(f"   ✅ {recent_count} metrics updated in last 24 hours")
            if stale_count > 0:
                print(f"   ⚠️  {stale_count} metrics are stale (>7 days old)")
        else:
            print("   ⚠️  Connected but no metrics found in database")
            print("   ℹ️  This suggests scrapers haven't run or data isn't being stored")
        
    except Exception as e:
        print(f"   ❌ Error connecting to PlanetScale: {e}")
        print("   ℹ️  Check DATABASE_URL is correct and database is accessible")
    
    print()

def check_local_data_files():
    """Check local data files for recent updates."""
    print("=" * 60)
    print("4. LOCAL DATA FILES")
    print("=" * 60)
    
    data_dir = Path(__file__).parent.parent / 'data'
    if not data_dir.exists():
        print(f"   ⚠️  Data directory not found: {data_dir}")
        print()
        return
    
    data_files = [
        'bond_issuance_weekly.json',
        'bdc_discount_discount_to_nav.json',
        'credit_fund_gross_asset_value.json',
        'bank_provision_non_bank_financial_provisions.json'
    ]
    
    now = datetime.now()
    for filename in data_files:
        file_path = data_dir / filename
        if file_path.exists():
            mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
            age = now - mtime
            
            if age < timedelta(days=1):
                status = "✅"
            elif age < timedelta(days=7):
                status = "⚠️"
            else:
                status = "❌"
            
            print(f"   {status} {filename}: last modified {age.days} days ago")
        else:
            print(f"   ❌ {filename}: file not found")
    
    print()
    print("   ℹ️  Local files are fallback - production should use PlanetScale")
    print()

def check_state_store_config():
    """Check state store configuration."""
    print("=" * 60)
    print("5. STATE STORE CONFIGURATION")
    print("=" * 60)
    
    try:
        from services.state_store import StateStore
        
        env = os.getenv('ENVIRONMENT', 'development')
        print(f"   Environment: {env}")
        
        # Try to initialize state store
        try:
            store = StateStore()
            store_type = type(store).__name__
            print(f"   ✅ StateStore initialized: {store_type}")
            
            if 'PlanetScale' in store_type:
                print("   ✅ Using PlanetScale for data storage")
            elif 'File' in store_type:
                print("   ⚠️  Using file-based storage (not ideal for production)")
            else:
                print(f"   ℹ️  Using {store_type} storage")
                
        except Exception as e:
            print(f"   ❌ Failed to initialize StateStore: {e}")
            
    except ImportError as e:
        print(f"   ❌ Could not import StateStore: {e}")
    
    print()

def check_scraper_execution():
    """Check if scrapers can execute."""
    print("=" * 60)
    print("6. SCRAPER EXECUTION TEST")
    print("=" * 60)
    
    scrapers_to_test = [
        ('bond_issuance', 'BondIssuanceScraper'),
        ('bdc_discount', 'BDCDiscountScraper'),
        ('credit_fund', 'CreditFundScraper'),
        ('bank_provision', 'BankProvisionScraper')
    ]
    
    for scraper_name, scraper_class in scrapers_to_test:
        try:
            module_name = f"scrapers.{scraper_name}_scraper"
            scraper_module = __import__(module_name, fromlist=[scraper_class])
            scraper = getattr(scraper_module, scraper_class)
            print(f"   ✅ {scraper_name}: Can import")
        except Exception as e:
            print(f"   ❌ {scraper_name}: Import failed - {e}")
    
    print()
    print("   ℹ️  To test execution, run: python scripts/run_all_scrapers_safe.py")
    print()

def generate_recommendations():
    """Generate recommendations based on findings."""
    print("=" * 60)
    print("7. RECOMMENDATIONS")
    print("=" * 60)
    
    recommendations = []
    
    database_url = os.getenv('DATABASE_URL', '')
    if not database_url:
        recommendations.append("❌ Set DATABASE_URL environment variable")
    
    env = os.getenv('ENVIRONMENT', 'development')
    if env != 'production':
        recommendations.append("⚠️  Set ENVIRONMENT=production for production runs")
    
    if recommendations:
        for rec in recommendations:
            print(f"   {rec}")
    else:
        print("   ✅ Configuration looks good!")
    
    print()
    print("   Next steps:")
    print("   1. Verify GitHub Actions workflow is enabled")
    print("   2. Check DATABASE_URL secret is configured in GitHub")
    print("   3. Run workflow manually to test")
    print("   4. Verify data appears in PlanetScale after workflow runs")
    print()

def main():
    """Run all diagnostic checks."""
    print("\n" + "=" * 60)
    print("SCRAPER AUTOMATION & DATA STORAGE DIAGNOSTIC")
    print("=" * 60)
    print()
    
    check_environment()
    check_github_workflow()
    check_planetscale_connection()
    check_local_data_files()
    check_state_store_config()
    check_scraper_execution()
    generate_recommendations()
    
    print("=" * 60)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 60)
    print()

if __name__ == "__main__":
    main()

