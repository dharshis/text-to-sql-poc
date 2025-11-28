"""
Dataset configuration for multi-database support.

This module defines available datasets and their metadata to support
dynamic dataset switching in the Text-to-SQL system.
"""

import os
from pathlib import Path

# Get project root
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Dataset configurations
DATASETS = {
    "sales": {
        "id": "sales",
        "name": "Sales Transactions",
        "description": "Transaction-level sales data with products, regions, and clients",
        "db_path": str(PROJECT_ROOT / "data" / "text_to_sql_poc.db"),
        "schema_type": "transactional",
        "fact_tables": ["sales"],
        "dimension_tables": ["products", "regions", "clients", "customer_segments"],
        "key_dimensions": {
            "products": ["product_name", "category", "price", "brand"],
            "regions": ["region"],
            "clients": ["client_name", "industry", "region"],
            "customer_segments": ["segment_name", "description"]
        },
        "metrics": ["revenue", "quantity", "profit_margin"],
        "time_field": "date",
        "client_isolation": {
            "enabled": True,
            "field": "client_id",
            "tables_requiring_filter": ["sales"]  # Fact tables only
        },
        "sample_queries": [
            "Top 5 products by revenue",
            "Sales by region for client Walmart",
            "Revenue trends for Q4 2024",
            "Products in Electronics category"
        ]
    },
    
    "market_size": {
        "id": "market_size",
        "name": "Market Size Analytics",
        "description": "Market size data (value & volume) with forecasts across geographies and segments",
        "db_path": str(PROJECT_ROOT / "data" / "market_size.db"),
        "schema_type": "dimensional",
        "fact_tables": ["fact_market_size", "fact_forecasts"],
        "dimension_tables": ["dim_markets", "dim_geography", "dim_time", "dim_currency", 
                            "dim_segment_types", "dim_segment_values"],
        "key_dimensions": {
            "dim_markets": ["market_name", "naics_code"],
            "dim_geography": ["country", "region", "country_code"],
            "dim_time": ["year", "quarter", "year_quarter"],
            "dim_currency": ["currency_code", "currency_type"],
            "dim_segment_types": ["segment_name"],
            "dim_segment_values": ["value_name", "description"]
        },
        "metrics": ["market_value_usd_m", "market_volume_units", "forecast_value_usd_m", "cagr"],
        "time_field": "year",
        "client_isolation": {
            "enabled": True,
            "field": "client_id",
            "tables_requiring_filter": ["fact_market_size", "fact_forecasts"]  # Fact tables
        },
        "sample_queries": [
            "Top 5 markets by value globally in 2023",
            "Electric vehicles market size trends from 2020 to 2024",
            "Compare EV market value across USA, China, Germany",
            "Forecast for automotive market in 2025",
            "Show market volume by region"
        ]
    }
}

# Default dataset
DEFAULT_DATASET = "sales"


def get_dataset(dataset_id: str = None):
    """
    Get dataset configuration.
    
    Args:
        dataset_id: Dataset identifier (defaults to DEFAULT_DATASET)
        
    Returns:
        Dict with dataset configuration
        
    Raises:
        ValueError: If dataset_id not found
    """
    if dataset_id is None:
        dataset_id = DEFAULT_DATASET
    
    if dataset_id not in DATASETS:
        raise ValueError(f"Dataset '{dataset_id}' not found. Available: {list(DATASETS.keys())}")
    
    return DATASETS[dataset_id]


def list_datasets():
    """
    List all available datasets.
    
    Returns:
        List of dicts with dataset summary info
    """
    return [
        {
            "id": ds["id"],
            "name": ds["name"],
            "description": ds["description"],
            "schema_type": ds["schema_type"],
            "fact_tables": ds["fact_tables"],
            "sample_queries": ds["sample_queries"][:3]  # First 3 samples
        }
        for ds in DATASETS.values()
    ]


def get_db_path(dataset_id: str = None):
    """
    Get database file path for a dataset.
    
    Args:
        dataset_id: Dataset identifier
        
    Returns:
        str: Absolute path to database file
    """
    dataset = get_dataset(dataset_id)
    return dataset["db_path"]


def validate_dataset_id(dataset_id: str):
    """
    Validate that a dataset ID exists.
    
    Args:
        dataset_id: Dataset identifier to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    return dataset_id in DATASETS

