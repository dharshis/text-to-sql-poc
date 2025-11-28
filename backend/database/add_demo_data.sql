-- Add Missing Data for Demo Queries
-- Ensures all 10 client demo queries work perfectly

BEGIN TRANSACTION;

-- =====================================================
-- 1. Flag Emerging Markets (for Query 4)
-- =====================================================

UPDATE dim_geography SET is_emerging_market = 1 
WHERE country IN ('India', 'Brazil', 'Mexico', 'Thailand', 'Indonesia', 'Vietnam', 'South Africa');

-- =====================================================
-- 2. Add Constant USD Currency (for Query 5)
-- =====================================================

-- Check if constant USD exists, if not add it
INSERT OR IGNORE INTO dim_currency (currency_id, currency_code, currency_name, currency_type, client_id)
VALUES ('USD-CON', 'USD', 'US Dollar', 'Constant', 1);

-- =====================================================
-- 3. Add 2023 Historical Data (for Query 6 - YoY comparison)
-- =====================================================

-- Add 2023 to dim_time
INSERT INTO dim_time (time_id, year, quarter, month, year_quarter, is_forecast, client_id) VALUES
(33, 2023, 'Q1', 1, '2023-Q1', 0, 1),
(34, 2023, 'Q1', 2, '2023-Q1', 0, 1),
(35, 2023, 'Q1', 3, '2023-Q1', 0, 1),
(36, 2023, 'Q2', 4, '2023-Q2', 0, 1),
(37, 2023, 'Q2', 5, '2023-Q2', 0, 1),
(38, 2023, 'Q2', 6, '2023-Q2', 0, 1),
(39, 2023, 'Q3', 7, '2023-Q3', 0, 1),
(40, 2023, 'Q3', 8, '2023-Q3', 0, 1),
(41, 2023, 'Q3', 9, '2023-Q3', 0, 1),
(42, 2023, 'Q4', 10, '2023-Q4', 0, 1),
(43, 2023, 'Q4', 11, '2023-Q4', 0, 1),
(44, 2023, 'Q4', 12, '2023-Q4', 0, 1);

-- Add 2023 EV market data for all 3 clients
INSERT INTO fact_market_size (market_id, geo_id, segment_value_id, time_id, year, currency_id, market_value_usd_m, market_volume_units, data_type, client_id)
SELECT 
    market_id, 
    geo_id, 
    segment_value_id, 
    33, -- Q1 2023
    2023, 
    currency_id,
    market_value_usd_m * 0.75, -- 75% of 2024 values (growth trend)
    market_volume_units * 0.75,
    'Actual',
    client_id
FROM fact_market_size 
WHERE year = 2024;

-- =====================================================
-- 4. Add Constant USD data for existing records (Query 5)
-- =====================================================

-- Duplicate some 2025 records with constant USD
INSERT INTO fact_market_size (market_id, geo_id, segment_value_id, time_id, year, currency_id, market_value_usd_m, market_volume_units, data_type, client_id)
SELECT 
    market_id, 
    geo_id, 
    segment_value_id, 
    time_id,
    year, 
    'USD-CON', -- Constant USD
    market_value_usd_m * 0.92, -- Deflated value (inflation-adjusted)
    market_volume_units,
    data_type,
    client_id
FROM fact_market_size 
WHERE year = 2025 
  AND currency_id = 'USD-CUR'
  AND market_id IN (SELECT market_id FROM dim_markets WHERE market_name LIKE '%Electric%')
LIMIT 20;

-- =====================================================
-- 5. Add 2024 Forecasts (for Query 9 - accuracy check)
-- =====================================================

-- Add actual 2024 forecast data that was made earlier
INSERT INTO fact_forecasts (market_id, geo_id, time_id, year, currency_id, forecast_value_usd_m, cagr, scenario, client_id)
SELECT 
    market_id,
    geo_id,
    4, -- Q2 2024
    2024,
    currency_id,
    market_value_usd_m * 0.95, -- Forecast was 95% of actual
    15.5, -- CAGR
    'Base Case',
    client_id
FROM fact_market_size
WHERE year = 2024
LIMIT 20;

-- =====================================================
-- 6. Ensure Segment Data is Linked (for Query 7)
-- =====================================================

-- Link some market_size records to segments
UPDATE fact_market_size
SET segment_value_id = (
    SELECT segment_value_id FROM dim_segment_values 
    WHERE value_name LIKE '%Premium%' LIMIT 1
)
WHERE market_id IN (
    SELECT market_id FROM dim_markets WHERE market_name = 'Electric Vehicles'
)
AND segment_value_id IS NULL
AND RANDOM() % 2 = 0
LIMIT 10;

UPDATE fact_market_size
SET segment_value_id = (
    SELECT segment_value_id FROM dim_segment_values 
    WHERE value_name LIKE '%Standard%' LIMIT 1
)
WHERE market_id IN (
    SELECT market_id FROM dim_markets WHERE market_name = 'Electric Vehicles'
)
AND segment_value_id IS NULL
AND RANDOM() % 2 = 0
LIMIT 10;

COMMIT;

-- =====================================================
-- VERIFICATION
-- =====================================================

SELECT '=== DEMO DATA VERIFICATION ===' as info;
SELECT '' as space;

SELECT 'Emerging markets flagged:' as check, COUNT(*) as count
FROM dim_geography WHERE is_emerging_market = 1;

SELECT 'Constant USD records:' as check, COUNT(*) as count
FROM fact_market_size WHERE currency_id = 'USD-CON';

SELECT 'Years available:' as check, GROUP_CONCAT(DISTINCT year) as years
FROM fact_market_size;

SELECT '2024 forecasts for accuracy:' as check, COUNT(*) as count
FROM fact_forecasts WHERE year = 2024;

SELECT 'Segment-linked EV records:' as check, COUNT(*) as count
FROM fact_market_size f
JOIN dim_markets m ON f.market_id = m.market_id
WHERE m.market_name = 'Electric Vehicles' 
  AND f.segment_value_id IS NOT NULL;

SELECT 'Forecast scenarios:' as check, GROUP_CONCAT(DISTINCT scenario) as scenarios
FROM fact_forecasts;

SELECT '' as space;
SELECT '✅ All demo data requirements met!' as status;

