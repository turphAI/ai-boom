"""
Tests for secrets management functionality.
"""

import pytest
import json
import os
from unittest.mock import Mock, patch, MagicMock
from config.secrets import (
    SecretManager, 
    AWSSecretManager, 
    GCPSecretManager, 
    MockSecretManager,
    SecretManagerInterface
)


class TestSecretManagerInterface:
    """Test the abstract interface."""
    
    def test_interface_cannot_be_instantiated(self):
        """Test that the interface cannot be instantiated directly."""
        with pytest.raises(TypeError):
            SecretManagerInterface()


class TestMockSecretManager:
    """Test the mock secret manager implementation."""
    
    def test_init_with_default_secrets(self):
        """Test initialization with default empty secrets."""
        manager = MockSecretManager()
        assert manager.mock_secrets == {}
    
    def test_init_with_custom_secrets(self):
        """Test initialization with custom secrets."""
        secrets = {'test-secret': {'key1': 'value1'}}
        manager = MockSecretManager(secrets)
        assert manager.mock_secrets == secrets
    
    def test_get_secret_success(self):
        """Test successful secret retrieval."""
        secrets = {'test-secret': {'key1': 'value1', 'key2': 'value2'}}
        manager = MockSecretManager(secrets)
        
        result = manager.get_secret('test-secret')
        assert result == {'key1': 'value1', 'key2': 'value2'}
    
    def test_get_secret_not_found(self):
        """Test secret not found error."""
        manager = MockSecretManager()
        
        with pytest.raises(ValueError, match="Mock secret nonexistent not found"):
            manager.get_secret('nonexistent')
    
    def test_get_secret_value_success(self):
        """Test successful secret value retrieval."""
        secrets = {'test-secret': {'key1': 'value1'}}
        manager = MockSecretManager(secrets)
        
        result = manager.get_secret_value('test-secret', 'key1')
        assert result == 'value1'
    
    def test_get_secret_value_key_not_found(self):
        """Test secret value retrieval with missing key."""
        secrets = {'test-secret': {'key1': 'value1'}}
        manager = MockSecretManager(secrets)
        
        result = manager.get_secret_value('test-secret', 'nonexistent')
        assert result is None
    
    def test_get_secret_value_secret_not_found(self):
        """Test secret value retrieval with missing secret."""
        manager = MockSecretManager()
        
        result = manager.get_secret_value('nonexistent', 'key1')
        assert result is None


class TestAWSSecretManager:
    """Test AWS Secrets Manager implementation."""
    
    @patch('boto3.client')
    def test_init_success(self, mock_boto3_client):
        """Test successful initialization."""
        mock_client = Mock()
        mock_boto3_client.return_value = mock_client
        
        manager = AWSSecretManager('us-west-2')
        
        assert manager.region_name == 'us-west-2'
        assert manager.client == mock_client
        mock_boto3_client.assert_called_once_with('secretsmanager', region_name='us-west-2')
    
    @patch('boto3.client')
    def test_init_default_region(self, mock_boto3_client):
        """Test initialization with default region."""
        mock_client = Mock()
        mock_boto3_client.return_value = mock_client
        
        with patch.dict(os.environ, {'AWS_REGION': 'eu-west-1'}):
            manager = AWSSecretManager()
            assert manager.region_name == 'eu-west-1'
    
    def test_init_boto3_not_available(self):
        """Test initialization when boto3 is not available."""
        with patch('builtins.__import__', side_effect=lambda name, *args: ImportError() if name == 'boto3' else __import__(name, *args)):
            with pytest.raises(ImportError, match="boto3 is required"):
                AWSSecretManager()
    
    @patch('boto3.client')
    def test_get_secret_success(self, mock_boto3_client):
        """Test successful secret retrieval."""
        mock_client = Mock()
        mock_boto3_client.return_value = mock_client
        
        secret_data = {'key1': 'value1', 'key2': 'value2'}
        mock_client.get_secret_value.return_value = {
            'SecretString': json.dumps(secret_data)
        }
        
        manager = AWSSecretManager()
        result = manager.get_secret('test-secret')
        
        assert result == secret_data
        mock_client.get_secret_value.assert_called_once_with(SecretId='test-secret')
    
    @patch('boto3.client')
    def test_get_secret_binary(self, mock_boto3_client):
        """Test secret retrieval with binary data."""
        mock_client = Mock()
        mock_boto3_client.return_value = mock_client
        
        mock_client.get_secret_value.return_value = {
            'SecretBinary': b'binary_data'
        }
        
        manager = AWSSecretManager()
        result = manager.get_secret('test-secret')
        
        assert result == {'binary': b'binary_data'}
    
    @patch('boto3.client')
    def test_get_secret_not_found(self, mock_boto3_client):
        """Test secret not found error."""
        mock_client = Mock()
        mock_boto3_client.return_value = mock_client
        
        from botocore.exceptions import ClientError
        error = ClientError(
            {'Error': {'Code': 'ResourceNotFoundException'}},
            'GetSecretValue'
        )
        mock_client.get_secret_value.side_effect = error
        
        manager = AWSSecretManager()
        
        with pytest.raises(ValueError, match="Secret test-secret not found"):
            manager.get_secret('test-secret')
    
    @patch('boto3.client')
    def test_get_secret_invalid_json(self, mock_boto3_client):
        """Test secret with invalid JSON."""
        mock_client = Mock()
        mock_boto3_client.return_value = mock_client
        
        mock_client.get_secret_value.return_value = {
            'SecretString': 'invalid json'
        }
        
        manager = AWSSecretManager()
        
        with pytest.raises(ValueError, match="Secret test-secret is not valid JSON"):
            manager.get_secret('test-secret')
    
    @patch('boto3.client')
    def test_get_secret_value_success(self, mock_boto3_client):
        """Test successful secret value retrieval."""
        mock_client = Mock()
        mock_boto3_client.return_value = mock_client
        
        secret_data = {'key1': 'value1', 'key2': 'value2'}
        mock_client.get_secret_value.return_value = {
            'SecretString': json.dumps(secret_data)
        }
        
        manager = AWSSecretManager()
        result = manager.get_secret_value('test-secret', 'key1')
        
        assert result == 'value1'


