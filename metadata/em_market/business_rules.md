# Dataset-Specific Instructions: Euromonitor Market Data

## Domain Context

**Business Domain:** Global market research for consumer goods (FMCG/CPG)

**Key Entity Hierarchy:**
```
Dim_Corporation (corp_id) ← FILTERING HAPPENS HERE
  └─ Dim_Brand (brand_id, corp_id FK)
      └─ Dim_SubBrand (subbrand_id, brand_id FK)
          └─ Dim_Product_SKU (sku_id, subbrand_id FK)
              └─ Fact_Sales_Transactions (sku_id FK) ← Use this for queries
```

**Critical**: All queries MUST filter by `corp_id` through the brand hierarchy to enforce corporation-level data isolation.

**Note**: Use **Fact_Sales_Transactions** (not Fact_Market_Summary) for all queries because it has direct SKU links. Fact_Market_Summary requires Bridge_Market_SKU which is not available in the current dataset.

## Database Schema Overview

### Fact Tables
- **Fact_Market_Summary**: Aggregate market size data (total market value/volume) by market definition, geography, and period
- **Fact_Sales_Transactions**: Detailed sales transactions by SKU, geography, and period

### Dimension Tables
- **Dim_Corporation**: Parent companies (corp_id, corp_name)
- **Dim_Brand**: Brands owned by corporations (brand_id, brand_name, corp_id)
- **Dim_SubBrand**: Brand variants (subbrand_id, subbrand_name, brand_id)
- **Dim_Product_SKU**: Individual products (sku_id, sku_name, subbrand_id)
- **Dim_Geography**: Geographic locations (geo_id, country_name, region)
- **Dim_Period**: Time periods (period_id, fiscal_year, quarter, month_name, period_type)
- **Dim_Market_Definition**: Market category definitions (market_def_id, market_name, category)

### Bridge Table
- **Bridge_Market_SKU**: Many-to-many relationship between SKUs and market definitions

### Time Handling
- **Dim_Period table EXISTS** - join to this table for time-based queries
- **Columns**: period_id (PK), fiscal_year, quarter, month_name, period_type
- **Granularity**: Monthly data (202201 = January 2022, 202202 = February 2022, etc.)
- **Year range**: Typically 2022-2024 in sample data
- **Format**: period_id is YYYYMM format (e.g., 202401 = January 2024)

## Filtering Examples

The system will instruct you to filter by `corp_id = {client_id}`.
Here's how this applies in common queries:

### Example 1: Simple brand listing
```sql
-- User asks: "Show me all my brands"
SELECT brand_name
FROM Dim_Brand b
WHERE b.corp_id = {client_id}
ORDER BY brand_name
```

### Example 2: Market size by brand (requires join through hierarchy)
```sql
-- User asks: "What is the total market size for my brands?"
SELECT b.brand_name,
       dp.fiscal_year,
       SUM(fms.total_market_value_usd) as total_market_value
FROM Fact_Market_Summary fms
JOIN Dim_Period dp ON fms.period_id = dp.period_id
JOIN Bridge_Market_SKU bms ON fms.market_def_id = bms.market_def_id
JOIN Dim_Product_SKU dps ON bms.sku_id = dps.sku_id
JOIN Dim_SubBrand dsb ON dps.subbrand_id = dsb.subbrand_id
JOIN Dim_Brand db ON dsb.brand_id = db.brand_id
WHERE db.corp_id = {client_id}
GROUP BY b.brand_name, dp.fiscal_year
ORDER BY dp.fiscal_year, total_market_value DESC
```

### Example 3: Market size by geography
```sql
-- User asks: "Show me market size by country"
SELECT dg.country_name,
       SUM(fms.total_market_value_usd) as total_value
FROM Fact_Market_Summary fms
JOIN Dim_Geography dg ON fms.geo_id = dg.geo_id
JOIN Bridge_Market_SKU bms ON fms.market_def_id = bms.market_def_id
JOIN Dim_Product_SKU dps ON bms.sku_id = dps.sku_id
JOIN Dim_SubBrand dsb ON dps.subbrand_id = dsb.subbrand_id
JOIN Dim_Brand db ON dsb.brand_id = db.brand_id
WHERE db.corp_id = {client_id}
GROUP BY dg.country_name
ORDER BY total_value DESC
```

