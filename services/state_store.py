"""
State store interface for persisting scraped data.
"""

import json
import os
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any
import logging

from config.settings import settings

# Import firestore conditionally to avoid dependency issues
try:
    from google.cloud import firestore
except ImportError:
    firestore = None


class BaseStateStore(ABC):
    """Abstract base class for state storage implementations."""
    
    @abstractmethod
    def save_data(self, data_source: str, metric_name: str, data: Dict[str, Any]) -> None:
        """Save data to the state store."""
        pass
    
    @abstractmethod
    def get_historical_data(self, data_source: str, metric: str, days: int = 7) -> List[Dict]:
        """Get historical data for comparison."""
        pass
    
    @abstractmethod
    def get_latest_value(self, data_source: str, metric: str) -> Optional[Dict]:
        """Get the most recent value for a metric."""
        pass
    
    @abstractmethod
    def cleanup_old_data(self, retention_days: int = 730) -> None:
        """Clean up old data based on retention policy."""
        pass


class FileStateStore(BaseStateStore):
    """File-based state store implementation for development and testing."""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.logger = logging.getLogger(__name__)
        
        # Create data directory if it doesn't exist
        os.makedirs(data_dir, exist_ok=True)
    
    def _get_file_path(self, data_source: str, metric: str) -> str:
        """Get the file path for a specific data source and metric."""
        filename = f"{data_source}_{metric}.json"
        return os.path.join(self.data_dir, filename)
    
    def _load_data(self, file_path: str) -> List[Dict[str, Any]]:
        """Load data from a JSON file."""
        if not os.path.exists(file_path):
            return []
        
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except (json.JSONDecodeError, IOError) as e:
            self.logger.error(f"Error loading data from {file_path}: {e}")
            return []
    
    def _save_data_to_file(self, file_path: str, data: List[Dict[str, Any]]) -> None:
        """Save data to a JSON file."""
        try:
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except IOError as e:
            self.logger.error(f"Error saving data to {file_path}: {e}")
            raise
    
    def save_data(self, data_source: str, metric_name: str, data: Dict[str, Any]) -> None:
        """Save data to the file-based store."""
        file_path = self._get_file_path(data_source, metric_name)
        
        # Add timestamp if not present
        if 'timestamp' not in data:
            data['timestamp'] = datetime.now(timezone.utc).isoformat()
        
        # Create the new data point
        data_point = {
            'data_source': data_source,
            'metric_name': metric_name,
            'timestamp': data['timestamp'],
            'data': data
        }
        
        # For daily automation, we only keep the most recent data point
        # This prevents duplicate cards in the dashboard
        new_data = [data_point]
        
        # Save to file (replacing any existing data)
        self._save_data_to_file(file_path, new_data)
        
        self.logger.info(f"Saved data for {data_source}.{metric_name}")
    
    def get_recent_data(self, data_source: str, metric_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent data points for a data source and metric."""
        file_path = self._get_file_path(data_source, metric_name)
        
        if not os.path.exists(file_path):
            return []
        
        try:
            existing_data = self._load_data_from_file(file_path)
            
            # Sort by timestamp (newest first)
            def get_timestamp_for_sort(item):
                timestamp = item['timestamp']
                if isinstance(timestamp, str):
                    try:
                        return datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    except:
                        return datetime.min.replace(tzinfo=timezone.utc)
                elif isinstance(timestamp, datetime):
                    # Ensure timezone-aware datetime
                    if timestamp.tzinfo is None:
                        return timestamp.replace(tzinfo=timezone.utc)
                    return timestamp
                else:
                    return datetime.min.replace(tzinfo=timezone.utc)
            
            existing_data.sort(key=get_timestamp_for_sort, reverse=True)
            
            return existing_data[:limit]
            
        except Exception as e:
            self.logger.error(f"Error loading recent data for {data_source}.{metric_name}: {e}")
            return []
    
    def get_historical_data(self, data_source: str, metric: str, days: int = 7) -> List[Dict]:
        """Get historical data for the specified number of days."""
        file_path = self._get_file_path(data_source, metric)
        all_data = self._load_data(file_path)
        
        # Filter data within the specified time range
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        historical_data = []
        for item in all_data:
            try:
                item_date = datetime.fromisoformat(item['timestamp'].replace('Z', '+00:00'))
                if item_date >= cutoff_date:
                    historical_data.append(item)
            except (ValueError, KeyError) as e:
                self.logger.warning(f"Invalid timestamp in data: {e}")
                continue
        
        return historical_data
    
    def get_latest_value(self, data_source: str, metric: str) -> Optional[Dict]:
        """Get the most recent value for a metric."""
        file_path = self._get_file_path(data_source, metric)
        all_data = self._load_data(file_path)
        
        if not all_data:
            return None
        
        # Data is already sorted by timestamp (newest first)
        return all_data[0]
    
    def cleanup_old_data(self, retention_days: int = 730) -> None:
        """Clean up old data based on retention policy."""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)
        
        # Get all data files
        if not os.path.exists(self.data_dir):
            return
        
        for filename in os.listdir(self.data_dir):
            if not filename.endswith('.json'):
                continue
            
            file_path = os.path.join(self.data_dir, filename)
            all_data = self._load_data(file_path)
            
            # Filter out old data
            filtered_data = []
            removed_count = 0
            
            for item in all_data:
                try:
                    item_date = datetime.fromisoformat(item['timestamp'].replace('Z', '+00:00'))
                    if item_date >= cutoff_date:
                        filtered_data.append(item)
                    else:
                        removed_count += 1
                except (ValueError, KeyError):
                    # Keep items with invalid timestamps for manual review
                    filtered_data.append(item)
            
            # Save cleaned data back to file
            if removed_count > 0:
                self._save_data_to_file(file_path, filtered_data)
                self.logger.info(f"Cleaned up {removed_count} old records from {filename}")


class DynamoDBStateStore(BaseStateStore):
    """DynamoDB-based state store implementation for production."""
    
    def __init__(self, table_name: str = "boom-bust-sentinel-data"):
        self.table_name = table_name
        self.logger = logging.getLogger(__name__)
        
        try:
            import boto3
            self.dynamodb = boto3.resource('dynamodb', region_name=settings.AWS_REGION)
            self.table = self.dynamodb.Table(table_name)
        except ImportError:
            self.logger.error("boto3 not installed. Install with: pip install boto3")
            raise
        except Exception as e:
            self.logger.error(f"Failed to initialize DynamoDB: {e}")
            raise
    
    def _generate_partition_key(self, data_source: str, metric: str) -> str:
        """Generate partition key for DynamoDB."""
        return f"{data_source}#{metric}"
    
    def save_data(self, data_source: str, metric_name: str, data: Dict[str, Any]) -> None:
        """Save data to DynamoDB."""
        timestamp = data.get('timestamp', datetime.now(timezone.utc).isoformat())
        
        # Calculate TTL (Time To Live) for automatic cleanup
        ttl_timestamp = int((datetime.now(timezone.utc) + timedelta(days=730)).timestamp())
        
        item = {
            'pk': self._generate_partition_key(data_source, metric_name),
            'sk': timestamp,
            'data_source': data_source,
            'metric_name': metric_name,
            'timestamp': timestamp,
            'data': data,
            'ttl': ttl_timestamp,
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        
        try:
            self.table.put_item(Item=item)
            self.logger.info(f"Saved data to DynamoDB for {data_source}.{metric_name}")
        except Exception as e:
            self.logger.error(f"Failed to save data to DynamoDB: {e}")
            raise
    
    def get_historical_data(self, data_source: str, metric: str, days: int = 7) -> List[Dict]:
        """Get historical data from DynamoDB."""
        pk = self._generate_partition_key(data_source, metric)
        cutoff_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        
        try:
            response = self.table.query(
                KeyConditionExpression='pk = :pk AND sk >= :cutoff',
                ExpressionAttributeValues={
                    ':pk': pk,
                    ':cutoff': cutoff_date
                },
                ScanIndexForward=False  # Sort by timestamp descending
            )
            return response.get('Items', [])
        except Exception as e:
            self.logger.error(f"Failed to query historical data from DynamoDB: {e}")
            return []
    
    def get_latest_value(self, data_source: str, metric: str) -> Optional[Dict]:
        """Get the most recent value from DynamoDB."""
        pk = self._generate_partition_key(data_source, metric)
        
        try:
            response = self.table.query(
                KeyConditionExpression='pk = :pk',
                ExpressionAttributeValues={':pk': pk},
                ScanIndexForward=False,  # Sort by timestamp descending
                Limit=1
            )
            items = response.get('Items', [])
            return items[0] if items else None
        except Exception as e:
            self.logger.error(f"Failed to get latest value from DynamoDB: {e}")
            return None
    
    def cleanup_old_data(self, retention_days: int = 730) -> None:
        """Clean up old data from DynamoDB (handled automatically by TTL)."""
        # DynamoDB TTL handles cleanup automatically
        self.logger.info("DynamoDB TTL handles automatic cleanup")


class PlanetScaleStateStore(BaseStateStore):
    """PlanetScale-based state store implementation for production."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        try:
            # Import the PlanetScale data service
            from services.planetscale_data_service import PlanetScaleDataService
            self.planet_scale_service = PlanetScaleDataService()
        except Exception as e:
            self.logger.error(f"Failed to initialize PlanetScale service: {e}")
            raise
    
    def save_data(self, data_source: str, metric_name: str, data: Dict[str, Any]) -> None:
        """Save data to PlanetScale."""
        try:
            success = self.planet_scale_service.store_metric_data(data_source, metric_name, data)
            if success:
                self.logger.info(f"Saved data to PlanetScale for {data_source}.{metric_name}")
            else:
                self.logger.error(f"Failed to save data to PlanetScale for {data_source}.{metric_name}")
                raise Exception("Failed to save data to PlanetScale")
        except Exception as e:
            self.logger.error(f"Error saving data to PlanetScale: {e}")
            raise
    
    def get_recent_data(self, data_source: str, metric_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent data from PlanetScale."""
        try:
            metrics = self.planet_scale_service.get_latest_metrics(data_source)
            # Filter by metric name and limit results
            filtered_metrics = [m for m in metrics if m.get('metricName') == metric_name][:limit]
            return filtered_metrics
        except Exception as e:
            self.logger.error(f"Error getting recent data from PlanetScale: {e}")
            return []
    
    def get_historical_data(self, data_source: str, metric: str, days: int = 7) -> List[Dict]:
        """Get historical data from PlanetScale."""
        try:
            # Get latest metrics first to find the metric ID
            metrics = self.planet_scale_service.get_latest_metrics(data_source)
            metric_id = None
            for m in metrics:
                if m.get('metricName') == metric:
                    metric_id = m.get('id')
                    break
            
            if not metric_id:
                self.logger.warning(f"No metric ID found for {data_source}.{metric}")
                return []
            
            return self.planet_scale_service.get_metric_history(metric_id, days)
        except Exception as e:
            self.logger.error(f"Error getting historical data from PlanetScale: {e}")
            return []
    
    def get_latest_value(self, data_source: str, metric_name: str) -> Optional[Dict[str, Any]]:
        """Get the latest value for a specific metric from PlanetScale."""
        try:
            metrics = self.planet_scale_service.get_latest_metrics(data_source)
            # Find the metric by name and return the most recent one
            for metric in metrics:
                if metric.get('metricName') == metric_name:
                    return metric
            return None
        except Exception as e:
            self.logger.error(f"Error getting latest value from PlanetScale: {e}")
            return None
    
    def cleanup_old_data(self, retention_days: int = 730) -> None:
        """Clean up old data from PlanetScale."""
        try:
            success = self.planet_scale_service.cleanup_old_data(retention_days)
            if success:
                self.logger.info(f"Cleaned up old data from PlanetScale (older than {retention_days} days)")
            else:
                self.logger.warning("Failed to cleanup old data from PlanetScale")
        except Exception as e:
            self.logger.error(f"Error cleaning up old data from PlanetScale: {e}")


class FirestoreStateStore(BaseStateStore):
    """Firestore-based state store implementation for Google Cloud."""
    
    def __init__(self, collection_name: str = "boom-bust-sentinel-data"):
        self.collection_name = collection_name
        self.logger = logging.getLogger(__name__)
        
        if firestore is None:
            self.logger.error("google-cloud-firestore not installed. Install with: pip install google-cloud-firestore")
            raise ImportError("google-cloud-firestore not available")
        
        try:
            self.db = firestore.Client()
            self.collection = self.db.collection(collection_name)
        except Exception as e:
            self.logger.error(f"Failed to initialize Firestore: {e}")
            raise
    
    def _generate_document_id(self, data_source: str, metric: str, timestamp: str) -> str:
        """Generate document ID for Firestore."""
        return f"{data_source}_{metric}_{timestamp.replace(':', '-').replace('.', '-')}"
    
    def save_data(self, data_source: str, metric_name: str, data: Dict[str, Any]) -> None:
        """Save data to Firestore."""
        timestamp = data.get('timestamp', datetime.now(timezone.utc).isoformat())
        
        doc_data = {
            'data_source': data_source,
            'metric_name': metric_name,
            'timestamp': timestamp,
            'data': data,
            'created_at': firestore.SERVER_TIMESTAMP,
            'ttl': datetime.now(timezone.utc) + timedelta(days=730)
        }
        
        try:
            doc_id = self._generate_document_id(data_source, metric_name, timestamp)
            self.collection.document(doc_id).set(doc_data)
            self.logger.info(f"Saved data to Firestore for {data_source}.{metric_name}")
        except Exception as e:
            self.logger.error(f"Failed to save data to Firestore: {e}")
            raise
    
    def get_historical_data(self, data_source: str, metric: str, days: int = 7) -> List[Dict]:
        """Get historical data from Firestore."""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        try:
            query = (self.collection
                    .where('data_source', '==', data_source)
                    .where('metric_name', '==', metric)
                    .where('timestamp', '>=', cutoff_date.isoformat())
                    .order_by('timestamp', direction=firestore.Query.DESCENDING))
            
            docs = query.stream()
            return [doc.to_dict() for doc in docs]
        except Exception as e:
            self.logger.error(f"Failed to query historical data from Firestore: {e}")
            return []
    
    def get_latest_value(self, data_source: str, metric: str) -> Optional[Dict]:
        """Get the most recent value from Firestore."""
        try:
            query = (self.collection
                    .where('data_source', '==', data_source)
                    .where('metric_name', '==', metric)
                    .order_by('timestamp', direction=firestore.Query.DESCENDING)
                    .limit(1))
            
            docs = list(query.stream())
            return docs[0].to_dict() if docs else None
        except Exception as e:
            self.logger.error(f"Failed to get latest value from Firestore: {e}")
            return None
    
    def cleanup_old_data(self, retention_days: int = 730) -> None:
        """Clean up old data from Firestore."""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)
        
        try:
            # Query old documents
            query = self.collection.where('timestamp', '<', cutoff_date.isoformat())
            docs = query.stream()
            
            # Delete in batches
            batch = self.db.batch()
            count = 0
            
            for doc in docs:
                batch.delete(doc.reference)
                count += 1
                
                # Commit batch every 500 operations (Firestore limit)
                if count % 500 == 0:
                    batch.commit()
                    batch = self.db.batch()
            
            # Commit remaining operations
            if count % 500 != 0:
                batch.commit()
            
            self.logger.info(f"Cleaned up {count} old records from Firestore")
        except Exception as e:
            self.logger.error(f"Failed to cleanup old data from Firestore: {e}")


# Factory function to create the appropriate state store
def create_state_store() -> BaseStateStore:
    """Create and return the appropriate state store based on configuration."""
    # Check environment variable first (takes precedence)
    env = os.getenv('ENVIRONMENT', settings.ENVIRONMENT)
    
    if env == 'production':
        database_url = os.getenv('DATABASE_URL', settings.DATABASE_URL)
        
        if database_url:
            if 'psdb.cloud' in database_url or 'planetscale' in database_url.lower() or 'pscale_pw' in database_url:
                try:
                    return PlanetScaleStateStore()
                except Exception as e:
                    logger = logging.getLogger(__name__)
                    logger.error(f"Failed to create PlanetScaleStateStore: {e}")
                    # Fall back to file store if PlanetScale fails
                    logger.warning("Falling back to FileStateStore")
                    return FileStateStore()
            elif 'dynamodb' in database_url.lower():
                return DynamoDBStateStore()
            elif 'firestore' in database_url.lower() or 'gcp' in database_url.lower():
                return FirestoreStateStore()
        
        # Default to PlanetScale for production if no specific URL (since we're using PlanetScale)
        try:
            return PlanetScaleStateStore()
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to create PlanetScaleStateStore: {e}")
            logger.warning("Falling back to FileStateStore")
            return FileStateStore()
    else:
        # Use file-based store for development
        return FileStateStore()


# Default state store instance
StateStore = create_state_store