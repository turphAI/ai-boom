"""
Data management utilities for the Boom-Bust Sentinel system.
"""

import json
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional

from services.state_store import create_state_store


class DataManager:
    """Utility class for managing stored data."""
    
    def __init__(self):
        self.state_store = create_state_store()
    
    def get_data_summary(self) -> Dict[str, any]:
        """Get a summary of all stored data."""
        # This is a simplified implementation for file-based storage
        # In production with DynamoDB, this would query all partition keys
        
        summary = {
            'total_data_sources': 0,
            'data_sources': {},
            'oldest_data': None,
            'newest_data': None
        }
        
        # For file-based storage, we can scan the data directory
        if hasattr(self.state_store, 'data_dir'):
            import os
            data_dir = self.state_store.data_dir
            
            if os.path.exists(data_dir):
                for filename in os.listdir(data_dir):
                    if filename.endswith('.json'):
                        # Parse filename to get data source and metric
                        parts = filename[:-5].split('_', 1)  # Remove .json extension
                        if len(parts) == 2:
                            data_source, metric = parts
                            
                            if data_source not in summary['data_sources']:
                                summary['data_sources'][data_source] = []
                            
                            summary['data_sources'][data_source].append(metric)
                
                summary['total_data_sources'] = len(summary['data_sources'])
        
        return summary
    
    def export_data(self, data_source: str, metric: str, days: int = 30) -> List[Dict]:
        """Export data for a specific data source and metric."""
        return self.state_store.get_historical_data(data_source, metric, days)
    
    def cleanup_data(self, retention_days: int = 730) -> None:
        """Clean up old data."""
        self.state_store.cleanup_old_data(retention_days)
        print(f"Cleaned up data older than {retention_days} days")
    
    def backup_data(self, backup_file: str) -> None:
        """Create a backup of all data."""
        summary = self.get_data_summary()
        backup_data = {
            'backup_timestamp': datetime.now(timezone.utc).isoformat(),
            'summary': summary,
            'data': {}
        }
        
        # Export all data
        for data_source, metrics in summary.get('data_sources', {}).items():
            backup_data['data'][data_source] = {}
            for metric in metrics:
                backup_data['data'][data_source][metric] = self.export_data(
                    data_source, metric, days=365 * 2  # 2 years
                )
        
        # Save backup
        with open(backup_file, 'w') as f:
            json.dump(backup_data, f, indent=2, default=str)
        
        print(f"Backup saved to {backup_file}")
    
    def restore_data(self, backup_file: str) -> None:
        """Restore data from a backup file."""
        with open(backup_file, 'r') as f:
            backup_data = json.load(f)
        
        # Restore data
        for data_source, metrics in backup_data.get('data', {}).items():
            for metric, data_points in metrics.items():
                for data_point in data_points:
                    self.state_store.save_data(
                        data_source, 
                        metric, 
                        data_point.get('data', {})
                    )
        
        print(f"Data restored from {backup_file}")


def main():
    """Command-line interface for data management."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python data_manager.py <command> [args]")
        print("Commands:")
        print("  summary - Show data summary")
        print("  cleanup [days] - Clean up old data (default: 730 days)")
        print("  backup <file> - Create backup")
        print("  restore <file> - Restore from backup")
        print("  export <data_source> <metric> [days] - Export specific data")
        return
    
    manager = DataManager()
    command = sys.argv[1]
    
    if command == 'summary':
        summary = manager.get_data_summary()
        print(json.dumps(summary, indent=2))
    
    elif command == 'cleanup':
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 730
        manager.cleanup_data(days)
    
    elif command == 'backup':
        if len(sys.argv) < 3:
            print("Error: backup file required")
            return
        manager.backup_data(sys.argv[2])
    
    elif command == 'restore':
        if len(sys.argv) < 3:
            print("Error: backup file required")
            return
        manager.restore_data(sys.argv[2])
    
    elif command == 'export':
        if len(sys.argv) < 4:
            print("Error: data_source and metric required")
            return
        data_source = sys.argv[2]
        metric = sys.argv[3]
        days = int(sys.argv[4]) if len(sys.argv) > 4 else 30
        
        data = manager.export_data(data_source, metric, days)
        print(json.dumps(data, indent=2, default=str))
    
    else:
        print(f"Unknown command: {command}")


if __name__ == "__main__":
    main()