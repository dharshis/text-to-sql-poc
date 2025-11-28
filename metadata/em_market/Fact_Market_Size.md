# Table: fact_market_size

## Metadata
* **Table Type:** Fact (Transactional)
* **Subject Area:** Market Size Data
* **Granularity:** One row per Market, Geography, Time Period, and Segment combination
* **Primary Key:** `record_id`
* **Indexes:** market_id, geo_id, year, time_id, client_id

## Description
This is the **primary fact table** containing historical and current market size data. It stores both market value (in USD millions) and market volume (in units) across different markets, geographies, time periods, and segments.

**Key Characteristics:**
- Multi-dimensional: Market × Geography × Time × Segment
- Multi-tenant: Isolated by client_id
- Dual metrics: Value (USD) and Volume (units)
- Data quality flags: data_type field indicates actual vs estimated

## Column Definitions

| Column Name | Data Type | Key Type | Nullable | Description |
| :--- | :--- | :--- | :--- | :--- |
| `record_id` | INTEGER | PK | NO | Auto-increment unique identifier |
| `market_id` | VARCHAR(20) | FK | YES | Link to dim_markets (INDEXED) |
| `geo_id` | VARCHAR(20) | FK | YES | Link to dim_geography (INDEXED) |
| `segment_value_id` | VARCHAR(20) | FK | YES | Link to dim_segment_values |
| `time_id` | INTEGER | FK | YES | Link to dim_time (INDEXED) |
| `year` | INTEGER | | YES | Denormalized year for fast filtering (INDEXED) |
| `currency_id` | VARCHAR(10) | FK | YES | Link to dim_currency |
| `market_value_usd_m` | DECIMAL(15,2) | | YES | Market value in USD millions |
| `market_volume_units` | DECIMAL(15,2) | | YES | Market volume in standard units |
| `data_type` | VARCHAR(20) | | YES | Data classification (actual/estimated/modeled) |
| `client_id` | INTEGER | FK | NO | Multi-tenant isolation (INDEXED, DEFAULT 1) |
| `last_updated` | DATE | | YES | Record modification timestamp |

## Relationships
* **References:** `dim_markets`, `dim_geography`, `dim_time`, `dim_currency`, `dim_segment_values`, `dim_clients`

## Business Rules

### Data Access
- **CRITICAL**: Always filter by `client_id` for data isolation
- Use indexed columns (market_id, geo_id, year, client_id) in WHERE clauses for performance

### NULL Handling
- `market_value_usd_m` and `market_volume_units` can be NULL
- Always filter NULL values in aggregations: `WHERE market_value_usd_m IS NOT NULL`

### Time Filtering
- Use `year` column for fast year-based filtering (indexed)
- Join to `dim_time` for quarter/period information
- Historical data: `WHERE t.is_forecast = 0`

## Common Query Patterns

### Pattern 1: Total Market Size by Year
```sql
-- Get total market value for a specific market across all geographies
SELECT 
    t.year,
    m.market_name,
    SUM(fms.market_value_usd_m) AS total_value_usd_m,
    SUM(fms.market_volume_units) AS total_volume_units
FROM fact_market_size fms
INNER JOIN dim_markets m ON fms.market_id = m.market_id
INNER JOIN dim_time t ON fms.time_id = t.time_id
WHERE fms.client_id = 1
    AND m.market_name = 'Electric Vehicles'
    AND fms.market_value_usd_m IS NOT NULL
    AND t.is_forecast = 0
GROUP BY t.year, m.market_name
ORDER BY t.year DESC;
```

