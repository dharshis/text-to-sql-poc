# Dataset: Euromonitor Market Data (em_market)

## Business Domain

Global market research data for consumer goods, tracking market size and company market share across countries, categories, brands, and time periods. This dataset enables analysis of competitive positioning, brand performance, and market trends in the FMCG/CPG industry.

## Key Concepts

- **Corporation**: Parent company that owns multiple brands (e.g., The Coca-Cola Company, PepsiCo, Unilever)
- **Brand**: Product brand owned by a corporation (e.g., Coca-Cola, Sprite, Fanta)
- **Sub-Brand**: Brand variant or line extension (e.g., Coca-Cola Zero, Coca-Cola Light)
- **Product SKU**: Individual sellable product unit at the most granular level
- **Market Size**: Total market value or volume for a category/geography combination
- **Market Share**: Percentage of market held by a specific brand or company
- **Forecast**: Forward-looking projections vs historical actuals

## Entity Hierarchy

```
Dim_Corporation (corp_id) ← FILTERING LEVEL (isolation by corp_id)
  └─ Dim_Brand (brand_id, corp_id FK)
      └─ Dim_SubBrand (subbrand_id, brand_id FK)
          └─ Dim_Product_SKU (sku_id, subbrand_id FK)
```

**Key Filtering Point**: All queries must filter at the **Corporation** level using `corp_id`, typically by joining through `Dim_Brand` table where the brand hierarchy begins.

## Dimension Tables

### Geographic Dimensions
- **Dim_Country**: Country-level geographic data (country_id, country_name, region)
- **Dim_Region**: Regional rollups (region_id, region_name)

### Product Dimensions
- **Dim_Corporation**: Parent companies (corp_id, corp_name)
- **Dim_Brand**: Brands owned by corporations (brand_id, brand_name, corp_id)
- **Dim_SubBrand**: Brand variants (subbrand_id, subbrand_name, brand_id)
- **Dim_Product_SKU**: Individual products (sku_id, sku_name, subbrand_id)

### Category Dimensions
- **Dim_Category**: Three-level hierarchy
  - Category (top level, e.g., "Soft Drinks")
  - Subcategory (mid level, e.g., "Carbonated Soft Drinks")
  - Segment (detailed level, e.g., "Cola")

## Fact Tables

### fact_market_size
Market size data by geography, category, brand, and time.

**Grain**: Country × Category × Brand × Year × Forecast Flag

**Key Columns**:
- `brand_id` → Dim_Brand (join here to filter by corp_id)
- `country_id` → Dim_Country
- `category_id` → Dim_Category
- `year` (integer, range: 2010-2030)
- `is_forecast` (0 = historical, 1 = forecast)
- `market_size_value` (numeric, market size in local currency or volume)
- `market_size_units` (string, e.g., "USD Millions", "Liters")

### fact_company_share
Market share data by brand, geography, category, and time.

**Grain**: Country × Category × Brand × Year

**Key Columns**:
- `brand_id` → Dim_Brand (join here to filter by corp_id)
- `country_id` → Dim_Country
- `category_id` → Dim_Category
- `year` (integer)
- `market_share_pct` (decimal, percentage 0-100)
- `is_forecast` (0 = historical, 1 = forecast)

## Time Dimension

- **Data Span**: 2010-2030 (20 years of historical + forecast data)
- **Forecast Flag**: `is_forecast` column distinguishes historical (0) from forecasted (1) data
- **Latest Historical Year**: Use `SELECT MAX(year) FROM fact_table WHERE is_forecast = 0`
- **Time Queries**: Always use fact table's MAX(year), NEVER use CURRENT_DATE or NOW()

**Important**: When users ask for "last N years", calculate from the latest historical year in the data, not from today's date.

## Common Query Patterns

### 1. Brand Performance
Filter by corp_id through Dim_Brand join to get all brands owned by the corporation.

### 2. Geographic Analysis
Join through Dim_Country or Dim_Region for location-based analysis.

### 3. Category Analysis
Join through Dim_Category for product category breakdowns.

### 4. Time Series Analysis
Use year column with is_forecast flag to separate historical from projections.

### 5. Market Share vs Market Size
- Market Size: Total market (all brands combined)
- Company Share: Corporation's portion of the total market

## Data Quality Notes

- All monetary values are in local currency unless specified
- Market share percentages sum to 100% within a geography/category/year
- Forecast data is predictive and should be labeled as such in results
- Some categories may not have data for all years (sparse data)
- Corp_id filtering is MANDATORY for all queries to enforce data isolation
