"""
Tool infrastructure for agentic workflows.

Provides:
- Tool base class with standardized execute() interface
- Error handling and performance tracking
- Reusable tool pattern for agent actions
- Metadata retrieval for business rules and query patterns

Architecture Reference: docs/architecture-agentic-text2sql.md Section 6.1
"""

from typing import Callable, Dict, List, Optional
from datetime import datetime
import logging
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)


class Tool:
    """
    Base tool class for agentic workflow.
    Architecture Reference: Section 6.1 (Tool Base Class)
    
    Tools are stateless, reusable components that agents can invoke.
    All tools follow standardized interface: execute(**kwargs) -> Dict
    """
    
    def __init__(self, name: str, description: str, function: Callable):
        """
        Initialize tool.
        
        Args:
            name: Tool identifier
            description: Human-readable description
            function: Callable to execute (receives **kwargs)
        """
        self.name = name
        self.description = description
        self.function = function
        logger.info(f"Tool initialized: {name}")
    
    def execute(self, **kwargs) -> Dict:
        """
        Execute the tool with standardized error handling.
        Architecture Reference: Section 6.1
        
        Returns:
            Dict with standardized format:
            - Success: {success: True, tool: str, result: Any, elapsed: float}
            - Failure: {success: False, tool: str, error: str, elapsed: float}
        """
        start_time = datetime.now()
        logger.info(f"Executing tool '{self.name}' with params: {list(kwargs.keys())}")
        
        try:
            result = self.function(**kwargs)
            
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(f"Tool '{self.name}' succeeded in {elapsed:.3f}s")
            
            return {
                "success": True,
                "tool": self.name,
                "result": result,
                "elapsed": elapsed
            }
            
        except Exception as e:
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.error(f"Tool '{self.name}' failed after {elapsed:.3f}s: {e}", exc_info=True)
            
            return {
                "success": False,
                "tool": self.name,
                "error": str(e),
                "elapsed": elapsed
            }


# ============================================================================
# METADATA RETRIEVAL FUNCTIONS
# ============================================================================

def load_metadata_for_dataset(dataset_id: str, metadata_type: Optional[str] = None) -> List[Dict]:
    """
    Load metadata documents for a specific dataset.
    
    Args:
        dataset_id: Dataset identifier (e.g., "em_market", "sales")
        metadata_type: Optional filter by type (business_rule, query_pattern, table_metadata)
        
    Returns:
        List of metadata document dictionaries
    """
    try:
        from services.metadata_loader import load_dataset_metadata
        
        logger.info(f"Loading metadata for dataset: {dataset_id}")
        loader = load_dataset_metadata(dataset_id)
        
        if metadata_type:
            documents = loader.get_documents_by_type(metadata_type)
        else:
            documents = loader.documents
        
        # Convert to dictionaries
        result = [doc.to_dict() for doc in documents]
        logger.info(f"Loaded {len(result)} metadata documents")
        return result
        
    except Exception as e:
        logger.error(f"Error loading metadata: {e}")
        return []


def search_business_rules(dataset_id: str, query: str, top_k: int = 5) -> List[Dict]:
    """
    Search business rules based on query keywords.
    
    Simple keyword-based search for relevant business rules.
    
    Args:
        dataset_id: Dataset identifier
        query: User query or keywords to search
        top_k: Number of top results to return
        
    Returns:
        List of relevant business rule documents
    """
    try:
        from services.metadata_loader import load_dataset_metadata
        
        logger.info(f"Searching business rules for: {query}")
        loader = load_dataset_metadata(dataset_id)
        
        # Get business rules
        rules = loader.get_documents_by_type("business_rule")
        
        # Simple keyword scoring
        query_lower = query.lower()
        query_keywords = set(query_lower.split())
        
        scored_rules = []
        for rule in rules:
            content_lower = rule.content.lower()
            
            # Count keyword matches
            score = 0
            for keyword in query_keywords:
                if len(keyword) >= 3:  # Skip very short words
                    score += content_lower.count(keyword)
            
            if score > 0:
                scored_rules.append((score, rule))
        
        # Sort by score and get top k
        scored_rules.sort(key=lambda x: x[0], reverse=True)
        top_rules = [rule.to_dict() for score, rule in scored_rules[:top_k]]
        
        logger.info(f"Found {len(top_rules)} relevant business rules")
        return top_rules
        
    except Exception as e:
        logger.error(f"Error searching business rules: {e}")
        return []


