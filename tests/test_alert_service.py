"""
Tests for the alert service and notification channels.
"""

import json
import os
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock
import pytest

from services.alert_service import (
    AlertService, 
    SNSNotificationChannel, 
    TelegramNotificationChannel,
    DashboardNotificationChannel
)


class TestSNSNotificationChannel:
    """Tests for SNS notification channel."""
    
    @patch('boto3.client')
    @patch('services.alert_service.settings')
    def test_sns_send_success(self, mock_settings, mock_boto3):
        """Test successful SNS notification."""
        # Mock settings
        mock_settings.SNS_TOPIC_ARN = 'arn:aws:sns:us-east-1:123456789012:test-topic'
        mock_settings.AWS_REGION = 'us-east-1'
        
        # Mock SNS client
        mock_sns_client = Mock()
        mock_sns_client.publish.return_value = {'MessageId': 'test-message-id'}
        mock_boto3.return_value = mock_sns_client
        
        # Test notification
        channel = SNSNotificationChannel()
        alert_data = {
            'alert_type': 'threshold_breach',
            'data_source': 'test_source',
            'metric_name': 'test_metric',
            'current_value': 100,
            'previous_value': 50,
            'message': 'Test alert message'
        }
        
        result = channel.send(alert_data)
        
        assert result is True
        mock_sns_client.publish.assert_called_once()
        
        # Verify call arguments
        call_args = mock_sns_client.publish.call_args[1]
        assert call_args['TopicArn'] == 'arn:aws:sns:us-east-1:123456789012:test-topic'
        assert 'Test alert message' in call_args['Message']
        assert 'test_source' in call_args['Subject']
    
    @patch('services.alert_service.settings')
    def test_sns_not_configured(self, mock_settings):
        """Test SNS when not configured."""
        mock_settings.SNS_TOPIC_ARN = None
        
        channel = SNSNotificationChannel()
        result = channel.send({'test': 'data'})
        
        assert result is False


class TestTelegramNotificationChannel:
    """Tests for Telegram notification channel."""
    
    @patch('requests.post')
    @patch('services.alert_service.settings')
    def test_telegram_send_success(self, mock_settings, mock_requests):
        """Test successful Telegram notification."""
        # Mock settings
        mock_settings.TELEGRAM_BOT_TOKEN = 'test-bot-token'
        mock_settings.TELEGRAM_CHAT_ID = 'test-chat-id'
        
        # Mock successful response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_requests.return_value = mock_response
        
        # Test notification
        channel = TelegramNotificationChannel()
        alert_data = {
            'alert_type': 'threshold_breach',
            'data_source': 'test_source',
            'metric_name': 'test_metric',
            'current_value': 100,
            'message': 'Test alert message'
        }
        
        result = channel.send(alert_data)
        
        assert result is True
        mock_requests.assert_called_once()
        
        # Verify call arguments
        call_args = mock_requests.call_args
        assert 'https://api.telegram.org/bot' in call_args[0][0]
        
        payload = call_args[1]['json']
        assert payload['chat_id'] == 'test-chat-id'
        assert 'test_source' in payload['text']
        assert payload['parse_mode'] == 'Markdown'
    
    @patch('services.alert_service.settings')
    def test_telegram_not_configured(self, mock_settings):
        """Test Telegram when not configured."""
        mock_settings.TELEGRAM_BOT_TOKEN = None
        mock_settings.TELEGRAM_CHAT_ID = None
        
        channel = TelegramNotificationChannel()
        result = channel.send({'test': 'data'})
        
        assert result is False


