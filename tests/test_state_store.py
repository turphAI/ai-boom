"""
Tests for the state store implementations.
"""

import json
import os
import tempfile
import shutil
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch
import pytest

from services.state_store import FileStateStore, DynamoDBStateStore, FirestoreStateStore, create_state_store


class TestFileStateStore:
    """Tests for the file-based state store."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.store = FileStateStore(self.temp_dir)
    
    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)
    
    def test_save_and_retrieve_data(self):
        """Test saving and retrieving data."""
        test_data = {
            'value': 100.5,
            'confidence': 0.95,
            'metadata': {'source': 'test'}
        }
        
        # Save data
        self.store.save_data('test_source', 'test_metric', test_data)
        
        # Retrieve latest value
        latest = self.store.get_latest_value('test_source', 'test_metric')
        
        assert latest is not None
        assert latest['data_source'] == 'test_source'
        assert latest['metric_name'] == 'test_metric'
        assert latest['data']['value'] == 100.5
        assert 'timestamp' in latest
    
    def test_historical_data_retrieval(self):
        """Test retrieving historical data within time range."""
        # Save multiple data points
        for i in range(5):
            test_data = {
                'value': i * 10,
                'timestamp': (datetime.now(timezone.utc) - timedelta(days=i)).isoformat()
            }
            self.store.save_data('test_source', 'test_metric', test_data)
        
        # Get historical data for last 3 days
        historical = self.store.get_historical_data('test_source', 'test_metric', days=3)
        
        # Should get 4 records (days 0, 1, 2, 3)
        assert len(historical) == 4
        
        # Check that data is sorted by timestamp (newest first)
        timestamps = [item['timestamp'] for item in historical]
        assert timestamps == sorted(timestamps, reverse=True)
    
    def test_nonexistent_data(self):
        """Test retrieving data that doesn't exist."""
        latest = self.store.get_latest_value('nonexistent', 'metric')
        assert latest is None
        
        historical = self.store.get_historical_data('nonexistent', 'metric')
        assert historical == []
    
    def test_cleanup_old_data(self):
        """Test cleaning up old data."""
        # Save data points with different ages
        old_data = {
            'value': 1,
            'timestamp': (datetime.now(timezone.utc) - timedelta(days=800)).isoformat()
        }
        recent_data = {
            'value': 2,
            'timestamp': (datetime.now(timezone.utc) - timedelta(days=100)).isoformat()
        }
        
        self.store.save_data('test_source', 'test_metric', old_data)
        self.store.save_data('test_source', 'test_metric', recent_data)
        
        # Verify both records exist
        all_data = self.store.get_historical_data('test_source', 'test_metric', days=1000)
        assert len(all_data) == 2
        
        # Clean up data older than 730 days
        self.store.cleanup_old_data(retention_days=730)
        
        # Verify only recent data remains
        remaining_data = self.store.get_historical_data('test_source', 'test_metric', days=1000)
        assert len(remaining_data) == 1
        assert remaining_data[0]['data']['value'] == 2
    
    def test_file_creation(self):
        """Test that data files are created correctly."""
        test_data = {'value': 42}
        self.store.save_data('test_source', 'test_metric', test_data)
        
        expected_file = os.path.join(self.temp_dir, 'test_source_test_metric.json')
        assert os.path.exists(expected_file)
        
        # Verify file content
        with open(expected_file, 'r') as f:
            file_data = json.load(f)
        
        assert len(file_data) == 1
        assert file_data[0]['data_source'] == 'test_source'
        assert file_data[0]['metric_name'] == 'test_metric'
    
    def test_invalid_json_handling(self):
        """Test handling of corrupted JSON files."""
        # Create a corrupted JSON file
        corrupted_file = os.path.join(self.temp_dir, 'test_source_test_metric.json')
        with open(corrupted_file, 'w') as f:
            f.write('invalid json content')
        
        # Should return empty list for corrupted file
        historical = self.store.get_historical_data('test_source', 'test_metric')
        assert historical == []
        
        latest = self.store.get_latest_value('test_source', 'test_metric')
        assert latest is None
    
    def test_data_sorting(self):
        """Test that data is properly sorted by timestamp."""
        # Save data points out of order
        timestamps = [
            '2024-01-03T00:00:00',
            '2024-01-01T00:00:00', 
            '2024-01-02T00:00:00'
        ]
        
        for i, timestamp in enumerate(timestamps):
            test_data = {'value': i, 'timestamp': timestamp}
            self.store.save_data('test_source', 'test_metric', test_data)
        
        # Get all data
        historical = self.store.get_historical_data('test_source', 'test_metric', days=30)
        
        # Should be sorted by timestamp (newest first)
        assert len(historical) == 3
        assert historical[0]['timestamp'] == '2024-01-03T00:00:00'
        assert historical[1]['timestamp'] == '2024-01-02T00:00:00'
        assert historical[2]['timestamp'] == '2024-01-01T00:00:00'
    
    def test_automatic_timestamp_addition(self):
        """Test that timestamps are automatically added when missing."""
        test_data = {'value': 100}  # No timestamp
        
        with patch('services.state_store.datetime') as mock_datetime:
            mock_now = datetime(2024, 1, 1, 12, 0, 0)
            mock_datetime.utcnow.return_value = mock_now
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
            
            self.store.save_data('test_source', 'test_metric', test_data)
            
            latest = self.store.get_latest_value('test_source', 'test_metric')
            assert latest is not None
            assert latest['timestamp'] == mock_now.isoformat()


