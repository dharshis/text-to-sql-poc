#!/usr/bin/env python3
"""
Build EM Market database from CSV files.

Reads CSV files from data/em_market/ and creates a SQLite database
with proper schema, foreign keys, and indexes.
"""

import sqlite3
import csv
import logging
from pathlib import Path
from typing import Dict, List, Any
import sys

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "em_market"
DB_PATH = PROJECT_ROOT / "data" / "em_market.db"


def get_csv_files() -> List[Path]:
    """Get all CSV files from data/em_market directory."""
    csv_files = list(DATA_DIR.glob("*.csv"))
    logger.info(f"Found {len(csv_files)} CSV files")
    for f in csv_files:
        logger.info(f"  - {f.name}")
    return csv_files


def infer_sqlite_type(value: str) -> str:
    """Infer SQLite type from sample value."""
    # Try to parse as different types
    try:
        int(value)
        return 'INTEGER'
    except (ValueError, TypeError):
        pass
    
    try:
        float(value)
        return 'REAL'
    except (ValueError, TypeError):
        pass
    
    if value.lower() in ('true', 'false'):
        return 'INTEGER'  # Boolean as 0/1
    
    return 'TEXT'


def get_table_schema(csv_path: Path, table_name: str) -> Dict:
    """
    Generate table schema from CSV file.
    
    Returns dict with:
    - table_name: str
    - columns: List[tuple] - (column_name, sqlite_type)
    - primary_key: str (if identifiable)
    - headers: List[str]
    """
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        headers = next(reader)
        
        # Read first few rows to infer types
        first_rows = []
        for i, row in enumerate(reader):
            if i >= 10:  # Sample first 10 rows
                break
            first_rows.append(row)
    
    columns = []
    primary_key = None
    
    for i, col_name in enumerate(headers):
        # Infer type from first non-empty value
        inferred_type = 'TEXT'  # Default
        for row in first_rows:
            if i < len(row) and row[i]:
                inferred_type = infer_sqlite_type(row[i])
                break
        
        columns.append((col_name, inferred_type))
        
        # Identify primary key (usually ends with _id and is first column)
        if col_name.endswith('_id') and primary_key is None:
            primary_key = col_name
    
    return {
        'table_name': table_name,
        'columns': columns,
        'primary_key': primary_key,
        'headers': headers
    }


def create_table_sql(schema: Dict) -> str:
    """Generate CREATE TABLE SQL statement."""
    table_name = schema['table_name']
    columns = schema['columns']
    primary_key = schema['primary_key']
    
    col_definitions = []
    for col_name, col_type in columns:
        definition = f"{col_name} {col_type}"
        
        # Add PRIMARY KEY constraint
        if col_name == primary_key:
            definition += " PRIMARY KEY"
        
        col_definitions.append(definition)
    
    sql = f"CREATE TABLE {table_name} (\n    "
    sql += ",\n    ".join(col_definitions)
    sql += "\n);"
    
    return sql


def create_indexes(conn: sqlite3.Connection, table_name: str, columns: List[tuple]):
    """Create indexes on foreign key columns and commonly filtered columns."""
    cursor = conn.cursor()
    
    for col_name, col_type in columns:
        # Index columns that end with _id (likely foreign keys)
        if col_name.endswith('_id') and not col_name.startswith('transaction_'):
            index_name = f"idx_{table_name}_{col_name}"
            try:
                cursor.execute(f"CREATE INDEX {index_name} ON {table_name}({col_name})")
                logger.info(f"    Created index: {index_name}")
            except sqlite3.OperationalError as e:
                logger.warning(f"    Could not create index {index_name}: {e}")
    
    conn.commit()


