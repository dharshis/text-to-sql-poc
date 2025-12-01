# Table: dim_markets

## Metadata
* **Table Type:** Dimension
* **Subject Area:** Market Definitions
* **Granularity:** One row per Market
* **Primary Key:** `market_id`
* **Hierarchy:** Self-referencing (parent-child relationships)

## Description
This dimension table defines all markets tracked in the system. Markets can have hierarchical relationships (parent-child), allowing for aggregation at different levels (e.g., "Automotive" → "Electric Vehicles" → "Battery Electric Vehicles").

**Key Features:**
- Hierarchical structure via `parent_market_id`
- Industry classification via NAICS codes
- Detailed market definitions
- Multi-tenant support

## Column Definitions

| Column Name | Data Type | Key Type | Nullable | Description |
| :--- | :--- | :--- | :--- | :--- |
| `market_id` | VARCHAR(20) | PK | NO | Unique market identifier |
| `market_name` | VARCHAR(255) | | YES | Display name of the market |
| `parent_market_id` | VARCHAR(20) | FK | YES | Link to parent market (self-reference) |
| `definition` | TEXT | | YES | Detailed explanation of market scope |
| `naics_code` | VARCHAR(20) | | YES | North American Industry Classification System code |
| `client_id` | INTEGER | FK | YES | Multi-tenant isolation (DEFAULT 1) |

## Relationships
* **Self-Referencing:** `parent_market_id` → `market_id` (creates hierarchy)
* **Referenced By:** `fact_market_size.market_id`, `fact_forecasts.market_id`

## Hierarchy Structure

```
Consumer Goods (parent)
├── Electronics
│   ├── Smartphones
│   ├── Laptops
│   └── Tablets
├── Automotive
│   ├── Electric Vehicles
│   │   ├── Battery Electric (BEV)
│   │   └── Plug-in Hybrid (PHEV)
│   └── Internal Combustion Engine (ICE)
└── Home Appliances
    ├── Refrigerators
    └── Washing Machines
```

## Common Query Patterns

### Pattern 1: List All Markets
```sql
-- Get all markets with their parent relationships
SELECT 
    m.market_id,
    m.market_name,
    m.naics_code,
    parent.market_name AS parent_market,
    m.definition
FROM dim_markets m
LEFT JOIN dim_markets parent ON m.parent_market_id = parent.market_id
WHERE m.client_id = 1
ORDER BY m.market_name;
```

### Pattern 2: Get Market Hierarchy Tree
```sql
-- Build hierarchical view (parent → child)
SELECT 
    parent.market_name AS parent_market,
    child.market_name AS child_market,
    child.definition,
    child.naics_code
FROM dim_markets parent
INNER JOIN dim_markets child ON parent.market_id = child.parent_market_id
WHERE parent.client_id = 1
ORDER BY parent.market_name, child.market_name;
```

### Pattern 3: Find Root/Top-Level Markets
```sql
-- Markets with no parent (top of hierarchy)
SELECT 
    market_id,
    market_name,
    naics_code,
    definition
FROM dim_markets
WHERE parent_market_id IS NULL
    AND client_id = 1
ORDER BY market_name;
```

### Pattern 4: Get All Sub-Markets for a Parent
```sql
-- Find all child markets under "Automotive"
SELECT 
    m.market_id,
    m.market_name,
    m.naics_code,
    m.definition,
    COUNT(fms.record_id) AS data_points
FROM dim_markets m
LEFT JOIN fact_market_size fms ON m.market_id = fms.market_id
WHERE m.parent_market_id = (
    SELECT market_id 
    FROM dim_markets 
    WHERE market_name = 'Automotive' AND client_id = 1
)
AND m.client_id = 1
GROUP BY m.market_id, m.market_name, m.naics_code, m.definition
ORDER BY m.market_name;
```

### Pattern 5: Market Search by Name
```sql
-- Fuzzy search for markets containing keyword
SELECT 
    market_id,
    market_name,
    definition,
    naics_code
FROM dim_markets
WHERE market_name LIKE '%Electric%'
    AND client_id = 1
ORDER BY market_name;
```

### Pattern 6: Markets by NAICS Classification
```sql
-- Get all markets in a NAICS category
SELECT 
    market_id,
    market_name,
    naics_code,
    definition
FROM dim_markets
WHERE naics_code LIKE '336%'  -- Automotive industry
    AND client_id = 1
ORDER BY naics_code, market_name;
```