class TestDynamoDBStateStore:
    """Tests for the DynamoDB state store."""
    
    @patch('boto3.resource')
    def test_initialization(self, mock_boto3):
        """Test DynamoDB store initialization."""
        mock_dynamodb = Mock()
        mock_table = Mock()
        mock_boto3.return_value = mock_dynamodb
        mock_dynamodb.Table.return_value = mock_table
        
        store = DynamoDBStateStore('test-table')
        
        assert store.table_name == 'test-table'
        mock_boto3.assert_called_once()
        mock_dynamodb.Table.assert_called_once_with('test-table')
    
    @patch('boto3.resource')
    def test_save_data(self, mock_boto3):
        """Test saving data to DynamoDB."""
        mock_dynamodb = Mock()
        mock_table = Mock()
        mock_boto3.return_value = mock_dynamodb
        mock_dynamodb.Table.return_value = mock_table
        
        store = DynamoDBStateStore('test-table')
        test_data = {'value': 100, 'confidence': 0.9}
        
        store.save_data('test_source', 'test_metric', test_data)
        
        # Verify put_item was called
        mock_table.put_item.assert_called_once()
        call_args = mock_table.put_item.call_args[1]['Item']
        
        assert call_args['pk'] == 'test_source#test_metric'
        assert call_args['data_source'] == 'test_source'
        assert call_args['metric_name'] == 'test_metric'
        assert call_args['data'] == test_data
        assert 'timestamp' in call_args
        assert 'ttl' in call_args
        assert 'created_at' in call_args
    
    @patch('boto3.resource')
    def test_get_latest_value(self, mock_boto3):
        """Test getting latest value from DynamoDB."""
        mock_dynamodb = Mock()
        mock_table = Mock()
        mock_boto3.return_value = mock_dynamodb
        mock_dynamodb.Table.return_value = mock_table
        
        # Mock query response
        mock_table.query.return_value = {
            'Items': [{'pk': 'test_source#test_metric', 'data': {'value': 42}}]
        }
        
        store = DynamoDBStateStore('test-table')
        result = store.get_latest_value('test_source', 'test_metric')
        
        assert result is not None
        assert result['data']['value'] == 42
        
        # Verify query was called correctly
        mock_table.query.assert_called_once()
        call_args = mock_table.query.call_args[1]
        assert call_args['Limit'] == 1
        assert call_args['ScanIndexForward'] is False
    
    @patch('boto3.resource')
    def test_get_historical_data(self, mock_boto3):
        """Test getting historical data from DynamoDB."""
        mock_dynamodb = Mock()
        mock_table = Mock()
        mock_boto3.return_value = mock_dynamodb
        mock_dynamodb.Table.return_value = mock_table
        
        # Mock query response
        mock_table.query.return_value = {
            'Items': [
                {'pk': 'test_source#test_metric', 'data': {'value': 42}, 'timestamp': '2024-01-01T00:00:00'},
                {'pk': 'test_source#test_metric', 'data': {'value': 43}, 'timestamp': '2024-01-02T00:00:00'}
            ]
        }
        
        store = DynamoDBStateStore('test-table')
        result = store.get_historical_data('test_source', 'test_metric', days=7)
        
        assert len(result) == 2
        assert result[0]['data']['value'] == 42
        
        # Verify query was called correctly
        mock_table.query.assert_called_once()
        call_args = mock_table.query.call_args[1]
        assert 'KeyConditionExpression' in call_args
        assert call_args['ScanIndexForward'] is False
    
    @patch('boto3.resource')
    def test_ttl_configuration(self, mock_boto3):
        """Test TTL configuration in saved data."""
        mock_dynamodb = Mock()
        mock_table = Mock()
        mock_boto3.return_value = mock_dynamodb
        mock_dynamodb.Table.return_value = mock_table
        
        store = DynamoDBStateStore('test-table')
        test_data = {'value': 100}
        
        with patch('services.state_store.datetime') as mock_datetime:
            mock_now = datetime(2024, 1, 1, 12, 0, 0)
            mock_datetime.utcnow.return_value = mock_now
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
            
            store.save_data('test_source', 'test_metric', test_data)
            
            call_args = mock_table.put_item.call_args[1]['Item']
            expected_ttl = int((mock_now + timedelta(days=730)).timestamp())
            assert call_args['ttl'] == expected_ttl


