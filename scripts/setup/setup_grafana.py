#!/usr/bin/env python3
"""
Setup script for Grafana Cloud integration
"""

import os
import sys
import json
import requests
from datetime import datetime, timezone

def get_grafana_config():
    """Get Grafana configuration from user"""
    print("🔧 Grafana Cloud Setup")
    print("=" * 40)
    
    print("\n📋 You'll need these from your Grafana Cloud account:")
    print("   1. Stack URL (e.g., https://your-stack.grafana.net)")
    print("   2. API Key (create one with MetricsPublisher role)")
    
    print("\n🔑 To create an API Key:")
    print("   1. Go to your Grafana Cloud dashboard")
    print("   2. Click 'Security' → 'API Keys'")
    print("   3. Click 'Add API Key'")
    print("   4. Name: 'boom-bust-sentinel'")
    print("   5. Role: 'MetricsPublisher'")
    print("   6. Copy the generated key")
    
    grafana_url = input("\n📍 Enter your Grafana Stack URL: ").strip()
    if not grafana_url.startswith('http'):
        grafana_url = f"https://{grafana_url}"
    
    api_key = input("🔑 Enter your API Key: ").strip()
    
    return grafana_url, api_key

def test_grafana_connection(grafana_url, api_key):
    """Test connection to Grafana"""
    print("\n🧪 Testing Grafana connection...")
    
    try:
        # Test with a simple API call
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(f"{grafana_url}/api/org", headers=headers, timeout=10)
        
        if response.status_code == 200:
            org_info = response.json()
            print(f"✅ Connected to Grafana!")
            print(f"   Organization: {org_info.get('name', 'Unknown')}")
            return True
        else:
            print(f"❌ Connection failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

def update_env_file(grafana_url, api_key):
    """Update .env file with Grafana configuration"""
    print("\n📝 Updating .env file...")
    
    # Read existing .env file
    env_content = []
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            env_content = f.readlines()
    
    # Remove existing Grafana config
    env_content = [line for line in env_content if not line.startswith(('GRAFANA_URL=', 'GRAFANA_API_KEY=', 'MONITORING_PROVIDER='))]
    
    # Add new Grafana config
    env_content.extend([
        f"\n# Grafana Cloud Configuration\n",
        f"GRAFANA_URL={grafana_url}\n",
        f"GRAFANA_API_KEY={api_key}\n",
        f"MONITORING_PROVIDER=grafana\n"
    ])
    
    # Write updated .env file
    with open('.env', 'w') as f:
        f.writelines(env_content)
    
    print("✅ .env file updated with Grafana configuration")

def send_test_metric(grafana_url, api_key):
    """Send a test metric to Grafana"""
    print("\n📊 Sending test metric...")
    
    try:
        # Grafana Cloud uses Prometheus format
        metric_data = {
            "streams": [
                {
                    "stream": {
                        "job": "boom-bust-sentinel",
                        "instance": "local-test",
                        "__name__": "boom_bust_test_metric"
                    },
                    "values": [
                        [str(int(datetime.now(timezone.utc).timestamp() * 1000000000)), "1"]
                    ]
                }
            ]
        }
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        # Note: This is a simplified example. Grafana Cloud typically uses different endpoints
        # for metrics ingestion (like Prometheus remote write)
        print("📈 Test metric prepared (actual sending requires Prometheus endpoint)")
        print("   Metric: boom_bust_test_metric = 1")
        print("   Timestamp:", datetime.now(timezone.utc).isoformat())
        
        return True
        
    except Exception as e:
        print(f"❌ Error sending test metric: {e}")
        return False

def create_sample_dashboard_config():
    """Create a sample dashboard configuration"""
    print("\n📊 Creating sample dashboard configuration...")
    
    dashboard_config = {
        "dashboard": {
            "title": "Boom-Bust Sentinel Monitoring",
            "tags": ["boom-bust-sentinel", "financial", "monitoring"],
            "timezone": "UTC",
            "panels": [
                {
                    "title": "Bond Issuance Volume",
                    "type": "stat",
                    "targets": [
                        {
                            "expr": "boom_bust_bond_issuance_value",
                            "legendFormat": "Bond Issuance ($)"
                        }
                    ],
                    "fieldConfig": {
                        "defaults": {
                            "unit": "currencyUSD",
                            "decimals": 0
                        }
                    }
                },
                {
                    "title": "BDC Discount Average",
                    "type": "stat",
                    "targets": [
                        {
                            "expr": "boom_bust_bdc_discount_average",
                            "legendFormat": "Average Discount (%)"
                        }
                    ],
                    "fieldConfig": {
                        "defaults": {
                            "unit": "percent",
                            "decimals": 2
                        }
                    }
                },
                {
                    "title": "Scraper Execution Times",
                    "type": "timeseries",
                    "targets": [
                        {
                            "expr": "boom_bust_scraper_execution_time",
                            "legendFormat": "{{scraper_name}}"
                        }
                    ]
                },
                {
                    "title": "System Health",
                    "type": "stat",
                    "targets": [
                        {
                            "expr": "boom_bust_system_health",
                            "legendFormat": "Health Score"
                        }
                    ]
                }
            ]
        }
    }
    
    # Save dashboard config
    with open('config/grafana_dashboard_sample.json', 'w') as f:
        json.dump(dashboard_config, f, indent=2)
    
    print("✅ Sample dashboard config saved to config/grafana_dashboard_sample.json")
    print("   You can import this into Grafana later")

def main():
    """Main setup function"""
    print("🚀 Setting up Grafana Cloud for Boom-Bust Sentinel")
    print("=" * 60)
    
    # Get Grafana configuration
    grafana_url, api_key = get_grafana_config()
    
    # Test connection
    if not test_grafana_connection(grafana_url, api_key):
        print("\n❌ Setup failed: Could not connect to Grafana")
        print("   Please check your URL and API key")
        return False
    
    # Update environment file
    update_env_file(grafana_url, api_key)
    
    # Send test metric
    send_test_metric(grafana_url, api_key)
    
    # Create sample dashboard
    create_sample_dashboard_config()
    
    print("\n" + "=" * 60)
    print("🎉 Grafana setup complete!")
    
    print("\n📋 Next steps:")
    print("   1. Run a scraper to generate metrics: python scripts/demo_local_system.py")
    print("   2. Check your Grafana dashboard for data")
    print("   3. Import the sample dashboard from config/grafana_dashboard_sample.json")
    print("   4. Set up alerts in Grafana for threshold breaches")
    
    print("\n💡 Useful Grafana queries:")
    print("   • boom_bust_bond_issuance_value - Bond issuance amounts")
    print("   • boom_bust_scraper_execution_time - Performance monitoring")
    print("   • boom_bust_system_health - Overall system status")
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)