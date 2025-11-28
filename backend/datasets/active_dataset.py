"""
Active dataset configuration for backend.

This module manages which dataset is currently active for queries.
The frontend doesn't need to know about datasets - the backend handles it.
"""

import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

# File to store active dataset configuration
CONFIG_FILE = Path(__file__).parent / ".active_dataset"

# Default dataset
DEFAULT_DATASET = "sales"


def get_active_dataset() -> str:
    """
    Get the currently active dataset ID.
    
    Returns:
        str: Active dataset ID (e.g., "sales", "market_size")
    """
    # Check environment variable first
    env_dataset = os.environ.get('ACTIVE_DATASET')
    if env_dataset:
        logger.info(f"Active dataset from environment: {env_dataset}")
        return env_dataset
    
    # Check config file
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r') as f:
                dataset_id = f.read().strip()
                if dataset_id:
                    logger.info(f"Active dataset from config file: {dataset_id}")
                    return dataset_id
        except Exception as e:
            logger.warning(f"Error reading active dataset config: {e}")
    
    # Default
    logger.info(f"Using default dataset: {DEFAULT_DATASET}")
    return DEFAULT_DATASET


def set_active_dataset(dataset_id: str) -> bool:
    """
    Set the active dataset ID.
    
    Args:
        dataset_id: Dataset ID to activate
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        from datasets.dataset_config import validate_dataset_id
        
        # Validate dataset exists
        if not validate_dataset_id(dataset_id):
            logger.error(f"Invalid dataset ID: {dataset_id}")
            return False
        
        # Write to config file
        with open(CONFIG_FILE, 'w') as f:
            f.write(dataset_id)
        
        logger.info(f"✓ Active dataset changed to: {dataset_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error setting active dataset: {e}")
        return False


def get_active_dataset_info() -> dict:
    """
    Get full configuration for the active dataset.
    
    Returns:
        dict: Dataset configuration
    """
    from datasets.dataset_config import get_dataset
    
    dataset_id = get_active_dataset()
    return get_dataset(dataset_id)

