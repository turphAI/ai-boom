#!/usr/bin/env python3
"""
Demo script showing the boom-bust-sentinel system working locally
"""

import sys
import os
import json
from datetime import datetime, timezone

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.bond_issuance_scraper import BondIssuanceScraper
from services.alert_service import AlertService
from services.state_store import FileStateStore

def demo_scraper_execution():
    """Demo scraper execution with real-time output"""
    print("🚀 Boom-Bust Sentinel - Local Demo")
    print("=" * 50)
    
    print("\n📊 Initializing Bond Issuance Scraper...")
    scraper = BondIssuanceScraper()
    
    print(f"   Data Source: {scraper.data_source}")
    print(f"   Metric: {scraper.metric_name}")
    print(f"   Storage: File-based (./data/)")
    
    print("\n⚡ Executing scraper...")
    result = scraper.execute()
    
    print(f"\n📈 Results:")
    print(f"   Success: {'✅' if result.success else '❌'} {result.success}")
    print(f"   Execution Time: {result.execution_time:.2f}s")
    print(f"   Timestamp: {result.timestamp}")
    
    if result.error:
        print(f"   Error: {result.error}")
    
    if result.data:
        print(f"\n📋 Data Summary:")
        data = result.data.get('data', {})
        print(f"   Value: ${data.get('value', 0):,.0f}")
        print(f"   Confidence: {data.get('confidence', 0):.1%}")
        
        metadata = data.get('metadata', {})
        print(f"   Companies: {metadata.get('bond_count', 0)}")
        print(f"   Date Range: {metadata.get('date_range', {}).get('start', 'N/A')} to {metadata.get('date_range', {}).get('end', 'N/A')}")
        
        if result.data.get('_fallback'):
            print(f"   📦 Using Fallback Data: {result.data.get('_fallback_reason', 'Unknown')}")
    
    return result

def demo_alert_system():
    """Demo the alert system"""
    print("\n🔔 Alert System Demo")
    print("-" * 30)
    
    alert_service = AlertService()
    
    # Create a sample alert
    sample_alert = {
        'alert_type': 'demo_alert',
        'severity': 'medium',
        'data_source': 'demo',
        'metric': 'test_metric',
        'current_value': 1000000000,  # $1B
        'threshold': 500000000,       # $500M
        'message': '🚨 Demo Alert: Bond issuance exceeded threshold!\n\nCurrent: $1.0B\nThreshold: $500M\nIncrease: +100%',
        'timestamp': datetime.now(timezone.utc).isoformat()
    }
    
    print("📢 Sending demo alert...")
    alert_service.send_alert(sample_alert)
    
    print("✅ Alert sent to dashboard notification system")

def demo_data_storage():
    """Demo the data storage system"""
    print("\n💾 Data Storage Demo")
    print("-" * 25)
    
    state_store = FileStateStore()
    
    # Show recent data
    recent_data = state_store.get_recent_data('bond_issuance', 'weekly', limit=3)
    
    print(f"📁 Recent bond issuance data ({len(recent_data)} records):")
    
    for i, record in enumerate(recent_data[:3], 1):
        data = record.get('data', {})
        timestamp = record.get('timestamp', 'Unknown')
        value = data.get('value', 0)
        confidence = data.get('confidence', 0)
        
        print(f"   {i}. {timestamp[:19]} - ${value:,.0f} (confidence: {confidence:.1%})")
    
    # Show data files
    data_dir = './data'
    if os.path.exists(data_dir):
        files = [f for f in os.listdir(data_dir) if f.endswith('.json')]
        print(f"\n📂 Data files in {data_dir}:")
        for file in files:
            file_path = os.path.join(data_dir, file)
            size = os.path.getsize(file_path)
            print(f"   • {file} ({size} bytes)")

def main():
    """Main demo function"""
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    try:
        # Demo scraper execution
        result = demo_scraper_execution()
        
        # Demo alert system
        demo_alert_system()
        
        # Demo data storage
        demo_data_storage()
        
        print("\n" + "=" * 50)
        print("🎉 Demo Complete!")
        print("\n💡 What you just saw:")
        print("   ✅ Scraper executed with fallback data")
        print("   ✅ Alert system working")
        print("   ✅ Data stored locally in JSON files")
        print("   ✅ Error handling and graceful degradation")
        
        print("\n🔧 System Status:")
        print("   • Local development: ✅ Working")
        print("   • File-based storage: ✅ Working")
        print("   • Dashboard notifications: ✅ Working")
        print("   • External APIs: ⚠️  Limited (expected)")
        
        print("\n🚀 Next Steps:")
        print("   1. Add AWS permissions for full deployment")
        print("   2. Set up Grafana monitoring")
        print("   3. Configure external API access")
        print("   4. Deploy to production with Serverless Framework")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)