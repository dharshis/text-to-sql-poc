# EM Market - Common Query Patterns

This document provides reusable SQL query templates for common business questions.

---

## TIME-BASED QUERIES

### Latest Year Data
```sql
-- Pattern: Get most recent year's data for any market
SELECT 
    m.market_name,
    g.country,
    t.year,
    SUM(fms.market_value_usd_m) AS market_value_usd_m
FROM fact_market_size fms
INNER JOIN dim_markets m ON fms.market_id = m.market_id
INNER JOIN dim_geography g ON fms.geo_id = g.geo_id
INNER JOIN dim_time t ON fms.time_id = t.time_id
WHERE fms.client_id = {{client_id}}
    AND t.year = (SELECT MAX(year) FROM dim_time WHERE is_forecast = 0)
    AND m.market_name = '{{market_name}}'
GROUP BY m.market_name, g.country, t.year;
```

### Year-Over-Year Growth
```sql
-- Pattern: Calculate YoY growth rate
WITH yearly_values AS (
    SELECT 
        t.year,
        SUM(fms.market_value_usd_m) AS market_value
    FROM fact_market_size fms
    INNER JOIN dim_time t ON fms.time_id = t.time_id
    WHERE fms.client_id = {{client_id}}
        AND fms.market_id = '{{market_id}}'
        AND fms.geo_id = '{{geo_id}}'
    GROUP BY t.year
)
SELECT 
    current.year,
    current.market_value AS current_year_value,
    previous.market_value AS previous_year_value,
    ROUND(
        ((current.market_value - previous.market_value) / previous.market_value * 100), 
        2
    ) AS yoy_growth_pct
FROM yearly_values current
LEFT JOIN yearly_values previous ON current.year = previous.year + 1
WHERE previous.market_value IS NOT NULL
ORDER BY current.year;
```

### Time Series Trend
```sql
-- Pattern: Multi-year trend analysis
SELECT 
    t.year,
    SUM(fms.market_value_usd_m) AS market_value_usd_m,
    SUM(fms.market_volume_units) AS market_volume_units
FROM fact_market_size fms
INNER JOIN dim_time t ON fms.time_id = t.time_id
WHERE fms.client_id = {{client_id}}
    AND fms.market_id = '{{market_id}}'
    AND t.year BETWEEN {{start_year}} AND {{end_year}}
    AND t.is_forecast = 0
GROUP BY t.year
ORDER BY t.year;
```

---

## GEOGRAPHIC QUERIES

### Country Ranking
```sql
-- Pattern: Rank countries by market value
SELECT 
    g.country,
    g.region,
    SUM(fms.market_value_usd_m) AS total_market_value,
    RANK() OVER (ORDER BY SUM(fms.market_value_usd_m) DESC) AS country_rank
FROM fact_market_size fms
INNER JOIN dim_geography g ON fms.geo_id = g.geo_id
INNER JOIN dim_time t ON fms.time_id = t.time_id
WHERE fms.client_id = {{client_id}}
    AND t.year = {{year}}
    AND fms.market_id = '{{market_id}}'
GROUP BY g.country, g.region
ORDER BY total_market_value DESC
LIMIT {{limit}};
```

### Regional Aggregation
```sql
-- Pattern: Aggregate by region
SELECT 
    g.region,
    COUNT(DISTINCT g.country) AS num_countries,
    SUM(fms.market_value_usd_m) AS total_market_value,
    AVG(fms.market_value_usd_m) AS avg_market_value_per_country
FROM fact_market_size fms
INNER JOIN dim_geography g ON fms.geo_id = g.geo_id
INNER JOIN dim_time t ON fms.time_id = t.time_id
WHERE fms.client_id = {{client_id}}
    AND t.year = {{year}}
GROUP BY g.region
ORDER BY total_market_value DESC;
```