class TestFirestoreStateStore:
    """Tests for the Firestore state store."""
    
    @patch('services.state_store.firestore')
    def test_initialization(self, mock_firestore):
        """Test Firestore store initialization."""
        mock_client = Mock()
        mock_collection = Mock()
        mock_firestore.Client.return_value = mock_client
        mock_client.collection.return_value = mock_collection
        
        store = FirestoreStateStore('test-collection')
        
        assert store.collection_name == 'test-collection'
        mock_firestore.Client.assert_called_once()
        mock_client.collection.assert_called_once_with('test-collection')
    
    @patch('services.state_store.firestore')
    def test_save_data(self, mock_firestore):
        """Test saving data to Firestore."""
        mock_client = Mock()
        mock_collection = Mock()
        mock_document = Mock()
        mock_firestore.Client.return_value = mock_client
        mock_client.collection.return_value = mock_collection
        mock_collection.document.return_value = mock_document
        mock_firestore.SERVER_TIMESTAMP = 'SERVER_TIMESTAMP'
        
        store = FirestoreStateStore('test-collection')
        test_data = {'value': 100, 'confidence': 0.9}
        
        store.save_data('test_source', 'test_metric', test_data)
        
        # Verify document was created
        mock_collection.document.assert_called_once()
        mock_document.set.assert_called_once()
        
        call_args = mock_document.set.call_args[0][0]
        assert call_args['data_source'] == 'test_source'
        assert call_args['metric_name'] == 'test_metric'
        assert call_args['data'] == test_data
        assert 'timestamp' in call_args
        assert 'ttl' in call_args
        assert call_args['created_at'] == 'SERVER_TIMESTAMP'
    
    @patch('services.state_store.firestore')
    def test_get_latest_value(self, mock_firestore):
        """Test getting latest value from Firestore."""
        mock_client = Mock()
        mock_collection = Mock()
        mock_query = Mock()
        mock_doc = Mock()
        
        mock_firestore.Client.return_value = mock_client
        mock_client.collection.return_value = mock_collection
        mock_collection.where.return_value = mock_query
        mock_query.where.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.stream.return_value = [mock_doc]
        mock_doc.to_dict.return_value = {'data': {'value': 42}}
        mock_firestore.Query.DESCENDING = 'DESCENDING'
        
        store = FirestoreStateStore('test-collection')
        result = store.get_latest_value('test_source', 'test_metric')
        
        assert result is not None
        assert result['data']['value'] == 42
        
        # Verify query was constructed correctly
        assert mock_collection.where.call_count == 2
        mock_query.order_by.assert_called_with('timestamp', direction='DESCENDING')
        mock_query.limit.assert_called_with(1)
    
    @patch('services.state_store.firestore')
    def test_cleanup_old_data(self, mock_firestore):
        """Test cleaning up old data from Firestore."""
        mock_client = Mock()
        mock_collection = Mock()
        mock_query = Mock()
        mock_batch = Mock()
        mock_doc1 = Mock()
        mock_doc2 = Mock()
        
        mock_firestore.Client.return_value = mock_client
        mock_client.collection.return_value = mock_collection
        mock_client.batch.return_value = mock_batch
        mock_collection.where.return_value = mock_query
        mock_query.stream.return_value = [mock_doc1, mock_doc2]
        
        store = FirestoreStateStore('test-collection')
        store.cleanup_old_data(retention_days=30)
        
        # Verify batch operations
        assert mock_batch.delete.call_count == 2
        mock_batch.commit.assert_called_once()


def test_create_state_store():
    """Test the state store factory function."""
    with patch('services.state_store.settings') as mock_settings:
        # Test development environment
        mock_settings.ENVIRONMENT = 'development'
        mock_settings.DATABASE_URL = None
        
        store = create_state_store()
        assert isinstance(store, FileStateStore)
        
        # Test production environment with DynamoDB
        mock_settings.ENVIRONMENT = 'production'
        mock_settings.DATABASE_URL = 'dynamodb://test'
        
        with patch('boto3.resource'):
            store = create_state_store()
            assert isinstance(store, DynamoDBStateStore)
        
        # Test production environment with Firestore
        mock_settings.DATABASE_URL = 'firestore://test'
        
        with patch('services.state_store.firestore') as mock_firestore:
            mock_firestore.Client.return_value = Mock()
            store = create_state_store()
            assert isinstance(store, FirestoreStateStore)
        
        # Test production environment with GCP URL
        mock_settings.DATABASE_URL = 'gcp://test'
        
        with patch('services.state_store.firestore') as mock_firestore:
            mock_firestore.Client.return_value = Mock()
            store = create_state_store()
            assert isinstance(store, FirestoreStateStore)


if __name__ == "__main__":
    pytest.main([__file__])