class TestGCPSecretManager:
    """Test GCP Secret Manager implementation."""
    
    @patch('google.cloud.secretmanager.SecretManagerServiceClient')
    def test_init_success(self, mock_client_class):
        """Test successful initialization."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        with patch.dict(os.environ, {'GCP_PROJECT_ID': 'test-project'}):
            manager = GCPSecretManager()
            
            assert manager.project_id == 'test-project'
            assert manager.client == mock_client
    
    @patch('google.cloud.secretmanager.SecretManagerServiceClient')
    def test_init_custom_project(self, mock_client_class):
        """Test initialization with custom project ID."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        manager = GCPSecretManager('custom-project')
        assert manager.project_id == 'custom-project'
    
    @patch('google.cloud.secretmanager.SecretManagerServiceClient')
    def test_init_no_project_id(self, mock_client_class):
        """Test initialization without project ID."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="GCP_PROJECT_ID environment variable is required"):
                GCPSecretManager()
    
    def test_init_gcp_not_available(self):
        """Test initialization when GCP client is not available."""
        with patch('builtins.__import__', side_effect=lambda name, *args: ImportError() if 'google.cloud' in name else __import__(name, *args)):
            with pytest.raises(ImportError, match="google-cloud-secret-manager is required"):
                GCPSecretManager('test-project')
    
    @patch('google.cloud.secretmanager.SecretManagerServiceClient')
    def test_get_secret_success(self, mock_client_class):
        """Test successful secret retrieval."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        secret_data = {'key1': 'value1', 'key2': 'value2'}
        mock_response = Mock()
        mock_response.payload.data.decode.return_value = json.dumps(secret_data)
        mock_client.access_secret_version.return_value = mock_response
        
        manager = GCPSecretManager('test-project')
        result = manager.get_secret('test-secret')
        
        assert result == secret_data
        expected_name = "projects/test-project/secrets/test-secret/versions/latest"
        mock_client.access_secret_version.assert_called_once_with(request={"name": expected_name})


