"""
Domain Vocabulary Extractor

Automatically extracts domain-specific keywords from database schema.
Used for follow-up detection and clarification detection in agentic text-to-SQL service.
"""

import sqlite3
import re
import logging
from typing import Dict, List, Set
from pathlib import Path

logger = logging.getLogger(__name__)

# Module-level cache to avoid repeated schema queries
_vocabulary_cache = {}


class DomainVocabularyExtractor:
    """Extract domain-specific vocabulary from database schema."""

    def __init__(self, dataset_id: str, db_path: str):
        """
        Initialize extractor for a specific dataset.

        Args:
            dataset_id: Dataset identifier (e.g., "sales", "em_market")
            db_path: Path to SQLite database file
        """
        self.dataset_id = dataset_id
        self.db_path = db_path
        self._cache = None

        logger.info(f"Initialized DomainVocabularyExtractor for dataset: {dataset_id}")

    def extract_vocabulary(self) -> Dict[str, List[str]]:
        """
        Extract entity and metric keywords from schema.

        Returns:
            Dictionary with extracted vocabulary:
            {
                "entities": ["product", "customer", "brand", "market"...],
                "metrics": ["revenue", "quantity", "value", "count"...],
                "dimensions": ["region", "category", "country"...]
            }
        """
        if self._cache:
            return self._cache

        logger.info(f"Extracting vocabulary from schema: {self.db_path}")

        try:
            # Connect to database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            tables = [row[0] for row in cursor.fetchall()]

            logger.debug(f"Found {len(tables)} tables in schema")

            # Extract entities from table names
            entities = self._extract_entities(tables)

            # Extract metrics and dimensions from columns
            metrics = set()
            dimensions = set()

            for table in tables:
                cursor.execute(f"PRAGMA table_info({table})")
                columns = cursor.fetchall()

                # Determine if this is a dimension table
                is_dimension_table = table.lower().startswith('dim_')

                for col_info in columns:
                    col_name = col_info[1]  # Column name
                    col_type = col_info[2]  # Column type

                    # Extract metrics from numeric columns
                    if self._is_numeric_type(col_type):
                        metric_words = self._extract_words_from_column(col_name)
                        metrics.update(metric_words)

                    # Extract dimensions from dimension table columns
                    if is_dimension_table:
                        dimension_words = self._extract_words_from_column(col_name)
                        dimensions.update(dimension_words)

            conn.close()

            # Convert to sorted lists
            vocabulary = {
                "entities": sorted(list(entities)),
                "metrics": sorted(list(metrics)),
                "dimensions": sorted(list(dimensions))
            }

            logger.info(f"Extracted vocabulary: {len(vocabulary['entities'])} entities, "
                       f"{len(vocabulary['metrics'])} metrics, {len(vocabulary['dimensions'])} dimensions")
            logger.debug(f"Entities: {vocabulary['entities'][:10]}...")
            logger.debug(f"Metrics: {vocabulary['metrics'][:10]}...")
            logger.debug(f"Dimensions: {vocabulary['dimensions'][:10]}...")

            self._cache = vocabulary
            return vocabulary

        except Exception as e:
            logger.error(f"Failed to extract vocabulary from schema: {e}", exc_info=True)
            return self._get_fallback_vocabulary()

    def _extract_entities(self, tables: List[str]) -> Set[str]:
        """
        Extract entity keywords from table names.

        Args:
            tables: List of table names

        Returns:
            Set of entity keywords (singular and plural forms)
        """
        entities = set()

        for table in tables:
            # Remove common prefixes (Fact_, Dim_, fact_, dim_)
            clean_name = re.sub(r'^(Fact_|Dim_|fact_|dim_)', '', table, flags=re.IGNORECASE)

            # Convert snake_case to words
            words = clean_name.lower().split('_')

            for word in words:
                if len(word) > 2:  # Skip very short words
                    # Add singular form
                    entities.add(word)

                    # Add plural form (simple pluralization)
                    if not word.endswith('s'):
                        entities.add(word + 's')

                    # Handle special cases
                    if word.endswith('y') and len(word) > 3:
                        # category → categories
                        entities.add(word[:-1] + 'ies')

        # Add common generic entities
        entities.update(['data', 'records', 'report', 'reports'])

        return entities

    def _extract_words_from_column(self, col_name: str) -> Set[str]:
        """
        Extract meaningful words from a column name.

        Args:
            col_name: Column name (e.g., "value_sold_usd", "market_value")

        Returns:
            Set of extracted words
        """
        words = set()

        # Remove common suffixes
        clean_name = re.sub(r'_(id|usd|m|k|pct|percent|flag)$', '', col_name.lower())

        # Split by underscore
        parts = clean_name.split('_')

        for part in parts:
            if len(part) > 2:  # Skip very short words and IDs
                words.add(part)

        # Add common synonyms for metrics
        synonym_map = {
            'value': ['revenue', 'sales', 'amount'],
            'qty': ['quantity', 'volume'],
            'amt': ['amount'],
            'sold': ['sales'],
            'count': ['total', 'number']
        }

        for word in list(words):
            if word in synonym_map:
                words.update(synonym_map[word])

        return words

    def _is_numeric_type(self, col_type: str) -> bool:
        """
        Check if a column type is numeric.

        Args:
            col_type: SQL column type

        Returns:
            True if numeric type
        """
        numeric_types = ['INTEGER', 'REAL', 'NUMERIC', 'DECIMAL', 'FLOAT', 'DOUBLE']
        return any(t in col_type.upper() for t in numeric_types)

    def _get_fallback_vocabulary(self) -> Dict[str, List[str]]:
        """
        Get minimal fallback vocabulary when schema extraction fails.

        Returns:
            Dictionary with minimal generic keywords
        """
        logger.warning(f"Using fallback vocabulary for dataset: {self.dataset_id}")

        return {
            "entities": ["data", "records", "metric", "metrics"],
            "metrics": ["value", "count", "total", "amount"],
            "dimensions": ["category", "type", "group"]
        }