### Multi-Country Comparison
```sql
-- Pattern: Compare specific countries
SELECT 
    g.country,
    t.year,
    SUM(fms.market_value_usd_m) AS market_value_usd_m,
    SUM(fms.market_volume_units) AS market_volume_units
FROM fact_market_size fms
INNER JOIN dim_geography g ON fms.geo_id = g.geo_id
INNER JOIN dim_time t ON fms.time_id = t.time_id
WHERE fms.client_id = {{client_id}}
    AND g.country IN ({{country_list}})  -- e.g., 'United States', 'China', 'Germany'
    AND fms.market_id = '{{market_id}}'
    AND t.year = {{year}}
GROUP BY g.country, t.year
ORDER BY market_value_usd_m DESC;
```

### Emerging Markets
```sql
-- Pattern: Filter emerging markets
SELECT 
    g.country,
    g.region,
    SUM(fms.market_value_usd_m) AS market_value_usd_m,
    g.is_emerging_market
FROM fact_market_size fms
INNER JOIN dim_geography g ON fms.geo_id = g.geo_id
INNER JOIN dim_time t ON fms.time_id = t.time_id
WHERE fms.client_id = {{client_id}}
    AND g.is_emerging_market = 1
    AND t.year = {{year}}
GROUP BY g.country, g.region, g.is_emerging_market
ORDER BY market_value_usd_m DESC;
```

---

## MARKET QUERIES

### Top Markets by Value
```sql
-- Pattern: Find largest markets
SELECT 
    m.market_name,
    m.naics_code,
    parent.market_name AS parent_market,
    SUM(fms.market_value_usd_m) AS total_value_usd_m,
    COUNT(DISTINCT fms.geo_id) AS num_geographies
FROM fact_market_size fms
INNER JOIN dim_markets m ON fms.market_id = m.market_id
LEFT JOIN dim_markets parent ON m.parent_market_id = parent.market_id
INNER JOIN dim_time t ON fms.time_id = t.time_id
WHERE fms.client_id = {{client_id}}
    AND t.year = {{year}}
    AND fms.market_value_usd_m IS NOT NULL
GROUP BY m.market_name, m.naics_code, parent.market_name
ORDER BY total_value_usd_m DESC
LIMIT {{limit}};
```

### Market Hierarchy
```sql
-- Pattern: Show market parent-child relationships
SELECT 
    parent.market_name AS parent_market,
    child.market_name AS child_market,
    child.definition AS child_definition,
    COUNT(fms.record_id) AS data_point_count
FROM dim_markets parent
INNER JOIN dim_markets child ON parent.market_id = child.parent_market_id
LEFT JOIN fact_market_size fms ON child.market_id = fms.market_id 
    AND fms.client_id = {{client_id}}
WHERE parent.client_id = {{client_id}}
GROUP BY parent.market_name, child.market_name, child.definition
ORDER BY parent.market_name, data_point_count DESC;
```

### Market Search
```sql
-- Pattern: Fuzzy search for markets
SELECT 
    market_id,
    market_name,
    definition,
    naics_code,
    parent_market_id
FROM dim_markets
WHERE client_id = {{client_id}}
    AND (
        market_name LIKE '%{{search_term}}%'
        OR definition LIKE '%{{search_term}}%'
    )
ORDER BY market_name;
```

---

## SEGMENTATION QUERIES

### Market by Segment
```sql
-- Pattern: Break down market by segment
SELECT 
    st.segment_name,
    sv.value_name AS segment_value,
    SUM(fms.market_value_usd_m) AS segment_market_value,
    ROUND(
        SUM(fms.market_value_usd_m) * 100.0 / 
        SUM(SUM(fms.market_value_usd_m)) OVER (), 
        2
    ) AS percentage_share
FROM fact_market_size fms
INNER JOIN dim_segment_values sv ON fms.segment_value_id = sv.segment_value_id
INNER JOIN dim_segment_types st ON sv.segment_type_id = st.segment_type_id
INNER JOIN dim_time t ON fms.time_id = t.time_id
WHERE fms.client_id = {{client_id}}
    AND fms.market_id = '{{market_id}}'
    AND t.year = {{year}}
    AND fms.market_value_usd_m IS NOT NULL
GROUP BY st.segment_name, sv.value_name
ORDER BY segment_market_value DESC;
```

