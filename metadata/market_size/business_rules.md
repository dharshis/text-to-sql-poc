# EM Market Database - Business Rules

This document contains business rules for SQL query generation. Each rule is designed to be independently retrievable based on user query context.

---

## RULE: Market Size Value Queries
**When to use**: User asks for "market size", "market value", "revenue", or "total sales"
**Definition**: Aggregate market value in USD millions
**SQL Implementation**:
```sql
SELECT SUM(market_value_usd_m) AS total_market_value
FROM fact_market_size
WHERE market_value_usd_m IS NOT NULL
```
**Critical**: Always filter NULL values and aggregate by USD millions
**Example queries**: "What is the market size?", "Total market value", "Revenue for automotive"

---

## RULE: Market Volume Queries
**When to use**: User asks for "volume", "units", "quantity", or "physical sales"
**Definition**: Market volume in standardized units
**SQL Implementation**:
```sql
SELECT SUM(market_volume_units) AS total_volume
FROM fact_market_size
WHERE market_volume_units IS NOT NULL
```
**Example queries**: "Market volume", "How many units", "Physical sales"

---

## RULE: Latest Year Data Query Pattern
**When to use**: User asks for "latest", "current", "most recent", or no time specified
**Definition**: Use the most recent year available in the dataset
**SQL Implementation**:
```sql
SELECT year 
FROM dim_time 
WHERE is_forecast = 0 
ORDER BY year DESC 
LIMIT 1
```
**Then use in main query**:
```sql
WHERE t.year = (SELECT MAX(year) FROM dim_time WHERE is_forecast = 0)
```
**Example queries**: "Current market size", "Latest data", "What is the market value?"

---

## RULE: Historical Data Query Pattern
**When to use**: User asks for "historical", "past", "trend", or mentions specific years
**Definition**: Time series data excluding forecasts
**SQL Implementation**:
```sql
WHERE t.is_forecast = 0
ORDER BY t.year ASC
```
**Example queries**: "Historical trends", "Market size from 2020 to 2024", "Past 5 years"

---

## RULE: Forecast Data Query Pattern
**When to use**: User asks for "forecast", "prediction", "projected", "future", or "outlook"
**Definition**: Projected future data from fact_forecasts table
**SQL Implementation**:
```sql
SELECT ff.year, ff.forecast_value_usd_m, ff.cagr
FROM fact_forecasts ff
JOIN dim_time t ON ff.time_id = t.time_id
WHERE t.is_forecast = 1
```
**Example queries**: "Forecast for 2025", "Future market outlook", "Projected growth"

---

## RULE: CAGR Calculation and Display
**When to use**: User asks for "growth rate", "CAGR", "compound annual growth", or "growth percentage"
**Definition**: Compound Annual Growth Rate showing market growth velocity
**SQL Implementation**:
```sql
SELECT 
    m.market_name,
    ff.cagr,
    CONCAT(ROUND(ff.cagr, 1), '%') AS growth_rate_display
FROM fact_forecasts ff
JOIN dim_markets m ON ff.market_id = m.market_id
```
**Example queries**: "What's the CAGR?", "Growth rate for EVs", "Fastest growing markets"

---

## RULE: Geographic Aggregation by Region
**When to use**: User asks for "by region", "regional breakdown", or mentions regions
**Definition**: Group data by geographic region (EMEA, APAC, Americas, etc.)
**SQL Implementation**:
```sql
SELECT 
    g.region,
    SUM(fms.market_value_usd_m) AS total_value
FROM fact_market_size fms
JOIN dim_geography g ON fms.geo_id = g.geo_id
GROUP BY g.region
ORDER BY total_value DESC
```
**Common regions**: Western Europe, Asia Pacific, North America, Latin America, Middle East & Africa
**Example queries**: "Market size by region", "Regional breakdown", "Which region is largest"

---

## RULE: Country-Specific Queries
**When to use**: User mentions specific country names or asks for country data
**Definition**: Filter by country name (full text match)
**SQL Implementation**:
```sql
WHERE g.country = 'United States'
-- OR for multiple countries:
WHERE g.country IN ('United States', 'China', 'Germany')
```
**Critical**: Use full country names, not abbreviations or codes in the WHERE clause
**Country code available**: Use g.country_code for ISO codes (USA, CHN, DEU)
**Example queries**: "Market size in USA", "China vs India comparison", "Germany data"

---

## RULE: Country Code vs Country Name
**When to use**: Deciding between country_code and country fields
**Definition**: 
- `country`: Full name for display and filtering (e.g., "United States")
- `country_code`: ISO 3-letter code (e.g., "USA") for compact storage/joins
**SQL Implementation**:
```sql
-- Filtering: Use country name
WHERE g.country = 'United States'

-- Display: Show both for clarity
SELECT g.country, g.country_code
```