def get_vocabulary(dataset_id: str, db_path: str) -> Dict[str, List[str]]:
    """
    Get domain vocabulary with caching.

    Args:
        dataset_id: Dataset identifier
        db_path: Path to database file

    Returns:
        Dictionary with vocabulary (entities, metrics, dimensions)
    """
    cache_key = f"{dataset_id}:{db_path}"

    if cache_key not in _vocabulary_cache:
        logger.info(f"Loading vocabulary for dataset: {dataset_id} (not in cache)")
        extractor = DomainVocabularyExtractor(dataset_id, db_path)
        _vocabulary_cache[cache_key] = extractor.extract_vocabulary()
    else:
        logger.debug(f"Using cached vocabulary for dataset: {dataset_id}")

    return _vocabulary_cache[cache_key]


def clear_cache():
    """Clear the vocabulary cache. Useful for testing."""
    global _vocabulary_cache
    _vocabulary_cache = {}
    logger.info("Vocabulary cache cleared")


# Example usage and testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Test with sales dataset
    print("\n=== Testing with Sales Dataset ===")
    vocab = get_vocabulary("sales", "../data/text_to_sql_poc.db")
    print(f"Entities: {vocab['entities'][:15]}")
    print(f"Metrics: {vocab['metrics'][:15]}")
    print(f"Dimensions: {vocab['dimensions'][:15]}")

    # Test with em_market dataset
    print("\n=== Testing with EM Market Dataset ===")
    vocab_em = get_vocabulary("em_market", "../data/em_market/em_market.db")
    print(f"Entities: {vocab_em['entities'][:15]}")
    print(f"Metrics: {vocab_em['metrics'][:15]}")
    print(f"Dimensions: {vocab_em['dimensions'][:15]}")
