# EM Market Database

SQLite database created from CSV files in this directory.

## 📊 Database: `em_market.db`

**Location**: `/data/em_market.db`  
**Size**: 2.12 MB  
**Total Rows**: 24,559

## 📋 Tables

### Dimension Tables (7)
| Table | Rows | Description |
|-------|------|-------------|
| `Dim_Geography` | 24 | Countries, regions, currency info |
| `Dim_Period` | 36 | Time periods (YYYYMM format) |
| `Dim_Market_Definition` | 5 | Market category definitions |
| `Dim_Corporation` | 15 | Parent corporations |
| `Dim_Brand` | 49 | Brand names |
| `Dim_SubBrand` | 66 | Sub-brand names |
| `Dim_Product_SKU` | 100 | Product SKUs with attributes |

### Fact Tables (2)
| Table | Rows | Description |
|-------|------|-------------|
| `Fact_Sales_Transactions` | 20,000 | Individual sales transactions |
| `Fact_Market_Summary` | 4,264 | Market totals (denominators) |

### Bridge Tables (1)
| Table | Rows | Description |
|-------|------|-------------|
| `Bridge_Market_SKU` | 0 | Many-to-many market-SKU mapping (empty, populate as needed) |

### Views (2)
- `vw_sales_detail` - Sales with all dimension details
- `vw_market_summary` - Market summaries with geography and market names

## 🔑 Key Relationships

```
Fact_Sales_Transactions
├── period_id → Dim_Period
├── geo_id → Dim_Geography
└── sku_id → Dim_Product_SKU
    └── subbrand_id → Dim_SubBrand
        └── brand_id → Dim_Brand
            └── corp_id → Dim_Corporation

Fact_Market_Summary
├── period_id → Dim_Period
├── geo_id → Dim_Geography
└── market_def_id → Dim_Market_Definition
```

## 📈 Sample Queries

### Sales by Country
```sql
SELECT 
    g.country_name,
    g.region_name,
    COUNT(*) as transaction_count,
    SUM(fst.value_sold_usd) as total_value_usd
FROM Fact_Sales_Transactions fst
JOIN Dim_Geography g ON fst.geo_id = g.geo_id
GROUP BY g.country_name, g.region_name
ORDER BY total_value_usd DESC
LIMIT 10;
```

### Top Products
```sql
SELECT 
    ps.sku_name,
    ps.product_category,
    b.brand_name,
    COUNT(*) as sales_count,
    SUM(fst.units_sold) as total_units
FROM Fact_Sales_Transactions fst
JOIN Dim_Product_SKU ps ON fst.sku_id = ps.sku_id
JOIN Dim_SubBrand sb ON ps.subbrand_id = sb.subbrand_id
JOIN Dim_Brand b ON sb.brand_id = b.brand_id
GROUP BY ps.sku_name, ps.product_category, b.brand_name
ORDER BY sales_count DESC
LIMIT 10;
```

### Market Summary by Region
```sql
SELECT 
    g.region_name,
    md.market_name,
    SUM(fms.total_market_value_usd) as total_market_usd
FROM Fact_Market_Summary fms
JOIN Dim_Geography g ON fms.geo_id = g.geo_id
JOIN Dim_Market_Definition md ON fms.market_def_id = md.market_def_id
GROUP BY g.region_name, md.market_name
ORDER BY total_market_usd DESC;
```

### Using Views
```sql
-- Sales detail with all dimensions
SELECT * FROM vw_sales_detail
WHERE country_name = 'USA'
LIMIT 10;

-- Market summary with geography
SELECT * FROM vw_market_summary
WHERE region_name = 'Europe'
LIMIT 10;
```

## 🔧 Rebuilding the Database

To rebuild from CSV files:

```bash
cd backend
python database/build_em_market_db.py
```

This will:
1. Read all CSV files from `data/em_market/`
2. Create tables with appropriate data types
3. Load data from CSVs
4. Create indexes on foreign keys
5. Create views for common queries
6. Generate statistics

## 📝 Schema Details

### Dim_Geography
- `geo_id` (PRIMARY KEY)
- `country_name`
- `region_name` 
- `currency_code`
- `currency_exchange_rate`

### Dim_Product_SKU
- `sku_id` (PRIMARY KEY)
- `sku_name`
- `product_category`
- `package_size`
- `unit_measure`
- `launch_date`
- `subbrand_id` (FOREIGN KEY)
- And more...

### Fact_Sales_Transactions
- `transaction_id` (PRIMARY KEY)
- `period_id` (FOREIGN KEY)
- `geo_id` (FOREIGN KEY)
- `sku_id` (FOREIGN KEY)
- `units_sold`
- `volume_sold_std`
- `value_sold_local`
- `value_sold_usd`
- `is_promotion`
- `distribution_points`

## 🎯 Usage with Text-to-SQL System

### 1. Add to Dataset Configuration

Edit `backend/datasets/dataset_config.py`:

```python
DATASETS = {
    "em_market": {
        "id": "em_market",
        "name": "EM Market Data",
        "db_path": str(PROJECT_ROOT / "data" / "em_market.db"),
        # ... rest of config
    }
}
```

### 2. Metadata Already Created

Comprehensive metadata exists in `metadata/em_market/`:
- `business_rules.md` - 60+ SQL patterns
- `Fact_Sales_Transactions.md` - Table documentation
- `Dim_Geography.md` - Dimension documentation
- And more...

### 3. Test the Database

```bash
cd backend
python test_metadata_system.py
```

### 4. Use in Queries

The database is ready for:
- Natural language queries via the API
- Agentic SQL generation
- Direct SQL analysis
- Data visualization

## 📊 Data Quality

- **Completeness**: All dimension and fact tables populated
- **Relationships**: Foreign keys enforced
- **Indexes**: Created on all FK columns for performance
- **Views**: Pre-built for common queries
- **Data Types**: Properly inferred from CSV data

## 🚀 Quick Start

```python
import sqlite3

# Connect to database
conn = sqlite3.connect('data/em_market.db')
conn.row_factory = sqlite3.Row

# Run a query
cursor = conn.cursor()
cursor.execute("""
    SELECT country_name, COUNT(*) as sales 
    FROM vw_sales_detail 
    GROUP BY country_name
""")

for row in cursor:
    print(f"{row['country_name']}: {row['sales']} sales")

conn.close()
```

## 📦 Source CSV Files

All data sourced from:
- `Dim_Brand.csv` (49 rows)
- `Dim_Corporation.csv` (15 rows)
- `Dim_Geography.csv` (24 rows)
- `Dim_Market_Definition.csv` (5 rows)
- `Dim_Period.csv` (36 rows)
- `Dim_Product_SKU.csv` (100 rows)
- `Dim_SubBrand.csv` (66 rows)
- `Fact_Market_Summary.csv` (4,264 rows)
- `Fact_Sales_Transactions.csv` (20,000 rows)

Total: 24,559 rows across 9 tables

---

**Database ready for use!** ✅


