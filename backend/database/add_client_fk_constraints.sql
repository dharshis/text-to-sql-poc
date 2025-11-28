-- Migration Script: Add Foreign Key Constraints from Fact Tables to dim_clients
-- This script recreates fact tables with proper FK constraints to dim_clients

PRAGMA foreign_keys = OFF;

BEGIN TRANSACTION;

-- =====================================================
-- STEP 1: Create new fact_market_size with FK to dim_clients
-- =====================================================
CREATE TABLE fact_market_size_new (
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
    client_id INTEGER DEFAULT 1 NOT NULL,
    last_updated DATE DEFAULT CURRENT_DATE,
    
    -- Foreign Keys
    FOREIGN KEY (market_id) REFERENCES dim_markets(market_id),
    FOREIGN KEY (geo_id) REFERENCES dim_geography(geo_id),
    FOREIGN KEY (time_id) REFERENCES dim_time(time_id),
    FOREIGN KEY (currency_id) REFERENCES dim_currency(currency_id),
    FOREIGN KEY (client_id) REFERENCES dim_clients(client_id) ON DELETE RESTRICT
);

-- Copy data from old table
INSERT INTO fact_market_size_new 
SELECT * FROM fact_market_size;

-- Drop old table
DROP TABLE fact_market_size;

-- Rename new table
ALTER TABLE fact_market_size_new RENAME TO fact_market_size;

-- Recreate indexes
CREATE INDEX idx_market_size_market ON fact_market_size(market_id);
CREATE INDEX idx_market_size_geo ON fact_market_size(geo_id);
CREATE INDEX idx_market_size_year ON fact_market_size(year);
CREATE INDEX idx_market_size_time ON fact_market_size(time_id);
CREATE INDEX idx_market_size_client ON fact_market_size(client_id);

-- =====================================================
-- STEP 2: Create new fact_forecasts with FK to dim_clients
-- =====================================================
CREATE TABLE fact_forecasts_new (
    forecast_id INTEGER PRIMARY KEY AUTOINCREMENT,
    market_id VARCHAR(20),
    geo_id VARCHAR(20),
    time_id INTEGER,
    year INTEGER,
    currency_id VARCHAR(10),
    forecast_value_usd_m DECIMAL(15,2),
    cagr DECIMAL(5,2),
    scenario VARCHAR(50),
    client_id INTEGER DEFAULT 1 NOT NULL,
    last_updated DATE DEFAULT CURRENT_DATE,
    
    -- Foreign Keys
    FOREIGN KEY (market_id) REFERENCES dim_markets(market_id),
    FOREIGN KEY (geo_id) REFERENCES dim_geography(geo_id),
    FOREIGN KEY (time_id) REFERENCES dim_time(time_id),
    FOREIGN KEY (currency_id) REFERENCES dim_currency(currency_id),
    FOREIGN KEY (client_id) REFERENCES dim_clients(client_id) ON DELETE RESTRICT
);

-- Copy data from old table
INSERT INTO fact_forecasts_new 
SELECT * FROM fact_forecasts;

-- Drop old table
DROP TABLE fact_forecasts;

-- Rename new table
ALTER TABLE fact_forecasts_new RENAME TO fact_forecasts;

-- Recreate indexes
CREATE INDEX idx_forecasts_market ON fact_forecasts(market_id);
CREATE INDEX idx_forecasts_geo ON fact_forecasts(geo_id);
CREATE INDEX idx_forecasts_year ON fact_forecasts(year);
CREATE INDEX idx_forecasts_time ON fact_forecasts(time_id);
CREATE INDEX idx_forecasts_client ON fact_forecasts(client_id);

COMMIT;

-- =====================================================
-- STEP 3: Enable foreign keys and verify
-- =====================================================
PRAGMA foreign_keys = ON;

-- Verify FK constraints
SELECT 'Foreign Key Constraints Verification:' as info;
PRAGMA foreign_key_list(fact_market_size);
SELECT '---' as separator;
PRAGMA foreign_key_list(fact_forecasts);

-- Verify data integrity
SELECT '' as separator;
SELECT 'Data Integrity Check:' as info;
SELECT 'fact_market_size records: ' || COUNT(*) FROM fact_market_size;
SELECT 'fact_forecasts records: ' || COUNT(*) FROM fact_forecasts;
SELECT 'All client_ids have matching dim_clients: ' || 
    CASE 
        WHEN NOT EXISTS (
            SELECT 1 FROM fact_market_size f 
            WHERE NOT EXISTS (
                SELECT 1 FROM dim_clients c WHERE c.client_id = f.client_id
            )
        ) THEN 'PASS ✓'
        ELSE 'FAIL ✗'
    END;