## Domain-Specific Patterns

### Pattern 1: Time Range Queries
**Rule**: Use Dim_Period table for ALL time-based queries
**Rule**: For "last N years", use: `fiscal_year >= (SELECT MAX(fiscal_year) FROM Dim_Period) - N + 1`
**Rule**: NEVER use CURRENT_DATE, NOW(), or system date functions
**Rule**: period_id format is YYYYMM (e.g., 202401 = January 2024, 202412 = December 2024)

**Examples**:
```sql
-- Last 3 years of data
JOIN Dim_Period dp ON fms.period_id = dp.period_id
WHERE dp.fiscal_year >= (SELECT MAX(fiscal_year) - 2 FROM Dim_Period)

-- Latest available year
WHERE dp.fiscal_year = (SELECT MAX(fiscal_year) FROM Dim_Period)

-- Specific year (2024)
WHERE dp.fiscal_year = 2024

-- Specific quarter
WHERE dp.fiscal_year = 2024 AND dp.quarter = 1

-- Year-over-year comparison
WHERE dp.fiscal_year IN (2023, 2024)
```

### Pattern 2: Geographic Filters
**Rule**: Join through Dim_Geography for location-based queries
**Rule**: Always include corp_id filter even with geography

**Examples**:
```sql
-- Specific country
JOIN Dim_Geography dg ON fms.geo_id = dg.geo_id
WHERE dg.country_name = 'United States'
  AND db.corp_id = {client_id}

-- Regional analysis
WHERE dg.region = 'North America'
```

### Pattern 3: Brand Hierarchy Navigation
**Rule**: Must traverse FULL hierarchy to reach corp_id filter
**Rule**: Join path: Fact → Bridge_Market_SKU → Dim_Product_SKU → Dim_SubBrand → Dim_Brand

**Standard Join Pattern**:
```sql
FROM Fact_Market_Summary fms
JOIN Bridge_Market_SKU bms ON fms.market_def_id = bms.market_def_id
JOIN Dim_Product_SKU dps ON bms.sku_id = dps.sku_id
JOIN Dim_SubBrand dsb ON dps.subbrand_id = dsb.subbrand_id
JOIN Dim_Brand db ON dsb.brand_id = db.brand_id
WHERE db.corp_id = {client_id}
```

### Pattern 4: Market Definition
**Rule**: Bridge_Market_SKU connects products to market definitions
**Rule**: Use Dim_Market_Definition for market category information

## Common Query Patterns

### Query 1: Sales trend over time (use Fact_Sales_Transactions)
```sql
-- Natural language: "Show me the sales trend in 2023"
-- Note: Use Fact_Sales_Transactions which has direct SKU links
-- Important: For quarterly trends, create a readable quarter label as first column
SELECT CASE dp.quarter
         WHEN 1 THEN 'Q1 ' || CAST(dp.fiscal_year AS TEXT)
         WHEN 2 THEN 'Q2 ' || CAST(dp.fiscal_year AS TEXT)
         WHEN 3 THEN 'Q3 ' || CAST(dp.fiscal_year AS TEXT)
         WHEN 4 THEN 'Q4 ' || CAST(dp.fiscal_year AS TEXT)
       END as quarter_label,
       SUM(fst.value_sold_usd) as total_sales_usd,
       SUM(fst.volume_sold_std) as total_volume
FROM Fact_Sales_Transactions fst
JOIN Dim_Period dp ON fst.period_id = dp.period_id
JOIN Dim_Product_SKU dps ON fst.sku_id = dps.sku_id
JOIN Dim_SubBrand dsb ON dps.subbrand_id = dsb.subbrand_id
JOIN Dim_Brand db ON dsb.brand_id = db.brand_id
WHERE dp.fiscal_year = 2023
  AND db.corp_id = {client_id}
GROUP BY dp.quarter, dp.fiscal_year
ORDER BY dp.quarter
```

