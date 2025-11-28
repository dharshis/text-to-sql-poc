# EM Market - Common Query Patterns

This document provides reusable SQL query templates for the em_market database.

**Database**: `em_market.db`  
**Schema**: Star schema with Sales & Market Summary facts  
**Primary Use Case**: FMCG/CPG brand performance and market share analysis

---

## SALES ANALYSIS QUERIES

### Pattern 1: Total Sales by Country
```sql
-- Get total sales value and volume by country
SELECT 
    g.country_name,
    g.region_name,
    COUNT(*) AS transaction_count,
    SUM(fst.units_sold) AS total_units,
    SUM(fst.volume_sold_std) AS total_volume_std,
    SUM(fst.value_sold_usd) AS total_value_usd,
    ROUND(AVG(fst.value_sold_usd), 2) AS avg_transaction_value
FROM Fact_Sales_Transactions fst
INNER JOIN Dim_Geography g ON fst.geo_id = g.geo_id
WHERE fst.period_id BETWEEN {{start_period}} AND {{end_period}}
GROUP BY g.country_name, g.region_name
ORDER BY total_value_usd DESC
LIMIT {{limit}};
```

**Variables**: 
- `{{start_period}}` - Start period (YYYYMM format, e.g., 202201)
- `{{end_period}}` - End period (YYYYMM format, e.g., 202212)
- `{{limit}}` - Number of results (default: 10)

**Example**: "Show me top 10 countries by sales in 2023"

---

### Pattern 2: Brand Performance Report
```sql
-- Brand sales with hierarchy (Corporation > Brand > SubBrand)
SELECT 
    c.corporation_name,
    b.brand_name,
    b.price_segment,
    sb.sub_brand_name,
    COUNT(DISTINCT fst.sku_id) AS sku_count,
    SUM(fst.units_sold) AS total_units,
    SUM(fst.value_sold_usd) AS total_value_usd,
    ROUND(SUM(fst.value_sold_usd) * 100.0 / 
        (SELECT SUM(value_sold_usd) FROM Fact_Sales_Transactions 
         WHERE period_id BETWEEN {{start_period}} AND {{end_period}}), 2
    ) AS value_share_pct
FROM Fact_Sales_Transactions fst
INNER JOIN Dim_Product_SKU ps ON fst.sku_id = ps.sku_id
INNER JOIN Dim_SubBrand sb ON ps.subbrand_id = sb.subbrand_id
INNER JOIN Dim_Brand b ON sb.brand_id = b.brand_id
INNER JOIN Dim_Corporation c ON b.corp_id = c.corp_id
WHERE fst.period_id BETWEEN {{start_period}} AND {{end_period}}
GROUP BY c.corporation_name, b.brand_name, b.price_segment, sb.sub_brand_name
ORDER BY total_value_usd DESC
LIMIT {{limit}};
```

**Variables**: 
- `{{start_period}}`, `{{end_period}}`, `{{limit}}`

**Example**: "Show me top brands by sales"

---

### Pattern 3: Product Category Performance
```sql
-- Sales by product category
SELECT 
    ps.category_name,
    COUNT(DISTINCT ps.sku_id) AS unique_skus,
    COUNT(*) AS transaction_count,
    SUM(fst.units_sold) AS total_units,
    SUM(fst.volume_sold_std) AS total_volume_std,
    SUM(fst.value_sold_usd) AS total_value_usd,
    ROUND(AVG(fst.value_sold_usd / fst.units_sold), 2) AS avg_price_per_unit
FROM Fact_Sales_Transactions fst
INNER JOIN Dim_Product_SKU ps ON fst.sku_id = ps.sku_id
WHERE fst.period_id BETWEEN {{start_period}} AND {{end_period}}
GROUP BY ps.category_name
ORDER BY total_value_usd DESC;
```

**Example**: "What are the top product categories?"

---

