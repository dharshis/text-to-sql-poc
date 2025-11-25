"""
Database manager module for text-to-sql-poc.

Provides utilities for:
- Database initialization
- Connection management
- Query execution helpers
- Database seeding coordination

Usage:
    from database.db_manager import get_engine, init_database, get_session
"""

import logging
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session as SessionType
from database.schema import Base

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Default database path
DEFAULT_DB_PATH = "../data/text_to_sql_poc.db"


def get_database_path():
    """
    Get the database path from environment variable or use default.

    Returns:
        str: Path to SQLite database file
    """
    db_path = os.getenv("DATABASE_PATH", DEFAULT_DB_PATH)
    return db_path


def get_engine(db_path=None):
    """
    Create and return a SQLAlchemy engine for the database.

    Args:
        db_path (str, optional): Path to database file. Uses environment or default if None.

    Returns:
        Engine: SQLAlchemy engine instance
    """
    if db_path is None:
        db_path = get_database_path()

    logger.info(f"Creating database engine for: {db_path}")

    # Create engine with connection pooling disabled (SQLite single-user for POC)
    engine = create_engine(
        f'sqlite:///{db_path}',
        connect_args={'check_same_thread': False},  # Allow multi-threaded access
        echo=False  # Set to True for SQL query logging during development
    )

    return engine


def init_database(db_path=None):
    """
    Initialize the database by creating all tables defined in schema.

    Args:
        db_path (str, optional): Path to database file. Uses environment or default if None.

    Returns:
        Engine: SQLAlchemy engine instance with tables created
    """
    engine = get_engine(db_path)

    logger.info("Creating database tables...")

    try:
        # Create all tables defined in Base metadata
        Base.metadata.create_all(engine)
        logger.info("✓ Database tables created successfully")

        # Log table names
        table_names = Base.metadata.tables.keys()
        logger.info(f"Tables: {', '.join(table_names)}")

        return engine

    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise


def get_session(engine=None):
    """
    Create and return a new database session.

    Args:
        engine (Engine, optional): SQLAlchemy engine. Creates new engine if None.

    Returns:
        Session: SQLAlchemy session instance
    """
    if engine is None:
        engine = get_engine()

    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    logger.debug("Database session created")
    return session


def execute_query(sql_query, engine=None):
    """
    Execute a raw SQL query and return results.

    Args:
        sql_query (str): SQL query to execute
        engine (Engine, optional): SQLAlchemy engine. Creates new engine if None.

    Returns:
        list: List of result rows as dictionaries

    Raises:
        Exception: If query execution fails
    """
    if engine is None:
        engine = get_engine()

    logger.info(f"Executing query: {sql_query[:100]}...")  # Log first 100 chars

    try:
        with engine.connect() as connection:
            result = connection.execute(sql_query)

            # Convert result to list of dictionaries
            rows = []
            for row in result:
                rows.append(dict(row))

            logger.info(f"✓ Query executed successfully, returned {len(rows)} rows")
            return rows

    except Exception as e:
        logger.error(f"Query execution error: {e}")
        raise


def get_table_info(engine=None):
    """
    Get information about all tables in the database.

    Args:
        engine (Engine, optional): SQLAlchemy engine. Creates new engine if None.

    Returns:
        dict: Dictionary with table names and column information
    """
    if engine is None:
        engine = get_engine()

    table_info = {}

    try:
        # Get all table names
        for table_name, table in Base.metadata.tables.items():
            columns = []
            for column in table.columns:
                columns.append({
                    "name": column.name,
                    "type": str(column.type),
                    "nullable": column.nullable,
                    "primary_key": column.primary_key
                })

            table_info[table_name] = {
                "columns": columns,
                "row_count": None  # Can be populated by querying
            }

            # Get row count
            with engine.connect() as connection:
                result = connection.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = result.fetchone()[0]
                table_info[table_name]["row_count"] = count

        logger.info(f"Retrieved info for {len(table_info)} tables")
        return table_info

    except Exception as e:
        logger.error(f"Error getting table info: {e}")
        raise


def verify_database_integrity(db_path=None):
    """
    Verify database exists and contains expected data.

    Args:
        db_path (str, optional): Path to database file. Uses environment or default if None.

    Returns:
        dict: Verification results with table counts and status

    Raises:
        FileNotFoundError: If database file doesn't exist
    """
    if db_path is None:
        db_path = get_database_path()

    # Check if database file exists
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database file not found: {db_path}")

    logger.info(f"Verifying database integrity: {db_path}")

    engine = get_engine(db_path)
    verification = {
        "database_path": db_path,
        "tables": {},
        "status": "ok"
    }

    try:
        # Get table info and counts
        table_info = get_table_info(engine)

        for table_name, info in table_info.items():
            verification["tables"][table_name] = {
                "exists": True,
                "row_count": info["row_count"],
                "columns": len(info["columns"])
            }

            # Log table verification
            logger.info(f"✓ {table_name}: {info['row_count']} rows, {len(info['columns'])} columns")

        # Check for expected minimum data
        expected_minimums = {
            "clients": 5,
            "products": 100,
            "sales": 1000,
            "customer_segments": 9  # 3 segments * 3 clients minimum
        }

        for table, min_count in expected_minimums.items():
            actual_count = verification["tables"][table]["row_count"]
            if actual_count < min_count:
                logger.warning(f"⚠ {table} has {actual_count} rows, expected at least {min_count}")
                verification["status"] = "warning"

        logger.info(f"Database verification complete: {verification['status']}")
        return verification

    except Exception as e:
        logger.error(f"Database verification failed: {e}")
        verification["status"] = "error"
        verification["error"] = str(e)
        return verification


if __name__ == "__main__":
    # Test database initialization
    print("Testing database initialization...")

    # Initialize database
    engine = init_database()

    # Get table info
    print("\nTable Information:")
    table_info = get_table_info(engine)
    for table_name, info in table_info.items():
        print(f"  {table_name}: {info['row_count']} rows, {len(info['columns'])} columns")

    print("\n✓ Database manager module working correctly")
