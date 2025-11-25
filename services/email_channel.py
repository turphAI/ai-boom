"""
Email notification channel for sending agent summaries via email.

Supports:
- SendGrid API (recommended)
- SMTP (Gmail, Outlook, etc.)
"""

import logging
import os
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod

from tenacity import retry, stop_after_attempt, wait_exponential


class EmailProvider(ABC):
    """Abstract base class for email providers."""
    
    @abstractmethod
    def send_email(self, to: str, subject: str, html_content: str, text_content: str) -> bool:
        """Send email. Returns True if successful."""
        pass


class SendGridProvider(EmailProvider):
    """SendGrid email provider."""
    
    def __init__(self, api_key: str):
        self.logger = logging.getLogger(__name__)
        self.api_key = api_key
        self.api_url = "https://api.sendgrid.com/v3/mail/send"
        
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def send_email(self, to: str, subject: str, html_content: str, text_content: str) -> bool:
        """Send email via SendGrid API."""
        try:
            import requests
            
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'personalizations': [{
                    'to': [{'email': to}]
                }],
                'from': {
                    'email': os.getenv('EMAIL_FROM', 'noreply@boom-bust-sentinel.com'),
                    'name': 'Boom-Bust Sentinel'
                },
                'subject': subject,
                'content': [
                    {
                        'type': 'text/plain',
                        'value': text_content
                    },
                    {
                        'type': 'text/html',
                        'value': html_content
                    }
                ]
            }
            
            response = requests.post(self.api_url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            
            self.logger.info(f"Email sent successfully via SendGrid to {to}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send email via SendGrid: {e}")
            return False


class SMTPProvider(EmailProvider):
    """SMTP email provider (Gmail, Outlook, etc.)."""
    
    def __init__(self, smtp_host: str, smtp_port: int, smtp_user: str, smtp_password: str):
        self.logger = logging.getLogger(__name__)
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def send_email(self, to: str, subject: str, html_content: str, text_content: str) -> bool:
        """Send email via SMTP."""
        try:
            import smtplib
            from email.mime.multipart import MIMEMultipart
            from email.mime.text import MIMEText
            
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.smtp_user
            msg['To'] = to
            
            # Add both text and HTML parts
            text_part = MIMEText(text_content, 'plain')
            html_part = MIMEText(html_content, 'html')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            self.logger.info(f"Email sent successfully via SMTP to {to}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send email via SMTP: {e}")
            return False


class EmailNotificationChannel:
    """
    Email notification channel for agent summaries.
    
    Can be used as a NotificationChannel or standalone for summaries.
    """
    
    def __init__(self, recipient: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self.recipient = recipient or os.getenv('EMAIL_RECIPIENT', '')
        self.provider: Optional[EmailProvider] = None
        
        self._initialize_provider()
    
    def _initialize_provider(self) -> None:
        """Initialize email provider based on configuration."""
        # Try SendGrid first
        sendgrid_key = os.getenv('SENDGRID_API_KEY')
        if sendgrid_key:
            self.provider = SendGridProvider(sendgrid_key)
            self.logger.info("Initialized SendGrid email provider")
            return
        
        # Try SMTP
        smtp_host = os.getenv('SMTP_HOST')
        smtp_user = os.getenv('SMTP_USER')
        smtp_password = os.getenv('SMTP_PASSWORD')
        
        if smtp_host and smtp_user and smtp_password:
            smtp_port = int(os.getenv('SMTP_PORT', '587'))
            self.provider = SMTPProvider(smtp_host, smtp_port, smtp_user, smtp_password)
            self.logger.info("Initialized SMTP email provider")
            return
        
        self.logger.warning("No email provider configured. Set SENDGRID_API_KEY or SMTP settings.")
    
    def get_channel_name(self) -> str:
        """Get the name of this notification channel."""
        return "Email"
    
    def is_configured(self) -> bool:
        """Check if email is configured."""
        return self.provider is not None and bool(self.recipient)
    
    def send_summary(self, subject: str, html_content: str, text_content: str, 
                    recipient: Optional[str] = None) -> bool:
        """
        Send email summary.
        
        Args:
            subject: Email subject
            html_content: HTML email body
            text_content: Plain text email body
            recipient: Email recipient (uses default if not provided)
            
        Returns:
            True if sent successfully
        """
        if not self.is_configured():
            self.logger.warning("Email not configured, skipping email summary")
            return False
        
        recipient_email = recipient or self.recipient
        if not recipient_email:
            self.logger.warning("No email recipient configured")
            return False
        
        return self.provider.send_email(recipient_email, subject, html_content, text_content)
    
    def send(self, alert: Dict[str, Any]) -> bool:
        """
        Send alert via email (implements NotificationChannel interface).
        
        For agent summaries, use send_summary() instead.
        """
        if not self.is_configured():
            return False
        
        # Format alert as email
        subject = f"Boom-Bust Sentinel Alert: {alert.get('data_source', 'Unknown')}"
        text_content = self._format_alert_text(alert)
        html_content = self._format_alert_html(alert)
        
        return self.send_summary(subject, html_content, text_content)
    
    def _format_alert_text(self, alert: Dict[str, Any]) -> str:
        """Format alert as plain text."""
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
            f"Time: {alert.get('timestamp', 'Unknown')}",
            "",
            f"Message: {alert.get('message', 'No additional details')}"
        ]
        return "\n".join(lines)
    
    def _format_alert_html(self, alert: Dict[str, Any]) -> str:
        """Format alert as HTML."""
        alert_type = alert.get('alert_type', 'Unknown').replace('_', ' ').title()
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <h2 style="color: #d32f2f;">🚨 MARKET ALERT: {alert_type}</h2>
            <table style="border-collapse: collapse; width: 100%;">
                <tr><td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Data Source:</strong></td><td style="padding: 8px; border-bottom: 1px solid #ddd;">{alert.get('data_source', 'Unknown')}</td></tr>
                <tr><td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Metric:</strong></td><td style="padding: 8px; border-bottom: 1px solid #ddd;">{alert.get('metric_name', 'Unknown')}</td></tr>
                <tr><td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Current Value:</strong></td><td style="padding: 8px; border-bottom: 1px solid #ddd;">{alert.get('current_value', 'N/A')}</td></tr>
                <tr><td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Previous Value:</strong></td><td style="padding: 8px; border-bottom: 1px solid #ddd;">{alert.get('previous_value', 'N/A')}</td></tr>
                <tr><td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Change:</strong></td><td style="padding: 8px; border-bottom: 1px solid #ddd;">{alert.get('change_percent', 'N/A')}%</td></tr>
                <tr><td style="padding: 8px;"><strong>Time:</strong></td><td style="padding: 8px;">{alert.get('timestamp', 'Unknown')}</td></tr>
            </table>
            <p style="margin-top: 20px;">{alert.get('message', 'No additional details')}</p>
        </body>
        </html>
        """