### Pattern 4: Regional Sales Breakdown
```sql
-- Sales aggregated by region
SELECT 
    g.region_name,
    COUNT(DISTINCT g.country_name) AS country_count,
    COUNT(*) AS transaction_count,
    SUM(fst.value_sold_usd) AS total_value_usd,
    ROUND(AVG(fst.value_sold_usd), 2) AS avg_transaction_value,
    ROUND(SUM(fst.value_sold_usd) * 100.0 / 
        (SELECT SUM(value_sold_usd) FROM Fact_Sales_Transactions 
         WHERE period_id BETWEEN {{start_period}} AND {{end_period}}), 2
    ) AS region_value_share_pct
FROM Fact_Sales_Transactions fst
INNER JOIN Dim_Geography g ON fst.geo_id = g.geo_id
WHERE fst.period_id BETWEEN {{start_period}} AND {{end_period}}
GROUP BY g.region_name
ORDER BY total_value_usd DESC;
```

**Example**: "Compare sales across regions"

---

## TIME-BASED ANALYSIS

### Pattern 5: Monthly Sales Trend
```sql
-- Sales trend over time (monthly)
SELECT 
    p.period_id,
    p.fiscal_year,
    p.quarter,
    p.month_name,
    COUNT(*) AS transaction_count,
    SUM(fst.value_sold_usd) AS total_value_usd,
    SUM(fst.volume_sold_std) AS total_volume_std
FROM Fact_Sales_Transactions fst
INNER JOIN Dim_Period p ON fst.period_id = p.period_id
WHERE p.fiscal_year = {{year}}
GROUP BY p.period_id, p.fiscal_year, p.quarter, p.month_name
ORDER BY p.period_id;
```

**Variables**: 
- `{{year}}` - Fiscal year (e.g., 2023)

**Example**: "Show monthly sales trend for 2023"

---

### Pattern 6: Year-Over-Year Growth
```sql
-- YoY growth calculation
WITH monthly_sales AS (
    SELECT 
        p.fiscal_year,
        p.month_name,
        SUM(fst.value_sold_usd) AS total_value_usd
    FROM Fact_Sales_Transactions fst
    INNER JOIN Dim_Period p ON fst.period_id = p.period_id
    WHERE p.fiscal_year IN ({{year}}, {{year}} - 1)
    GROUP BY p.fiscal_year, p.month_name
)
SELECT 
    current.month_name,
    current.total_value_usd AS current_year_value,
    previous.total_value_usd AS previous_year_value,
    ROUND((current.total_value_usd - previous.total_value_usd), 2) AS absolute_growth,
    ROUND(((current.total_value_usd - previous.total_value_usd) / 
           previous.total_value_usd * 100), 2) AS yoy_growth_pct
FROM monthly_sales current
LEFT JOIN monthly_sales previous 
    ON current.month_name = previous.month_name 
    AND current.fiscal_year = previous.fiscal_year + 1
WHERE current.fiscal_year = {{year}}
ORDER BY current.month_name;
```

**Example**: "Show year-over-year growth for 2023"

---

### Pattern 7: Quarterly Performance
```sql
-- Quarterly sales aggregation
SELECT 
    p.fiscal_year,
    p.quarter,
    COUNT(*) AS transaction_count,
    SUM(fst.units_sold) AS total_units,
    SUM(fst.value_sold_usd) AS total_value_usd,
    ROUND(AVG(fst.value_sold_usd), 2) AS avg_transaction_value
FROM Fact_Sales_Transactions fst
INNER JOIN Dim_Period p ON fst.period_id = p.period_id
WHERE p.fiscal_year BETWEEN {{start_year}} AND {{end_year}}
GROUP BY p.fiscal_year, p.quarter
ORDER BY p.fiscal_year, p.quarter;
```

**Example**: "Show quarterly sales breakdown"

---

## MARKET SHARE ANALYSIS

