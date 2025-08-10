"""
Alert service for sending notifications through multiple channels.
"""

import json
import logging
import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from config.settings import settings
from models.core import Alert


class NotificationChannel(ABC):
    """Abstract base class for notification channels."""
    
    @abstractmethod
    def send(self, alert: Dict[str, Any]) -> bool:
        """Send alert through this channel. Returns True if successful."""
        pass
    
    @abstractmethod
    def get_channel_name(self) -> str:
        """Get the name of this notification channel."""
        pass


class SNSNotificationChannel(NotificationChannel):
    """AWS SNS notification channel for email/SMS."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.topic_arn = settings.SNS_TOPIC_ARN
        
        if self.topic_arn:
            try:
                import boto3
                self.sns_client = boto3.client('sns', region_name=settings.AWS_REGION)
            except ImportError:
                self.logger.error("boto3 not installed. Install with: pip install boto3")
                self.sns_client = None
        else:
            self.sns_client = None
    
    def get_channel_name(self) -> str:
        return "SNS"
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def send(self, alert: Dict[str, Any]) -> bool:
        """Send alert via AWS SNS."""
        if not self.sns_client or not self.topic_arn:
            self.logger.warning("SNS not configured, skipping SNS notification")
            return False
        
        try:
            # Format message for SNS
            subject = f"Boom-Bust Sentinel Alert: {alert.get('data_source', 'Unknown')}"
            message = self._format_sns_message(alert)
            
            # Send to SNS topic
            response = self.sns_client.publish(
                TopicArn=self.topic_arn,
                Subject=subject,
                Message=message
            )
            
            self.logger.info(f"SNS alert sent successfully. MessageId: {response.get('MessageId')}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send SNS alert: {e}")
            return False
    
    def _format_sns_message(self, alert: Dict[str, Any]) -> str:
        """Format alert message for SNS."""
        lines = [
            f"🚨 MARKET ALERT: {alert.get('alert_type', 'Unknown').replace('_', ' ').title()}",
            "",
            f"Data Source: {alert.get('data_source', 'Unknown')}",
            f"Metric: {alert.get('metric_name', 'Unknown')}",
            f"Current Value: {alert.get('current_value', 'N/A')}",
            f"Previous Value: {alert.get('previous_value', 'N/A')}",
            f"Change: {alert.get('change_percent', 'N/A')}%",
            f"Threshold: {alert.get('threshold', 'N/A')}",
            "",
            f"Time: {alert.get('timestamp', datetime.now(timezone.utc).isoformat())}",
            "",
            f"Message: {alert.get('message', 'No additional details')}"
        ]
        
        # Add context if available
        context = alert.get('context', {})
        if context:
            lines.append("")
            lines.append("Additional Context:")
            for key, value in context.items():
                lines.append(f"  {key}: {value}")
        
        return "\n".join(lines)


class TelegramNotificationChannel(NotificationChannel):
    """Telegram Bot notification channel."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.bot_token = settings.TELEGRAM_BOT_TOKEN
        self.chat_id = settings.TELEGRAM_CHAT_ID
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage" if self.bot_token else None
    
    def get_channel_name(self) -> str:
        return "Telegram"
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def send(self, alert: Dict[str, Any]) -> bool:
        """Send alert via Telegram Bot API."""
        if not self.api_url or not self.chat_id:
            self.logger.warning("Telegram not configured, skipping Telegram notification")
            return False
        
        try:
            message = self._format_telegram_message(alert)
            
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'Markdown',
                'disable_web_page_preview': True
            }
            
            response = requests.post(self.api_url, json=payload, timeout=10)
            response.raise_for_status()
            
            self.logger.info("Telegram alert sent successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send Telegram alert: {e}")
            return False
    
    def _format_telegram_message(self, alert: Dict[str, Any]) -> str:
        """Format alert message for Telegram with Markdown."""
        alert_type = alert.get('alert_type', 'Unknown').replace('_', ' ').title()
        
        lines = [
            f"🚨 *MARKET ALERT*: {alert_type}",
            "",
            f"*Data Source:* {alert.get('data_source', 'Unknown')}",
            f"*Metric:* {alert.get('metric_name', 'Unknown')}",
            f"*Current Value:* `{alert.get('current_value', 'N/A')}`",
            f"*Previous Value:* `{alert.get('previous_value', 'N/A')}`",
            f"*Change:* `{alert.get('change_percent', 'N/A')}%`",
            f"*Threshold:* `{alert.get('threshold', 'N/A')}`",
            "",
            f"*Time:* {alert.get('timestamp', datetime.now(timezone.utc).isoformat())}",
            "",
            f"*Details:* {alert.get('message', 'No additional details')}"
        ]
        
        # Add context if available
        context = alert.get('context', {})
        if context:
            lines.append("")
            lines.append("*Additional Context:*")
            for key, value in context.items():
                lines.append(f"  • {key}: `{value}`")
        
        return "\n".join(lines)


