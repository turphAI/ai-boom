"""
Secrets management wrapper for AWS Secrets Manager and GCP Secret Manager.
"""

import json
import os
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class SecretManagerInterface(ABC):
    """Abstract interface for secret management providers."""
    
    @abstractmethod
    def get_secret(self, secret_name: str) -> Dict[str, Any]:
        """Retrieve a secret by name."""
        pass
    
    @abstractmethod
    def get_secret_value(self, secret_name: str, key: str) -> Optional[str]:
        """Retrieve a specific value from a secret."""
        pass


class AWSSecretManager(SecretManagerInterface):
    """AWS Secrets Manager implementation."""
    
    def __init__(self, region_name: str = None):
        try:
            import boto3
            from botocore.exceptions import ClientError, NoCredentialsError
            
            self.region_name = region_name or os.getenv('AWS_REGION', 'us-east-1')
            self.client = boto3.client('secretsmanager', region_name=self.region_name)
            self.ClientError = ClientError
            self.NoCredentialsError = NoCredentialsError
            
        except ImportError:
            raise ImportError("boto3 is required for AWS Secrets Manager. Install with: pip install boto3")
    
    def get_secret(self, secret_name: str) -> Dict[str, Any]:
        """Retrieve a secret from AWS Secrets Manager."""
        try:
            response = self.client.get_secret_value(SecretId=secret_name)
            secret_string = response.get('SecretString')
            
            if secret_string:
                return json.loads(secret_string)
            else:
                # Handle binary secrets if needed
                return {'binary': response.get('SecretBinary')}
                
        except self.ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'ResourceNotFoundException':
                logger.error(f"Secret {secret_name} not found in AWS Secrets Manager")
                raise ValueError(f"Secret {secret_name} not found")
            elif error_code == 'InvalidRequestException':
                logger.error(f"Invalid request for secret {secret_name}")
                raise ValueError(f"Invalid request for secret {secret_name}")
            elif error_code == 'InvalidParameterException':
                logger.error(f"Invalid parameter for secret {secret_name}")
                raise ValueError(f"Invalid parameter for secret {secret_name}")
            else:
                logger.error(f"Error retrieving secret {secret_name}: {str(e)}")
                raise
        except self.NoCredentialsError:
            logger.error("AWS credentials not found")
            raise ValueError("AWS credentials not configured")
        except json.JSONDecodeError:
            logger.error(f"Secret {secret_name} is not valid JSON")
            raise ValueError(f"Secret {secret_name} is not valid JSON")
    
    def get_secret_value(self, secret_name: str, key: str) -> Optional[str]:
        """Retrieve a specific value from a secret."""
        try:
            secret_data = self.get_secret(secret_name)
            return secret_data.get(key)
        except Exception as e:
            logger.error(f"Error retrieving key {key} from secret {secret_name}: {str(e)}")
            return None


class GCPSecretManager(SecretManagerInterface):
    """Google Cloud Secret Manager implementation."""
    
    def __init__(self, project_id: str = None):
        try:
            from google.cloud import secretmanager
            from google.api_core import exceptions
            
            self.project_id = project_id or os.getenv('GCP_PROJECT_ID')
            if not self.project_id:
                raise ValueError("GCP_PROJECT_ID environment variable is required")
            
            self.client = secretmanager.SecretManagerServiceClient()
            self.exceptions = exceptions
            
        except ImportError:
            raise ImportError(
                "google-cloud-secret-manager is required for GCP Secret Manager. "
                "Install with: pip install google-cloud-secret-manager"
            )
    
    def get_secret(self, secret_name: str) -> Dict[str, Any]:
        """Retrieve a secret from GCP Secret Manager."""
        try:
            # Build the resource name
            name = f"projects/{self.project_id}/secrets/{secret_name}/versions/latest"
            
            # Access the secret version
            response = self.client.access_secret_version(request={"name": name})
            secret_string = response.payload.data.decode("UTF-8")
            
            return json.loads(secret_string)
            
        except self.exceptions.NotFound:
            logger.error(f"Secret {secret_name} not found in GCP Secret Manager")
            raise ValueError(f"Secret {secret_name} not found")
        except self.exceptions.PermissionDenied:
            logger.error(f"Permission denied accessing secret {secret_name}")
            raise ValueError(f"Permission denied accessing secret {secret_name}")
        except json.JSONDecodeError:
            logger.error(f"Secret {secret_name} is not valid JSON")
            raise ValueError(f"Secret {secret_name} is not valid JSON")
        except Exception as e:
            logger.error(f"Error retrieving secret {secret_name}: {str(e)}")
            raise
    
    def get_secret_value(self, secret_name: str, key: str) -> Optional[str]:
        """Retrieve a specific value from a secret."""
        try:
            secret_data = self.get_secret(secret_name)
            return secret_data.get(key)
        except Exception as e:
            logger.error(f"Error retrieving key {key} from secret {secret_name}: {str(e)}")
            return None