---

## RULE: Emerging Markets Filter
**When to use**: User asks for "emerging markets", "developing countries", or "high growth regions"
**Definition**: Markets with high growth potential flag
**SQL Implementation**:
```sql
WHERE g.is_emerging_market = 1
```
**Example queries**: "Emerging markets", "Developing countries", "High growth regions"

---

## RULE: Market Hierarchy Navigation
**When to use**: User asks for "submakes", "categories", "segments", or parent-child relationships
**Definition**: Markets can have parent-child relationships
**SQL Implementation**:
```sql
-- Get child markets
SELECT 
    child.market_name,
    parent.market_name AS parent_market
FROM dim_markets child
LEFT JOIN dim_markets parent ON child.parent_market_id = parent.market_id
WHERE parent.market_name = 'Automotive'
```
**Example queries**: "Show me automotive sub-markets", "Categories under consumer goods"

---

## RULE: Market Definition Lookup
**When to use**: Understanding what a specific market includes
**Definition**: Each market has a definition explaining its scope
**SQL Implementation**:
```sql
SELECT 
    market_name,
    definition,
    naics_code
FROM dim_markets
WHERE market_name LIKE '%Electric Vehicles%'
```
**Example queries**: "What does EV market include?", "Define automotive market"

---

## RULE: NAICS Code Reference
**When to use**: User mentions industry codes or asks for classification
**Definition**: North American Industry Classification System codes
**SQL Implementation**:
```sql
WHERE m.naics_code = '336111'
-- OR search by code pattern:
WHERE m.naics_code LIKE '336%'  -- All automotive-related
```
**Example queries**: "Markets in NAICS 336", "Industry classification"

---

## RULE: Market Segmentation Query Pattern
**When to use**: User asks for "by segment", "segment breakdown", or mentions specific segments
**Definition**: Markets can be segmented by various dimensions (price, demographics, etc.)
**SQL Implementation**:
```sql
SELECT 
    st.segment_name,
    sv.value_name,
    SUM(fms.market_value_usd_m) AS segment_value
FROM fact_market_size fms
JOIN dim_segment_values sv ON fms.segment_value_id = sv.segment_value_id
JOIN dim_segment_types st ON sv.segment_type_id = st.segment_type_id
GROUP BY st.segment_name, sv.value_name
```
**Example queries**: "Market by price segment", "Premium vs economy", "Demographic breakdown"

---

## RULE: Time Period Aggregation - Annual
**When to use**: User asks for yearly data or doesn't specify period
**Definition**: Group by calendar year
**SQL Implementation**:
```sql
SELECT 
    t.year,
    SUM(fms.market_value_usd_m) AS annual_value
FROM fact_market_size fms
JOIN dim_time t ON fms.time_id = t.time_id
GROUP BY t.year
ORDER BY t.year
```
**Default**: Use annual aggregation unless quarterly specified

---

## RULE: Time Period Aggregation - Quarterly
**When to use**: User asks for "quarterly", "Q1", "Q2", or mentions quarters
**Definition**: Group by quarter within year
**SQL Implementation**:
```sql
SELECT 
    t.year_quarter,
    t.quarter,
    SUM(fms.market_value_usd_m) AS quarterly_value
FROM fact_market_size fms
JOIN dim_time t ON fms.time_id = t.time_id
WHERE t.quarter IS NOT NULL
GROUP BY t.year_quarter, t.quarter
ORDER BY t.year_quarter
```
**Example queries**: "Q1 2024 data", "Quarterly breakdown", "Last quarter"

---

## RULE: Year-Over-Year Growth Calculation
**When to use**: User asks for "YoY growth", "year over year", "annual growth", or "change from last year"
**Definition**: Calculate percentage change between consecutive years
**SQL Implementation**:
```sql
WITH yearly_data AS (
    SELECT 
        t.year,
        SUM(fms.market_value_usd_m) AS market_value
    FROM fact_market_size fms
    JOIN dim_time t ON fms.time_id = t.time_id
    GROUP BY t.year
)
SELECT 
    current.year,
    current.market_value,
    previous.market_value AS previous_year_value,
    ROUND(((current.market_value - previous.market_value) / previous.market_value * 100), 2) AS yoy_growth_pct
FROM yearly_data current
LEFT JOIN yearly_data previous ON current.year = previous.year + 1
ORDER BY current.year
```
**Example queries**: "YoY growth", "How much did it grow?", "Change from 2023 to 2024"

---

