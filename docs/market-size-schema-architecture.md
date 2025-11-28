# Market Size Database Schema Architecture

**Date:** November 27, 2025  
**Version:** 2.0 (Enhanced with Client Dimension)  
**Architect:** Winston

---

## Overview

The market_size database implements a **star schema** with `dim_clients` as a first-class dimension, providing complete multi-tenancy support with proper referential integrity.

---

## Star Schema Design

```
                    dim_clients ★
                         ↓
                         ↓ FK: client_id (ON DELETE RESTRICT)
                         ↓
    ┌────────────────────────────────────────┐
    │                                        │
    │   FACT TABLES (Grain: Market Data)    │
    │   • fact_market_size (135 records)    │
    │   • fact_forecasts (105 records)      │
    │                                        │
    └────────────────────────────────────────┘
             ↓           ↓           ↓
    ┌────────────┬────────────┬────────────┬────────────┐
    ↓            ↓            ↓            ↓            ↓
dim_markets  dim_geography dim_time   dim_currency  dim_segments
(12 markets) (25 countries) (52 periods) (7 types)   (44 values)
```

---

## Enhanced Client Dimension

### Schema: dim_clients

```sql
CREATE TABLE dim_clients (
    -- Primary Key
    client_id INTEGER PRIMARY KEY,
    client_name VARCHAR(100) NOT NULL,
    
    -- Business Context
    industry VARCHAR(100),              -- e.g., 'Manufacturing', 'Technology', 'Retail'
    region VARCHAR(100),                -- Client's primary region
    subscription_tier VARCHAR(50),      -- 'Enterprise', 'Professional', 'Basic'
    
    -- Hierarchical Support
    parent_client_id INTEGER,           -- For parent-subsidiary relationships
    
    -- Account Management
    account_manager VARCHAR(100),       -- Relationship owner
    contract_start_date DATE,           -- Subscription start
    contract_end_date DATE,             -- Subscription end
    
    -- Access Control
    data_access_level VARCHAR(50) DEFAULT 'standard',  -- 'basic', 'standard', 'enterprise'
    max_users INTEGER DEFAULT 10,       -- License limit
    
    -- Metadata
    created_date DATE DEFAULT CURRENT_DATE,
    last_modified_date DATE,
    is_active INTEGER DEFAULT 1,        -- Soft delete flag
    
    -- Referential Integrity
    FOREIGN KEY (parent_client_id) REFERENCES dim_clients(client_id)
);
```

### Current Clients

| ID | Client Name | Industry | Region | Tier | Access Level | Max Users | Account Manager |
|----|-------------|----------|--------|------|--------------|-----------|-----------------|
| 1  | Acme Corporation | Manufacturing | North America | Enterprise | enterprise | 50 | Sarah Johnson |
| 2  | GlobalTech Industries | Technology | Europe | Professional | professional | 25 | Michael Chen |
| 6  | MegaRetail Group | Retail | Asia Pacific | Enterprise | enterprise | 100 | Emily Rodriguez |

---

## Fact Tables with Client Relationships

### fact_market_size

```sql
CREATE TABLE fact_market_size (
    record_id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Dimension Keys
    market_id VARCHAR(20),
    geo_id VARCHAR(20),
    segment_value_id VARCHAR(20),
    time_id INTEGER,
    currency_id VARCHAR(10),
    client_id INTEGER NOT NULL,         -- ★ Security partition + dimension
    
    -- Degenerate Dimensions
    year INTEGER,
    data_type VARCHAR(20),              -- 'Actual', 'Estimate', 'Forecast'
    
    -- Measures
    market_value_usd_m DECIMAL(15,2),   -- Market value in millions USD
    market_volume_units DECIMAL(15,2),  -- Market volume in units
    
    -- Metadata
    last_updated DATE DEFAULT CURRENT_DATE,
    
    -- Foreign Keys with Referential Integrity
    FOREIGN KEY (market_id) REFERENCES dim_markets(market_id),
    FOREIGN KEY (geo_id) REFERENCES dim_geography(geo_id),
    FOREIGN KEY (time_id) REFERENCES dim_time(time_id),
    FOREIGN KEY (currency_id) REFERENCES dim_currency(currency_id),
    FOREIGN KEY (client_id) REFERENCES dim_clients(client_id) ON DELETE RESTRICT
);
```

**Grain:** One row per market, geography, time period, and client

**Record Count:** 135 (45 per client × 3 clients)

**Data Variations by Client:**
- Client 1: Baseline data (100%)
- Client 2: 80% of baseline (smaller market coverage)
- Client 6: 120% of baseline (larger market coverage)

### fact_forecasts

