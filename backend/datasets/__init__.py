"""
Configuration package for Text-to-SQL POC.

This package contains:
- dataset_config.py: Dataset definitions and multi-database support
- active_dataset.py: Backend configuration for active dataset
"""

from .dataset_config import DATASETS, get_dataset, list_datasets, get_db_path, validate_dataset_id
from .active_dataset import get_active_dataset, set_active_dataset, get_active_dataset_info

__all__ = [
    'DATASETS', 
    'get_dataset', 
    'list_datasets', 
    'get_db_path', 
    'validate_dataset_id',
    'get_active_dataset',
    'set_active_dataset',
    'get_active_dataset_info'
]

