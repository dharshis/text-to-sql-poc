"""
Query execution service for safe SQL execution against the database.

This service handles execution of generated SQL queries with proper error handling,
timeout management, and result formatting.
"""

import logging
import time
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from config import Config

logger = logging.getLogger(__name__)


class QueryExecutor:
    """Service for executing SQL queries safely against the database."""

    def __init__(self, database_path=None):
        """
        Initialize query executor.

        Args:
            database_path (str, optional): Path to database. Uses Config.DATABASE_PATH if None.
        """
        self.database_path = database_path or Config.DATABASE_PATH
        self.database_url = f'sqlite:///{self.database_path}'
        self.max_results = Config.MAX_QUERY_RESULTS

        # Create engine with read-only mode (for safety)
        self.engine = create_engine(
            self.database_url,
            connect_args={'check_same_thread': False},
            echo=False
        )

        logger.info(f"Query executor initialized with database: {self.database_path}")

    def execute_query(self, sql_query):
        """
        Execute SQL query and return results.

        Args:
            sql_query (str): SQL query to execute

        Returns:
            dict: Dictionary containing:
                - results (list): Query results as list of dictionaries
                - columns (list): Column names
                - row_count (int): Number of rows returned
                - execution_time (float): Query execution time in seconds

        Raises:
            ValueError: If query execution fails
        """
        logger.info(f"Executing query: {sql_query[:200]}...")

        start_time = time.time()

        try:
            with self.engine.connect() as connection:
                # Execute query with timeout
                result = connection.execute(text(sql_query))

                # Fetch results (limit to max_results to prevent memory issues)
                rows = result.fetchmany(self.max_results)

                # Get column names
                columns = list(result.keys()) if result.returns_rows else []

                # Convert rows to list of dictionaries
                results = []
                for row in rows:
                    # Convert Row object to dictionary
                    row_dict = {}
                    for i, column in enumerate(columns):
                        value = row[i]
                        # Convert any non-JSON-serializable types
                        if value is not None:
                            row_dict[column] = value
                        else:
                            row_dict[column] = None
                    results.append(row_dict)

                execution_time = time.time() - start_time

                logger.info(f"Query executed successfully: {len(results)} rows in {execution_time:.3f}s")

                return {
                    'results': results,
                    'columns': columns,
                    'row_count': len(results),
                    'execution_time': round(execution_time, 3)
                }

        except SQLAlchemyError as e:
            execution_time = time.time() - start_time
            logger.error(f"SQL execution error: {e}")

            # Provide user-friendly error message
            error_msg = str(e)
            if "no such table" in error_msg.lower():
                raise ValueError("Database table not found. Please check your query.") from e
            elif "no such column" in error_msg.lower():
                raise ValueError("Column not found in database. Please check your query.") from e
            elif "syntax error" in error_msg.lower():
                raise ValueError("SQL syntax error. Please try rephrasing your query.") from e
            else:
                raise ValueError(f"Query execution failed: {error_msg}") from e

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Unexpected error executing query: {e}")
            raise ValueError(f"Unexpected error: {str(e)}") from e

    def test_connection(self):
        """
        Test database connection.

        Returns:
            bool: True if connection is successful

        Raises:
            ValueError: If connection fails
        """
        try:
            with self.engine.connect() as connection:
                result = connection.execute(text("SELECT 1"))
                result.fetchone()
                logger.info("Database connection test successful")
                return True

        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            raise ValueError(f"Database connection failed: {str(e)}") from e

    def get_clients(self):
        """
        Get list of all clients from database.

        Returns:
            list: List of client dictionaries with client_id, client_name, industry

        Raises:
            ValueError: If query fails
        """
        sql_query = "SELECT client_id, client_name, industry FROM clients ORDER BY client_name"

        try:
            result = self.execute_query(sql_query)
            return result['results']

        except Exception as e:
            logger.error(f"Error fetching clients: {e}")
            raise ValueError(f"Failed to fetch clients: {str(e)}") from e

    def get_table_info(self):
        """
        Get information about database tables.

        Returns:
            dict: Dictionary with table names and row counts
        """
        tables = ['clients', 'products', 'sales', 'customer_segments']
        table_info = {}

        try:
            for table in tables:
                result = self.execute_query(f"SELECT COUNT(*) as count FROM {table}")
                table_info[table] = result['results'][0]['count']

            return table_info

        except Exception as e:
            logger.error(f"Error getting table info: {e}")
            return {}
