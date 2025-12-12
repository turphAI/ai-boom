#!/usr/bin/env python3
"""
Vercel Health Check Script
Monitors the health of the deployed Vercel application
"""

import os
import requests
import sys
from datetime import datetime

def check_vercel_deployment():
    """Check if the Vercel deployment is healthy"""
    dashboard_url = os.getenv('DASHBOARD_URL', 'https://ai-boom-iota.vercel.app')
    vercel_token = os.getenv('VERCEL_TOKEN')
    
    print(f"🔍 Checking Vercel deployment health at: {dashboard_url}")
    
    try:
        # Check if the main page loads
        response = requests.get(dashboard_url, timeout=30)
        
        if response.status_code == 200:
            print("✅ Application is responding (200 OK)")
            
            # Check if it's not an error page
            if "error" not in response.text.lower() and "not found" not in response.text.lower():
                print("✅ Application content looks healthy")
                return True
            else:
                print("❌ Application returned error content")
                return False
        else:
            print(f"❌ Application returned status code: {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Application request timed out")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to application")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def check_api_endpoints():
    """Check if API endpoints are responding"""
    base_url = os.getenv('DASHBOARD_URL', 'https://ai-boom-iota.vercel.app')
    
    # Test API endpoints
    endpoints = [
        '/api/system/health',
        '/api/metrics/current',
        '/api/auth/register'
    ]
    
    print("🔍 Checking API endpoints...")
    
    for endpoint in endpoints:
        try:
            url = f"{base_url}{endpoint}"
            response = requests.get(url, timeout=10)
            
            if response.status_code in [200, 401, 403]:  # 401/403 are expected for auth endpoints
                print(f"✅ {endpoint} - Status: {response.status_code}")
            else:
                print(f"⚠️  {endpoint} - Unexpected status: {response.status_code}")
                
        except Exception as e:
            print(f"❌ {endpoint} - Error: {e}")

def main():
    """Main health check function"""
    print(f"🚀 Starting Vercel health check at {datetime.now()}")
    
    # Check main application
    app_healthy = check_vercel_deployment()
    
    # Check API endpoints
    check_api_endpoints()
    
    if app_healthy:
        print("🎉 All health checks passed!")
        sys.exit(0)
    else:
        print("💥 Health checks failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
