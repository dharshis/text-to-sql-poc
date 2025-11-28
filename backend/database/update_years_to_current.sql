-- Migration Script: Update all years to 2024-Nov 2025
-- This makes the data current and fixes "last X years" queries

BEGIN TRANSACTION;

-- =====================================================
-- STEP 1: Update dim_time to reflect 2024-Nov 2025
-- =====================================================

-- Clear existing time periods
DELETE FROM dim_time;

-- Add 2024 (full year)
INSERT INTO dim_time (time_id, year, quarter, month, year_quarter, is_forecast, client_id) VALUES
(1, 2024, 'Q1', 1, '2024-Q1', 0, 1),
(2, 2024, 'Q1', 2, '2024-Q1', 0, 1),
(3, 2024, 'Q1', 3, '2024-Q1', 0, 1),
(4, 2024, 'Q2', 4, '2024-Q2', 0, 1),
(5, 2024, 'Q2', 5, '2024-Q2', 0, 1),
(6, 2024, 'Q2', 6, '2024-Q2', 0, 1),
(7, 2024, 'Q3', 7, '2024-Q3', 0, 1),
(8, 2024, 'Q3', 8, '2024-Q3', 0, 1),
(9, 2024, 'Q3', 9, '2024-Q3', 0, 1),
(10, 2024, 'Q4', 10, '2024-Q4', 0, 1),
(11, 2024, 'Q4', 11, '2024-Q4', 0, 1),
(12, 2024, 'Q4', 12, '2024-Q4', 0, 1);

-- Add 2025 (through November)
INSERT INTO dim_time (time_id, year, quarter, month, year_quarter, is_forecast, client_id) VALUES
(13, 2025, 'Q1', 1, '2025-Q1', 0, 1),
(14, 2025, 'Q1', 2, '2025-Q1', 0, 1),
(15, 2025, 'Q1', 3, '2025-Q1', 0, 1),
(16, 2025, 'Q2', 4, '2025-Q2', 0, 1),
(17, 2025, 'Q2', 5, '2025-Q2', 0, 1),
(18, 2025, 'Q2', 6, '2025-Q2', 0, 1),
(19, 2025, 'Q3', 7, '2025-Q3', 0, 1),
(20, 2025, 'Q3', 8, '2025-Q3', 0, 1),
(21, 2025, 'Q3', 9, '2025-Q3', 0, 1),
(22, 2025, 'Q4', 10, '2025-Q4', 0, 1),
(23, 2025, 'Q4', 11, '2025-Q4', 0, 1);

-- Add future forecasts (Dec 2025 - 2026)
INSERT INTO dim_time (time_id, year, quarter, month, year_quarter, is_forecast, client_id) VALUES
(24, 2025, 'Q4', 12, '2025-Q4', 1, 1),
(25, 2026, 'Q1', NULL, '2026-Q1', 1, 1),
(26, 2026, 'Q2', NULL, '2026-Q2', 1, 1),
(27, 2026, 'Q3', NULL, '2026-Q3', 1, 1),
(28, 2026, 'Q4', NULL, '2026-Q4', 1, 1);

-- =====================================================
-- STEP 2: Update fact_market_size years
-- =====================================================

-- Map old years to new years:
-- 2020 → 2024
-- 2021 → 2024
-- 2022 → 2025
-- 2023 → 2025

UPDATE fact_market_size
SET year = 2024,
    time_id = CASE 
        WHEN time_id <= 13 THEN 4  -- Q2 2024
        ELSE 10                     -- Q4 2024
    END
WHERE year = 2020;

UPDATE fact_market_size
SET year = 2024,
    time_id = 7  -- Q3 2024
WHERE year = 2021;

UPDATE fact_market_size
SET year = 2025,
    time_id = 16  -- Q2 2025
WHERE year = 2022;

UPDATE fact_market_size
SET year = 2025,
    time_id = 22  -- Q4 2025 (through Nov)
WHERE year = 2023;

-- =====================================================
-- STEP 3: Update fact_forecasts years
-- =====================================================

UPDATE fact_forecasts
SET year = 2025,
    time_id = 22  -- Q4 2025
WHERE year = 2024;

UPDATE fact_forecasts
SET year = 2026,
    time_id = 25  -- Q1 2026 (forecast)
WHERE year = 2025;

UPDATE fact_forecasts
SET year = 2026,
    time_id = 26  -- Q2 2026 (forecast)
WHERE year = 2026;

UPDATE fact_forecasts
SET year = 2027,
    time_id = 25  -- Forecast period
WHERE year = 2027;

UPDATE fact_forecasts
SET year = 2028,
    time_id = 25  -- Forecast period
WHERE year = 2028;

COMMIT;

-- =====================================================
-- VERIFICATION
-- =====================================================

SELECT '=== Data Year Distribution ===' as info;

SELECT 'fact_market_size' as table_name, year, COUNT(*) as records
FROM fact_market_size
GROUP BY year
ORDER BY year;

SELECT '' as separator;

SELECT 'fact_forecasts' as table_name, year, COUNT(*) as records
FROM fact_forecasts
GROUP BY year
ORDER BY year;

SELECT '' as separator;

SELECT 'dim_time periods' as info, 
       MIN(year) || ' to ' || MAX(year) as year_range,
       COUNT(DISTINCT year) as num_years,
       COUNT(*) as total_periods
FROM dim_time;

SELECT '' as separator;

SELECT 'Sample EV data (recent)' as info;
SELECT m.market_name, f.year, COUNT(*) as records, 
       CAST(SUM(f.market_value_usd_m) AS INTEGER) as total_value_m
FROM fact_market_size f
JOIN dim_markets m ON f.market_id = m.market_id
WHERE m.market_name LIKE '%Electric%'
GROUP BY m.market_name, f.year
ORDER BY f.year DESC, total_value_m DESC;

