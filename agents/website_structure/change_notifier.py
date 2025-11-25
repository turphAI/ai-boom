"""
Change Notifier - Alerts when website structure changes are detected.

Integrates with alert service to send notifications about structure changes.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from agents.website_structure.website_structure_monitor import StructureChange
from services.alert_service import AlertService


class ChangeNotifier:
    """
    Notifies about structure changes via alert service.
    
    Usage:
        notifier = ChangeNotifier()
        notifier.notify_changes(changes)
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.alert_service = AlertService()
    
    def notify_changes(self, changes: List[StructureChange]) -> Dict[str, bool]:
        """
        Send notifications for detected structure changes.
        
        Args:
            changes: List of StructureChange objects
            
        Returns:
            Dictionary mapping notification channels to success status
        """
        if not changes:
            return {}
        
        results = {}
        
        # Group changes by severity
        critical_changes = [c for c in changes if c.severity == 'CRITICAL']
        high_changes = [c for c in changes if c.severity == 'HIGH']
        other_changes = [c for c in changes if c.severity in ['MEDIUM', 'LOW']]
        
        # Send critical alerts immediately
        if critical_changes:
            results.update(self._send_critical_alert(critical_changes))
        
        # Send high priority alerts
        if high_changes:
            results.update(self._send_high_priority_alert(high_changes))
        
        # Send summary for all changes
        if changes:
            results.update(self._send_summary_alert(changes))
        
        return results
    
    def _send_critical_alert(self, changes: List[StructureChange]) -> Dict[str, bool]:
        """Send critical alert for broken selectors."""
        change = changes[0]  # Focus on first critical change
        
        alert_data = {
            'alert_type': 'STRUCTURE_CHANGE_CRITICAL',
            'data_source': change.url,
            'metric_name': 'website_structure',
            'current_value': 'CRITICAL',
            'previous_value': 'OK',
            'change_percent': 100,
            'threshold': 'CRITICAL',
            'message': f"🚨 CRITICAL: Website structure changed - {len(change.broken_selectors)} selector(s) broken",
            'timestamp': change.detected_at.isoformat(),
            'context': {
                'url': change.url,
                'change_type': change.change_type,
                'severity': change.severity,
                'broken_selectors': change.broken_selectors,
                'description': change.description,
                'total_critical_changes': len(changes)
            }
        }
        
        return self.alert_service.send_alert(alert_data)
    
    def _send_high_priority_alert(self, changes: List[StructureChange]) -> Dict[str, bool]:
        """Send high priority alert for structure changes."""
        change = changes[0]  # Focus on first high priority change
        
        alert_data = {
            'alert_type': 'STRUCTURE_CHANGE_HIGH',
            'data_source': change.url,
            'metric_name': 'website_structure',
            'current_value': 'HIGH',
            'previous_value': 'OK',
            'change_percent': 50,
            'threshold': 'HIGH',
            'message': f"⚠️ HIGH: Website structure changed - may affect scrapers",
            'timestamp': change.detected_at.isoformat(),
            'context': {
                'url': change.url,
                'change_type': change.change_type,
                'severity': change.severity,
                'description': change.description,
                'total_high_changes': len(changes)
            }
        }
        
        return self.alert_service.send_alert(alert_data)
    
    def _send_summary_alert(self, changes: List[StructureChange]) -> Dict[str, bool]:
        """Send summary alert for all changes."""
        total_changes = len(changes)
        critical_count = len([c for c in changes if c.severity == 'CRITICAL'])
        high_count = len([c for c in changes if c.severity == 'HIGH'])
        
        # Get first change for details
        first_change = changes[0]
        
        alert_data = {
            'alert_type': 'STRUCTURE_CHANGE_SUMMARY',
            'data_source': 'website_structure_monitor',
            'metric_name': 'structure_changes',
            'current_value': total_changes,
            'previous_value': 0,
            'change_percent': 100,
            'threshold': 'ANY',
            'message': f"📊 Structure Monitoring Summary: {total_changes} change(s) detected ({critical_count} critical, {high_count} high)",
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'context': {
                'total_changes': total_changes,
                'critical_count': critical_count,
                'high_count': high_count,
                'changes': [
                    {
                        'url': c.url,
                        'severity': c.severity,
                        'change_type': c.change_type,
                        'broken_selectors': c.broken_selectors
                    }
                    for c in changes[:5]  # Limit to first 5
                ]
            }
        }
        
        return self.alert_service.send_alert(alert_data)

