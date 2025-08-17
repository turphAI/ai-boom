#!/usr/bin/env python3
"""
Database Health Check Script
Monitors the health of the PlanetScale database connection
"""

import os
import sys
from datetime import datetime

def check_database_connection():
    """Check if the database connection is healthy"""
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        print("❌ DATABASE_URL environment variable not set")
        return False
    
    print("🔍 Checking PlanetScale database connection...")
    
    try:
        # Import database connection
        sys.path.append('src')
        from lib.db.connection import db
        from lib.db.schema import users
        
        # Try to perform a simple query
        result = db.execute("SELECT 1 as test")
        
        if result:
            print("✅ Database connection successful")
            
            # Try to query the users table
            try:
                user_count = db.execute("SELECT COUNT(*) as count FROM users")
                print(f"✅ Users table accessible - {user_count[0]['count'] if user_count else 0} users found")
                return True
            except Exception as e:
                print(f"⚠️  Users table query failed: {e}")
                return True  # Connection works, table might not exist yet
                
        else:
            print("❌ Database query failed")
            return False
            
    except ImportError as e:
        print(f"❌ Could not import database modules: {e}")
        return False
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def check_database_schema():
    """Check if required database tables exist"""
    print("🔍 Checking database schema...")
    
    try:
        sys.path.append('src')
        from lib.db.connection import db
        
        # Check for required tables
        required_tables = ['users', 'alert_configurations', 'user_preferences']
        
        for table in required_tables:
            try:
                result = db.execute(f"SHOW TABLES LIKE '{table}'")
                if result:
                    print(f"✅ Table '{table}' exists")
                else:
                    print(f"⚠️  Table '{table}' not found")
            except Exception as e:
                print(f"❌ Error checking table '{table}': {e}")
                
    except Exception as e:
        print(f"❌ Schema check failed: {e}")

def main():
    """Main database health check function"""
    print(f"🗄️  Starting database health check at {datetime.now()}")
    
    # Check database connection
    connection_healthy = check_database_connection()
    
    # Check database schema
    check_database_schema()
    
    if connection_healthy:
        print("🎉 Database health checks passed!")
        sys.exit(0)
    else:
        print("💥 Database health checks failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