### Pattern 7: Market with Latest Data Availability
```sql
-- Check which markets have recent data
SELECT 
    m.market_id,
    m.market_name,
    MAX(t.year) AS latest_year,
    COUNT(DISTINCT fms.geo_id) AS num_geographies,
    SUM(fms.market_value_usd_m) AS total_value
FROM dim_markets m
INNER JOIN fact_market_size fms ON m.market_id = fms.market_id
INNER JOIN dim_time t ON fms.time_id = t.time_id
WHERE m.client_id = 1
    AND fms.market_value_usd_m IS NOT NULL
GROUP BY m.market_id, m.market_name
HAVING MAX(t.year) >= 2023  -- Only markets with recent data
ORDER BY latest_year DESC, total_value DESC;
```

## NAICS Code Reference

Common NAICS codes in market data:

| NAICS Code | Industry Category | Example Markets |
|------------|------------------|-----------------|
| 336 | Transportation Equipment | Automotive, Aviation |
| 3361 | Motor Vehicle Manufacturing | Cars, Trucks, Motorcycles |
| 336111 | Automobile Manufacturing | Passenger Vehicles, EVs |
| 3362 | Motor Vehicle Body/Parts | Auto Parts, Components |
| 334 | Computer/Electronic Products | Smartphones, Laptops, Tablets |
| 3341 | Computer Equipment | PCs, Servers, Workstations |
| 335 | Electrical Equipment | Home Appliances, Lighting |
| 3352 | Household Appliances | Refrigerators, Washers, Dryers |

## Business Rules

### Market Definition Guidelines
- Each market must have a clear definition in the `definition` field
- Use NAICS codes to align with industry standards
- Parent-child relationships should be logically sound (child ⊂ parent)

### Naming Conventions
- Use clear, descriptive names (e.g., "Electric Vehicles" not "EVs")
- Consistent capitalization
- Avoid abbreviations unless widely recognized

### Hierarchy Rules
- Maximum hierarchy depth: 4 levels recommended
- Leaf markets (no children) should have fact data
- Parent markets aggregate child data

## Example User Questions Mapped to Queries

| User Question | Key Pattern | Notes |
|--------------|-------------|-------|
| "What markets are available?" | Pattern 1 | List all with relationships |
| "Show me the automotive market structure" | Pattern 2 | Hierarchy tree |
| "What are the top-level markets?" | Pattern 3 | Root markets only |
| "What are the sub-markets of Electronics?" | Pattern 4 | Children of parent |
| "Find markets related to electric" | Pattern 5 | Fuzzy text search |
| "Show automotive industry markets" | Pattern 6 | NAICS-based filter |
| "Which markets have recent data?" | Pattern 7 | Join with facts |

## Integration with Fact Tables

When querying market data:

```sql
-- Always join to dim_markets for market name and context
SELECT 
    m.market_name,
    m.definition,
    parent.market_name AS parent_market,
    SUM(fms.market_value_usd_m) AS total_value
FROM fact_market_size fms
INNER JOIN dim_markets m ON fms.market_id = m.market_id
LEFT JOIN dim_markets parent ON m.parent_market_id = parent.market_id
WHERE fms.client_id = 1
GROUP BY m.market_name, m.definition, parent.market_name;
```

## Performance Tips

1. **Index Usage:**
   - `market_id` is primary key (automatic index)
   - Consider adding index on `parent_market_id` for hierarchy queries
   - Consider index on `naics_code` for classification queries

2. **Query Optimization:**
   - Use LEFT JOIN when parent may be NULL
   - Filter by client_id early in WHERE clause
   - Cache market hierarchy for repeated hierarchical queries

3. **Recursive Queries:**
   For deep hierarchy traversal, consider CTEs:
   ```sql
   WITH RECURSIVE market_hierarchy AS (
       SELECT market_id, market_name, parent_market_id, 1 as level
       FROM dim_markets
       WHERE parent_market_id IS NULL AND client_id = 1
       
       UNION ALL
       
       SELECT m.market_id, m.market_name, m.parent_market_id, mh.level + 1
       FROM dim_markets m
       INNER JOIN market_hierarchy mh ON m.parent_market_id = mh.market_id
       WHERE m.client_id = 1
   )
   SELECT * FROM market_hierarchy
   ORDER BY level, market_name;
   ```

## Data Maintenance Notes

- New markets should be assigned to appropriate parent markets
- NAICS codes should be validated against official classifications
- Market definitions should be reviewed periodically for accuracy
- Deprecated markets should be marked (consider adding `is_active` flag)