### Pattern 8: Brand Market Share Calculation
```sql
-- Calculate brand value share using numerator/denominator approach
WITH brand_sales AS (
    SELECT 
        fst.geo_id,
        b.brand_name,
        SUM(fst.value_sold_usd) AS brand_value
    FROM Fact_Sales_Transactions fst
    INNER JOIN Dim_Product_SKU ps ON fst.sku_id = ps.sku_id
    INNER JOIN Dim_SubBrand sb ON ps.subbrand_id = sb.subbrand_id
    INNER JOIN Dim_Brand b ON sb.brand_id = b.brand_id
    WHERE fst.period_id BETWEEN {{start_period}} AND {{end_period}}
    GROUP BY fst.geo_id, b.brand_name
),
market_totals AS (
    SELECT 
        fms.geo_id,
        SUM(fms.total_market_value_usd) AS market_total_value
    FROM Fact_Market_Summary fms
    WHERE fms.period_id BETWEEN {{start_period}} AND {{end_period}}
    GROUP BY fms.geo_id
)
SELECT 
    g.country_name,
    bs.brand_name,
    bs.brand_value AS numerator,
    mt.market_total_value AS denominator,
    ROUND((bs.brand_value / mt.market_total_value * 100), 2) AS value_share_pct
FROM brand_sales bs
INNER JOIN market_totals mt ON bs.geo_id = mt.geo_id
INNER JOIN Dim_Geography g ON bs.geo_id = g.geo_id
WHERE mt.market_total_value > 0
ORDER BY value_share_pct DESC
LIMIT {{limit}};
```

**Example**: "Calculate market share for top brands"

---

### Pattern 9: Volume Share by Product
```sql
-- Volume-based market share
WITH product_volume AS (
    SELECT 
        ps.category_name,
        SUM(fst.volume_sold_std) AS product_volume
    FROM Fact_Sales_Transactions fst
    INNER JOIN Dim_Product_SKU ps ON fst.sku_id = ps.sku_id
    WHERE fst.period_id BETWEEN {{start_period}} AND {{end_period}}
    GROUP BY ps.category_name
),
market_volume AS (
    SELECT 
        SUM(fms.total_market_volume_std) AS total_volume
    FROM Fact_Market_Summary fms
    WHERE fms.period_id BETWEEN {{start_period}} AND {{end_period}}
)
SELECT 
    pv.category_name,
    pv.product_volume,
    mv.total_volume,
    ROUND((pv.product_volume / mv.total_volume * 100), 2) AS volume_share_pct
FROM product_volume pv
CROSS JOIN market_volume mv
WHERE mv.total_volume > 0
ORDER BY volume_share_pct DESC;
```

**Example**: "Show volume market share by category"

---

## PROMOTIONAL ANALYSIS

### Pattern 10: Promotion Effectiveness
```sql
-- Compare promotional vs non-promotional sales
SELECT 
    CASE WHEN fst.is_promotion = 1 THEN 'Promotional' ELSE 'Regular Price' END AS sale_type,
    COUNT(*) AS transaction_count,
    SUM(fst.units_sold) AS total_units,
    SUM(fst.value_sold_usd) AS total_value_usd,
    ROUND(AVG(fst.value_sold_usd / fst.units_sold), 2) AS avg_price_per_unit,
    ROUND(SUM(fst.value_sold_usd) * 100.0 / 
        (SELECT SUM(value_sold_usd) FROM Fact_Sales_Transactions 
         WHERE period_id BETWEEN {{start_period}} AND {{end_period}}), 2
    ) AS value_contribution_pct
FROM Fact_Sales_Transactions fst
WHERE fst.period_id BETWEEN {{start_period}} AND {{end_period}}
GROUP BY fst.is_promotion
ORDER BY total_value_usd DESC;
```

**Example**: "How effective are promotions?"

---

### Pattern 11: Brand Promotional Mix
```sql
-- Promotional vs regular price sales by brand
SELECT 
    b.brand_name,
    SUM(CASE WHEN fst.is_promotion = 1 THEN fst.value_sold_usd ELSE 0 END) AS promo_value,
    SUM(CASE WHEN fst.is_promotion = 0 THEN fst.value_sold_usd ELSE 0 END) AS regular_value,
    SUM(fst.value_sold_usd) AS total_value,
    ROUND(SUM(CASE WHEN fst.is_promotion = 1 THEN fst.value_sold_usd ELSE 0 END) * 100.0 / 
          SUM(fst.value_sold_usd), 2) AS promo_mix_pct
FROM Fact_Sales_Transactions fst
INNER JOIN Dim_Product_SKU ps ON fst.sku_id = ps.sku_id
INNER JOIN Dim_SubBrand sb ON ps.subbrand_id = sb.subbrand_id
INNER JOIN Dim_Brand b ON sb.brand_id = b.brand_id
WHERE fst.period_id BETWEEN {{start_period}} AND {{end_period}}
GROUP BY b.brand_name
HAVING total_value > 0
ORDER BY promo_mix_pct DESC
LIMIT {{limit}};
```