def get_table_metadata(dataset_id: str, table_name: Optional[str] = None) -> List[Dict]:
    """
    Get table metadata documents.
    
    Args:
        dataset_id: Dataset identifier
        table_name: Optional specific table name to filter
        
    Returns:
        List of table metadata documents
    """
    try:
        from services.metadata_loader import load_dataset_metadata
        
        logger.info(f"Getting table metadata for dataset: {dataset_id}")
        loader = load_dataset_metadata(dataset_id)
        
        # Get all table metadata
        table_docs = loader.get_documents_by_type("table_metadata")
        
        # Filter by table name if specified
        if table_name:
            table_name_normalized = table_name.lower().replace('_', ' ')
            table_docs = [
                doc for doc in table_docs 
                if table_name_normalized in doc.file_name.lower() or 
                   table_name_normalized in doc.content.lower()
            ]
        
        result = [doc.to_dict() for doc in table_docs]
        logger.info(f"Found {len(result)} table metadata documents")
        return result
        
    except Exception as e:
        logger.error(f"Error getting table metadata: {e}")
        return []


def get_query_patterns(dataset_id: str, pattern_type: Optional[str] = None) -> List[Dict]:
    """
    Get query pattern templates.
    
    Args:
        dataset_id: Dataset identifier
        pattern_type: Optional filter by pattern category
        
    Returns:
        List of query pattern documents
    """
    try:
        from services.metadata_loader import load_dataset_metadata
        
        logger.info(f"Getting query patterns for dataset: {dataset_id}")
        loader = load_dataset_metadata(dataset_id)
        
        # Get query patterns
        patterns = loader.get_documents_by_type("query_pattern")
        
        # Filter by pattern type if specified
        if pattern_type:
            pattern_type_lower = pattern_type.lower()
            patterns = [
                doc for doc in patterns 
                if pattern_type_lower in doc.content.lower()
            ]
        
        result = [doc.to_dict() for doc in patterns]
        logger.info(f"Found {len(result)} query patterns")
        return result
        
    except Exception as e:
        logger.error(f"Error getting query patterns: {e}")
        return []


def get_sample_data(db_path: str, table_name: str, limit: int = 5) -> List[Dict]:
    """
    Fetch sample rows from a table to show data format.
    
    Args:
        db_path: Path to SQLite database
        table_name: Name of table to sample
        limit: Number of rows to return
        
    Returns:
        List of sample rows as dictionaries
    """
    try:
        logger.info(f"Fetching {limit} sample rows from {table_name}")
        
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        cursor = conn.cursor()
        
        cursor.execute(f"SELECT * FROM {table_name} LIMIT ?", (limit,))
        rows = cursor.fetchall()
        
        # Convert to list of dicts
        result = [dict(row) for row in rows]
        
        cursor.close()
        conn.close()
        
        logger.info(f"Retrieved {len(result)} sample rows")
        return result
        
    except Exception as e:
        logger.error(f"Error fetching sample data: {e}")
        return []


def format_metadata_for_prompt(metadata_docs: List[Dict], max_docs: int = 5) -> str:
    """
    Format metadata documents into a string suitable for LLM context.
    
    Args:
        metadata_docs: List of metadata document dictionaries
        max_docs: Maximum number of documents to include
        
    Returns:
        Formatted string with metadata content
    """
    if not metadata_docs:
        return "No relevant metadata found."
    
    # Limit number of docs
    docs_to_include = metadata_docs[:max_docs]
    
    formatted_parts = []
    formatted_parts.append("=== RELEVANT METADATA ===\n")
    
    for i, doc in enumerate(docs_to_include, 1):
        doc_type = doc.get('metadata', {}).get('type', 'unknown')
        section = doc.get('section', 'unknown')
        content = doc.get('content', '')
        
        formatted_parts.append(f"\n--- Document {i}: {doc_type} ({section}) ---")
        formatted_parts.append(content)
        formatted_parts.append("")
    
    formatted_parts.append("=== END METADATA ===")
    
    return "\n".join(formatted_parts)


