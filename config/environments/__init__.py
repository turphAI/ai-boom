"""
Environment-specific configuration loader for Boom-Bust Sentinel
"""

import os
import importlib
from typing import Any, Dict

def load_environment_config() -> Dict[str, Any]:
    """
    Load configuration based on the current environment.
    
    Returns:
        Dict containing environment-specific configuration
    """
    environment = os.getenv("STAGE", "development").lower()
    
    try:
        # Import the appropriate environment module
        config_module = importlib.import_module(f"config.environments.{environment}")
        
        # Extract all uppercase attributes as configuration
        config = {}
        for attr_name in dir(config_module):
            if attr_name.isupper():
                config[attr_name] = getattr(config_module, attr_name)
        
        return config
    
    except ImportError:
        # Fallback to development if environment not found
        print(f"Warning: Environment '{environment}' not found, falling back to development")
        config_module = importlib.import_module("config.environments.development")
        
        config = {}
        for attr_name in dir(config_module):
            if attr_name.isupper():
                config[attr_name] = getattr(config_module, attr_name)
        
        return config

def get_config(key: str, default: Any = None) -> Any:
    """
    Get a specific configuration value.
    
    Args:
        key: Configuration key to retrieve
        default: Default value if key not found
        
    Returns:
        Configuration value or default
    """
    config = load_environment_config()
    return config.get(key, default)

def is_production() -> bool:
    """Check if running in production environment."""
    return os.getenv("STAGE", "development").lower() == "production"

def is_staging() -> bool:
    """Check if running in staging environment."""
    return os.getenv("STAGE", "development").lower() == "staging"

def is_development() -> bool:
    """Check if running in development environment."""
    return os.getenv("STAGE", "development").lower() == "development"