### Query 2: Top brands by sales
```sql
-- Natural language: "Show me top 10 brands by sales"
SELECT db.brand_name,
       SUM(fst.value_sold_usd) as total_sales
FROM Fact_Sales_Transactions fst
JOIN Dim_Product_SKU dps ON fst.sku_id = dps.sku_id
JOIN Dim_SubBrand dsb ON dps.subbrand_id = dsb.subbrand_id
JOIN Dim_Brand db ON dsb.brand_id = db.brand_id
WHERE db.corp_id = {client_id}
GROUP BY db.brand_name
ORDER BY total_sales DESC
LIMIT 10
```

### Query 3: Sales by country and year
```sql
-- Natural language: "Sales by country for the last 2 years"
SELECT dg.country_name,
       dp.fiscal_year,
       SUM(fst.value_sold_usd) as total_value
FROM Fact_Sales_Transactions fst
JOIN Dim_Period dp ON fst.period_id = dp.period_id
JOIN Dim_Geography dg ON fst.geo_id = dg.geo_id
JOIN Dim_Product_SKU dps ON fst.sku_id = dps.sku_id
JOIN Dim_SubBrand dsb ON dps.subbrand_id = dsb.subbrand_id
JOIN Dim_Brand db ON dsb.brand_id = db.brand_id
WHERE db.corp_id = {client_id}
  AND dp.fiscal_year >= (SELECT MAX(fiscal_year) - 1 FROM Dim_Period)
GROUP BY dg.country_name, dp.fiscal_year
ORDER BY dp.fiscal_year, total_value DESC
```

### Query 4: Quarterly breakdown
```sql
-- Natural language: "Show quarterly breakdown for 2023"
SELECT dp.quarter,
       COUNT(DISTINCT fst.transaction_id) as transaction_count,
       SUM(fst.value_sold_usd) as total_value,
       SUM(fst.volume_sold_std) as total_volume
FROM Fact_Sales_Transactions fst
JOIN Dim_Period dp ON fst.period_id = dp.period_id
JOIN Dim_Product_SKU dps ON fst.sku_id = dps.sku_id
JOIN Dim_SubBrand dsb ON dps.subbrand_id = dsb.subbrand_id
JOIN Dim_Brand db ON dsb.brand_id = db.brand_id
WHERE dp.fiscal_year = 2023
  AND db.corp_id = {client_id}
GROUP BY dp.quarter
ORDER BY dp.quarter
```

### Query 5: Sales by product
```sql
-- Natural language: "Show me sales by product"
SELECT dps.sku_name,
       dsb.subbrand_name,
       db.brand_name,
       SUM(fst.value_sold_usd) as total_sales
FROM Fact_Sales_Transactions fst
JOIN Dim_Product_SKU dps ON fst.sku_id = dps.sku_id
JOIN Dim_SubBrand dsb ON dps.subbrand_id = dsb.subbrand_id
JOIN Dim_Brand db ON dsb.brand_id = db.brand_id
WHERE db.corp_id = {client_id}
GROUP BY dps.sku_name, dsb.subbrand_name, db.brand_name
ORDER BY total_sales DESC
LIMIT 20
```

## Important Reminders

1. **ALWAYS** use **Fact_Sales_Transactions** (not Fact_Market_Summary) for queries

2. **ALWAYS** filter by `corp_id = {client_id}` through the full hierarchy:
   - Fact_Sales_Transactions → Dim_Product_SKU → Dim_SubBrand → Dim_Brand

3. **ALWAYS** join to Dim_Period for time-based queries (don't use raw period_id)

4. **NEVER** use CURRENT_DATE or NOW() - use MAX(fiscal_year) from Dim_Period

5. **Period_id format**: YYYYMM (202401 = January 2024, not 2024-01)

6. **Time granularity**: Monthly (use fiscal_year and quarter for rollups)

7. **Available years**: Check the actual data, sample data is typically 2022-2023

8. **Limit** results to 100 rows unless user specifies otherwise

9. **Order** results meaningfully (by value DESC or by time ASC)

10. **Corp_id filtering is MANDATORY** for all queries to enforce data isolation