**Example**: "Which brands rely most on promotions?"

---

## DISTRIBUTION ANALYSIS

### Pattern 12: Distribution Points Performance
```sql
-- Sales by distribution coverage level
SELECT 
    CASE 
        WHEN fst.distribution_points < 25 THEN '< 25 points (Low)'
        WHEN fst.distribution_points < 50 THEN '25-49 points (Medium)'
        WHEN fst.distribution_points < 75 THEN '50-74 points (High)'
        ELSE '75+ points (Very High)'
    END AS distribution_level,
    COUNT(*) AS transaction_count,
    SUM(fst.value_sold_usd) AS total_value_usd,
    ROUND(AVG(fst.distribution_points), 1) AS avg_distribution_points,
    ROUND(AVG(fst.value_sold_usd), 2) AS avg_transaction_value
FROM Fact_Sales_Transactions fst
WHERE fst.period_id BETWEEN {{start_period}} AND {{end_period}}
GROUP BY distribution_level
ORDER BY avg_distribution_points;
```

**Example**: "How does distribution affect sales?"

---

## PRODUCT ANALYSIS

### Pattern 13: Top SKUs by Sales
```sql
-- Top-selling SKUs with full product details
SELECT 
    ps.sku_id,
    ps.sku_description,
    ps.category_name,
    ps.pack_size_value || ps.pack_size_unit AS package_size,
    b.brand_name,
    sb.sub_brand_name,
    COUNT(*) AS transaction_count,
    SUM(fst.units_sold) AS total_units,
    SUM(fst.value_sold_usd) AS total_value_usd,
    ROUND(AVG(fst.value_sold_usd / fst.units_sold), 2) AS avg_price_per_unit
FROM Fact_Sales_Transactions fst
INNER JOIN Dim_Product_SKU ps ON fst.sku_id = ps.sku_id
INNER JOIN Dim_SubBrand sb ON ps.subbrand_id = sb.subbrand_id
INNER JOIN Dim_Brand b ON sb.brand_id = b.brand_id
WHERE fst.period_id BETWEEN {{start_period}} AND {{end_period}}
GROUP BY ps.sku_id, ps.sku_description, ps.category_name, 
         package_size, b.brand_name, sb.sub_brand_name
ORDER BY total_value_usd DESC
LIMIT {{limit}};
```

**Example**: "Show top 20 selling products"

---

### Pattern 14: Package Size Analysis
```sql
-- Sales by package size/format
SELECT 
    ps.pack_size_value || ps.pack_size_unit AS package_size,
    ps.pack_type,
    ps.form_factor,
    COUNT(DISTINCT ps.sku_id) AS sku_count,
    SUM(fst.units_sold) AS total_units,
    SUM(fst.value_sold_usd) AS total_value_usd,
    ROUND(AVG(fst.value_sold_usd / fst.units_sold), 2) AS avg_price_per_unit
FROM Fact_Sales_Transactions fst
INNER JOIN Dim_Product_SKU ps ON fst.sku_id = ps.sku_id
WHERE fst.period_id BETWEEN {{start_period}} AND {{end_period}}
  AND ps.category_name = '{{category}}'
GROUP BY package_size, ps.pack_type, ps.form_factor
ORDER BY total_value_usd DESC;
```

**Variables**: 
- `{{category}}` - Product category name

**Example**: "What package sizes sell best in Hair Care?"

---

## PRICE SEGMENT ANALYSIS

