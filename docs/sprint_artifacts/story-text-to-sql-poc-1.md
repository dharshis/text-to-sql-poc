# Story 1.1: Database Foundation and Sample Data Generation

**Status:** Draft

---

## User Story

As a **developer**,
I want **a SQLite database with realistic retail market research sample data**,
So that **I can test and demonstrate text-to-SQL queries against a representative dataset**.

---

## Acceptance Criteria

**Given** I run the data generation script
**When** the script completes successfully
**Then** a SQLite database file is created at `data/text_to_sql_poc.db`

**And** the database contains:
- 5-10 client records with realistic company names and industries
- ~200 product records with realistic names, categories (electronics, apparel, home goods), and prices
- ~2000 sales records with temporal patterns (Q4 higher volume) across 2023-2024
- Customer segment data (Premium, Standard, Budget) for each client
- Proper foreign key relationships between tables
- Indexes on frequently queried columns (client_id, date, category)

---

## Implementation Details

### Tasks / Subtasks

1. **Set up project structure**
   - [x] Create `backend/` directory
   - [ ] Create `backend/database/` subdirectory
   - [ ] Create `data/` directory for SQLite file
   - [ ] Initialize Python virtual environment
   - [ ] Create requirements.txt with dependencies

2. **Define database schema (SQLAlchemy models)**
   - [ ] Create `backend/database/schema.py`
   - [ ] Define `Client` model (client_id, client_name, industry)
   - [ ] Define `Product` model (product_id, client_id, product_name, category, brand, price)
   - [ ] Define `Sale` model (sale_id, client_id, product_id, region, date, quantity, revenue)
   - [ ] Define `CustomerSegment` model (segment_id, client_id, segment_name, demographics)
   - [ ] Add foreign key relationships
   - [ ] Add indexes for performance

3. **Implement data generation logic**
   - [ ] Create `backend/database/seed_data.py`
   - [ ] Install Faker library for realistic data
   - [ ] Implement `generate_clients()` function (5-10 retail companies)
   - [ ] Implement `generate_products()` function (~200 products, mix of categories)
   - [ ] Implement `generate_sales()` function (~2000 sales with Q4 seasonality)
   - [ ] Implement `generate_customer_segments()` function (3 segments per client)
   - [ ] Add realistic product names (electronics: "Samsung Galaxy S24", apparel: "Nike Air Max", etc.)
   - [ ] Add price ranges: Electronics ($50-$2000), Apparel ($20-$300), Home Goods ($30-$800)
   - [ ] Add temporal patterns: Higher sales in Oct-Dec (holiday season)

4. **Create database initialization module**
   - [ ] Create `backend/database/db_manager.py`
   - [ ] Implement `init_database()` function to create tables
   - [ ] Implement `seed_database()` function to populate data
   - [ ] Add logging for progress tracking

5. **Test data generation**
   - [ ] Run `python -m database.seed_data` to generate database
   - [ ] Verify database file created at `data/text_to_sql_poc.db`
   - [ ] Query database to verify client count (5-10)
   - [ ] Query database to verify product count (~200)
   - [ ] Query database to verify sales count (~2000)
   - [ ] Verify Q4 sales are higher than other quarters
   - [ ] Verify foreign key relationships work correctly

### Technical Summary

**Technology Stack:**
- Python 3.13.9
- SQLAlchemy 2.0.36 (ORM)
- SQLite 3.x (bundled with Python)
- Faker 33.1.0 (realistic data generation)

**Database Schema:**
```sql
CREATE TABLE clients (
    client_id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_name TEXT NOT NULL,
    industry TEXT NOT NULL
);

CREATE TABLE products (
    product_id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    product_name TEXT NOT NULL,
    category TEXT NOT NULL,
    brand TEXT NOT NULL,
    price REAL NOT NULL,
    FOREIGN KEY (client_id) REFERENCES clients(client_id)
);

CREATE TABLE sales (
    sale_id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    region TEXT NOT NULL,
    date TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    revenue REAL NOT NULL,
    FOREIGN KEY (client_id) REFERENCES clients(client_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

CREATE TABLE customer_segments (
    segment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    segment_name TEXT NOT NULL,
    demographics TEXT,
    FOREIGN KEY (client_id) REFERENCES clients(client_id)
);

CREATE INDEX idx_sales_client_date ON sales(client_id, date);
CREATE INDEX idx_products_client_category ON products(client_id, category);
```

**Data Generation Strategy:**
- **Realistic products:** Use Faker + manual curation for recognizable brand names
- **Synthetic sales:** Random generation with seasonal weighting (Q4 * 1.5)
- **Temporal distribution:** Spread evenly across 2023-2024 with Q4 boost
- **Regional distribution:** Equal distribution across North, South, East, West

### Project Structure Notes