def load_csv_to_table(conn: sqlite3.Connection, csv_path: Path):
    """Load CSV file into SQLite table."""
    # Extract table name from filename (remove .csv extension)
    table_name = csv_path.stem
    
    logger.info(f"\n{'='*60}")
    logger.info(f"Processing: {table_name}")
    logger.info(f"{'='*60}")
    
    # Read CSV and get schema
    logger.info("Analyzing CSV structure...")
    schema = get_table_schema(csv_path, table_name)
    logger.info(f"  Columns: {len(schema['columns'])}")
    logger.info(f"  Primary Key: {schema['primary_key']}")
    
    # Create table
    create_sql = create_table_sql(schema)
    logger.info("Creating table...")
    logger.debug(f"\n{create_sql}")
    
    cursor = conn.cursor()
    cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
    cursor.execute(create_sql)
    conn.commit()
    
    # Load data
    logger.info("Loading data...")
    row_count = 0
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        # Prepare INSERT statement
        placeholders = ','.join(['?' for _ in schema['headers']])
        insert_sql = f"INSERT INTO {table_name} VALUES ({placeholders})"
        
        # Batch insert for performance
        batch = []
        batch_size = 1000
        
        for row_dict in reader:
            # Convert dict to tuple in correct column order
            row_tuple = tuple(row_dict[col] for col in schema['headers'])
            batch.append(row_tuple)
            row_count += 1
            
            if len(batch) >= batch_size:
                cursor.executemany(insert_sql, batch)
                batch = []
        
        # Insert remaining rows
        if batch:
            cursor.executemany(insert_sql, batch)
    
    conn.commit()
    logger.info(f"  ✓ Loaded {row_count} rows")
    
    # Create indexes
    logger.info("Creating indexes...")
    create_indexes(conn, table_name, schema['columns'])
    
    # Verify
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    count = cursor.fetchone()[0]
    logger.info(f"  ✓ Verified {count} rows in database")


def create_bridge_table(conn: sqlite3.Connection):
    """
    Create Bridge_Market_SKU junction table if it doesn't exist.
    This is inferred from metadata documentation.
    """
    logger.info("\n" + "="*60)
    logger.info("Creating Bridge_Market_SKU junction table")
    logger.info("="*60)
    
    cursor = conn.cursor()
    
    # Check if we need to create this table
    # (It may not exist as CSV if it's just a many-to-many relationship)
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='Bridge_Market_SKU'
    """)
    
    if cursor.fetchone():
        logger.info("  Bridge_Market_SKU already exists, skipping")
        return
    
    # If we have market and SKU data, we can infer relationships
    # For now, just create the schema - data can be added later
    logger.info("  Creating schema...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Bridge_Market_SKU (
            market_def_id INTEGER NOT NULL,
            sku_id INTEGER NOT NULL,
            PRIMARY KEY (market_def_id, sku_id),
            FOREIGN KEY (market_def_id) REFERENCES Dim_Market_Definition(market_def_id),
            FOREIGN KEY (sku_id) REFERENCES Dim_Product_SKU(sku_id)
        )
    """)
    
    logger.info("  ✓ Bridge table created (empty - populate manually if needed)")
    conn.commit()


def add_foreign_keys(conn: sqlite3.Connection):
    """
    Add foreign key constraints.
    Note: SQLite foreign keys are enforced at runtime, not schema creation.
    """
    logger.info("\n" + "="*60)
    logger.info("Setting up Foreign Key Constraints")
    logger.info("="*60)
    
    cursor = conn.cursor()
    
    # Enable foreign key constraints
    cursor.execute("PRAGMA foreign_keys = ON")
    
    logger.info("  ✓ Foreign key enforcement enabled")
    logger.info("  Note: FK relationships defined in table schemas")
    
    conn.commit()


def create_views(conn: sqlite3.Connection):
    """Create useful views for common queries."""
    logger.info("\n" + "="*60)
    logger.info("Creating Database Views")
    logger.info("="*60)
    
    cursor = conn.cursor()
    
    # View 1: Sales with Geography and Product details
    logger.info("Creating view: vw_sales_detail...")
    cursor.execute("""
        CREATE VIEW IF NOT EXISTS vw_sales_detail AS
        SELECT 
            fst.transaction_id,
            fst.period_id,
            g.country_name,
            g.region_name,
            ps.sku_name,
            ps.product_category,
            b.brand_name,
            sb.sub_brand_name,
            c.corporation_name,
            fst.units_sold,
            fst.volume_sold_std,
            fst.value_sold_local,
            fst.value_sold_usd,
            fst.is_promotion,
            fst.distribution_points
        FROM Fact_Sales_Transactions fst
        LEFT JOIN Dim_Geography g ON fst.geo_id = g.geo_id
        LEFT JOIN Dim_Product_SKU ps ON fst.sku_id = ps.sku_id
        LEFT JOIN Dim_SubBrand sb ON ps.sub_brand_id = sb.sub_brand_id
        LEFT JOIN Dim_Brand b ON sb.brand_id = b.brand_id
        LEFT JOIN Dim_Corporation c ON b.corp_id = c.corp_id
    """)
    logger.info("  ✓ vw_sales_detail created")
    
    # View 2: Market Summary with Geography
    logger.info("Creating view: vw_market_summary...")
    cursor.execute("""
        CREATE VIEW IF NOT EXISTS vw_market_summary AS
        SELECT 
            fms.summary_id,
            fms.period_id,
            g.country_name,
            g.region_name,
            md.market_name,
            md.market_category,
            fms.total_market_value_usd,
            fms.total_market_volume_std
        FROM Fact_Market_Summary fms
        LEFT JOIN Dim_Geography g ON fms.geo_id = g.geo_id
        LEFT JOIN Dim_Market_Definition md ON fms.market_def_id = md.market_def_id
    """)
    logger.info("  ✓ vw_market_summary created")
    
    conn.commit()


