-- 1. Markets Dimension
CREATE TABLE dim_markets (
    market_id VARCHAR(20) PRIMARY KEY,
    market_name VARCHAR(255),
    parent_market_id VARCHAR(20),
    definition TEXT,
    naics_code VARCHAR(20)
);

-- 2. Geography Dimension
CREATE TABLE dim_geography (
    geo_id VARCHAR(20) PRIMARY KEY,
    region VARCHAR(100),
    country VARCHAR(100),
    country_code VARCHAR(3),
    is_emerging_market BOOLEAN
);

-- 3. Segment Types (The "Slices")
CREATE TABLE dim_segment_types (
    segment_type_id VARCHAR(20) PRIMARY KEY,
    market_id VARCHAR(20),
    segment_name VARCHAR(100),
    FOREIGN KEY (market_id) REFERENCES dim_markets(market_id)
);

-- 4. Segment Values (The "Granular Details")
CREATE TABLE dim_segment_values (
    segment_value_id VARCHAR(20) PRIMARY KEY,
    segment_type_id VARCHAR(20),
    value_name VARCHAR(100),
    description TEXT,
    FOREIGN KEY (segment_type_id) REFERENCES dim_segment_types(segment_type_id)
);

-- 5. Fact Table: Historical Market Size
CREATE TABLE fact_market_size (
    record_id SERIAL PRIMARY KEY,
    market_id VARCHAR(20),
    geo_id VARCHAR(20),
    segment_value_id VARCHAR(20), -- Can be NULL for Total Market numbers
    year INT,
    market_value_usd_m DECIMAL(15,2),
    market_volume_units DECIMAL(15,2),
    data_type VARCHAR(20), -- 'Actual' or 'Estimate'
    FOREIGN KEY (market_id) REFERENCES dim_markets(market_id),
    FOREIGN KEY (geo_id) REFERENCES dim_geography(geo_id)
);

-- 6. Fact Table: Forecasts
CREATE TABLE fact_forecasts (
    forecast_id SERIAL PRIMARY KEY,
    market_id VARCHAR(20),
    geo_id VARCHAR(20),
    year INT,
    forecast_value_usd_m DECIMAL(15,2),
    cagr DECIMAL(5,2),
    scenario VARCHAR(50),
    FOREIGN KEY (market_id) REFERENCES dim_markets(market_id),
    FOREIGN KEY (geo_id) REFERENCES dim_geography(geo_id)
);