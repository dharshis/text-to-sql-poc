# Dataset-Specific Instructions: Euromonitor Market Data

## Domain Context

**Business Domain:** Global market research for consumer goods (FMCG/CPG)

**Key Entity Hierarchy:**
```
Dim_Corporation (corp_id) ← FILTERING HAPPENS HERE
  └─ Dim_Brand (brand_id, corp_id FK)
      └─ Dim_SubBrand (subbrand_id, brand_id FK)
          └─ Dim_Product_SKU (sku_id, subbrand_id FK)
              └─ Fact_Sales_Transactions (sku_id FK)
```

**Critical**: All queries MUST filter by `corp_id` through the `Dim_Brand` table to enforce corporation-level data isolation.

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

### Example 2: Sales transactions with brand join
```sql
-- User asks: "Total sales by brand"
SELECT b.brand_name, SUM(f.value_sold_usd) as total_sales
FROM Fact_Sales_Transactions f
JOIN Dim_Product_SKU sku ON f.sku_id = sku.sku_id
JOIN Dim_SubBrand sb ON sku.subbrand_id = sb.subbrand_id
JOIN Dim_Brand b ON sb.brand_id = b.brand_id
WHERE b.corp_id = {client_id}
GROUP BY b.brand_name
ORDER BY total_sales DESC
```

### Example 3: Multi-table join with corp_id filter
```sql
-- User asks: "Sales by brand and country"
SELECT b.brand_name, g.country_name,
       SUM(f.value_sold_usd) as total_sales
FROM Fact_Sales_Transactions f
JOIN Dim_Product_SKU sku ON f.sku_id = sku.sku_id
JOIN Dim_SubBrand sb ON sku.subbrand_id = sb.subbrand_id
JOIN Dim_Brand b ON sb.brand_id = b.brand_id
JOIN Dim_Geography g ON f.geo_id = g.geo_id
WHERE b.corp_id = {client_id}
GROUP BY b.brand_name, g.country_name
ORDER BY total_sales DESC
LIMIT 20
```

## Domain-Specific Patterns

### Pattern 1: Time Range Queries
**Rule**: Use `Dim_Period.fiscal_year` for yearly analysis
**Rule**: For "last N years", use: `fiscal_year >= (SELECT MAX(fiscal_year) - N FROM Dim_Period)`
**Rule**: NEVER use CURRENT_DATE, NOW(), or system date functions

**Examples**:
```sql
-- Last 3 years of data
JOIN Dim_Period p ON f.period_id = p.period_id
WHERE p.fiscal_year >= (SELECT MAX(fiscal_year) - 2 FROM Dim_Period)

-- Latest available year
WHERE p.fiscal_year = (SELECT MAX(fiscal_year) FROM Dim_Period)

-- Specific year
WHERE p.fiscal_year = 2024
```

### Pattern 2: Geographic Filters
**Rule**: Join through Dim_Geography for country and regional data
**Rule**: Always include corp_id filter even with geography

**Examples**:
```sql
-- Specific country
JOIN Dim_Geography g ON f.geo_id = g.geo_id
WHERE g.country_name = 'United States'
  AND b.corp_id = {client_id}

-- Multiple countries
WHERE g.country_name IN ('United States', 'United Kingdom', 'Germany')

-- Regional analysis
WHERE g.region_name = 'North America'
```

### Pattern 3: Category Analysis
**Rule**: Dim_Product_SKU has category_name field for product categorization
**Rule**: Use for category-level grouping and filtering

**Examples**:
```sql
-- Category level
JOIN Dim_Product_SKU sku ON f.sku_id = sku.sku_id
WHERE sku.category_name = 'Soft Drinks'

-- Multiple categories
WHERE sku.category_name IN ('Soft Drinks', 'Juice', 'Water')
```

### Pattern 4: Product Hierarchy Navigation
**Rule**: Navigate from SKU → SubBrand → Brand → Corporation
**Rule**: ALWAYS join through this hierarchy to reach corp_id filter

**Example**:
```sql
-- Full hierarchy join for corp_id filtering
FROM Fact_Sales_Transactions f
JOIN Dim_Product_SKU sku ON f.sku_id = sku.sku_id
JOIN Dim_SubBrand sb ON sku.subbrand_id = sb.subbrand_id
JOIN Dim_Brand b ON sb.brand_id = b.brand_id
WHERE b.corp_id = {client_id}
```

## Common Table Relationships

```
Fact_Sales_Transactions:
  - period_id → Dim_Period (fiscal_year, quarter, month_name)
  - geo_id → Dim_Geography (country_name, region_name)
  - sku_id → Dim_Product_SKU (category_name, subbrand_id)
  - value_sold_usd (sales revenue in USD)
  - volume_sold_std (sales volume in standard units)
  - units_sold (number of units)
  - is_promotion (0 = regular, 1 = promotional)

Dim_Product_SKU:
  - sku_id (PK)
  - sku_description
  - subbrand_id → Dim_SubBrand
  - category_name
  - form_factor, pack_type, pack_size

Dim_SubBrand:
  - subbrand_id (PK)
  - subbrand_name
  - brand_id → Dim_Brand

Dim_Brand:
  - brand_id (PK)
  - brand_name
  - corp_id (FK to Dim_Corporation) ← FILTER BY THIS

Dim_Period:
  - period_id (PK)
  - fiscal_year (integer, e.g., 2024)
  - quarter (1-4)
  - month_name

Dim_Geography:
  - geo_id (PK)
  - country_name
  - region_name
  - currency_code
```