### Pattern 2: Market Size by Geography (Latest Year)
```sql
-- Compare market values across different countries for the most recent year
SELECT 
    g.country,
    g.region,
    SUM(fms.market_value_usd_m) AS market_value_usd_m,
    RANK() OVER (ORDER BY SUM(fms.market_value_usd_m) DESC) AS country_rank
FROM fact_market_size fms
INNER JOIN dim_geography g ON fms.geo_id = g.geo_id
INNER JOIN dim_time t ON fms.time_id = t.time_id
WHERE fms.client_id = 1
    AND t.year = (SELECT MAX(year) FROM dim_time WHERE is_forecast = 0)
    AND fms.market_value_usd_m IS NOT NULL
GROUP BY g.country, g.region
ORDER BY market_value_usd_m DESC
LIMIT 10;
```

### Pattern 3: Market Trend Analysis (Time Series)
```sql
-- Show year-over-year trend for a specific market and geography
SELECT 
    t.year,
    m.market_name,
    g.country,
    SUM(fms.market_value_usd_m) AS market_value_usd_m,
    LAG(SUM(fms.market_value_usd_m)) OVER (ORDER BY t.year) AS previous_year_value,
    ROUND(
        (SUM(fms.market_value_usd_m) - LAG(SUM(fms.market_value_usd_m)) OVER (ORDER BY t.year)) 
        / LAG(SUM(fms.market_value_usd_m)) OVER (ORDER BY t.year) * 100, 
        2
    ) AS yoy_growth_pct
FROM fact_market_size fms
INNER JOIN dim_markets m ON fms.market_id = m.market_id
INNER JOIN dim_geography g ON fms.geo_id = g.geo_id
INNER JOIN dim_time t ON fms.time_id = t.time_id
WHERE fms.client_id = 1
    AND m.market_name = 'Smartphones'
    AND g.country = 'United States'
    AND t.is_forecast = 0
GROUP BY t.year, m.market_name, g.country
ORDER BY t.year;
```

### Pattern 4: Segment Breakdown
```sql
-- Market value breakdown by segment for a specific market
SELECT 
    m.market_name,
    st.segment_name,
    sv.value_name AS segment_value,
    SUM(fms.market_value_usd_m) AS segment_market_value,
    ROUND(
        SUM(fms.market_value_usd_m) * 100.0 / 
        SUM(SUM(fms.market_value_usd_m)) OVER (), 
        2
    ) AS percentage_share
FROM fact_market_size fms
INNER JOIN dim_markets m ON fms.market_id = m.market_id
INNER JOIN dim_segment_values sv ON fms.segment_value_id = sv.segment_value_id
INNER JOIN dim_segment_types st ON sv.segment_type_id = st.segment_type_id
INNER JOIN dim_time t ON fms.time_id = t.time_id
WHERE fms.client_id = 1
    AND m.market_name = 'Laptops'
    AND t.year = 2024
    AND fms.market_value_usd_m IS NOT NULL
GROUP BY m.market_name, st.segment_name, sv.value_name
ORDER BY segment_market_value DESC;
```

### Pattern 5: Regional Comparison
```sql
-- Compare market performance across regions
SELECT 
    g.region,
    COUNT(DISTINCT g.country) AS num_countries,
    SUM(fms.market_value_usd_m) AS total_market_value,
    AVG(fms.market_value_usd_m) AS avg_market_value,
    SUM(fms.market_volume_units) AS total_volume
FROM fact_market_size fms
INNER JOIN dim_geography g ON fms.geo_id = g.geo_id
INNER JOIN dim_time t ON fms.time_id = t.time_id
WHERE fms.client_id = 1
    AND t.year = 2024
    AND fms.market_value_usd_m IS NOT NULL
GROUP BY g.region
ORDER BY total_market_value DESC;
```

### Pattern 6: Top Markets Ranking
```sql
-- Find top N markets by total value globally
SELECT 
    m.market_name,
    m.naics_code,
    SUM(fms.market_value_usd_m) AS total_global_value,
    COUNT(DISTINCT fms.geo_id) AS num_geographies,
    MIN(t.year) AS first_year,
    MAX(t.year) AS latest_year
FROM fact_market_size fms
INNER JOIN dim_markets m ON fms.market_id = m.market_id
INNER JOIN dim_time t ON fms.time_id = t.time_id
WHERE fms.client_id = 1
    AND t.year BETWEEN 2020 AND 2024
    AND fms.market_value_usd_m IS NOT NULL
GROUP BY m.market_name, m.naics_code
ORDER BY total_global_value DESC
LIMIT 10;
```