### Segment Trend Over Time
```sql
-- Pattern: Track segment performance across years
SELECT 
    t.year,
    sv.value_name AS segment,
    SUM(fms.market_value_usd_m) AS market_value_usd_m
FROM fact_market_size fms
INNER JOIN dim_segment_values sv ON fms.segment_value_id = sv.segment_value_id
INNER JOIN dim_time t ON fms.time_id = t.time_id
WHERE fms.client_id = {{client_id}}
    AND fms.market_id = '{{market_id}}'
    AND t.year BETWEEN {{start_year}} AND {{end_year}}
GROUP BY t.year, sv.value_name
ORDER BY t.year, market_value_usd_m DESC;
```

---

## FORECAST QUERIES

### Market Forecast
```sql
-- Pattern: Get forecast projections
SELECT 
    m.market_name,
    g.country,
    t.year,
    ff.forecast_value_usd_m,
    ff.cagr,
    ff.scenario
FROM fact_forecasts ff
INNER JOIN dim_markets m ON ff.market_id = m.market_id
INNER JOIN dim_geography g ON ff.geo_id = g.geo_id
INNER JOIN dim_time t ON ff.time_id = t.time_id
WHERE ff.client_id = {{client_id}}
    AND m.market_name = '{{market_name}}'
    AND g.country = '{{country}}'
    AND t.year >= {{forecast_start_year}}
    AND ff.scenario = '{{scenario}}'  -- base_case, optimistic, pessimistic
ORDER BY t.year;
```

### Historical + Forecast Combined
```sql
-- Pattern: Show historical and forecast together
SELECT 
    t.year,
    'Historical' AS data_type,
    SUM(fms.market_value_usd_m) AS market_value_usd_m,
    NULL AS cagr
FROM fact_market_size fms
INNER JOIN dim_time t ON fms.time_id = t.time_id
WHERE fms.client_id = {{client_id}}
    AND fms.market_id = '{{market_id}}'
    AND fms.geo_id = '{{geo_id}}'
    AND t.is_forecast = 0
GROUP BY t.year

UNION ALL

SELECT 
    t.year,
    'Forecast' AS data_type,
    ff.forecast_value_usd_m,
    ff.cagr
FROM fact_forecasts ff
INNER JOIN dim_time t ON ff.time_id = t.time_id
WHERE ff.client_id = {{client_id}}
    AND ff.market_id = '{{market_id}}'
    AND ff.geo_id = '{{geo_id}}'
    AND ff.scenario = 'base_case'

ORDER BY year;
```

### Highest CAGR Markets
```sql
-- Pattern: Find fastest growing markets
SELECT 
    m.market_name,
    g.country,
    AVG(ff.cagr) AS avg_cagr,
    MIN(t.year) AS forecast_start,
    MAX(t.year) AS forecast_end
FROM fact_forecasts ff
INNER JOIN dim_markets m ON ff.market_id = m.market_id
INNER JOIN dim_geography g ON ff.geo_id = g.geo_id
INNER JOIN dim_time t ON ff.time_id = t.time_id
WHERE ff.client_id = {{client_id}}
    AND ff.scenario = 'base_case'
    AND ff.cagr IS NOT NULL
GROUP BY m.market_name, g.country
HAVING AVG(ff.cagr) > {{minimum_cagr}}  -- e.g., 5.0 for 5%+
ORDER BY avg_cagr DESC
LIMIT {{limit}};
```

---

## MULTI-DIMENSIONAL QUERIES