```sql
CREATE TABLE fact_forecasts (
    forecast_id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Dimension Keys
    market_id VARCHAR(20),
    geo_id VARCHAR(20),
    time_id INTEGER,
    currency_id VARCHAR(10),
    client_id INTEGER NOT NULL,         -- ★ Security partition + dimension
    
    -- Degenerate Dimensions
    year INTEGER,
    scenario VARCHAR(50),               -- 'base', 'optimistic', 'pessimistic'
    
    -- Measures
    forecast_value_usd_m DECIMAL(15,2), -- Forecast value
    cagr DECIMAL(5,2),                  -- Compound annual growth rate
    
    -- Metadata
    last_updated DATE DEFAULT CURRENT_DATE,
    
    -- Foreign Keys with Referential Integrity
    FOREIGN KEY (market_id) REFERENCES dim_markets(market_id),
    FOREIGN KEY (geo_id) REFERENCES dim_geography(geo_id),
    FOREIGN KEY (time_id) REFERENCES dim_time(time_id),
    FOREIGN KEY (currency_id) REFERENCES dim_currency(currency_id),
    FOREIGN KEY (client_id) REFERENCES dim_clients(client_id) ON DELETE RESTRICT
);
```

**Grain:** One row per market, geography, forecast period, scenario, and client

**Record Count:** 105 (35 per client × 3 clients)

---

## Performance Indexes

```sql
-- fact_market_size indexes
CREATE INDEX idx_market_size_market ON fact_market_size(market_id);
CREATE INDEX idx_market_size_geo ON fact_market_size(geo_id);
CREATE INDEX idx_market_size_year ON fact_market_size(year);
CREATE INDEX idx_market_size_time ON fact_market_size(time_id);
CREATE INDEX idx_market_size_client ON fact_market_size(client_id);  -- ★ Security

-- fact_forecasts indexes
CREATE INDEX idx_forecasts_market ON fact_forecasts(market_id);
CREATE INDEX idx_forecasts_geo ON fact_forecasts(geo_id);
CREATE INDEX idx_forecasts_year ON fact_forecasts(year);
CREATE INDEX idx_forecasts_time ON fact_forecasts(time_id);
CREATE INDEX idx_forecasts_client ON fact_forecasts(client_id);      -- ★ Security
```

---

## Referential Integrity

### Foreign Key Enforcement

```
ON DELETE RESTRICT: Cannot delete a client if fact records exist
```

**Example - This will FAIL:**

```sql
-- Try to delete client 1 (has 45 market size records)
DELETE FROM dim_clients WHERE client_id = 1;
-- Error: FOREIGN KEY constraint failed
```

**Correct approach - Soft delete:**

```sql
-- Mark client as inactive
UPDATE dim_clients SET is_active = 0 WHERE client_id = 1;
```

---

## Query Patterns

### 1. Client-Specific Analysis

```sql
-- Get all electric vehicle data for MegaRetail Group (client_id=6)
SELECT 
    c.client_name,
    c.subscription_tier,
    m.market_name,
    g.country,
    t.year,
    f.market_value_usd_m
FROM fact_market_size f
JOIN dim_clients c ON f.client_id = c.client_id
JOIN dim_markets m ON f.market_id = m.market_id
JOIN dim_geography g ON f.geo_id = g.geo_id
JOIN dim_time t ON f.time_id = t.time_id
WHERE f.client_id = 6
  AND m.market_name = 'Electric Vehicles'
  AND t.year = 2023;
```

### 2. Client Segmentation Analysis

```sql
-- Compare market access by subscription tier
SELECT 
    c.subscription_tier,
    COUNT(DISTINCT c.client_id) as num_clients,
    SUM(f.market_value_usd_m) as total_market_value
FROM fact_market_size f
JOIN dim_clients c ON f.client_id = c.client_id
WHERE c.is_active = 1
GROUP BY c.subscription_tier;
```

### 3. Account Manager Performance

```sql
-- Show total market value managed by each account manager
SELECT 
    c.account_manager,
    COUNT(DISTINCT c.client_id) as num_clients,
    SUM(f.market_value_usd_m) as total_portfolio_value,
    AVG(f.market_value_usd_m) as avg_market_value
FROM fact_market_size f
JOIN dim_clients c ON f.client_id = c.client_id
WHERE c.is_active = 1
GROUP BY c.account_manager
ORDER BY total_portfolio_value DESC;
```

### 4. Client Hierarchy Queries

```sql
-- When hierarchies are implemented
-- Consolidated view for parent company + subsidiaries
SELECT 
    parent.client_name as parent_company,
    COUNT(DISTINCT child.client_id) as subsidiaries,
    SUM(f.market_value_usd_m) as consolidated_value
FROM fact_market_size f
JOIN dim_clients child ON f.client_id = child.client_id
LEFT JOIN dim_clients parent ON child.parent_client_id = parent.client_id
GROUP BY parent.client_name;
```

### 5. Contract Expiration Analysis

```sql
-- Clients with contracts expiring in next 90 days
SELECT 
    c.client_name,
    c.contract_end_date,
    c.subscription_tier,
    c.account_manager,
    COUNT(DISTINCT f.record_id) as total_records,
    SUM(f.market_value_usd_m) as total_data_value
FROM dim_clients c
LEFT JOIN fact_market_size f ON c.client_id = f.client_id
WHERE c.contract_end_date BETWEEN DATE('now') AND DATE('now', '+90 days')
  AND c.is_active = 1
GROUP BY c.client_name, c.contract_end_date, c.subscription_tier, c.account_manager;
```

