#!/usr/bin/env python3
"""
Helper script to guide users in setting up DATABASE_URL.
This script checks if DATABASE_URL is set and provides instructions.
"""

import os
import sys

def check_database_url():
    """Check if DATABASE_URL is configured."""
    print("=" * 60)
    print("DATABASE_URL CONFIGURATION CHECK")
    print("=" * 60)
    print()
    
    database_url = os.getenv('DATABASE_URL', '')
    
    if not database_url:
        print("❌ DATABASE_URL is NOT set")
        print()
        print("To fix this, you need to:")
        print()
        print("1. Get your PlanetScale connection string:")
        print("   - Go to https://app.planetscale.com/")
        print("   - Select your database")
        print("   - Click 'Connect' → Select 'Node.js' or 'General'")
        print("   - Copy the connection string")
        print()
        print("2. For GitHub Actions (REQUIRED for automation):")
        print("   - Go to your GitHub repository")
        print("   - Settings → Secrets and variables → Actions")
        print("   - Click 'New repository secret'")
        print("   - Name: DATABASE_URL")
        print("   - Value: Paste your PlanetScale connection string")
        print()
        print("3. For local testing (optional):")
        print("   export DATABASE_URL='mysql://user:pass@host/db?sslaccept=strict'")
        print("   export ENVIRONMENT='production'")
        print()
        print("Format should be:")
        print("   mysql://username:password@host.connect.psdb.cloud/database?sslaccept=strict")
        print()
        return False
    else:
        # Mask password in output
        if '@' in database_url:
            parts = database_url.split('@')
            if ':' in parts[0]:
                user_pass = parts[0].split(':')
                masked = f"{user_pass[0]}:****@{parts[1]}"
                print(f"✅ DATABASE_URL is set: mysql://{masked}")
            else:
                print(f"✅ DATABASE_URL is set: {database_url[:50]}...")
        else:
            print(f"✅ DATABASE_URL is set: {database_url[:50]}...")
        
        # Validate format
        if not database_url.startswith('mysql://'):
            print("⚠️  Warning: DATABASE_URL should start with 'mysql://'")
            return False
        
        if 'psdb.cloud' not in database_url and 'planetscale' not in database_url.lower():
            print("⚠️  Warning: DATABASE_URL doesn't appear to be a PlanetScale URL")
            print("   Expected format: mysql://user:pass@host.connect.psdb.cloud/db?sslaccept=strict")
        
        if 'sslaccept' not in database_url.lower():
            print("⚠️  Warning: DATABASE_URL should include '?sslaccept=strict'")
        
        print()
        print("✅ DATABASE_URL format looks correct!")
        print()
        return True

def main():
    """Main function."""
    is_set = check_database_url()
    
    if not is_set:
        print("=" * 60)
        print("ACTION REQUIRED")
        print("=" * 60)
        print()
        print("You must set DATABASE_URL before scrapers can store data.")
        print("See SETUP_DATABASE_URL.md for detailed instructions.")
        print()
        sys.exit(1)
    else:
        print("=" * 60)
        print("READY TO TEST")
        print("=" * 60)
        print()
        print("DATABASE_URL is configured. You can now:")
        print("  1. Test connection: python scripts/test_planetscale_connection.py")
        print("  2. Run diagnostic: python scripts/diagnose_scraper_status.py")
        print("  3. Test scrapers: python scripts/run_all_scrapers_safe.py")
        print()
        sys.exit(0)

if __name__ == "__main__":
    main()

