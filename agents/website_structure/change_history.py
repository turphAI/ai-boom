"""
Change History - Tracks and stores structure change history.

Maintains a history of all detected structure changes for analysis and reporting.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import asdict

from agents.website_structure.website_structure_monitor import StructureChange


class ChangeHistory:
    """
    Manages history of structure changes.
    
    Usage:
        history = ChangeHistory()
        history.record_change(change)
        recent_changes = history.get_recent_changes(days=7)
    """
    
    def __init__(self, storage_dir: str = "logs/website_structure"):
        self.logger = logging.getLogger(__name__)
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.history_file = self.storage_dir / "change_history.jsonl"
    
    def record_change(self, change: StructureChange) -> bool:
        """
        Record a structure change to history.
        
        Args:
            change: StructureChange object to record
            
        Returns:
            True if recorded successfully
        """
        try:
            change_data = {
                'url': change.url,
                'change_type': change.change_type,
                'severity': change.severity,
                'detected_at': change.detected_at.isoformat(),
                'broken_selectors': change.broken_selectors,
                'description': change.description,
                'baseline_timestamp': change.baseline_snapshot.timestamp.isoformat(),
                'current_timestamp': change.current_snapshot.timestamp.isoformat()
            }
            
            # Append to JSONL file
            with open(self.history_file, 'a') as f:
                f.write(json.dumps(change_data) + '\n')
            
            self.logger.info(f"✅ Recorded structure change: {change.url} ({change.severity})")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to record change: {e}")
            return False
    
    def get_recent_changes(self, days: int = 7, url: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get recent structure changes.
        
        Args:
            days: Number of days to look back
            url: Filter by specific URL (optional)
            
        Returns:
            List of change dictionaries
        """
        if not self.history_file.exists():
            return []
        
        cutoff_date = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        cutoff_date = cutoff_date.replace(day=cutoff_date.day - days)
        
        changes = []
        
        try:
            with open(self.history_file, 'r') as f:
                for line in f:
                    if not line.strip():
                        continue
                    
                    change_data = json.loads(line)
                    
                    # Filter by date
                    detected_at = datetime.fromisoformat(change_data['detected_at'])
                    if detected_at < cutoff_date:
                        continue
                    
                    # Filter by URL if specified
                    if url and change_data['url'] != url:
                        continue
                    
                    changes.append(change_data)
            
            # Sort by date (newest first)
            changes.sort(key=lambda x: x['detected_at'], reverse=True)
            
        except Exception as e:
            self.logger.error(f"Failed to read change history: {e}")
        
        return changes
    
    def get_change_stats(self, days: int = 30) -> Dict[str, Any]:
        """
        Get statistics about structure changes.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dictionary with statistics
        """
        changes = self.get_recent_changes(days=days)
        
        if not changes:
            return {
                'total_changes': 0,
                'by_severity': {},
                'by_url': {},
                'by_type': {}
            }
        
        stats = {
            'total_changes': len(changes),
            'by_severity': {},
            'by_url': {},
            'by_type': {}
        }
        
        for change in changes:
            # Count by severity
            severity = change.get('severity', 'UNKNOWN')
            stats['by_severity'][severity] = stats['by_severity'].get(severity, 0) + 1
            
            # Count by URL
            url = change.get('url', 'UNKNOWN')
            stats['by_url'][url] = stats['by_url'].get(url, 0) + 1
            
            # Count by type
            change_type = change.get('change_type', 'UNKNOWN')
            stats['by_type'][change_type] = stats['by_type'].get(change_type, 0) + 1
        
        return stats
    
    def get_url_change_history(self, url: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get change history for a specific URL.
        
        Args:
            url: URL to get history for
            limit: Maximum number of changes to return
            
        Returns:
            List of change dictionaries
        """
        changes = self.get_recent_changes(days=365, url=url)  # Look back 1 year
        return changes[:limit]