## Example Queries

### Query 1: Top 10 brands by sales value
```sql
-- Natural language: "Show me top 10 brands by sales"
SELECT b.brand_name, SUM(f.value_sold_usd) as total_sales
FROM Fact_Sales_Transactions f
JOIN Dim_Product_SKU sku ON f.sku_id = sku.sku_id
JOIN Dim_SubBrand sb ON sku.subbrand_id = sb.subbrand_id
JOIN Dim_Brand b ON sb.brand_id = b.brand_id
WHERE b.corp_id = {client_id}
GROUP BY b.brand_name
ORDER BY total_sales DESC
LIMIT 10
```

### Query 2: Geographic analysis - sales by country
```sql
-- Natural language: "Sales by country last 3 years"
SELECT g.country_name, p.fiscal_year, SUM(f.value_sold_usd) as total
FROM Fact_Sales_Transactions f
JOIN Dim_Product_SKU sku ON f.sku_id = sku.sku_id
JOIN Dim_SubBrand sb ON sku.subbrand_id = sb.subbrand_id
JOIN Dim_Brand b ON sb.brand_id = b.brand_id
JOIN Dim_Geography g ON f.geo_id = g.geo_id
JOIN Dim_Period p ON f.period_id = p.period_id
WHERE b.corp_id = {client_id}
  AND p.fiscal_year >= (SELECT MAX(fiscal_year) - 2 FROM Dim_Period)
GROUP BY g.country_name, p.fiscal_year
ORDER BY p.fiscal_year, total DESC
```

### Query 3: Category breakdown
```sql
-- Natural language: "Sales by category"
SELECT sku.category_name, SUM(f.value_sold_usd) as total_sales
FROM Fact_Sales_Transactions f
JOIN Dim_Product_SKU sku ON f.sku_id = sku.sku_id
JOIN Dim_SubBrand sb ON sku.subbrand_id = sb.subbrand_id
JOIN Dim_Brand b ON sb.brand_id = b.brand_id
WHERE b.corp_id = {client_id}
GROUP BY sku.category_name
ORDER BY total_sales DESC
```

### Query 4: Year-over-year growth
```sql
-- Natural language: "Show year over year sales growth"
SELECT b.brand_name, p.fiscal_year,
       SUM(f.value_sold_usd) as sales,
       LAG(SUM(f.value_sold_usd)) OVER (PARTITION BY b.brand_name ORDER BY p.fiscal_year) as prev_year_sales
FROM Fact_Sales_Transactions f
JOIN Dim_Product_SKU sku ON f.sku_id = sku.sku_id
JOIN Dim_SubBrand sb ON sku.subbrand_id = sb.subbrand_id
JOIN Dim_Brand b ON sb.brand_id = b.brand_id
JOIN Dim_Period p ON f.period_id = p.period_id
WHERE b.corp_id = {client_id}
GROUP BY b.brand_name, p.fiscal_year
ORDER BY b.brand_name, p.fiscal_year
```

### Query 5: Brand performance in specific geography
```sql
-- Natural language: "How are my brands performing in the United States?"
SELECT b.brand_name,
       SUM(f.value_sold_usd) as sales,
       SUM(f.volume_sold_std) as volume,
       SUM(f.units_sold) as units
FROM Fact_Sales_Transactions f
JOIN Dim_Product_SKU sku ON f.sku_id = sku.sku_id
JOIN Dim_SubBrand sb ON sku.subbrand_id = sb.subbrand_id
JOIN Dim_Brand b ON sb.brand_id = b.brand_id
JOIN Dim_Geography g ON f.geo_id = g.geo_id
JOIN Dim_Period p ON f.period_id = p.period_id
WHERE b.corp_id = {client_id}
  AND g.country_name = 'United States'
  AND p.fiscal_year = (SELECT MAX(fiscal_year) FROM Dim_Period)
GROUP BY b.brand_name
ORDER BY sales DESC
```

### Query 6: Promotional vs Regular sales
```sql
-- Natural language: "Compare promotional vs regular sales"
SELECT b.brand_name,
       SUM(CASE WHEN f.is_promotion = 0 THEN f.value_sold_usd ELSE 0 END) as regular_sales,
       SUM(CASE WHEN f.is_promotion = 1 THEN f.value_sold_usd ELSE 0 END) as promo_sales
FROM Fact_Sales_Transactions f
JOIN Dim_Product_SKU sku ON f.sku_id = sku.sku_id
JOIN Dim_SubBrand sb ON sku.subbrand_id = sb.subbrand_id
JOIN Dim_Brand b ON sb.brand_id = b.brand_id
JOIN Dim_Period p ON f.period_id = p.period_id
WHERE b.corp_id = {client_id}
  AND p.fiscal_year = (SELECT MAX(fiscal_year) FROM Dim_Period)
GROUP BY b.brand_name
ORDER BY regular_sales + promo_sales DESC
```

