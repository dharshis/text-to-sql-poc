"""
Claude API service for SQL query generation.

This service integrates with Anthropic's Claude API to convert natural language
queries into SQL queries for the retail market research database.
"""

import logging
from anthropic import Anthropic, APIError, APITimeoutError
from config import Config

logger = logging.getLogger(__name__)


# Database schema for Claude context
DATABASE_SCHEMA = """
CREATE TABLE clients (
    client_id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_name TEXT NOT NULL,
    industry TEXT NOT NULL
);

CREATE TABLE products (
    product_id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    product_name TEXT NOT NULL,
    category TEXT NOT NULL,  -- electronics, apparel, home_goods
    brand TEXT NOT NULL,
    price REAL NOT NULL,
    FOREIGN KEY (client_id) REFERENCES clients(client_id)
);

CREATE TABLE sales (
    sale_id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    region TEXT NOT NULL,  -- North, South, East, West
    date TEXT NOT NULL,    -- ISO format: YYYY-MM-DD
    quantity INTEGER NOT NULL,
    revenue REAL NOT NULL,
    FOREIGN KEY (client_id) REFERENCES clients(client_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

CREATE TABLE customer_segments (
    segment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    segment_name TEXT NOT NULL,  -- Premium, Standard, Budget
    demographics TEXT,            -- JSON string
    FOREIGN KEY (client_id) REFERENCES clients(client_id)
);

-- Indexes
CREATE INDEX idx_sales_client_date ON sales(client_id, date);
CREATE INDEX idx_products_client_category ON products(client_id, category);
"""


SYSTEM_PROMPT = f"""You are an expert SQL query generator for SQLite databases.
You specialize in retail market research data analysis.

DATABASE SCHEMA:
{DATABASE_SCHEMA}

CRITICAL RULES:
1. ALWAYS include "WHERE client_id = {{client_id}}" in your queries to enforce data isolation
2. Use ONLY the tables and columns defined in the schema above
3. Generate valid SQLite syntax
4. Return ONLY the SQL query - no explanations, no markdown, no code blocks
5. Use appropriate JOINs when querying multiple tables
6. For aggregations, use GROUP BY and appropriate aggregate functions
7. Limit results to 100 rows unless explicitly requested otherwise
8. Use proper date formats (YYYY-MM-DD) for date comparisons
9. Always include the client_id filter even when JOINing tables

EXAMPLE QUERIES:

User: "Top 10 products by revenue"
SQL: SELECT p.product_name, SUM(s.revenue) as total_revenue FROM sales s JOIN products p ON s.product_id = p.product_id WHERE s.client_id = {{client_id}} GROUP BY p.product_name ORDER BY total_revenue DESC LIMIT 10

User: "Electronics sales by region"
SQL: SELECT s.region, COUNT(*) as sale_count, SUM(s.revenue) as total_revenue FROM sales s JOIN products p ON s.product_id = p.product_id WHERE s.client_id = {{client_id}} AND p.category = 'electronics' GROUP BY s.region ORDER BY total_revenue DESC

User: "Average transaction value by customer segment"
SQL: SELECT cs.segment_name, AVG(s.revenue) as avg_revenue FROM sales s JOIN customer_segments cs ON s.client_id = cs.client_id WHERE s.client_id = {{client_id}} GROUP BY cs.segment_name ORDER BY avg_revenue DESC
"""


class ClaudeService:
    """Service for interacting with Claude API to generate SQL queries."""

    def __init__(self, api_key=None):
        """
        Initialize Claude service.

        Args:
            api_key (str, optional): Anthropic API key. Uses Config.ANTHROPIC_API_KEY if None.
        """
        self.api_key = api_key or Config.ANTHROPIC_API_KEY

        if not self.api_key:
            raise ValueError("Anthropic API key is required. Set ANTHROPIC_API_KEY in .env file.")

        self.client = Anthropic(api_key=self.api_key)
        self.model = Config.CLAUDE_MODEL
        self.max_tokens = Config.CLAUDE_MAX_TOKENS
        self.timeout = Config.CLAUDE_TIMEOUT

        logger.info(f"Claude service initialized with model: {self.model}")

    def generate_sql(self, natural_language_query, client_id, client_name=None, custom_schema=None):
        """
        Generate SQL query from natural language using Claude API.

        Args:
            natural_language_query (str): User's natural language query
            client_id (int): Client ID for data isolation
            client_name (str, optional): Client name for additional context
            custom_schema (str, optional): Custom database schema (overrides default)

        Returns:
            str: Generated SQL query

        Raises:
            APITimeoutError: If Claude API times out
            APIError: If Claude API returns an error
            ValueError: If generated SQL is invalid
        """
        logger.info(f"Generating SQL for client_id={client_id}, query='{natural_language_query[:100]}'")

        # Build user prompt with client context
        user_prompt = f"""Client Context: client_id = {client_id}"""
        if client_name:
            user_prompt += f', client_name = "{client_name}"'

        user_prompt += f"""

Natural Language Query: {natural_language_query}

Generate the SQL query:"""

        # Use custom schema if provided, otherwise use default
        schema_to_use = custom_schema if custom_schema else DATABASE_SCHEMA
        system_prompt = f"""You are an expert SQL query generator for SQLite databases.
You specialize in retail market research data analysis.

DATABASE SCHEMA:
{schema_to_use}

CRITICAL RULES:
1. ALWAYS include "WHERE client_id = {{client_id}}" in your queries to enforce data isolation
2. Use ONLY the tables and columns defined in the schema above
3. Generate valid SQLite syntax
4. Return ONLY the SQL query without explanations
5. Use proper JOINs when querying across multiple tables
6. Always filter by the provided client_id in WHERE clauses

Generate clean, efficient SQL queries based on the user's natural language input."""

        try:
            # Call Claude API
            message = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                timeout=self.timeout,
                system=system_prompt.replace('{{client_id}}', str(client_id)),
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )

            # Extract SQL from response
            sql_query = message.content[0].text.strip()

            # Clean up any markdown code blocks if present
            if sql_query.startswith('```'):
                # Remove markdown code blocks
                lines = sql_query.split('\n')
                sql_query = '\n'.join(line for line in lines if not line.startswith('```'))
                sql_query = sql_query.strip()

            logger.info(f"Generated SQL: {sql_query[:200]}...")
            return sql_query

        except APITimeoutError as e:
            logger.error(f"Claude API timeout: {e}")
            raise ValueError("SQL generation timed out. Please try again.") from e

        except APIError as e:
            logger.error(f"Claude API error: {e}")
            raise ValueError(f"Failed to generate SQL: {str(e)}") from e

        except Exception as e:
            logger.error(f"Unexpected error generating SQL: {e}")
            raise ValueError(f"Unexpected error: {str(e)}") from e

    def get_schema_info(self):
        """
        Get database schema information.

        Returns:
            str: Database schema definition
        """
        return DATABASE_SCHEMA
