/* ==========================================================================
   FMCG MARKET INTELLIGENCE DATABASE SCHEMA
   Designed for: Market Size (Val/Vol), Company Share, Brand Share, SKU Attributes
   ========================================================================== */

-- 1. CLEANUP (Optional: Use with caution)
-- DROP TABLE IF EXISTS Fact_Sales_Transactions;
-- DROP TABLE IF EXISTS Fact_Market_Summary;
-- DROP TABLE IF EXISTS Dim_Product_SKU;
-- DROP TABLE IF EXISTS Dim_SubBrand;
-- DROP TABLE IF EXISTS Dim_Brand;
-- DROP TABLE IF EXISTS Dim_Corporation;
-- DROP TABLE IF EXISTS Dim_Market_Definition;
-- DROP TABLE IF EXISTS Dim_Geography;
-- DROP TABLE IF EXISTS Dim_Period;

/* ==========================================================================
   A. DIMENSION TABLES (The "Who, Where, What, When")
   ========================================================================== */

-- 1. TIME: Standardized reporting periods
CREATE TABLE Dim_Period (
    period_id INT PRIMARY KEY,       -- Format: YYYYMM (e.g., 202310)
    fiscal_year INT,
    quarter INT,
    month_name VARCHAR(20),
    period_type VARCHAR(20)          -- 'Monthly', '4-Week', 'Quarterly'
);

-- 2. GEOGRAPHY: Handling Multi-Currency and Regions
CREATE TABLE Dim_Geography (
    geo_id INT PRIMARY KEY,
    country_name VARCHAR(100) NOT NULL,
    region_name VARCHAR(100),        -- e.g., 'APAC', 'North America'
    currency_code CHAR(3),           -- e.g., 'USD', 'EUR', 'INR'
    currency_exchange_rate DECIMAL(10, 6) -- Rate to convert to standard USD
);

-- 3. CORPORATION: The Ultimate Owners (e.g., Unilever, P&G)
CREATE TABLE Dim_Corporation (
    corp_id INT PRIMARY KEY,
    corp_name VARCHAR(100) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    global_headquarters VARCHAR(100)
);

-- 4. BRAND: The Major Brand Names (e.g., Dove, Pantene)
CREATE TABLE Dim_Brand (
    brand_id INT PRIMARY KEY,
    brand_name VARCHAR(100) NOT NULL,
    corp_id INT,                     -- Link to Parent Company
    price_segment VARCHAR(50),       -- 'Premium', 'Mass', 'Economy'
    FOREIGN KEY (corp_id) REFERENCES Dim_Corporation(corp_id)
);

-- 5. SUB-BRAND: Variants (e.g., Dove Men+Care, Dove Baby)
CREATE TABLE Dim_SubBrand (
    subbrand_id INT PRIMARY KEY,
    subbrand_name VARCHAR(100),
    brand_id INT,
    FOREIGN KEY (brand_id) REFERENCES Dim_Brand(brand_id)
);

-- 6. SKU: The Atomic Unit (FMCG Specifics)
-- This handles the complexity of "Pack Size" and "Form Factor"
CREATE TABLE Dim_Product_SKU (
    sku_id BIGINT PRIMARY KEY,
    sku_description VARCHAR(255),    -- "Dove Shampoo Intensive Repair 400ml"
    barcode_ean VARCHAR(20),         -- Scannable Code
    subbrand_id INT,
    
    -- Detailed Attributes for Analysis
    category_name VARCHAR(100),      -- 'Shampoo', 'Toothpaste'
    form_factor VARCHAR(50),         -- 'Liquid', 'Bar', 'Gel', 'Powder'
    pack_type VARCHAR(50),           -- 'Bottle', 'Sachet', 'Multipack'
    
    -- Volume normalization (Crucial for Market Volume calc)
    pack_size_value DECIMAL(10,2),   -- e.g., 400
    pack_size_unit VARCHAR(20),      -- e.g., 'ml', 'g'
    volume_in_liters_kg DECIMAL(10,4), -- Standardized volume (0.400)
    
    FOREIGN KEY (subbrand_id) REFERENCES Dim_SubBrand(subbrand_id)
);

/* ==========================================================================
   B. MARKET DEFINITIONS (The "Scope")
   ========================================================================== */

-- 7. MARKET DEFINITION: Grouping SKUs into reportable markets
-- Allows dynamic definitions like "Total Hair Care" vs "Just Shampoos"
CREATE TABLE Dim_Market_Definition (
    market_def_id INT PRIMARY KEY,
    market_name VARCHAR(100)         -- e.g., 'Total Carbonated Soft Drinks'
);

