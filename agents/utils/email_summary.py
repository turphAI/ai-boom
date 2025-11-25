"""
Email Summary Generator - Creates formatted email summaries from agent results.

Generates HTML and text email content for agent execution summaries.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

from services.email_channel import EmailNotificationChannel
from agents.website_structure.change_history import ChangeHistory


class EmailSummaryGenerator:
    """Generates email summaries from agent results."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.email_channel = EmailNotificationChannel()
    
    def generate_summary_from_report(self, report: Dict[str, Any]) -> tuple[str, str]:
        """
        Generate HTML and text email content from agent report.
        
        Returns:
            Tuple of (html_content, text_content)
        """
        summary = report.get('execution_summary', {})
        scraper_results = report.get('scraper_results', {})
        patterns = report.get('detected_patterns', [])
        timestamp = report.get('timestamp', datetime.now().isoformat())
        
        # Get recent structure changes
        change_history = ChangeHistory()
        recent_changes = change_history.get_recent_changes(days=1)  # Last 24 hours
        
        # Format timestamp
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            formatted_time = dt.strftime('%B %d, %Y at %I:%M %p UTC')
        except:
            formatted_time = timestamp
        
        # Calculate stats
        total = summary.get('total', 0)
        successful = summary.get('successful', 0)
        failed = summary.get('failed', 0)
        success_rate = (successful / total * 100) if total > 0 else 0
        
        # Generate HTML
        html_content = self._generate_html_summary(
            formatted_time, total, successful, failed, success_rate,
            scraper_results, patterns, recent_changes
        )
        
        # Generate text
        text_content = self._generate_text_summary(
            formatted_time, total, successful, failed, success_rate,
            scraper_results, patterns, recent_changes
        )
        
        return html_content, text_content
    
    def _generate_html_summary(self, timestamp: str, total: int, successful: int,
                              failed: int, success_rate: float,
                              scraper_results: Dict[str, Any],
                              patterns: List[Dict[str, Any]],
                              structure_changes: List[Dict[str, Any]] = None) -> str:
        """Generate HTML email content."""
        
        # Status color
        if success_rate >= 90:
            status_color = "#4caf50"  # Green
            status_emoji = "✅"
        elif success_rate >= 70:
            status_color = "#ff9800"  # Orange
            status_emoji = "⚠️"
        else:
            status_color = "#f44336"  # Red
            status_emoji = "❌"
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 10px 10px 0 0; color: white;">
                <h1 style="margin: 0; font-size: 24px;">🤖 Boom-Bust Sentinel</h1>
                <p style="margin: 10px 0 0 0; opacity: 0.9;">Daily Agent Summary</p>
            </div>
            
            <div style="background: #f8f9fa; padding: 20px; border-radius: 0 0 10px 10px;">
                <p style="margin: 0 0 20px 0; color: #666; font-size: 14px;">Generated: {timestamp}</p>
                
                <div style="background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <h2 style="margin: 0 0 15px 0; color: {status_color}; font-size: 20px;">
                        {status_emoji} Scraper Execution Summary
                    </h2>
                    <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px;">
                        <div>
                            <div style="font-size: 32px; font-weight: bold; color: {status_color};">{successful}/{total}</div>
                            <div style="color: #666; font-size: 14px;">Successful</div>
                        </div>
                        <div>
                            <div style="font-size: 32px; font-weight: bold; color: #f44336;">{failed}/{total}</div>
                            <div style="color: #666; font-size: 14px;">Failed</div>
                        </div>
                    </div>
                    <div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid #eee;">
                        <div style="font-size: 18px; font-weight: bold; color: {status_color};">{success_rate:.1f}%</div>
                        <div style="color: #666; font-size: 14px;">Success Rate</div>
                    </div>
                </div>
        """
        
        # Scraper results
        if scraper_results:
            html += """
                <div style="background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <h2 style="margin: 0 0 15px 0; font-size: 18px;">🔍 Scraper Results</h2>
                    <table style="width: 100%; border-collapse: collapse;">
            """
            
            for name, result in scraper_results.items():
                success = result.get('success', False)
                status_icon = "✅" if success else "❌"
                status_color = "#4caf50" if success else "#f44336"
                exec_time = result.get('execution_time', 0)
                error = result.get('error_message', '')
                
                html += f"""
                        <tr style="border-bottom: 1px solid #eee;">
                            <td style="padding: 10px 0;">
                                <span style="font-size: 18px; margin-right: 8px;">{status_icon}</span>
                                <strong>{name.replace('_', ' ').title()}</strong>
                            </td>
                            <td style="text-align: right; padding: 10px 0; color: #666;">
                                {exec_time:.2f}s
                            </td>
                        </tr>
                """
                
                if error:
                    html += f"""
                        <tr>
                            <td colspan="2" style="padding: 5px 0 10px 30px; color: #f44336; font-size: 13px;">
                                {error[:100]}{'...' if len(error) > 100 else ''}
                            </td>
                        </tr>
                    """
            
            html += """
                    </table>
                </div>
            """
        
        # Patterns
        if patterns:
            html += """
                <div style="background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <h2 style="margin: 0 0 15px 0; font-size: 18px;">🔍 Failure Patterns Detected</h2>
            """
            
            for i, pattern in enumerate(patterns[:5], 1):  # Limit to 5
                pattern_type = pattern.get('pattern_type', 'Unknown')
                scraper_name = pattern.get('scraper_name', 'Unknown')
                frequency = pattern.get('frequency', 0)
                confidence = pattern.get('confidence', 0)
                suggested_fix = pattern.get('suggested_fix', 'N/A')
                
                html += f"""
                    <div style="margin-bottom: 15px; padding: 15px; background: #fff3cd; border-left: 4px solid #ff9800; border-radius: 4px;">
                        <div style="font-weight: bold; margin-bottom: 5px;">
                            Pattern {i}: {pattern_type.replace('_', ' ').title()}
                        </div>
                        <div style="color: #666; font-size: 14px; margin-bottom: 5px;">
                            Scraper: <strong>{scraper_name}</strong> | 
                            Frequency: <strong>{frequency}</strong> | 
                            Confidence: <strong>{confidence:.2f}</strong>
                        </div>
                        <div style="color: #333; font-size: 13px; margin-top: 8px;">
                            💡 <strong>Suggested Fix:</strong> {suggested_fix[:150]}{'...' if len(suggested_fix) > 150 else ''}
                        </div>
                    </div>
                """
            
            html += """
                </div>
            """
        
        # Structure Changes
        if structure_changes:
            html += """
                <div style="background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <h2 style="margin: 0 0 15px 0; font-size: 18px;">🌐 Website Structure Changes</h2>
            """
            
            for change in structure_changes[:5]:  # Limit to 5
                severity = change.get('severity', 'UNKNOWN')
                severity_color = {
                    'CRITICAL': '#f44336',
                    'HIGH': '#ff9800',
                    'MEDIUM': '#ffc107',
                    'LOW': '#4caf50'
                }.get(severity, '#666')
                
                url = change.get('url', 'Unknown')
                broken_selectors = change.get('broken_selectors', [])
                
                html += f"""
                    <div style="margin-bottom: 15px; padding: 15px; background: #fff3cd; border-left: 4px solid {severity_color}; border-radius: 4px;">
                        <div style="font-weight: bold; margin-bottom: 5px; color: {severity_color};">
                            {severity} - {change.get('change_type', 'Unknown').replace('_', ' ').title()}
                        </div>
                        <div style="color: #666; font-size: 14px; margin-bottom: 5px;">
                            URL: <strong>{url[:60]}{'...' if len(url) > 60 else ''}</strong>
                        </div>
                """
                
                if broken_selectors:
                    html += f"""
                        <div style="color: #f44336; font-size: 13px; margin-top: 8px;">
                            ⚠️ Broken Selectors: {', '.join(broken_selectors[:3])}
                            {'...' if len(broken_selectors) > 3 else ''}
                        </div>
                    """
                
                html += """
                    </div>
                """
            
            html += """
                </div>
            """
        
        # Footer
        html += """
                <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; color: #666; font-size: 12px;">
                    <p>View full reports in GitHub Actions or run: <code>python scripts/view_agent_report.py</code></p>
                    <p style="margin-top: 10px;">Boom-Bust Sentinel Agent System</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _generate_text_summary(self, timestamp: str, total: int, successful: int,
                             failed: int, success_rate: float,
                             scraper_results: Dict[str, Any],
                             patterns: List[Dict[str, Any]],
                             structure_changes: List[Dict[str, Any]] = None) -> str:
        """Generate plain text email content."""
        
        lines = [
            "=" * 60,
            "🤖 BOOM-BUST SENTINEL - DAILY AGENT SUMMARY",
            "=" * 60,
            f"Generated: {timestamp}",
            "",
            f"📊 SCRAPER EXECUTION SUMMARY",
            f"   Successful: {successful}/{total}",
            f"   Failed: {failed}/{total}",
            f"   Success Rate: {success_rate:.1f}%",
            ""
        ]
        
        # Scraper results
        if scraper_results:
            lines.append("🔍 SCRAPER RESULTS:")
            for name, result in scraper_results.items():
                success = result.get('success', False)
                status = "✅" if success else "❌"
                exec_time = result.get('execution_time', 0)
                error = result.get('error_message', '')
                
                lines.append(f"   {status} {name.replace('_', ' ').title()}: {exec_time:.2f}s")
                if error:
                    lines.append(f"      Error: {error[:80]}...")
            lines.append("")
        
        # Patterns
        if patterns:
            lines.append("🔍 FAILURE PATTERNS DETECTED:")
            for i, pattern in enumerate(patterns[:5], 1):
                pattern_type = pattern.get('pattern_type', 'Unknown')
                scraper_name = pattern.get('scraper_name', 'Unknown')
                frequency = pattern.get('frequency', 0)
                confidence = pattern.get('confidence', 0)
                suggested_fix = pattern.get('suggested_fix', 'N/A')
                
                lines.append(f"   Pattern {i}: {pattern_type.replace('_', ' ').title()}")
                lines.append(f"      Scraper: {scraper_name}")
                lines.append(f"      Frequency: {frequency} | Confidence: {confidence:.2f}")
                lines.append(f"      Suggested Fix: {suggested_fix[:100]}...")
                lines.append("")
        
        # Structure Changes
        if structure_changes:
            lines.append("🌐 WEBSITE STRUCTURE CHANGES:")
            for change in structure_changes[:5]:
                severity = change.get('severity', 'UNKNOWN')
                url = change.get('url', 'Unknown')
                broken_selectors = change.get('broken_selectors', [])
                
                lines.append(f"   {severity}: {change.get('change_type', 'Unknown').replace('_', ' ').title()}")
                lines.append(f"      URL: {url[:60]}...")
                if broken_selectors:
                    lines.append(f"      Broken Selectors: {', '.join(broken_selectors[:3])}")
                lines.append("")
        
        lines.extend([
            "=" * 60,
            "View full reports: python scripts/view_agent_report.py",
            "=" * 60
        ])
        
        return "\n".join(lines)
    
    def send_summary_email(self, report: Dict[str, Any], 
                          recipient: Optional[str] = None) -> bool:
        """
        Generate and send email summary from agent report.
        
        Args:
            report: Agent report dictionary
            recipient: Email recipient (uses default if not provided)
            
        Returns:
            True if sent successfully
        """
        if not self.email_channel.is_configured():
            self.logger.warning("Email not configured, skipping email summary")
            return False
        
        try:
            # Generate content
            html_content, text_content = self.generate_summary_from_report(report)
            
            # Generate subject
            summary = report.get('execution_summary', {})
            total = summary.get('total', 0)
            successful = summary.get('successful', 0)
            failed = summary.get('failed', 0)
            
            # Format date
            timestamp = report.get('timestamp', datetime.now().isoformat())
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                date_str = dt.strftime('%b %d, %Y')
            except:
                date_str = datetime.now().strftime('%b %d, %Y')
            
            if failed > 0:
                subject = f"⚠️ Boom-Bust Sentinel Summary ({date_str}) - {successful}/{total} Successful, {failed} Failed"
            else:
                subject = f"✅ Boom-Bust Sentinel Summary ({date_str}) - All {total} Scrapers Successful"
            
            # Send email
            return self.email_channel.send_summary(subject, html_content, text_content, recipient)
            
        except Exception as e:
            self.logger.error(f"Failed to send email summary: {e}", exc_info=True)
            return False