### Market × Geography × Time Cube
```sql
-- Pattern: Full dimensional analysis
SELECT 
    m.market_name,
    g.country,
    g.region,
    t.year,
    SUM(fms.market_value_usd_m) AS market_value_usd_m,
    SUM(fms.market_volume_units) AS market_volume_units,
    COUNT(*) AS record_count
FROM fact_market_size fms
INNER JOIN dim_markets m ON fms.market_id = m.market_id
INNER JOIN dim_geography g ON fms.geo_id = g.geo_id
INNER JOIN dim_time t ON fms.time_id = t.time_id
WHERE fms.client_id = {{client_id}}
    AND t.year BETWEEN {{start_year}} AND {{end_year}}
    AND fms.market_value_usd_m IS NOT NULL
GROUP BY m.market_name, g.country, g.region, t.year
ORDER BY t.year DESC, market_value_usd_m DESC;
```

### Market Share Analysis
```sql
-- Pattern: Calculate market share by segment/geography
WITH total_market AS (
    SELECT 
        SUM(market_value_usd_m) AS total_value
    FROM fact_market_size
    WHERE client_id = {{client_id}}
        AND market_id = '{{market_id}}'
        AND year = {{year}}
),
segment_values AS (
    SELECT 
        g.country,
        sv.value_name,
        SUM(fms.market_value_usd_m) AS segment_value
    FROM fact_market_size fms
    INNER JOIN dim_geography g ON fms.geo_id = g.geo_id
    INNER JOIN dim_segment_values sv ON fms.segment_value_id = sv.segment_value_id
    WHERE fms.client_id = {{client_id}}
        AND fms.market_id = '{{market_id}}'
        AND fms.year = {{year}}
    GROUP BY g.country, sv.value_name
)
SELECT 
    sv.country,
    sv.value_name,
    sv.segment_value,
    tm.total_value,
    ROUND((sv.segment_value / tm.total_value * 100), 2) AS market_share_pct
FROM segment_values sv
CROSS JOIN total_market tm
ORDER BY market_share_pct DESC;
```

---

## TEMPLATE VARIABLE REFERENCE

| Variable | Type | Example | Description |
|----------|------|---------|-------------|
| `{{client_id}}` | INTEGER | 1 | Current client identifier (REQUIRED) |
| `{{market_id}}` | VARCHAR | 'MKT001' | Market identifier from dim_markets |
| `{{market_name}}` | VARCHAR | 'Electric Vehicles' | Market display name |
| `{{geo_id}}` | VARCHAR | 'GEO_USA' | Geography identifier |
| `{{country}}` | VARCHAR | 'United States' | Country name (full text) |
| `{{country_list}}` | VARCHAR[] | 'USA', 'CHN', 'DEU' | Comma-separated country names |
| `{{region}}` | VARCHAR | 'North America' | Region name |
| `{{year}}` | INTEGER | 2024 | Specific year |
| `{{start_year}}` | INTEGER | 2020 | Range start year |
| `{{end_year}}` | INTEGER | 2024 | Range end year |
| `{{segment_value_id}}` | VARCHAR | 'SEG001' | Segment value identifier |
| `{{search_term}}` | VARCHAR | 'electric' | Text search term |
| `{{limit}}` | INTEGER | 10 | Result limit (default: 100) |
| `{{minimum_cagr}}` | DECIMAL | 5.0 | Minimum growth rate threshold |
| `{{scenario}}` | VARCHAR | 'base_case' | Forecast scenario |

---

## BEST PRACTICES

1. **Always include `client_id` filter** - Required for data isolation
2. **Filter NULL values in aggregations** - `WHERE market_value_usd_m IS NOT NULL`
3. **Use indexed columns in WHERE** - market_id, geo_id, year, client_id
4. **Specify year explicitly** - Don't assume default year
5. **Use INNER JOIN for required dimensions** - markets, geography, time
6. **Use LEFT JOIN for optional dimensions** - segments, currency
7. **Include units in column aliases** - `market_value_usd_m`, not just `value`
8. **Limit results appropriately** - Use LIMIT for detail queries
9. **Order results logically** - By most relevant dimension first
10. **Handle NULL parent markets** - Use LEFT JOIN for hierarchy