class TestDashboardNotificationChannel:
    """Tests for dashboard notification channel."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.alerts_file = os.path.join(self.temp_dir, 'dashboard_alerts.json')
        
        # Patch the alerts file path
        self.channel = DashboardNotificationChannel()
        self.channel.alerts_file = self.alerts_file
    
    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)
    
    def test_dashboard_send_success(self):
        """Test successful dashboard notification storage."""
        alert_data = {
            'alert_type': 'threshold_breach',
            'data_source': 'test_source',
            'metric_name': 'test_metric',
            'current_value': 100,
            'message': 'Test alert message'
        }
        
        result = self.channel.send(alert_data)
        
        assert result is True
        assert os.path.exists(self.alerts_file)
        
        # Verify alert was stored
        with open(self.alerts_file, 'r') as f:
            alerts = json.load(f)
        
        assert len(alerts) == 1
        assert alerts[0]['alert_data']['data_source'] == 'test_source'
        assert alerts[0]['acknowledged'] is False
    
    def test_get_recent_alerts(self):
        """Test retrieving recent alerts."""
        # Add multiple alerts
        for i in range(3):
            alert_data = {
                'data_source': f'source_{i}',
                'metric_name': 'test_metric',
                'current_value': i * 10
            }
            self.channel.send(alert_data)
        
        # Get recent alerts
        recent_alerts = self.channel.get_recent_alerts(limit=2)
        
        assert len(recent_alerts) == 2
        # Should be in reverse chronological order (newest first)
        assert recent_alerts[0]['alert_data']['data_source'] == 'source_2'
        assert recent_alerts[1]['alert_data']['data_source'] == 'source_1'
    
    def test_acknowledge_alert(self):
        """Test acknowledging an alert."""
        # Send an alert
        alert_data = {'data_source': 'test_source', 'message': 'test'}
        self.channel.send(alert_data)
        
        # Get the alert ID
        alerts = self.channel.get_recent_alerts()
        alert_id = alerts[0]['id']
        
        # Acknowledge the alert
        result = self.channel.acknowledge_alert(alert_id)
        
        assert result is True
        
        # Verify acknowledgment
        updated_alerts = self.channel.get_recent_alerts()
        assert updated_alerts[0]['acknowledged'] is True
        assert 'acknowledged_at' in updated_alerts[0]


class TestAlertService:
    """Tests for the main alert service."""
    
    @patch('services.alert_service.settings')
    def test_alert_service_initialization(self, mock_settings):
        """Test alert service initialization with different configurations."""
        # Test with no external services configured
        mock_settings.SNS_TOPIC_ARN = None
        mock_settings.TELEGRAM_BOT_TOKEN = None
        mock_settings.TELEGRAM_CHAT_ID = None
        
        service = AlertService()
        
        # Should have at least dashboard channel
        assert len(service.channels) >= 1
        channel_names = [c.get_channel_name() for c in service.channels]
        assert 'Dashboard' in channel_names
    
    @patch('services.alert_service.settings')
    def test_send_alert_multiple_channels(self, mock_settings):
        """Test sending alert through multiple channels."""
        # Configure all channels
        mock_settings.SNS_TOPIC_ARN = 'test-topic'
        mock_settings.TELEGRAM_BOT_TOKEN = 'test-token'
        mock_settings.TELEGRAM_CHAT_ID = 'test-chat'
        
        with patch('boto3.client'), patch('requests.post'):
            service = AlertService()
            
            # Mock channel send methods
            for channel in service.channels:
                channel.send = Mock(return_value=True)
            
            alert_data = {
                'alert_type': 'test_alert',
                'data_source': 'test_source',
                'message': 'Test message'
            }
            
            results = service.send_alert(alert_data)
            
            # Verify all channels were called
            assert len(results) == len(service.channels)
            for channel in service.channels:
                channel.send.assert_called_once_with(alert_data)
    
    def test_send_empty_alert(self):
        """Test sending empty alert data."""
        service = AlertService()
        results = service.send_alert({})
        
        assert results == {}
    
    @patch('services.alert_service.settings')
    def test_get_dashboard_alerts(self, mock_settings):
        """Test getting dashboard alerts."""
        mock_settings.SNS_TOPIC_ARN = None
        mock_settings.TELEGRAM_BOT_TOKEN = None
        mock_settings.TELEGRAM_CHAT_ID = None
        
        service = AlertService()
        
        # Send a test alert
        alert_data = {'data_source': 'test', 'message': 'test alert'}
        service.send_alert(alert_data)
        
        # Get dashboard alerts
        alerts = service.get_dashboard_alerts()
        
        assert len(alerts) >= 1
        assert alerts[0]['alert_data']['data_source'] == 'test'


if __name__ == "__main__":
    pytest.main([__file__])