# ============================================================================
# TOOL FACTORY FUNCTIONS
# ============================================================================

def create_metadata_search_tool(dataset_id: str) -> Tool:
    """
    Create a tool for searching metadata (business rules + query patterns).
    
    Args:
        dataset_id: Dataset identifier
        
    Returns:
        Tool instance for metadata search
    """
    def search_metadata(query: str, top_k: int = 5) -> Dict:
        """Search metadata for relevant context."""
        # Search business rules
        rules = search_business_rules(dataset_id, query, top_k=top_k)
        
        # Also get relevant query patterns
        patterns = get_query_patterns(dataset_id)
        
        # Score patterns similarly
        query_lower = query.lower()
        query_keywords = set(query_lower.split())
        
        scored_patterns = []
        for pattern in patterns:
            content_lower = pattern['content'].lower()
            score = sum(
                content_lower.count(keyword) 
                for keyword in query_keywords 
                if len(keyword) >= 3
            )
            if score > 0:
                scored_patterns.append((score, pattern))
        
        scored_patterns.sort(key=lambda x: x[0], reverse=True)
        top_patterns = [p for score, p in scored_patterns[:3]]
        
        return {
            "business_rules": rules,
            "query_patterns": top_patterns,
            "formatted_context": format_metadata_for_prompt(rules + top_patterns)
        }
    
    return Tool(
        name="search_metadata",
        description=f"Search business rules and query patterns for dataset {dataset_id}",
        function=search_metadata
    )


def create_table_schema_tool(dataset_id: str) -> Tool:
    """
    Create a tool for retrieving table schema information.
    
    Args:
        dataset_id: Dataset identifier
        
    Returns:
        Tool instance for table schema retrieval
    """
    def get_schema_info(table_name: Optional[str] = None) -> Dict:
        """Get table schema metadata."""
        metadata = get_table_metadata(dataset_id, table_name)
        
        return {
            "table_metadata": metadata,
            "formatted_context": format_metadata_for_prompt(metadata)
        }
    
    return Tool(
        name="get_table_schema",
        description=f"Get table schema and metadata for dataset {dataset_id}",
        function=get_schema_info
    )


def create_sample_data_tool(db_path: str) -> Tool:
    """
    Create a tool for fetching sample data from tables.
    
    Args:
        db_path: Path to database file
        
    Returns:
        Tool instance for sample data retrieval
    """
    def fetch_samples(table_name: str, limit: int = 5) -> Dict:
        """Fetch sample rows from table."""
        samples = get_sample_data(db_path, table_name, limit)
        
        # Format for display
        if samples:
            formatted = f"Sample data from {table_name} ({len(samples)} rows):\n"
            for i, row in enumerate(samples, 1):
                formatted += f"\nRow {i}: {row}"
        else:
            formatted = f"No sample data available for {table_name}"
        
        return {
            "samples": samples,
            "formatted": formatted
        }
    
    return Tool(
        name="get_sample_data",
        description=f"Fetch sample rows from database tables to understand data format",
        function=fetch_samples
    )


def create_metadata_tools_for_dataset(dataset_id: str, db_path: str) -> Dict[str, Tool]:
    """
    Create a complete set of metadata tools for a dataset.
    
    Args:
        dataset_id: Dataset identifier
        db_path: Path to database file
        
    Returns:
        Dictionary of tool_name -> Tool instances
    """
    return {
        "search_metadata": create_metadata_search_tool(dataset_id),
        "get_table_schema": create_table_schema_tool(dataset_id),
        "get_sample_data": create_sample_data_tool(db_path)
    }