### Pattern 15: Performance by Price Tier
```sql
-- Sales by brand price segment
SELECT 
    b.price_segment,
    COUNT(DISTINCT b.brand_id) AS brand_count,
    COUNT(*) AS transaction_count,
    SUM(fst.value_sold_usd) AS total_value_usd,
    ROUND(AVG(fst.value_sold_usd / fst.units_sold), 2) AS avg_price_per_unit,
    ROUND(SUM(fst.value_sold_usd) * 100.0 / 
        (SELECT SUM(value_sold_usd) FROM Fact_Sales_Transactions 
         WHERE period_id BETWEEN {{start_period}} AND {{end_period}}), 2
    ) AS value_share_pct
FROM Fact_Sales_Transactions fst
INNER JOIN Dim_Product_SKU ps ON fst.sku_id = ps.sku_id
INNER JOIN Dim_SubBrand sb ON ps.subbrand_id = sb.subbrand_id
INNER JOIN Dim_Brand b ON sb.brand_id = b.brand_id
WHERE fst.period_id BETWEEN {{start_period}} AND {{end_period}}
GROUP BY b.price_segment
ORDER BY total_value_usd DESC;
```

**Example**: "Compare Premium vs Mass Market performance"

---

## GEOGRAPHIC COMPARISONS

### Pattern 16: Country-to-Country Comparison
```sql
-- Compare specific countries
SELECT 
    g.country_name,
    g.currency_code,
    COUNT(*) AS transaction_count,
    SUM(fst.units_sold) AS total_units,
    SUM(fst.value_sold_local) AS total_value_local,
    SUM(fst.value_sold_usd) AS total_value_usd,
    ROUND(AVG(fst.value_sold_usd), 2) AS avg_transaction_value,
    g.currency_exchange_rate
FROM Fact_Sales_Transactions fst
INNER JOIN Dim_Geography g ON fst.geo_id = g.geo_id
WHERE fst.period_id BETWEEN {{start_period}} AND {{end_period}}
  AND g.country_name IN ({{country_list}})
GROUP BY g.country_name, g.currency_code, g.currency_exchange_rate
ORDER BY total_value_usd DESC;
```

**Variables**: 
- `{{country_list}}` - Comma-separated list (e.g., 'USA', 'United Kingdom', 'Germany')

**Example**: "Compare USA vs UK vs Germany"

---

## VIEW-BASED QUERIES

### Pattern 17: Using Sales Detail View
```sql
-- Simplified query using pre-built view
SELECT 
    country_name,
    region_name,
    brand_name,
    sub_brand_name,
    category_name,
    COUNT(*) AS transaction_count,
    SUM(units_sold) AS total_units,
    SUM(value_sold_usd) AS total_value_usd
FROM vw_sales_detail
WHERE period_id BETWEEN {{start_period}} AND {{end_period}}
GROUP BY country_name, region_name, brand_name, sub_brand_name, category_name
ORDER BY total_value_usd DESC
LIMIT {{limit}};
```

**Note**: Views simplify queries by pre-joining dimensions

**Example**: "Show me sales breakdown by brand and country"

---

### Pattern 18: Using Market Summary View
```sql
-- Market totals using view
SELECT 
    country_name,
    region_name,
    market_name,
    market_category,
    SUM(total_market_value_usd) AS market_value,
    SUM(total_market_volume_std) AS market_volume
FROM vw_market_summary
WHERE period_id BETWEEN {{start_period}} AND {{end_period}}
GROUP BY country_name, region_name, market_name, market_category
ORDER BY market_value DESC
LIMIT {{limit}};
```

**Example**: "What are the total market sizes by country?"

---

## ADVANCED ANALYSIS

### Pattern 19: Basket Analysis
```sql
-- Find products often sold in same period/geography
SELECT 
    ps1.sku_description AS product_1,
    ps2.sku_description AS product_2,
    COUNT(*) AS co_occurrence_count,
    SUM(fst1.value_sold_usd + fst2.value_sold_usd) AS combined_value
FROM Fact_Sales_Transactions fst1
INNER JOIN Fact_Sales_Transactions fst2 
    ON fst1.period_id = fst2.period_id 
    AND fst1.geo_id = fst2.geo_id
    AND fst1.sku_id < fst2.sku_id
INNER JOIN Dim_Product_SKU ps1 ON fst1.sku_id = ps1.sku_id
INNER JOIN Dim_Product_SKU ps2 ON fst2.sku_id = ps2.sku_id
WHERE fst1.period_id BETWEEN {{start_period}} AND {{end_period}}
GROUP BY ps1.sku_description, ps2.sku_description
HAVING co_occurrence_count > 5
ORDER BY co_occurrence_count DESC
LIMIT {{limit}};
```