---

## Security Architecture

### Row-Level Security via client_id

```sql
-- Every query MUST include client_id filter
SELECT ...
FROM fact_market_size
WHERE client_id = {authenticated_client_id}  -- Enforced by backend
```

### Multi-Layered Security

```
1. Application Layer (Backend)
   ↓ Validates client_id in SQL queries
   
2. Database Layer (SQLite)
   ↓ FK constraints ensure client exists
   ↓ Indexes optimize client filtering
   
3. Business Layer (dim_clients)
   ↓ is_active flag for soft deletes
   ↓ data_access_level for feature gating
   ↓ max_users for license enforcement
```

---

## Data Isolation Model

### Client Data Distribution

```
Total Records: 240 (135 market_size + 105 forecasts)

Per Client:
├─ Client 1 (Acme): 80 records (45 + 35)
├─ Client 2 (GlobalTech): 80 records (45 + 35)
└─ Client 6 (MegaRetail): 80 records (45 + 35)

Dimensions: SHARED (client_id=1 for all dimension records)
Facts: ISOLATED (each client has separate fact records)
```

### Shared vs. Isolated Data

**Shared (Reference Data):**
- dim_markets (12 markets)
- dim_geography (25 countries)
- dim_time (52 time periods)
- dim_currency (7 currency types)
- dim_segment_types (9 types)
- dim_segment_values (35 values)

**Isolated (Transactional Data):**
- fact_market_size (per client)
- fact_forecasts (per client)

**Client Context (Metadata):**
- dim_clients (client profiles)

---

## Design Rationale

### Why dim_clients is a Dimension (Not Just a Filter)

1. **Rich Attributes:** Clients have descriptive business properties
2. **Analytical Value:** Enables client segmentation and analysis
3. **Independent Changes:** Client metadata changes separately from facts
4. **Hierarchy Support:** Can model parent-subsidiary relationships
5. **Business Context:** Provides meaning beyond security filtering

### Why client_id is in Fact Tables

1. **Security:** Enforces row-level data isolation
2. **Performance:** Indexed for fast filtering
3. **Audit:** Tracks data ownership
4. **Flexibility:** Supports client-specific data variations

### Why FK Constraints Matter

1. **Data Integrity:** Can't reference non-existent clients
2. **Cascade Control:** DELETE RESTRICT prevents orphaned facts
3. **Documentation:** Schema self-documents relationships
4. **Query Optimization:** Helps query planner

---

## Migration History

### Version 1.0 → 2.0 Changes

| Change | Reason | Impact |
|--------|--------|--------|
| Added dim_clients table | Proper client management | New dimension table |
| Added 8 client attributes | Business context & control | Enhanced metadata |
| Added FK constraints | Referential integrity | Data quality enforcement |
| Added client data for 2, 6 | Multi-tenancy testing | 240 total records |
| Recreated fact tables | FK support in SQLite | Zero data loss migration |

---

## Future Enhancements

### Potential Extensions

1. **Client Hierarchies**
   - Parent-subsidiary trees
   - Consolidated reporting
   - Inherited permissions

2. **Client-Market Access Control**
   - Bridge table: bridge_client_markets
   - Selective market visibility
   - Tiered data access

3. **Client Activity Tracking**
   - Query audit log
   - Usage metrics
   - Billing integration

4. **Multi-Database Support**
   - Client-specific databases
   - Federated queries
   - Data residency compliance

---

## Validation & Testing

### Schema Integrity Checks

```sql
-- 1. All fact records have valid clients
SELECT COUNT(*) FROM fact_market_size f
WHERE NOT EXISTS (SELECT 1 FROM dim_clients c WHERE c.client_id = f.client_id);
-- Expected: 0

-- 2. FK constraints are enforced
PRAGMA foreign_key_check;
-- Expected: No violations

-- 3. All clients are active
SELECT COUNT(*) FROM dim_clients WHERE is_active = 0;
-- Expected: 0 (currently)
```

### Performance Benchmarks

```sql
-- Query with client filter (should be fast due to index)
EXPLAIN QUERY PLAN
SELECT * FROM fact_market_size WHERE client_id = 6;
-- Expected: Uses idx_market_size_client
```

---

## Architecture Compliance

✅ **Dimensional Modeling Best Practices**
- Conforms dimension (client attributes)
- Proper grain definition
- Clear fact/dimension separation

✅ **Security by Design**
- Row-level isolation
- FK enforcement
- Soft delete support

✅ **Performance Optimized**
- Targeted indexes
- Shared dimension tables
- Efficient joins

✅ **Scalability Ready**
- Hierarchical support
- Extensible attributes
- Bridge table ready

---

**Schema Status:** Production-Ready ✅  
**Architect Approval:** Winston 🏗️  
**Last Updated:** November 27, 2025