-- 8. BRIDGE: Mapping SKUs to Markets (Many-to-Many)
CREATE TABLE Bridge_Market_SKU (
    market_def_id INT,
    sku_id BIGINT,
    PRIMARY KEY (market_def_id, sku_id),
    FOREIGN KEY (market_def_id) REFERENCES Dim_Market_Definition(market_def_id),
    FOREIGN KEY (sku_id) REFERENCES Dim_Product_SKU(sku_id)
);

/* ==========================================================================
   C. FACT TABLES (The Data)
   ========================================================================== */

-- 9. FACT: GRANULAR SALES (Bottom-Up)
-- Stores raw sales data. Used to calculate Company and Brand Share.
CREATE TABLE Fact_Sales_Transactions (
    transaction_id BIGINT PRIMARY KEY,
    period_id INT,
    geo_id INT,
    sku_id BIGINT,
    
    -- Metrics
    units_sold DECIMAL(18,0),
    volume_sold_std DECIMAL(18,2),   -- (Units * volume_in_liters_kg)
    value_sold_local DECIMAL(18,2),  -- Revenue in local currency
    value_sold_usd DECIMAL(18,2),    -- Revenue standardized to USD
    
    -- Context
    is_promotion BOOLEAN,            -- Was it sold on deal?
    distribution_points INT,         -- Number of stores selling it
    
    FOREIGN KEY (period_id) REFERENCES Dim_Period(period_id),
    FOREIGN KEY (geo_id) REFERENCES Dim_Geography(geo_id),
    FOREIGN KEY (sku_id) REFERENCES Dim_Product_SKU(sku_id)
);

-- 10. FACT: MARKET AGGREGATES (Top-Down)
-- Stores the "Total Market Size" (The Denominator). 
-- This ensures we have a fixed market size even if we filter out some small brands.
CREATE TABLE Fact_Market_Summary (
    summary_id BIGINT PRIMARY KEY,
    period_id INT,
    geo_id INT,
    market_def_id INT,
    
    -- Total Market Size Metrics
    total_market_value_usd DECIMAL(18,2),
    total_market_volume_std DECIMAL(18,2),
    
    FOREIGN KEY (period_id) REFERENCES Dim_Period(period_id),
    FOREIGN KEY (geo_id) REFERENCES Dim_Geography(geo_id),
    FOREIGN KEY (market_def_id) REFERENCES Dim_Market_Definition(market_def_id)
);

/* ==========================================================================
   D. VIEW FOR REPORTING (The "Magic" Layer)
   ========================================================================== */

-- This View automatically calculates Share % and consolidates the data
-- exactly as requested: Value, Volume, Company Share, Brand Share.

CREATE VIEW View_FMCG_Market_Report AS
SELECT 
    p.period_id,
    g.country_name,
    m.market_name,
    c.corp_name AS Company,
    b.brand_name AS Brand,
    
    -- 1. Absolute Performance (Numerator)
    SUM(f.value_sold_usd) AS Brand_Value_USD,
    SUM(f.volume_sold_std) AS Brand_Volume_LitersKG,
    
    -- 2. Market Size (Denominator - brought in via Join)
    MAX(ms.total_market_value_usd) AS Total_Market_Value,
    MAX(ms.total_market_volume_std) AS Total_Market_Volume,
    
    -- 3. Brand Share Calculation
    (SUM(f.value_sold_usd) / NULLIF(MAX(ms.total_market_value_usd),0)) * 100 AS Brand_Value_Share_Pct,
    
    -- 4. Company Share Calculation (Summing up all brands for that corp)
    SUM(SUM(f.value_sold_usd)) OVER (PARTITION BY p.period_id, g.geo_id, m.market_def_id, c.corp_id) 
    / NULLIF(MAX(ms.total_market_value_usd),0) * 100 AS Company_Value_Share_Pct

FROM Fact_Sales_Transactions f
-- Joins to get dimensions
JOIN Dim_Product_SKU sku ON f.sku_id = sku.sku_id
JOIN Bridge_Market_SKU br ON sku.sku_id = br.sku_id
JOIN Dim_Market_Definition m ON br.market_def_id = m.market_def_id
JOIN Dim_SubBrand sb ON sku.subbrand_id = sb.subbrand_id
JOIN Dim_Brand b ON sb.brand_id = b.brand_id
JOIN Dim_Corporation c ON b.corp_id = c.corp_id
JOIN Dim_Period p ON f.period_id = p.period_id
JOIN Dim_Geography g ON f.geo_id = g.geo_id
-- Join to Market Summary to get the "Denominator" (Total Market Size)
LEFT JOIN Fact_Market_Summary ms 
    ON f.period_id = ms.period_id 
    AND f.geo_id = ms.geo_id 
    AND m.market_def_id = ms.market_def_id

GROUP BY 
    p.period_id, g.geo_id, g.country_name, m.market_def_id, m.market_name, c.corp_id, c.corp_name, b.brand_id, b.brand_name;