### Query 7: Sub-brand analysis
```sql
-- Natural language: "Show me sub-brands for Coca-Cola"
SELECT b.brand_name, sb.subbrand_name, SUM(f.value_sold_usd) as total_sales
FROM Fact_Sales_Transactions f
JOIN Dim_Product_SKU sku ON f.sku_id = sku.sku_id
JOIN Dim_SubBrand sb ON sku.subbrand_id = sb.subbrand_id
JOIN Dim_Brand b ON sb.brand_id = b.brand_id
WHERE b.corp_id = {client_id}
  AND b.brand_name LIKE '%Coca-Cola%'
GROUP BY b.brand_name, sb.subbrand_name
ORDER BY total_sales DESC
```

### Query 8: Time series trend
```sql
-- Natural language: "Sales trend over last 5 years"
SELECT p.fiscal_year, SUM(f.value_sold_usd) as total_sales
FROM Fact_Sales_Transactions f
JOIN Dim_Product_SKU sku ON f.sku_id = sku.sku_id
JOIN Dim_SubBrand sb ON sku.subbrand_id = sb.subbrand_id
JOIN Dim_Brand b ON sb.brand_id = b.brand_id
JOIN Dim_Period p ON f.period_id = p.period_id
WHERE b.corp_id = {client_id}
  AND p.fiscal_year >= (SELECT MAX(fiscal_year) - 4 FROM Dim_Period)
GROUP BY p.fiscal_year
ORDER BY p.fiscal_year
```

### Query 9: Multi-dimensional analysis
```sql
-- Natural language: "Sales by brand, country, and category"
SELECT b.brand_name, g.country_name, sku.category_name,
       SUM(f.value_sold_usd) as total_sales
FROM Fact_Sales_Transactions f
JOIN Dim_Product_SKU sku ON f.sku_id = sku.sku_id
JOIN Dim_SubBrand sb ON sku.subbrand_id = sb.subbrand_id
JOIN Dim_Brand b ON sb.brand_id = b.brand_id
JOIN Dim_Geography g ON f.geo_id = g.geo_id
JOIN Dim_Period p ON f.period_id = p.period_id
WHERE b.corp_id = {client_id}
  AND p.fiscal_year = (SELECT MAX(fiscal_year) FROM Dim_Period)
GROUP BY b.brand_name, g.country_name, sku.category_name
HAVING SUM(f.value_sold_usd) > 10000
ORDER BY total_sales DESC
LIMIT 50
```

### Query 10: Regional rollup
```sql
-- Natural language: "Sales by region"
SELECT g.region_name, SUM(f.value_sold_usd) as total_sales
FROM Fact_Sales_Transactions f
JOIN Dim_Product_SKU sku ON f.sku_id = sku.sku_id
JOIN Dim_SubBrand sb ON sku.subbrand_id = sb.subbrand_id
JOIN Dim_Brand b ON sb.brand_id = b.brand_id
JOIN Dim_Geography g ON f.geo_id = g.geo_id
JOIN Dim_Period p ON f.period_id = p.period_id
WHERE b.corp_id = {client_id}
  AND p.fiscal_year = (SELECT MAX(fiscal_year) FROM Dim_Period)
GROUP BY g.region_name
ORDER BY total_sales DESC
```

### Query 11: Market trend analysis
```sql
-- Natural language: "Show me the market trend in 2024"
SELECT p.fiscal_year, p.quarter,
       SUM(f.value_sold_usd) as quarterly_sales,
       SUM(f.volume_sold_std) as quarterly_volume
FROM Fact_Sales_Transactions f
JOIN Dim_Product_SKU sku ON f.sku_id = sku.sku_id
JOIN Dim_SubBrand sb ON sku.subbrand_id = sb.subbrand_id
JOIN Dim_Brand b ON sb.brand_id = b.brand_id
JOIN Dim_Period p ON f.period_id = p.period_id
WHERE b.corp_id = {client_id}
  AND p.fiscal_year = 2024
GROUP BY p.fiscal_year, p.quarter
ORDER BY p.quarter
```

## Important Reminders

1. **ALWAYS** filter by `corp_id = {client_id}` through the complete product hierarchy join:
   - Fact_Sales_Transactions → Dim_Product_SKU → Dim_SubBrand → Dim_Brand
2. **NEVER** use CURRENT_DATE or NOW() - use MAX(fiscal_year) from Dim_Period
3. **Use** `Dim_Period.fiscal_year` for time-based queries
4. **Join** through the product hierarchy FIRST to ensure corp_id filtering
5. **Limit** results to 100 rows unless user specifies otherwise
6. **Order** results meaningfully (by value DESC or by date ASC)
7. **Use** table aliases (f, sku, sb, b, g, p) for readability
8. **Apply** aggregate functions (SUM, AVG, COUNT) appropriately for metrics
9. **Remember**: The only fact table available is `Fact_Sales_Transactions`