## RULE: Multi-Country Comparison
**When to use**: User asks to compare multiple countries
**Definition**: Side-by-side comparison of metrics across countries
**SQL Implementation**:
```sql
SELECT 
    g.country,
    SUM(fms.market_value_usd_m) AS total_value,
    AVG(fms.market_value_usd_m) AS avg_value
FROM fact_market_size fms
JOIN dim_geography g ON fms.geo_id = g.geo_id
WHERE g.country IN ('United States', 'China', 'Germany')
GROUP BY g.country
ORDER BY total_value DESC
```
**Example queries**: "Compare USA, China, and Germany", "Which is bigger: UK or France?"

---

## RULE: Top N Markets Ranking
**When to use**: User asks for "top 5", "largest markets", "biggest", or rankings
**Definition**: Rank markets by specified metric
**SQL Implementation**:
```sql
SELECT 
    m.market_name,
    SUM(fms.market_value_usd_m) AS total_value
FROM fact_market_size fms
JOIN dim_markets m ON fms.market_id = m.market_id
WHERE t.year = 2024
GROUP BY m.market_name
ORDER BY total_value DESC
LIMIT 5
```
**Default limit**: Use LIMIT 10 unless user specifies different number
**Example queries**: "Top 5 markets", "Largest markets by value", "Top 10 fastest growing"

---

## RULE: Currency Normalization
**When to use**: All value queries (implicit handling)
**Definition**: All monetary values are stored in USD millions for standardization
**SQL Implementation**:
```sql
SELECT 
    SUM(fms.market_value_usd_m) AS value_usd_millions
FROM fact_market_size fms
```
**Display format**: Include "USD millions" or "USD M" in output descriptions
**Critical**: Values are already normalized; no conversion needed

---

## RULE: Currency Metadata Reference
**When to use**: User asks about currency types or conversion information
**Definition**: Currency dimension provides metadata about currency handling
**SQL Implementation**:
```sql
SELECT 
    currency_code,
    currency_name,
    currency_type
FROM dim_currency
WHERE currency_code = 'USD'
```
**Example queries**: "What currencies are supported?", "Currency information"

---

## RULE: Client Data Isolation
**When to use**: ALWAYS - every query must filter by client
**Definition**: Multi-tenant system requires client_id filtering on all tables
**SQL Implementation**:
```sql
WHERE fms.client_id = [current_client_id]
-- Apply to ALL tables with client_id column
```
**Critical**: NEVER return data from other clients
**Tables requiring filter**: fact_market_size, fact_forecasts, all dimension tables
**Example**: If client_id = 1, all queries must include `WHERE client_id = 1`

---

## RULE: Data Type Classification
**When to use**: Distinguishing between actual and estimated data
**Definition**: fact_market_size has data_type field for data source classification
**SQL Implementation**:
```sql
WHERE fms.data_type = 'actual'
-- OR
WHERE fms.data_type = 'estimated'
```
**Values**: 'actual', 'estimated', 'modeled'
**Example queries**: "Show only actual data", "Exclude estimates"

---

## RULE: NULL Value Handling in Aggregations
**When to use**: ALL aggregation queries
**Definition**: Filter NULL values before aggregating to avoid incorrect totals
**SQL Implementation**:
```sql
SUM(CASE WHEN market_value_usd_m IS NOT NULL THEN market_value_usd_m ELSE 0 END)
-- OR better:
WHERE market_value_usd_m IS NOT NULL
```
**Fields that can be NULL**: market_value_usd_m, market_volume_units, cagr
**Critical**: Always check for NULL in SUM, AVG, COUNT operations

---

## RULE: Missing Data Indication
**When to use**: Displaying data that may have gaps
**Definition**: Some combinations may not have data
**SQL Implementation**:
```sql
SELECT 
    COALESCE(SUM(market_value_usd_m), 0) AS total_value,
    CASE 
        WHEN COUNT(*) = 0 THEN 'No data available'
        ELSE 'Data available'
    END AS data_status
```

---

## RULE: Date Range Filtering
**When to use**: User specifies time range like "from 2020 to 2023"
**Definition**: Filter by year range using BETWEEN
**SQL Implementation**:
```sql
WHERE t.year BETWEEN 2020 AND 2023
```
**Example queries**: "From 2020 to 2023", "Between 2018 and 2022", "Last 5 years"

---

## RULE: Standard Table Aliases
**When to use**: ALL queries for consistency and readability
**Definition**: Use consistent aliases across all queries
**Standard aliases**:
- fact_market_size → fms
- fact_forecasts → ff
- dim_markets → m
- dim_geography → g
- dim_time → t
- dim_currency → cur
- dim_segment_types → st
- dim_segment_values → sv
- dim_clients → c

