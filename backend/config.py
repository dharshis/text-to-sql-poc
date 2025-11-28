"""
Centralized configuration management for text-to-sql-poc backend.

Loads all configuration from config.json with support for environment
variable interpolation using ${VAR_NAME} syntax.
"""

import json
import os
import re
import logging
from pathlib import Path
from typing import Any, Dict, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

# Configuration file path
CONFIG_FILE = Path(__file__).parent / "config.json"

# Global config cache
_config_data: Optional[Dict] = None


def _interpolate_env_vars(value: Any) -> Any:
    """
    Recursively interpolate environment variables in config values.
    
    Supports ${VAR_NAME} syntax. If environment variable not found,
    keeps the original ${VAR_NAME} string.
    
    Args:
        value: Config value (str, dict, list, or other)
        
    Returns:
        Value with environment variables interpolated
    """
    if isinstance(value, str):
        # Find all ${VAR_NAME} patterns
        pattern = r'\$\{([^}]+)\}'
        
        def replacer(match):
            var_name = match.group(1)
            env_value = os.environ.get(var_name)
            if env_value is None:
                logger.warning(f"Environment variable {var_name} not found, keeping placeholder")
                return match.group(0)  # Keep ${VAR_NAME}
            return env_value
        
        return re.sub(pattern, replacer, value)
    
    elif isinstance(value, dict):
        return {k: _interpolate_env_vars(v) for k, v in value.items()}
    
    elif isinstance(value, list):
        return [_interpolate_env_vars(item) for item in value]
    
    else:
        return value


def load_config(force_reload: bool = False) -> Dict:
    """
    Load and parse config.json with environment variable interpolation.
    
    Args:
        force_reload: If True, reload config even if already cached
        
    Returns:
        Dict containing full configuration
        
    Raises:
        FileNotFoundError: If config.json doesn't exist
        json.JSONDecodeError: If config.json is invalid JSON
    """
    global _config_data
    
    if _config_data is not None and not force_reload:
        return _config_data
    
    if not CONFIG_FILE.exists():
        raise FileNotFoundError(
            f"Configuration file not found: {CONFIG_FILE}\n"
            "Please create config.json from config.json.example"
        )
    
    try:
        with open(CONFIG_FILE, 'r') as f:
            raw_config = json.load(f)
        
        # Interpolate environment variables
        _config_data = _interpolate_env_vars(raw_config)
        
        logger.info(f"Configuration loaded from {CONFIG_FILE}")
        return _config_data
    
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in config file: {e}")
        raise
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        raise


def _get_nested(data: Dict, *path: str, default: Any = None) -> Any:
    """
    Navigate nested dictionary using path.
    
    Args:
        data: Dictionary to navigate
        *path: Path components (e.g., 'flask', 'port')
        default: Default value if path not found
        
    Returns:
        Value at path or default
    """
    current = data
    for key in path:
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    return current


# Load configuration on module import
try:
    load_config()
except Exception as e:
    logger.error(f"Failed to load configuration on import: {e}")
    _config_data = {}