class MockSecretManager(SecretManagerInterface):
    """Mock implementation for testing and development."""
    
    def __init__(self, mock_secrets: Dict[str, Dict[str, Any]] = None):
        self.mock_secrets = mock_secrets or {}
    
    def get_secret(self, secret_name: str) -> Dict[str, Any]:
        """Retrieve a mock secret."""
        if secret_name not in self.mock_secrets:
            raise ValueError(f"Mock secret {secret_name} not found")
        return self.mock_secrets[secret_name]
    
    def get_secret_value(self, secret_name: str, key: str) -> Optional[str]:
        """Retrieve a specific value from a mock secret."""
        try:
            secret_data = self.get_secret(secret_name)
            return secret_data.get(key)
        except Exception:
            return None


class SecretManager:
    """Unified secret manager that abstracts different providers."""
    
    def __init__(self, provider: str = None):
        self.provider = provider or os.getenv('SECRET_PROVIDER', 'aws')
        self._client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the appropriate secret manager client."""
        if self.provider.lower() == 'aws':
            self._client = AWSSecretManager()
        elif self.provider.lower() == 'gcp':
            self._client = GCPSecretManager()
        elif self.provider.lower() == 'mock':
            # Load mock secrets from environment or use defaults
            mock_secrets = self._load_mock_secrets()
            self._client = MockSecretManager(mock_secrets)
        else:
            raise ValueError(f"Unsupported secret provider: {self.provider}")
    
    def _load_mock_secrets(self) -> Dict[str, Dict[str, Any]]:
        """Load mock secrets for development/testing."""
        return {
            'boom-bust-sentinel/api-keys': {
                'telegram_bot_token': 'mock_telegram_token',
                'grafana_api_key': 'mock_grafana_key',
                'symbl_api_key': 'mock_symbl_key',
                'finra_api_key': 'mock_finra_key'
            },
            'boom-bust-sentinel/database': {
                'connection_string': 'mock_db_connection',
                'username': 'mock_user',
                'password': 'mock_password'
            },
            'boom-bust-sentinel/notifications': {
                'sns_topic_arn': 'arn:aws:sns:us-east-1:123456789012:mock-topic',
                'slack_webhook_url': 'https://hooks.slack.com/mock/webhook',
                'telegram_chat_id': 'mock_chat_id'
            }
        }
    
    def get_secret(self, secret_name: str) -> Dict[str, Any]:
        """Retrieve a secret."""
        return self._client.get_secret(secret_name)
    
    def get_secret_value(self, secret_name: str, key: str) -> Optional[str]:
        """Retrieve a specific value from a secret."""
        return self._client.get_secret_value(secret_name, key)
    
    def get_api_credentials(self) -> Dict[str, str]:
        """Get all API credentials."""
        try:
            return self.get_secret('boom-bust-sentinel/api-keys')
        except Exception as e:
            logger.error(f"Error retrieving API credentials: {str(e)}")
            return {}
    
    def get_database_config(self) -> Dict[str, str]:
        """Get database configuration."""
        try:
            return self.get_secret('boom-bust-sentinel/database')
        except Exception as e:
            logger.error(f"Error retrieving database config: {str(e)}")
            return {}
    
    def get_notification_config(self) -> Dict[str, str]:
        """Get notification configuration."""
        try:
            return self.get_secret('boom-bust-sentinel/notifications')
        except Exception as e:
            logger.error(f"Error retrieving notification config: {str(e)}")
            return {}