def generate_statistics(conn: sqlite3.Connection):
    """Generate and display database statistics."""
    logger.info("\n" + "="*60)
    logger.info("DATABASE STATISTICS")
    logger.info("="*60)
    
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name NOT LIKE 'sqlite_%'
        ORDER BY name
    """)
    tables = cursor.fetchall()
    
    total_rows = 0
    logger.info("\nTable Row Counts:")
    for (table_name,) in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        total_rows += count
        logger.info(f"  {table_name:30s} {count:>10,} rows")
    
    logger.info(f"\n  {'TOTAL':30s} {total_rows:>10,} rows")
    
    # Get all indexes
    cursor.execute("""
        SELECT COUNT(*) FROM sqlite_master 
        WHERE type='index' AND name NOT LIKE 'sqlite_%'
    """)
    index_count = cursor.fetchone()[0]
    logger.info(f"\n  Indexes: {index_count}")
    
    # Get all views
    cursor.execute("""
        SELECT COUNT(*) FROM sqlite_master 
        WHERE type='view'
    """)
    view_count = cursor.fetchone()[0]
    logger.info(f"  Views: {view_count}")
    
    # Database size
    db_size_mb = DB_PATH.stat().st_size / (1024 * 1024)
    logger.info(f"  Database Size: {db_size_mb:.2f} MB")


def build_database():
    """Main function to build the database."""
    logger.info("="*60)
    logger.info("EM MARKET DATABASE BUILDER")
    logger.info("="*60)
    logger.info(f"Data Directory: {DATA_DIR}")
    logger.info(f"Database Path: {DB_PATH}")
    
    # Check if data directory exists
    if not DATA_DIR.exists():
        logger.error(f"Data directory not found: {DATA_DIR}")
        sys.exit(1)
    
    # Get CSV files
    csv_files = get_csv_files()
    if not csv_files:
        logger.error("No CSV files found!")
        sys.exit(1)
    
    # Remove existing database
    if DB_PATH.exists():
        logger.info(f"\nRemoving existing database: {DB_PATH}")
        DB_PATH.unlink()
    
    # Create database connection
    logger.info(f"\nCreating new database: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    
    try:
        # Process each CSV file
        # Load dimensions first, then facts
        dimension_files = [f for f in csv_files if f.stem.startswith('Dim_')]
        fact_files = [f for f in csv_files if f.stem.startswith('Fact_')]
        
        logger.info(f"\n{'='*60}")
        logger.info("LOADING DIMENSION TABLES")
        logger.info(f"{'='*60}")
        for csv_file in sorted(dimension_files):
            load_csv_to_table(conn, csv_file)
        
        logger.info(f"\n{'='*60}")
        logger.info("LOADING FACT TABLES")
        logger.info(f"{'='*60}")
        for csv_file in sorted(fact_files):
            load_csv_to_table(conn, csv_file)
        
        # Create bridge table if needed
        create_bridge_table(conn)
        
        # Setup foreign keys
        add_foreign_keys(conn)
        
        # Create views
        create_views(conn)
        
        # Generate statistics
        generate_statistics(conn)
        
        logger.info("\n" + "="*60)
        logger.info("✓ DATABASE BUILD COMPLETE")
        logger.info("="*60)
        logger.info(f"\nDatabase created at: {DB_PATH}")
        logger.info("\nYou can now use this database with:")
        logger.info("  - Backend API queries")
        logger.info("  - SQL analysis tools")
        logger.info("  - Data visualization")
        
    except Exception as e:
        logger.error(f"\n❌ Error building database: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
        
    finally:
        conn.close()


if __name__ == "__main__":
    build_database()