class TestSecretManager:
    """Test the unified SecretManager class."""
    
    @patch.dict(os.environ, {'SECRET_PROVIDER': 'aws'})
    @patch('config.secrets.AWSSecretManager')
    def test_init_aws_provider(self, mock_aws_manager):
        """Test initialization with AWS provider."""
        mock_instance = Mock()
        mock_aws_manager.return_value = mock_instance
        
        manager = SecretManager()
        
        assert manager.provider == 'aws'
        assert manager._client == mock_instance
        mock_aws_manager.assert_called_once()
    
    @patch.dict(os.environ, {'SECRET_PROVIDER': 'gcp'})
    @patch('config.secrets.GCPSecretManager')
    def test_init_gcp_provider(self, mock_gcp_manager):
        """Test initialization with GCP provider."""
        mock_instance = Mock()
        mock_gcp_manager.return_value = mock_instance
        
        manager = SecretManager()
        
        assert manager.provider == 'gcp'
        assert manager._client == mock_instance
        mock_gcp_manager.assert_called_once()
    
    @patch.dict(os.environ, {'SECRET_PROVIDER': 'mock'})
    @patch('config.secrets.MockSecretManager')
    def test_init_mock_provider(self, mock_mock_manager):
        """Test initialization with mock provider."""
        mock_instance = Mock()
        mock_mock_manager.return_value = mock_instance
        
        manager = SecretManager()
        
        assert manager.provider == 'mock'
        assert manager._client == mock_instance
        mock_mock_manager.assert_called_once()
    
    def test_init_unsupported_provider(self):
        """Test initialization with unsupported provider."""
        with pytest.raises(ValueError, match="Unsupported secret provider: invalid"):
            SecretManager('invalid')
    
    @patch('config.secrets.MockSecretManager')
    def test_get_secret(self, mock_mock_manager):
        """Test get_secret method delegation."""
        mock_instance = Mock()
        mock_instance.get_secret.return_value = {'key': 'value'}
        mock_mock_manager.return_value = mock_instance
        
        manager = SecretManager('mock')
        result = manager.get_secret('test-secret')
        
        assert result == {'key': 'value'}
        mock_instance.get_secret.assert_called_once_with('test-secret')
    
    @patch('config.secrets.MockSecretManager')
    def test_get_secret_value(self, mock_mock_manager):
        """Test get_secret_value method delegation."""
        mock_instance = Mock()
        mock_instance.get_secret_value.return_value = 'value'
        mock_mock_manager.return_value = mock_instance
        
        manager = SecretManager('mock')
        result = manager.get_secret_value('test-secret', 'key')
        
        assert result == 'value'
        mock_instance.get_secret_value.assert_called_once_with('test-secret', 'key')
    
    @patch('config.secrets.MockSecretManager')
    def test_get_api_credentials(self, mock_mock_manager):
        """Test get_api_credentials method."""
        mock_instance = Mock()
        credentials = {'telegram_bot_token': 'token123'}
        mock_instance.get_secret.return_value = credentials
        mock_mock_manager.return_value = mock_instance
        
        manager = SecretManager('mock')
        result = manager.get_api_credentials()
        
        assert result == credentials
        mock_instance.get_secret.assert_called_once_with('boom-bust-sentinel/api-keys')
    
    @patch('config.secrets.MockSecretManager')
    def test_get_api_credentials_error(self, mock_mock_manager):
        """Test get_api_credentials with error."""
        mock_instance = Mock()
        mock_instance.get_secret.side_effect = Exception("Secret not found")
        mock_mock_manager.return_value = mock_instance
        
        manager = SecretManager('mock')
        result = manager.get_api_credentials()
        
        assert result == {}
    
    @patch('config.secrets.MockSecretManager')
    def test_get_database_config(self, mock_mock_manager):
        """Test get_database_config method."""
        mock_instance = Mock()
        db_config = {'connection_string': 'test://db'}
        mock_instance.get_secret.return_value = db_config
        mock_mock_manager.return_value = mock_instance
        
        manager = SecretManager('mock')
        result = manager.get_database_config()
        
        assert result == db_config
        mock_instance.get_secret.assert_called_once_with('boom-bust-sentinel/database')
    
    @patch('config.secrets.MockSecretManager')
    def test_get_notification_config(self, mock_mock_manager):
        """Test get_notification_config method."""
        mock_instance = Mock()
        notif_config = {'sns_topic_arn': 'arn:aws:sns:us-east-1:123456789012:test'}
        mock_instance.get_secret.return_value = notif_config
        mock_mock_manager.return_value = mock_instance
        
        manager = SecretManager('mock')
        result = manager.get_notification_config()
        
        assert result == notif_config
        mock_instance.get_secret.assert_called_once_with('boom-bust-sentinel/notifications')


@pytest.fixture
def mock_secret_manager():
    """Fixture providing a mock secret manager."""
    secrets = {
        'boom-bust-sentinel/api-keys': {
            'telegram_bot_token': 'test_token',
            'grafana_api_key': 'test_grafana_key'
        },
        'boom-bust-sentinel/database': {
            'connection_string': 'test://connection',
            'username': 'test_user',
            'password': 'test_pass'
        },
        'boom-bust-sentinel/notifications': {
            'sns_topic_arn': 'arn:aws:sns:us-east-1:123456789012:test-topic',
            'telegram_chat_id': 'test_chat_id'
        }
    }
    return MockSecretManager(secrets)


class TestSecretManagerIntegration:
    """Integration tests for secret manager functionality."""
    
    def test_full_secret_retrieval_flow(self, mock_secret_manager):
        """Test complete secret retrieval workflow."""
        # Test API credentials
        api_creds = mock_secret_manager.get_secret('boom-bust-sentinel/api-keys')
        assert api_creds['telegram_bot_token'] == 'test_token'
        assert api_creds['grafana_api_key'] == 'test_grafana_key'
        
        # Test database config
        db_config = mock_secret_manager.get_secret('boom-bust-sentinel/database')
        assert db_config['connection_string'] == 'test://connection'
        assert db_config['username'] == 'test_user'
        
        # Test notification config
        notif_config = mock_secret_manager.get_secret('boom-bust-sentinel/notifications')
        assert notif_config['sns_topic_arn'] == 'arn:aws:sns:us-east-1:123456789012:test-topic'
        assert notif_config['telegram_chat_id'] == 'test_chat_id'
    
    def test_secret_value_retrieval(self, mock_secret_manager):
        """Test individual secret value retrieval."""
        token = mock_secret_manager.get_secret_value('boom-bust-sentinel/api-keys', 'telegram_bot_token')
        assert token == 'test_token'
        
        username = mock_secret_manager.get_secret_value('boom-bust-sentinel/database', 'username')
        assert username == 'test_user'
        
        # Test non-existent key
        missing = mock_secret_manager.get_secret_value('boom-bust-sentinel/api-keys', 'nonexistent')
        assert missing is None