class DashboardNotificationChannel(NotificationChannel):
    """Dashboard-based notification channel that stores alerts for web UI."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.alerts_file = "data/dashboard_alerts.json"
        
        # Ensure data directory exists
        import os
        os.makedirs(os.path.dirname(self.alerts_file), exist_ok=True)
    
    def get_channel_name(self) -> str:
        return "Dashboard"
    
    def send(self, alert: Dict[str, Any]) -> bool:
        """Store alert for dashboard display."""
        try:
            # Load existing alerts
            alerts = self._load_alerts()
            
            # Add new alert with unique ID
            alert_record = {
                'id': f"{alert.get('data_source', 'unknown')}_{int(time.time())}",
                'timestamp': alert.get('timestamp', datetime.now(timezone.utc).isoformat()),
                'acknowledged': False,
                'alert_data': alert
            }
            
            alerts.append(alert_record)
            
            # Keep only last 100 alerts to prevent file from growing too large
            alerts = alerts[-100:]
            
            # Save alerts
            self._save_alerts(alerts)
            
            self.logger.info(f"Alert stored for dashboard: {alert_record['id']}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to store dashboard alert: {e}")
            return False
    
    def _load_alerts(self) -> List[Dict[str, Any]]:
        """Load alerts from file."""
        try:
            with open(self.alerts_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def _save_alerts(self, alerts: List[Dict[str, Any]]) -> None:
        """Save alerts to file."""
        with open(self.alerts_file, 'w') as f:
            json.dump(alerts, f, indent=2, default=str)
    
    def get_recent_alerts(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent alerts for dashboard display."""
        alerts = self._load_alerts()
        # Sort by timestamp in reverse chronological order (newest first)
        alerts.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        return alerts[:limit]
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """Mark an alert as acknowledged."""
        try:
            alerts = self._load_alerts()
            
            for alert in alerts:
                if alert['id'] == alert_id:
                    alert['acknowledged'] = True
                    alert['acknowledged_at'] = datetime.now(timezone.utc).isoformat()
                    break
            
            self._save_alerts(alerts)
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to acknowledge alert {alert_id}: {e}")
            return False


class AlertService:
    """Main alert service that coordinates multiple notification channels."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.channels: List[NotificationChannel] = []
        
        # Initialize notification channels
        self._initialize_channels()
    
    def _initialize_channels(self) -> None:
        """Initialize all configured notification channels."""
        # Always add dashboard channel
        self.channels.append(DashboardNotificationChannel())
        
        # Add SNS if configured
        if settings.SNS_TOPIC_ARN:
            self.channels.append(SNSNotificationChannel())
        
        # Add Telegram if configured
        if settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_CHAT_ID:
            self.channels.append(TelegramNotificationChannel())
        
        self.logger.info(f"Initialized {len(self.channels)} notification channels: {[c.get_channel_name() for c in self.channels]}")
    
    def send_alert(self, alert_data: Dict[str, Any]) -> Dict[str, bool]:
        """Send alert through all configured channels."""
        if not alert_data:
            self.logger.warning("Empty alert data provided")
            return {}
        
        # Add timestamp if not present
        if 'timestamp' not in alert_data:
            alert_data['timestamp'] = datetime.now(timezone.utc).isoformat()
        
        results = {}
        successful_channels = []
        failed_channels = []
        
        # Send through each channel
        for channel in self.channels:
            channel_name = channel.get_channel_name()
            
            try:
                success = channel.send(alert_data)
                results[channel_name] = success
                
                if success:
                    successful_channels.append(channel_name)
                else:
                    failed_channels.append(channel_name)
                    
            except Exception as e:
                self.logger.error(f"Error sending alert through {channel_name}: {e}")
                results[channel_name] = False
                failed_channels.append(channel_name)
        
        # Log results
        if successful_channels:
            self.logger.info(f"Alert sent successfully through: {', '.join(successful_channels)}")
        
        if failed_channels:
            self.logger.warning(f"Alert failed to send through: {', '.join(failed_channels)}")
        
        return results
    
    def get_dashboard_alerts(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent alerts for dashboard display."""
        for channel in self.channels:
            if isinstance(channel, DashboardNotificationChannel):
                return channel.get_recent_alerts(limit)
        return []
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert in the dashboard."""
        for channel in self.channels:
            if isinstance(channel, DashboardNotificationChannel):
                return channel.acknowledge_alert(alert_id)
        return False