- **Files to create:**
  - `backend/requirements.txt`
  - `backend/database/__init__.py`
  - `backend/database/schema.py`
  - `backend/database/seed_data.py`
  - `backend/database/db_manager.py`

- **Expected test locations:**
  - `backend/tests/test_seed_data.py` (unit tests for data generation)
  - `backend/tests/test_schema.py` (model validation tests)

- **Estimated effort:** 3 story points

- **Prerequisites:** None (first story, greenfield)

### Key Code References

N/A - Greenfield project, no existing code to reference.

Refer to tech-spec.md sections:
- "Database Schema Design" (page 21)
- "Data Generation Logic" (page 22)
- "Development Setup" (page 28)

---

## Context References

**Tech-Spec:** [tech-spec.md](../tech-spec.md) - Primary context document containing:
- Complete database schema design with SQL DDL
- Data generation logic and realistic data requirements
- SQLAlchemy model structure
- Faker integration guidance
- Testing strategy for data validation

**Architecture:** [Architecture Diagram](../diagrams/diagram-text-to-sql-poc-architecture.excalidraw)
- Shows database as foundation layer for entire system

---

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4.5 (claude-sonnet-4-5-20250929)

### Debug Log References

N/A - No blocking issues encountered during implementation

### Completion Notes

**Implementation Summary:**

Story 1.1 (Database Foundation and Sample Data Generation) has been successfully completed. All acceptance criteria have been met:

1. **Project Structure**: Created backend/database/ and data/ directories, initialized Python virtual environment, and created requirements.txt with SQLAlchemy 2.0.36 and Faker 33.1.0

2. **Database Schema**: Implemented SQLAlchemy models in schema.py with:
   - Client, Product, Sale, and CustomerSegment models
   - Foreign key relationships properly defined
   - Performance indexes on sales(client_id, date) and products(client_id, category)

3. **Data Generation**: Implemented comprehensive data generation in seed_data.py with:
   - 10 clients with realistic company names and varied industries
   - 200 products with authentic brand names and proper price ranges by category
   - 2000 sales records with Q4 seasonality boost (542 sales in Q4 vs ~480 in other quarters)
   - 30 customer segments (3 per client: Premium, Standard, Budget)

4. **Database Manager**: Created db_manager.py with utilities for:
   - Database initialization and table creation
   - Session management
   - Query execution helpers
   - Database integrity verification

5. **Testing & Verification**: All verification checks passed:
   - ✓ Database file created at data/text_to_sql_poc.db
   - ✓ 10 clients, 200 products, 2000 sales, 30 segments
   - ✓ Q4 sales higher than other quarters (542 vs ~480 average)
   - ✓ Foreign key integrity 100% (0 orphaned records)
   - ✓ Realistic product names and pricing
   - ✓ Proper temporal distribution (2023-2024)

**Key Decisions:**
- Used Faker library for realistic company names while manually curating product catalog for brand authenticity
- Implemented Q4 seasonality with 1.5x quantity multiplier applied probabilistically
- Set random seed (42) for reproducible demo data
- Created comprehensive logging in db_manager for debugging

**Performance Notes:**
- Database seeding completes in <10 seconds
- All 200 products have realistic brand names (Samsung, Apple, Nike, etc.)
- Revenue calculations accurate (quantity * product price)

### Files Modified

**Created:**
- `backend/database/__init__.py` - Package initialization
- `backend/database/schema.py` - SQLAlchemy models (Client, Product, Sale, CustomerSegment)
- `backend/database/seed_data.py` - Data generation script with Faker integration
- `backend/database/db_manager.py` - Database utilities and initialization
- `backend/requirements.txt` - Python dependencies (SQLAlchemy, Faker)
- `data/text_to_sql_poc.db` - SQLite database file (generated)

**Modified:**
- N/A (greenfield implementation)

### Test Results

**Database Verification Results:**

```
Table Row Counts:
  clients                  10 rows ✓
  products                200 rows ✓
  sales                  2000 rows ✓
  customer_segments        30 rows ✓

Quarterly Sales Distribution:
  Q1:  493 sales, $5,544,306.41 revenue
  Q2:  470 sales, $5,145,270.91 revenue
  Q3:  495 sales, $5,828,381.98 revenue
  Q4:  542 sales, $7,635,025.53 revenue ✓ (highest)

Foreign Key Integrity:
  Products without valid client: 0 ✓
  Sales without valid client: 0 ✓
  Sales without valid product: 0 ✓

Sample Data Quality:
  ✓ Realistic company names (Webb Inc, Rivera LLC, etc.)
  ✓ Authentic product brands (Samsung, Apple, Nike, Dyson)
  ✓ Proper price ranges by category
  ✓ Date range spans 2023-2024
  ✓ Regional distribution (North, South, East, West)
```

**All Acceptance Criteria: PASSED ✓**

---

## Review Notes

<!-- Will be populated during code review -->