**Example**: "Which products are sold together?"

---

### Pattern 20: Currency Impact Analysis
```sql
-- Analyze local currency vs USD values
SELECT 
    g.country_name,
    g.currency_code,
    g.currency_exchange_rate,
    SUM(fst.value_sold_local) AS total_local_currency,
    SUM(fst.value_sold_usd) AS total_usd,
    ROUND(SUM(fst.value_sold_local) / COUNT(*), 2) AS avg_local_per_transaction,
    ROUND(SUM(fst.value_sold_usd) / COUNT(*), 2) AS avg_usd_per_transaction
FROM Fact_Sales_Transactions fst
INNER JOIN Dim_Geography g ON fst.geo_id = g.geo_id
WHERE fst.period_id BETWEEN {{start_period}} AND {{end_period}}
GROUP BY g.country_name, g.currency_code, g.currency_exchange_rate
ORDER BY total_usd DESC;
```

**Example**: "Show sales in local currency and USD"

---

## TEMPLATE VARIABLE REFERENCE

| Variable | Type | Example | Description |
|----------|------|---------|-------------|
| `{{start_period}}` | INTEGER | 202201 | Start period (YYYYMM format) |
| `{{end_period}}` | INTEGER | 202212 | End period (YYYYMM format) |
| `{{year}}` | INTEGER | 2023 | Fiscal year |
| `{{start_year}}` | INTEGER | 2022 | Start year for range |
| `{{end_year}}` | INTEGER | 2023 | End year for range |
| `{{limit}}` | INTEGER | 10 | Result limit (default: 10) |
| `{{country_list}}` | VARCHAR[] | 'USA', 'UK' | Comma-separated country names |
| `{{category}}` | VARCHAR | 'Hair Care' | Product category name |

---

## COMMON FILTERS

### By Time Period
```sql
WHERE p.period_id = 202312  -- Specific month
WHERE p.period_id BETWEEN 202301 AND 202312  -- Year range
WHERE p.fiscal_year = 2023  -- Full year
WHERE p.quarter = 4  -- Specific quarter
```

### By Geography
```sql
WHERE g.country_name = 'USA'  -- Specific country
WHERE g.region_name = 'Europe'  -- Specific region
WHERE g.country_name IN ('USA', 'United Kingdom', 'Germany')  -- Multiple countries
```

### By Product
```sql
WHERE ps.category_name = 'Hair Care'  -- Specific category
WHERE b.brand_name = 'Dove'  -- Specific brand
WHERE b.price_segment = 'Premium'  -- Price segment
WHERE ps.pack_size_value >= 500  -- Package size filter
```

### By Promotion
```sql
WHERE fst.is_promotion = 1  -- Only promotional sales
WHERE fst.is_promotion = 0  -- Only regular price sales
```

---

## BEST PRACTICES

1. **Always use period filters** - Limit data range for performance
2. **Join to dimensions** - Use INNER JOIN for required, LEFT JOIN for optional
3. **Aggregate carefully** - Use SUM for values, COUNT for transactions
4. **Handle NULLs** - Filter where appropriate (e.g., `WHERE value > 0`)
5. **Use aliases** - Standard aliases: fst, g, p, ps, b, sb, c
6. **Limit results** - Use LIMIT for top N queries
7. **Consider indexes** - Queries use indexed columns (period_id, geo_id, sku_id)

---

## PERFORMANCE TIPS

- **Indexed columns**: period_id, geo_id, sku_id, brand_id, corp_id
- **Filter early**: Apply WHERE clauses on indexed columns first
- **Use views**: vw_sales_detail and vw_market_summary for common joins
- **Avoid wildcards**: Be specific in SELECT clauses
- **Batch periods**: Query by month/quarter for large date ranges

---

**Total Patterns**: 20  
**Covers**: Sales, Market Share, Promotions, Distribution, Products, Geography, Time Series  
**Database**: em_market.db (24,559 rows)
