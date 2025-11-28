"""
Configuration package for Text-to-SQL POC.

This package now delegates to the centralized config.py module.
All configuration is stored in backend/config.json.

DEPRECATED: Import from config.Config instead of datasets.*
"""

import warnings
from config import Config

# Backward compatibility exports - these will raise deprecation warnings
def _deprecated_wrapper(func_name, new_location):
    """Create a wrapper that warns about deprecation"""
    def wrapper(*args, **kwargs):
        warnings.warn(
            f"{func_name} is deprecated. Use {new_location} instead.",
            DeprecationWarning,
            stacklevel=2
        )
        return getattr(Config, func_name)(*args, **kwargs)
    return wrapper

# Re-export Config methods with deprecation warnings
get_dataset = _deprecated_wrapper('get_dataset', 'Config.get_dataset')
list_datasets = _deprecated_wrapper('list_datasets', 'Config.list_datasets')
get_db_path = _deprecated_wrapper('get_db_path', 'Config.get_db_path')
validate_dataset_id = _deprecated_wrapper('validate_dataset_id', 'Config.validate_dataset_id')
get_active_dataset = _deprecated_wrapper('get_active_dataset', 'Config.get_active_dataset')
get_active_dataset_info = _deprecated_wrapper('get_active_dataset_info', 'Config.get_active_dataset_info')

# Note: set_active_dataset not directly available in Config
# Use _update_active_dataset_in_config from routes instead
def set_active_dataset(*args, **kwargs):
    warnings.warn(
        "set_active_dataset is deprecated. Use Config directly or the API endpoint.",
        DeprecationWarning,
        stacklevel=2
    )
    raise NotImplementedError("Use /dataset/active endpoint instead")

# DATASETS dict no longer available - query Config.list_datasets() instead
class _DatasetsProxy:
    """Proxy to warn about DATASETS usage"""
    def __getitem__(self, key):
        warnings.warn(
            "DATASETS dict is deprecated. Use Config.get_dataset(id) instead.",
            DeprecationWarning,
            stacklevel=2
        )
        return Config.get_dataset(key)
    
    def __iter__(self):
        warnings.warn(
            "DATASETS dict is deprecated. Use Config.list_datasets() instead.",
            DeprecationWarning,
            stacklevel=2
        )
        datasets = Config._get_nested(Config._config_data, 'datasets', default={})
        return iter(datasets)
    
    def keys(self):
        warnings.warn(
            "DATASETS dict is deprecated. Use Config.list_datasets() instead.",
            DeprecationWarning,
            stacklevel=2
        )
        datasets = Config._get_nested(Config._config_data, 'datasets', default={})
        return datasets.keys()

DATASETS = _DatasetsProxy()

__all__ = [
    'DATASETS',  # deprecated
    'get_dataset',  # deprecated
    'list_datasets',  # deprecated
    'get_db_path',  # deprecated
    'validate_dataset_id',  # deprecated
    'get_active_dataset',  # deprecated
    'set_active_dataset',  # deprecated
    'get_active_dataset_info'  # deprecated
]
