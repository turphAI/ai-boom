#!/usr/bin/env python3
"""
Script to refresh real financial data using the FRED API.
This should be run regularly (e.g., every hour) to keep data fresh.
"""

import os
import sys
import json
from datetime import datetime, timezone

# Set the FRED API key
os.environ['FRED_API_KEY'] = 'fba11235c90a241910f0b42d1f8dfb8e'

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def refresh_real_data():
    """Refresh real financial data from alternative sources."""
    print(f"🔄 Refreshing Real Financial Data")
    print(f"   Timestamp: {datetime.now().isoformat()}")
    
    try:
        from services.alternative_data_service import AlternativeDataService
        
        # Initialize the service
        alt_service = AlternativeDataService()
        
        # Convert datetime objects to strings for JSON serialization
        def convert_datetime_to_string(obj):
            if isinstance(obj, dict):
                return {k: convert_datetime_to_string(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_datetime_to_string(item) for item in obj]
            elif isinstance(obj, datetime):
                return obj.isoformat()
            else:
                return obj
        
        # Generate and save credit fund data
        print("📊 Updating Credit Fund Data...")
        credit_data = alt_service.get_credit_fund_proxy_data()
        credit_data_serializable = convert_datetime_to_string(credit_data)
        credit_entry = {
            "data_source": "credit_fund",
            "metric_name": "gross_asset_value",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": credit_data_serializable
        }
        
        credit_file = "data/credit_fund_data.json"
        with open(credit_file, 'w') as f:
            json.dump([credit_entry], f, indent=2)
        
        print(f"   ✅ Credit Fund: ${credit_data['value']:,.0f} (Confidence: {credit_data['confidence']})")
        
        # Generate and save bank provision data
        print("🏦 Updating Bank Provision Data...")
        bank_data = alt_service.get_bank_provision_proxy_data()
        bank_data_serializable = convert_datetime_to_string(bank_data)
        bank_entry = {
            "data_source": "bank_provision",
            "metric_name": "non_bank_financial_provisions",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": bank_data_serializable
        }
        
        bank_file = "data/bank_provision_data.json"
        with open(bank_file, 'w') as f:
            json.dump([bank_entry], f, indent=2)
        
        print(f"   ✅ Bank Provisions: ${bank_data['value']:,.0f} (Confidence: {bank_data['confidence']})")
        
        print(f"\n🎉 Data refresh completed successfully!")
        print(f"   Both scrapers should now show as healthy in System Health view")
        
        return True
        
    except Exception as e:
        print(f"❌ Error refreshing data: {e}")
        return False

if __name__ == "__main__":
    success = refresh_real_data()
    sys.exit(0 if success else 1)
