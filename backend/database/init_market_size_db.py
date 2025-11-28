"""
Initialize Market Size database from existing schema and CSV data.

This script:
1. Creates a new SQLite database at data/market_size.db
2. Executes the schema from docs/inspiration/tables.sql (adapted for SQLite)
3. Loads CSV data from docs/inspiration/data/ folder
"""

import sqlite3
import csv
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def create_database():
    """Create the market size database with schema and data."""
    
    # Paths
    project_root = Path(__file__).parent.parent.parent
    db_path = project_root / "data" / "market_size.db"
    data_dir = project_root / "docs" / "inspiration" / "data"
    
    print(f"Creating database at: {db_path}")
    print(f"Loading data from: {data_dir}")
    
    # Remove existing database if it exists
    if db_path.exists():
        print(f"Removing existing database...")
        db_path.unlink()
    
    # Create connection
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Create schema (SQLite-compatible version with Phase 1 enhancements)
        print("\n=== Creating Schema (Phase 1 Enhanced) ===")
        
        # NEW: Time Dimension (Phase 1 Enhancement)
        cursor.execute("""
            CREATE TABLE dim_time (
                time_id INTEGER PRIMARY KEY,
                year INTEGER NOT NULL,
                quarter VARCHAR(2),
                month INTEGER,
                year_quarter VARCHAR(7),
                is_forecast INTEGER DEFAULT 0,
                client_id INTEGER DEFAULT 1
            )
        """)
        print("✓ Created dim_time table")
        
        # NEW: Currency Dimension (Phase 1 Enhancement)
        cursor.execute("""
            CREATE TABLE dim_currency (
                currency_id VARCHAR(10) PRIMARY KEY,
                currency_code VARCHAR(3) NOT NULL,
                currency_name VARCHAR(50),
                currency_type VARCHAR(20),
                client_id INTEGER DEFAULT 1
            )
        """)
        print("✓ Created dim_currency table")
        
        # 1. Markets Dimension (with client_id)
        cursor.execute("""
            CREATE TABLE dim_markets (
                market_id VARCHAR(20) PRIMARY KEY,
                market_name VARCHAR(255),
                parent_market_id VARCHAR(20),
                definition TEXT,
                naics_code VARCHAR(20),
                client_id INTEGER DEFAULT 1
            )
        """)
        print("✓ Created dim_markets table")
        
        # 2. Geography Dimension (with client_id)
        cursor.execute("""
            CREATE TABLE dim_geography (
                geo_id VARCHAR(20) PRIMARY KEY,
                region VARCHAR(100),
                country VARCHAR(100),
                country_code VARCHAR(3),
                is_emerging_market INTEGER,
                client_id INTEGER DEFAULT 1
            )
        """)
        print("✓ Created dim_geography table")
        
        # 3. Segment Types (with client_id)
        cursor.execute("""
            CREATE TABLE dim_segment_types (
                segment_type_id VARCHAR(20) PRIMARY KEY,
                market_id VARCHAR(20),
                segment_name VARCHAR(100),
                client_id INTEGER DEFAULT 1,
                FOREIGN KEY (market_id) REFERENCES dim_markets(market_id)
            )
        """)
        print("✓ Created dim_segment_types table")
        
        # 4. Segment Values (with client_id)
        cursor.execute("""
            CREATE TABLE dim_segment_values (
                segment_value_id VARCHAR(20) PRIMARY KEY,
                segment_type_id VARCHAR(20),
                value_name VARCHAR(100),
                description TEXT,
                client_id INTEGER DEFAULT 1,
                FOREIGN KEY (segment_type_id) REFERENCES dim_segment_types(segment_type_id)
            )
        """)
        print("✓ Created dim_segment_values table")
        
        # 5. Fact Table: Historical Market Size (with client_id, time_id, currency_id)
        cursor.execute("""
            CREATE TABLE fact_market_size (
                record_id INTEGER PRIMARY KEY AUTOINCREMENT,
                market_id VARCHAR(20),
                geo_id VARCHAR(20),
                segment_value_id VARCHAR(20),
                time_id INTEGER,
                year INTEGER,
                currency_id VARCHAR(10),
                market_value_usd_m DECIMAL(15,2),
                market_volume_units DECIMAL(15,2),
                data_type VARCHAR(20),
                client_id INTEGER DEFAULT 1,
                last_updated DATE DEFAULT CURRENT_DATE,
                FOREIGN KEY (market_id) REFERENCES dim_markets(market_id),
                FOREIGN KEY (geo_id) REFERENCES dim_geography(geo_id),
                FOREIGN KEY (time_id) REFERENCES dim_time(time_id),
                FOREIGN KEY (currency_id) REFERENCES dim_currency(currency_id)
            )
        """)
        print("✓ Created fact_market_size table")
        
        # 6. Fact Table: Forecasts (with client_id, time_id, currency_id)
        cursor.execute("""
            CREATE TABLE fact_forecasts (
                forecast_id INTEGER PRIMARY KEY AUTOINCREMENT,
                market_id VARCHAR(20),
                geo_id VARCHAR(20),
                time_id INTEGER,
                year INTEGER,
                currency_id VARCHAR(10),
                forecast_value_usd_m DECIMAL(15,2),
                cagr DECIMAL(5,2),
                scenario VARCHAR(50),
                client_id INTEGER DEFAULT 1,
                last_updated DATE DEFAULT CURRENT_DATE,
                FOREIGN KEY (market_id) REFERENCES dim_markets(market_id),
                FOREIGN KEY (geo_id) REFERENCES dim_geography(geo_id),
                FOREIGN KEY (time_id) REFERENCES dim_time(time_id),
                FOREIGN KEY (currency_id) REFERENCES dim_currency(currency_id)
            )
        """)
        print("✓ Created fact_forecasts table")
        
        # Create indexes for performance
        print("\n=== Creating Indexes ===")
        cursor.execute("CREATE INDEX idx_market_size_market ON fact_market_size(market_id)")
        cursor.execute("CREATE INDEX idx_market_size_geo ON fact_market_size(geo_id)")
        cursor.execute("CREATE INDEX idx_market_size_year ON fact_market_size(year)")
        cursor.execute("CREATE INDEX idx_market_size_time ON fact_market_size(time_id)")
        cursor.execute("CREATE INDEX idx_market_size_client ON fact_market_size(client_id)")
        cursor.execute("CREATE INDEX idx_forecasts_market ON fact_forecasts(market_id)")
        cursor.execute("CREATE INDEX idx_forecasts_geo ON fact_forecasts(geo_id)")
        cursor.execute("CREATE INDEX idx_forecasts_year ON fact_forecasts(year)")
        cursor.execute("CREATE INDEX idx_forecasts_time ON fact_forecasts(time_id)")
        cursor.execute("CREATE INDEX idx_forecasts_client ON fact_forecasts(client_id)")
        cursor.execute("CREATE INDEX idx_time_year ON dim_time(year)")
        print("✓ Created indexes")
        
        # Generate seed data for new dimensions (Phase 1)
        print("\n=== Generating Seed Data for New Dimensions ===")
        
        # Populate dim_time (2018-2030)
        time_data = []
        time_id = 1
        for year in range(2018, 2031):
            for quarter in range(1, 5):
                q = f"Q{quarter}"
                yq = f"{year}-{q}"
                is_forecast = 1 if year >= 2024 else 0
                time_data.append((time_id, year, q, None, yq, is_forecast, 1))
                time_id += 1
        
        cursor.executemany("""
            INSERT INTO dim_time (time_id, year, quarter, month, year_quarter, is_forecast, client_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, time_data)
        print(f"✓ Generated {len(time_data)} time periods (2018-2030)")
        
        # Populate dim_currency
        currency_data = [
            ('USD-CUR', 'USD', 'US Dollar', 'Current', 1),
            ('USD-CON', 'USD', 'US Dollar', 'Constant', 1),
            ('EUR-CUR', 'EUR', 'Euro', 'Current', 1),
            ('EUR-CON', 'EUR', 'Euro', 'Constant', 1),
            ('GBP-CUR', 'GBP', 'British Pound', 'Current', 1),
            ('CNY-CUR', 'CNY', 'Chinese Yuan', 'Current', 1),
            ('JPY-CUR', 'JPY', 'Japanese Yen', 'Current', 1),
        ]
        
        cursor.executemany("""
            INSERT INTO dim_currency (currency_id, currency_code, currency_name, currency_type, client_id)
            VALUES (?, ?, ?, ?, ?)
        """, currency_data)
        print(f"✓ Generated {len(currency_data)} currency types")
        
        # Load data from CSV files
        print("\n=== Loading Data from CSV Files ===")
        
        # Load dimension tables (simple CSV load with client_id default)
        dimension_tables = [
            ('dim_markets', ['market_id', 'market_name', 'parent_market_id', 'definition', 'naics_code']),
            ('dim_geography', ['geo_id', 'region', 'country', 'country_code', 'is_emerging_market']),
            ('dim_segment_types', ['segment_type_id', 'market_id', 'segment_name']),
            ('dim_segment_values', ['segment_value_id', 'segment_type_id', 'value_name', 'description']),
        ]
        
        # Load dimension tables first
        for table_name, columns in dimension_tables:
            csv_file = data_dir / f"{table_name}.csv"
            
            if not csv_file.exists():
                print(f"⚠ Warning: {csv_file.name} not found, skipping...")
                continue
            
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
                if not rows:
                    print(f"⚠ Warning: {csv_file.name} is empty, skipping...")
                    continue
                
                # Prepare insert statement (client_id defaults to 1)
                placeholders = ','.join(['?' for _ in columns])
                insert_sql = f"INSERT INTO {table_name} ({','.join(columns)}) VALUES ({placeholders})"
                
                # Insert data
                for row in rows:
                    values = [row.get(col, None) for col in columns]
                    # Convert empty strings to None
                    values = [None if v == '' else v for v in values]
                    cursor.execute(insert_sql, values)
                
                print(f"✓ Loaded {len(rows)} rows into {table_name}")
        
        # Load fact tables with special handling for new fields
        print("\n=== Loading Fact Tables (with Phase 1 enhancements) ===")
        
        # Load fact_market_size
        csv_file = data_dir / "fact_market_size.csv"
        if csv_file.exists():
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
                for row in rows:
                    year = int(row.get('year', 2020))
                    
                    # Find time_id for this year (using Q1 as default)
                    cursor.execute("SELECT time_id FROM dim_time WHERE year = ? AND quarter = 'Q1' LIMIT 1", (year,))
                    time_result = cursor.fetchone()
                    time_id = time_result[0] if time_result else None
                    
                    # Default currency to USD Current
                    currency_id = 'USD-CUR'
                    
                    # Insert with new fields
                    cursor.execute("""
                        INSERT INTO fact_market_size 
                        (market_id, geo_id, segment_value_id, time_id, year, currency_id, 
                         market_value_usd_m, market_volume_units, data_type, client_id)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        row.get('market_id'),
                        row.get('geo_id'),
                        row.get('segment_value_id') if row.get('segment_value_id') else None,
                        time_id,
                        year,
                        currency_id,
                        row.get('market_value_usd_m'),
                        row.get('market_volume_units'),
                        row.get('data_type'),
                        1  # client_id
                    ))
                
                print(f"✓ Loaded {len(rows)} rows into fact_market_size")
        
        # Load fact_forecasts
        csv_file = data_dir / "fact_forecasts.csv"
        if csv_file.exists():
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
                for row in rows:
                    year = int(row.get('year', 2025))
                    
                    # Find time_id for this year (using Q1 as default)
                    cursor.execute("SELECT time_id FROM dim_time WHERE year = ? AND quarter = 'Q1' LIMIT 1", (year,))
                    time_result = cursor.fetchone()
                    time_id = time_result[0] if time_result else None
                    
                    # Default currency to USD Current
                    currency_id = 'USD-CUR'
                    
                    # Insert with new fields
                    cursor.execute("""
                        INSERT INTO fact_forecasts 
                        (market_id, geo_id, time_id, year, currency_id, 
                         forecast_value_usd_m, cagr, scenario, client_id)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        row.get('market_id'),
                        row.get('geo_id'),
                        time_id,
                        year,
                        currency_id,
                        row.get('forecast_value_usd_m'),
                        row.get('cagr'),
                        row.get('scenario'),
                        1  # client_id
                    ))
                
                print(f"✓ Loaded {len(rows)} rows into fact_forecasts")
        
        # Commit changes
        conn.commit()
        
        # Verify data
        print("\n=== Verification ===")
        
        # New dimensions (Phase 1)
        cursor.execute("SELECT COUNT(*) FROM dim_time")
        print(f"dim_time: {cursor.fetchone()[0]} rows")
        
        cursor.execute("SELECT COUNT(*) FROM dim_currency")
        print(f"dim_currency: {cursor.fetchone()[0]} rows")
        
        # Original dimensions
        cursor.execute("SELECT COUNT(*) FROM dim_markets")
        print(f"dim_markets: {cursor.fetchone()[0]} rows")
        
        cursor.execute("SELECT COUNT(*) FROM dim_geography")
        print(f"dim_geography: {cursor.fetchone()[0]} rows")
        
        cursor.execute("SELECT COUNT(*) FROM dim_segment_types")
        print(f"dim_segment_types: {cursor.fetchone()[0]} rows")
        
        cursor.execute("SELECT COUNT(*) FROM dim_segment_values")
        print(f"dim_segment_values: {cursor.fetchone()[0]} rows")
        
        # Fact tables
        cursor.execute("SELECT COUNT(*) FROM fact_market_size")
        print(f"fact_market_size: {cursor.fetchone()[0]} rows")
        
        cursor.execute("SELECT COUNT(*) FROM fact_forecasts")
        print(f"fact_forecasts: {cursor.fetchone()[0]} rows")
        
        # Sample query to verify relationships
        print("\n=== Sample Query Test ===")
        cursor.execute("""
            SELECT m.market_name, g.country, t.year_quarter, c.currency_code,
                   f.market_value_usd_m, f.data_type
            FROM fact_market_size f
            JOIN dim_markets m ON f.market_id = m.market_id
            JOIN dim_geography g ON f.geo_id = g.geo_id
            JOIN dim_time t ON f.time_id = t.time_id
            JOIN dim_currency c ON f.currency_id = c.currency_id
            LIMIT 3
        """)
        results = cursor.fetchall()
        print(f"✓ Verified joins across all dimensions: {len(results)} sample rows retrieved")
        
        print("\n✅ Database created successfully with Phase 1 enhancements!")
        print(f"Location: {db_path}")
        print("\nPhase 1 Changes Applied:")
        print("  ✓ dim_time table added (time-series analysis)")
        print("  ✓ dim_currency table added (currency tracking)")
        print("  ✓ client_id added to all tables (multi-tenancy)")
        print("  ✓ Foreign keys updated in fact tables")
        print("  ✓ Additional indexes created")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        conn.rollback()
        raise
    
    finally:
        conn.close()

if __name__ == "__main__":
    create_database()