### Pattern 7: Multi-Country Comparison
```sql
-- Compare specific countries for a market
SELECT 
    g.country,
    t.year,
    SUM(fms.market_value_usd_m) AS market_value_usd_m,
    SUM(fms.market_volume_units) AS market_volume_units
FROM fact_market_size fms
INNER JOIN dim_geography g ON fms.geo_id = g.geo_id
INNER JOIN dim_time t ON fms.time_id = t.time_id
INNER JOIN dim_markets m ON fms.market_id = m.market_id
WHERE fms.client_id = 1
    AND g.country IN ('United States', 'China', 'Germany', 'Japan')
    AND m.market_name = 'Electric Vehicles'
    AND t.year = 2024
    AND fms.market_value_usd_m IS NOT NULL
GROUP BY g.country, t.year
ORDER BY market_value_usd_m DESC;
```

### Pattern 8: Emerging Markets Analysis
```sql
-- Analyze emerging markets performance
SELECT 
    g.country,
    g.region,
    m.market_name,
    SUM(fms.market_value_usd_m) AS market_value_usd_m,
    CASE 
        WHEN g.is_emerging_market = 1 THEN 'Emerging'
        ELSE 'Developed'
    END AS market_classification
FROM fact_market_size fms
INNER JOIN dim_geography g ON fms.geo_id = g.geo_id
INNER JOIN dim_markets m ON fms.market_id = m.market_id
INNER JOIN dim_time t ON fms.time_id = t.time_id
WHERE fms.client_id = 1
    AND g.is_emerging_market = 1
    AND t.year = 2024
    AND fms.market_value_usd_m IS NOT NULL
GROUP BY g.country, g.region, m.market_name, g.is_emerging_market
ORDER BY market_value_usd_m DESC
LIMIT 20;
```

## Performance Tips

1. **Always use indexed columns in WHERE clauses:**
   - client_id (REQUIRED for security)
   - year (for time filtering)
   - market_id (for market filtering)
   - geo_id (for geography filtering)

2. **Filter early, aggregate late:**
   ```sql
   -- Good: Filter first
   WHERE client_id = 1 AND year = 2024
   
   -- Bad: Filter after aggregation
   HAVING year = 2024
   ```

3. **Use INNER JOIN for required dimensions:**
   - dim_markets, dim_geography, dim_time are typically required

4. **Use LEFT JOIN for optional dimensions:**
   - dim_segment_values, dim_currency may be NULL

## Data Quality Notes

- **NULL values**: Both value and volume fields can be NULL; filter in aggregations
- **Data types**: Check `data_type` field to distinguish actual vs estimated data
- **Currency**: All values pre-normalized to USD millions
- **Time coverage**: Historical data only (forecasts in separate table)
- **Client isolation**: NEVER query without client_id filter

## Example User Questions Mapped to Queries

| User Question | Key Pattern | Notes |
|--------------|-------------|-------|
| "What is the market size for EVs in 2024?" | Pattern 1 | Filter by market_name and year |
| "Show me the top 10 countries by market value" | Pattern 2 | Use RANK() window function |
| "How has the smartphone market grown over time?" | Pattern 3 | Use LAG() for YoY calculations |
| "Break down the laptop market by price segment" | Pattern 4 | Join to segment dimensions |
| "Compare regions by total market value" | Pattern 5 | GROUP BY region |
| "Which are the largest markets globally?" | Pattern 6 | Aggregate across all dimensions |
| "Compare USA vs China for automotive" | Pattern 7 | Filter specific countries |
| "Show emerging markets performance" | Pattern 8 | Use is_emerging_market flag |

