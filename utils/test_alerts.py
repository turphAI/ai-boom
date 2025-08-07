"""
Utility script to test alert notifications manually.
"""

import sys
from datetime import datetime
from services.alert_service import AlertService


def create_test_alert(alert_type: str = "test") -> dict:
    """Create a test alert for testing purposes."""
    return {
        'alert_type': 'threshold_breach',
        'data_source': 'test_source',
        'metric_name': 'test_metric',
        'current_value': 15000000000,  # $15B
        'previous_value': 8000000000,   # $8B
        'threshold': 5000000000,        # $5B
        'change_percent': 87.5,
        'timestamp': datetime.utcnow().isoformat(),
        'message': f'Test alert of type: {alert_type}',
        'context': {
            'companies_involved': ['MSFT', 'META'],
            'data_quality': 'high',
            'confidence': 0.95,
            'test_mode': True
        }
    }


def test_dashboard_alerts():
    """Test dashboard alert functionality."""
    print("Testing dashboard alerts...")
    
    service = AlertService()
    
    # Send a test alert
    test_alert = create_test_alert("dashboard_test")
    results = service.send_alert(test_alert)
    
    print(f"Alert sent with results: {results}")
    
    # Get recent alerts
    recent_alerts = service.get_dashboard_alerts(limit=5)
    print(f"Found {len(recent_alerts)} recent alerts")
    
    if recent_alerts:
        latest_alert = recent_alerts[-1]  # Most recent
        print(f"Latest alert ID: {latest_alert['id']}")
        print(f"Alert acknowledged: {latest_alert['acknowledged']}")
        
        # Test acknowledgment
        alert_id = latest_alert['id']
        ack_result = service.acknowledge_alert(alert_id)
        print(f"Acknowledgment result: {ack_result}")


def test_all_channels():
    """Test all configured notification channels."""
    print("Testing all notification channels...")
    
    service = AlertService()
    
    # Show configured channels
    channel_names = [c.get_channel_name() for c in service.channels]
    print(f"Configured channels: {', '.join(channel_names)}")
    
    # Send test alert
    test_alert = create_test_alert("multi_channel_test")
    results = service.send_alert(test_alert)
    
    print("\nResults by channel:")
    for channel, success in results.items():
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"  {channel}: {status}")


def test_specific_channel(channel_name: str):
    """Test a specific notification channel."""
    print(f"Testing {channel_name} channel...")
    
    service = AlertService()
    
    # Find the specific channel
    target_channel = None
    for channel in service.channels:
        if channel.get_channel_name().lower() == channel_name.lower():
            target_channel = channel
            break
    
    if not target_channel:
        print(f"Channel '{channel_name}' not found or not configured")
        available_channels = [c.get_channel_name() for c in service.channels]
        print(f"Available channels: {', '.join(available_channels)}")
        return
    
    # Test the specific channel
    test_alert = create_test_alert(f"{channel_name.lower()}_test")
    success = target_channel.send(test_alert)
    
    status = "✅ SUCCESS" if success else "❌ FAILED"
    print(f"{channel_name} test result: {status}")


def main():
    """Main function for command-line usage."""
    if len(sys.argv) < 2:
        print("Usage: python test_alerts.py <command> [args]")
        print("Commands:")
        print("  dashboard - Test dashboard alerts")
        print("  all - Test all configured channels")
        print("  channel <name> - Test specific channel (sns, telegram, dashboard)")
        return
    
    command = sys.argv[1].lower()
    
    try:
        if command == 'dashboard':
            test_dashboard_alerts()
        elif command == 'all':
            test_all_channels()
        elif command == 'channel':
            if len(sys.argv) < 3:
                print("Error: channel name required")
                return
            test_specific_channel(sys.argv[2])
        else:
            print(f"Unknown command: {command}")
    
    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()