---

## RULE: Market Share Calculation Pattern
**When to use**: User asks for "market share", "share of market", or percentage breakdowns
**Definition**: Calculate proportional share of total market
**SQL Implementation**:
```sql
WITH market_totals AS (
    SELECT 
        geo_id,
        SUM(market_value_usd_m) AS total_market
    FROM fact_market_size
    WHERE year = 2024
    GROUP BY geo_id
),
segment_values AS (
    SELECT 
        fms.geo_id,
        sv.value_name,
        SUM(fms.market_value_usd_m) AS segment_value
    FROM fact_market_size fms
    JOIN dim_segment_values sv ON fms.segment_value_id = sv.segment_value_id
    WHERE fms.year = 2024
    GROUP BY fms.geo_id, sv.value_name
)
SELECT 
    g.country,
    sv.value_name,
    sv.segment_value,
    mt.total_market,
    ROUND((sv.segment_value / mt.total_market * 100), 2) AS market_share_pct
FROM segment_values sv
JOIN market_totals mt ON sv.geo_id = mt.geo_id
JOIN dim_geography g ON sv.geo_id = g.geo_id
ORDER BY market_share_pct DESC
```

---

## RULE: Scenario-Based Forecasting
**When to use**: User mentions forecast scenarios like "optimistic", "conservative", "base case"
**Definition**: Forecasts can have different scenario assumptions
**SQL Implementation**:
```sql
WHERE ff.scenario = 'base_case'
-- OR
WHERE ff.scenario IN ('optimistic', 'base_case', 'pessimistic')
```
**Common scenarios**: base_case, optimistic, pessimistic, covid_recovery
**Example queries**: "Optimistic forecast", "Conservative projection"

---

## RULE: Standard JOIN Patterns
**When to use**: Connecting fact tables to dimensions
**Definition**: Use INNER JOIN for required dimensions, LEFT JOIN for optional
**SQL Implementation**:
```sql
-- Required dimensions (INNER JOIN):
FROM fact_market_size fms
INNER JOIN dim_markets m ON fms.market_id = m.market_id
INNER JOIN dim_geography g ON fms.geo_id = g.geo_id
INNER JOIN dim_time t ON fms.time_id = t.time_id

-- Optional dimensions (LEFT JOIN):
LEFT JOIN dim_segment_values sv ON fms.segment_value_id = sv.segment_value_id
LEFT JOIN dim_currency cur ON fms.currency_id = cur.currency_id
```

---

## RULE: Performance Optimization with Indexes
**When to use**: All queries for optimal performance
**Definition**: Filter on indexed columns first
**Indexed fields**:
- fact_market_size: market_id, geo_id, year, time_id, client_id
- dim_time: year
**Pattern**: Always include client_id and year in WHERE clause early

---

## RULE: Aggregate Query with Multiple Dimensions
**When to use**: User asks for breakdown by multiple factors
**Definition**: GROUP BY multiple dimensions with multiple metrics
**SQL Implementation**:
```sql
SELECT 
    m.market_name,
    g.country,
    t.year,
    SUM(fms.market_value_usd_m) AS total_value,
    SUM(fms.market_volume_units) AS total_volume,
    COUNT(*) AS record_count
FROM fact_market_size fms
JOIN dim_markets m ON fms.market_id = m.market_id
JOIN dim_geography g ON fms.geo_id = g.geo_id
JOIN dim_time t ON fms.time_id = t.time_id
GROUP BY m.market_name, g.country, t.year
ORDER BY total_value DESC
```

---

## RULE: Default Result Limiting
**When to use**: Non-aggregate queries returning detail records
**SQL Implementation**:
```sql
LIMIT 100
```
**Override**: If user asks for "all" or query is aggregate, don't limit
**Example**: Detail queries get LIMIT 100, aggregates don't need limits

---

## DATABASE SCHEMA SUMMARY

### Fact Tables
- **fact_market_size**: Historical market data (value & volume)
- **fact_forecasts**: Future projections with CAGR

### Dimension Tables
- **dim_markets**: Market definitions and hierarchy
- **dim_geography**: Countries, regions, emerging market flags
- **dim_time**: Years, quarters, forecast flags
- **dim_currency**: Currency metadata
- **dim_segment_types**: Segmentation categories
- **dim_segment_values**: Specific segment values
- **dim_clients**: Multi-tenant client data

### Key Relationships
- All facts link to dimensions via foreign keys
- Markets have parent-child relationships
- Segments have type-value hierarchy
- All tables have client_id for multi-tenancy

---