class Config:
    """
    Application configuration class.
    
    Provides backward-compatible API while loading from config.json
    Class attributes are initialized from config data.
    """
    
    # Initialize class attributes from config
    # These will be set after config loads
    APP_NAME: str = None
    VERSION: str = None
    ENV: str = None
    DEBUG: bool = None
    PORT: int = None
    HOST: str = None
    CORS_ORIGINS: list = None
    ANTHROPIC_API_KEY: Optional[str] = None
    CLAUDE_MODEL: str = None
    CLAUDE_MAX_TOKENS: int = None
    CLAUDE_TIMEOUT: int = None
    MAX_QUERY_RESULTS: int = None
    QUERY_TIMEOUT: int = None
    DATABASE_PATH: str = None
    
    @classmethod
    def _initialize_attributes(cls):
        """Initialize class attributes from config data"""
        cls.APP_NAME = _get_nested(_config_data, 'application', 'name', default='Text-to-SQL POC')
        cls.VERSION = _get_nested(_config_data, 'application', 'version', default='1.0.0')
        cls.ENV = _get_nested(_config_data, 'application', 'environment', default='development')
        cls.DEBUG = _get_nested(_config_data, 'flask', 'debug', default=True)
        
        # Check environment variable first for port
        env_port = os.environ.get('FLASK_PORT')
        cls.PORT = int(env_port) if env_port else _get_nested(_config_data, 'flask', 'port', default=5001)
        
        cls.HOST = _get_nested(_config_data, 'flask', 'host', default='0.0.0.0')
        cls.CORS_ORIGINS = _get_nested(_config_data, 'flask', 'cors_origins', default=['http://localhost:5173'])
        
        # API key with env var fallback
        key = _get_nested(_config_data, 'claude', 'api_key')
        if key and key.startswith('${'):
            key = os.environ.get('ANTHROPIC_API_KEY')
        cls.ANTHROPIC_API_KEY = key
        
        cls.CLAUDE_MODEL = _get_nested(_config_data, 'claude', 'model', default='claude-sonnet-4-5-20250929')
        cls.CLAUDE_MAX_TOKENS = _get_nested(_config_data, 'claude', 'max_tokens', default=1000)
        cls.CLAUDE_TIMEOUT = _get_nested(_config_data, 'claude', 'timeout', default=10)
        cls.MAX_QUERY_RESULTS = _get_nested(_config_data, 'query_execution', 'max_results', default=1000)
        cls.QUERY_TIMEOUT = _get_nested(_config_data, 'query_execution', 'timeout', default=30)
        
        # DATABASE_PATH from active dataset
        try:
            dataset_info = cls.get_active_dataset_info()
            cls.DATABASE_PATH = dataset_info.get('db_path', '../data/text_to_sql_poc.db')
        except:
            cls.DATABASE_PATH = '../data/text_to_sql_poc.db'
    
    # Dataset Management
    @classmethod
    def get_active_dataset(cls) -> str:
        """
        Get the currently active dataset ID.
        
        Returns:
            str: Active dataset ID (e.g., "sales", "em_market")
        """
        # Check environment variable first
        env_dataset = os.environ.get('ACTIVE_DATASET')
        if env_dataset:
            return env_dataset
        
        return _get_nested(_config_data, 'active_dataset', default='sales')
    
    @classmethod
    def get_dataset(cls, dataset_id: Optional[str] = None) -> Dict:
        """
        Get dataset configuration.
        
        Args:
            dataset_id: Dataset identifier (defaults to active dataset)
            
        Returns:
            Dict with dataset configuration
            
        Raises:
            ValueError: If dataset_id not found
        """
        if dataset_id is None:
            dataset_id = cls.get_active_dataset()
        
        datasets = _get_nested(_config_data, 'datasets', default={})
        
        if dataset_id not in datasets:
            available = list(datasets.keys())
            raise ValueError(
                f"Dataset '{dataset_id}' not found. "
                f"Available datasets: {available}"
            )
        
        # Return copy to prevent modification
        dataset_config = datasets[dataset_id].copy()
        
        # Resolve relative paths to absolute
        if 'db_path' in dataset_config:
            db_path = Path(dataset_config['db_path'])
            if not db_path.is_absolute():
                # Resolve relative to project root
                project_root = Path(__file__).parent.parent
                dataset_config['db_path'] = str((project_root / db_path).resolve())
        
        return dataset_config
    
    @classmethod
    def get_active_dataset_info(cls) -> Dict:
        """
        Get full configuration for the active dataset.
        
        Returns:
            dict: Active dataset configuration
        """
        dataset_id = cls.get_active_dataset()
        return cls.get_dataset(dataset_id)
    
    @classmethod
    def list_datasets(cls) -> list:
        """
        List all available datasets.
        
        Returns:
            List of dicts with dataset summary info (minimal - runtime essentials only)
        """
        datasets = _get_nested(_config_data, 'datasets', default={})
        
        return [
            {
                "id": ds.get("id"),
                "name": ds.get("name"),
                "db_path": ds.get("db_path"),
                "client_isolation_enabled": ds.get("client_isolation", {}).get("enabled", False)
            }
            for ds in datasets.values()
        ]
    
    @classmethod
    def get_db_path(cls, dataset_id: Optional[str] = None) -> str:
        """
        Get database file path for a dataset.
        
        Args:
            dataset_id: Dataset identifier (defaults to active)
            
        Returns:
            str: Absolute path to database file
        """
        dataset = cls.get_dataset(dataset_id)
        return dataset['db_path']
    
    @classmethod
    def validate_dataset_id(cls, dataset_id: str) -> bool:
        """
        Validate that a dataset ID exists.
        
        Args:
            dataset_id: Dataset identifier to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        datasets = _get_nested(_config_data, 'datasets', default={})
        return dataset_id in datasets
    
    @classmethod
    def get_client_config(cls, dataset_id: Optional[str] = None) -> Dict:
        """
        Get client/corporation configuration for a dataset.
        
        Different datasets use different tables for "clients":
        - sales: uses 'clients' table with 'client_id' field
        - em_market: uses 'Dim_Corporation' table with 'corp_id' field
        
        Args:
            dataset_id: Dataset identifier (defaults to active)
            
        Returns:
            dict: Configuration with table_name, id_field, name_field
        """
        dataset = cls.get_dataset(dataset_id)
        client_iso = dataset.get("client_isolation", {})
        
        # Check if dataset has custom client mapping
        if "client_table" in client_iso:
            return {
                "table_name": client_iso["client_table"],
                "id_field": client_iso["client_id_field"],
                "name_field": client_iso["client_name_field"]
            }
        
        # Default: use "clients" table
        return {
            "table_name": "clients",
            "id_field": "client_id",
            "name_field": "client_name"
        }
    
    @classmethod
    def validate(cls):
        """
        Validate that required configuration is present.
        
        Raises:
            ValueError: If required configuration is missing
        """
        errors = []
        
        if not cls.ANTHROPIC_API_KEY:
            errors.append(
                "ANTHROPIC_API_KEY is not set. "
                "Set environment variable or update config.json"
            )
        
        # Validate active dataset exists
        try:
            cls.get_active_dataset_info()
        except ValueError as e:
            errors.append(str(e))
        
        if errors:
            raise ValueError(
                "Configuration validation failed:\n" + 
                "\n".join(f"  - {e}" for e in errors)
            )
        
        return True
    
    @classmethod
    def reload(cls):
        """Reload configuration from config.json"""
        load_config(force_reload=True)
        cls._initialize_attributes()
        logger.info("Configuration reloaded")
    
    @classmethod
    def get_database_url(cls):
        """Get SQLAlchemy database URL for active dataset."""
        db_path = cls.get_db_path()
        return f'sqlite:///{db_path}'


# Initialize Config class attributes after class definition
if _config_data:
    Config._initialize_attributes()
