"""
Integration tests for alert service with scrapers.
"""

import tempfile
import shutil
from datetime import datetime
from typing import Dict, Any, Optional

from scrapers.base import BaseScraper
from services.alert_service import AlertService, DashboardNotificationChannel
from services.state_store import FileStateStore


class AlertTestScraper(BaseScraper):
    """Test scraper that triggers alerts for integration testing."""
    
    def __init__(self, data_source: str = "alert_test", metric_name: str = "test_metric"):
        super().__init__(data_source, metric_name)
        self.current_value = 100
        self.threshold = 50
        self.historical_value = 30
        self.force_alert = False
    
    def fetch_data(self) -> Dict[str, Any]:
        return {
            'value': self.current_value,
            'confidence': 0.95,
            'metadata': {'test_mode': True}
        }
    
    def should_alert(self, current_data: Dict[str, Any], historical_data: Optional[Dict[str, Any]]) -> bool:
        if self.force_alert:
            return True
        
        current_value = current_data.get('value', 0)
        
        if historical_data:
            historical_value = historical_data.get('data', {}).get('value', 0)
            change = abs(current_value - historical_value)
            return change > self.threshold
        
        return False
    
    def generate_alert_message(self, current_data: Dict[str, Any], historical_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        current_value = current_data.get('value', 0)
        historical_value = historical_data.get('data', {}).get('value', 0) if historical_data else 0
        change_percent = ((current_value - historical_value) / historical_value * 100) if historical_value > 0 else 0
        
        return {
            'alert_type': 'threshold_breach',
            'data_source': self.data_source,
            'metric_name': self.metric_name,
            'current_value': current_value,
            'previous_value': historical_value,
            'threshold': self.threshold,
            'change_percent': round(change_percent, 2),
            'timestamp': datetime.utcnow().isoformat(),
            'message': f'Value changed from {historical_value} to {current_value}',
            'context': {
                'test_mode': True,
                'confidence': current_data.get('confidence', 1.0)
            }
        }


def test_scraper_alert_integration():
    """Test that scraper properly triggers alerts through alert service."""
    # Set up test environment
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Create scraper with custom state store
        scraper = AlertTestScraper()
        scraper.state_store = FileStateStore(temp_dir)
        
        # Set up custom alert service for testing
        alert_service = AlertService()
        dashboard_channel = None
        for channel in alert_service.channels:
            if isinstance(channel, DashboardNotificationChannel):
                dashboard_channel = channel
                dashboard_channel.alerts_file = f"{temp_dir}/test_alerts.json"
                break
        
        scraper.alert_service = alert_service
        
        # First execution - no alert expected (no historical data)
        scraper.current_value = 100
        result1 = scraper.execute()
        
        assert result1.success is True
        
        # Check no alerts were generated
        alerts = alert_service.get_dashboard_alerts()
        initial_alert_count = len(alerts)
        
        # Second execution - should trigger alert due to large change
        scraper.current_value = 200  # Change of 100 > threshold of 50
        result2 = scraper.execute()
        
        assert result2.success is True
        
        # Check that alert was generated
        alerts = alert_service.get_dashboard_alerts()
        assert len(alerts) > initial_alert_count
        
        # Verify alert content
        latest_alert = alerts[-1]
        alert_data = latest_alert['alert_data']
        
        assert alert_data['data_source'] == 'alert_test'
        assert alert_data['metric_name'] == 'test_metric'
        assert alert_data['current_value'] == 200
        assert alert_data['previous_value'] == 100
        assert alert_data['alert_type'] == 'threshold_breach'
        assert latest_alert['acknowledged'] is False
        
        print("Scraper-alert integration test passed!")
        
    finally:
        # Clean up
        shutil.rmtree(temp_dir)


def test_multiple_scrapers_alerts():
    """Test multiple scrapers generating alerts."""
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Create multiple scrapers
        scraper1 = AlertTestScraper("bonds", "weekly_issuance")
        scraper2 = AlertTestScraper("bdc", "discount_nav")
        
        # Set up shared state store and alert service
        state_store = FileStateStore(temp_dir)
        alert_service = AlertService()
        
        # Configure dashboard channel
        for channel in alert_service.channels:
            if isinstance(channel, DashboardNotificationChannel):
                channel.alerts_file = f"{temp_dir}/multi_alerts.json"
        
        # Configure scrapers
        for scraper in [scraper1, scraper2]:
            scraper.state_store = state_store
            scraper.alert_service = alert_service
            scraper.force_alert = True  # Force alerts for testing
        
        # Execute scrapers
        result1 = scraper1.execute()
        result2 = scraper2.execute()
        
        assert result1.success is True
        assert result2.success is True
        
        # Check alerts from both scrapers
        alerts = alert_service.get_dashboard_alerts()
        assert len(alerts) >= 2
        
        # Verify we have alerts from both data sources
        data_sources = {alert['alert_data']['data_source'] for alert in alerts}
        assert 'bonds' in data_sources
        assert 'bdc' in data_sources
        
        print("Multiple scrapers alert test passed!")
        
    finally:
        # Clean up
        shutil.rmtree(temp_dir)


def test_alert_acknowledgment_workflow():
    """Test the complete alert acknowledgment workflow."""
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Set up scraper and alert service
        scraper = AlertTestScraper()
        scraper.state_store = FileStateStore(temp_dir)
        scraper.force_alert = True
        
        alert_service = AlertService()
        for channel in alert_service.channels:
            if isinstance(channel, DashboardNotificationChannel):
                channel.alerts_file = f"{temp_dir}/ack_alerts.json"
        
        scraper.alert_service = alert_service
        
        # Generate an alert
        result = scraper.execute()
        assert result.success is True
        
        # Get the alert
        alerts = alert_service.get_dashboard_alerts()
        assert len(alerts) >= 1
        
        alert = alerts[-1]
        alert_id = alert['id']
        
        # Verify alert is not acknowledged
        assert alert['acknowledged'] is False
        
        # Acknowledge the alert
        ack_result = alert_service.acknowledge_alert(alert_id)
        assert ack_result is True
        
        # Verify acknowledgment
        updated_alerts = alert_service.get_dashboard_alerts()
        acknowledged_alert = None
        for a in updated_alerts:
            if a['id'] == alert_id:
                acknowledged_alert = a
                break
        
        assert acknowledged_alert is not None
        assert acknowledged_alert['acknowledged'] is True
        assert 'acknowledged_at' in acknowledged_alert
        
        print("Alert acknowledgment workflow test passed!")
        
    finally:
        # Clean up
        shutil.rmtree(temp_dir)


if __name__ == "__main__":
    test_scraper_alert_integration()
    test_multiple_scrapers_alerts()
    test_alert_acknowledgment_workflow()
    print("All alert integration tests passed!")