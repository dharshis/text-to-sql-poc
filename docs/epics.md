# text-to-sql-poc - Epic Breakdown

**Date:** 2025-11-25
**Project Level:** Simple (Quick Flow)

---

## Epic 1: Text-to-SQL POC Development

**Slug:** text-to-sql-poc

### Goal

Build a proof-of-concept text-to-SQL system that demonstrates technical feasibility as an alternative to Number Station. The POC will showcase natural language query translation, client data isolation, and local deployment for a client demo.

### Scope

**In Scope:**
- SQLite database with sample retail market research data (5-10 clients, ~200 products, ~2000 sales)
- Flask backend API with Claude 4.5 Sonnet integration for SQL generation
- SQL validation layer enforcing client data isolation
- React frontend with Material-UI for query input and results display
- Recharts visualizations (bar, line, pie charts)
- Multi-client switching demonstration
- 5-8 prepared demo queries with validation metrics
- Local deployment (no cloud infrastructure)

**Out of Scope:**
- User authentication or multi-user support
- Query history or persistence
- Production deployment infrastructure
- Advanced SQL parsing (AST-based validation)
- Query result export functionality
- Real-time database connections

### Success Criteria

**POC is successful if:**
1. Natural language queries correctly translate to valid SQL
2. Client isolation validation works (rejects queries without client_id filters)
3. Multi-client switching demonstrates no data leakage
4. System runs 100% locally
5. Response time < 5 seconds per query
6. 5-8 demo queries work reliably for presentation
7. UI is professional enough for stakeholder demo
8. Stakeholders respond: "Yes, we can build this"

###

 Dependencies

**External Dependencies:**
- Anthropic Claude API (requires API key)
- Python 3.13.9 installed
- Node.js 24.10.0 installed

**No Internal Dependencies:** Greenfield project, no existing systems to integrate with.

---

## Story Map - Epic 1

```
Foundation Layer (Story 1)
  └─ Database + Sample Data Generation
       ↓
Backend Layer (Stories 2-3)
  ├─ Backend API + Claude Integration (Story 2)
  └─ SQL Validator + Security (Story 3)
       ↓
Frontend Layer (Story 4)
  └─ React UI + Visualization (Story 4)
       ↓
Integration Layer (Story 5)
  └─ End-to-End Testing + Demo Polish (Story 5)
```

**Development Approach:** Bottom-up
- Build foundation first (database)
- Then backend capabilities (API + validation)
- Then frontend interface
- Finally integrate and polish for demo

---

## Stories - Epic 1

### Story 1.1: Database Foundation and Sample Data Generation

As a **developer**,
I want **a SQLite database with realistic retail market research sample data**,
So that **I can test and demonstrate text-to-SQL queries against a representative dataset**.

**Acceptance Criteria:**

**Given** I run the data generation script
**When** the script completes successfully
**Then** a SQLite database file is created at `data/text_to_sql_poc.db`

**And** the database contains:
- 5-10 client records with realistic company names and industries
- ~200 product records with realistic names, categories (electronics, apparel, home goods), and prices
- ~2000 sales records with temporal patterns (Q4 higher volume) across 2023-2024
- Customer segment data (Premium, Standard, Budget) for each client
- Proper foreign key relationships between tables

**Prerequisites:** None (first story)

**Technical Notes:** Use Faker library for realistic product names. Implement schema with SQLAlchemy models.

---

### Story 1.2: Backend API with Claude Integration

As a **developer**,
I want **a Flask REST API that accepts natural language queries and uses Claude to generate SQL**,
So that **I can translate user questions into executable database queries**.

**Acceptance Criteria:**

**Given** the Flask server is running and database exists
**When** I POST to `/query` with `{query: "Show me top products", client_id: 1}`
**Then** the API responds with `{sql: "SELECT...", results: [...], validation: {...}, metrics: {...}}`

**And** the generated SQL includes appropriate WHERE clause for client_id
**And** the SQL is executed against the database
**And** results are returned as JSON array

**Prerequisites:** Story 1.1 (database must exist)

**Technical Notes:** Use Anthropic Python SDK 0.40.0+. Implement prompt engineering for schema context injection.

---

### Story 1.3: SQL Validation and Security Layer

As a **developer**,
I want **SQL validation that enforces client data isolation**,
So that **queries cannot access other clients' data and the POC demonstrates security capability**.

**Acceptance Criteria:**

**Given** the backend receives a generated SQL query
**When** the validator checks the query
**Then** validation passes if `WHERE client_id = X` is present

**And** validation fails if client_id is missing or references multiple clients
**And** validation fails if destructive keywords (DROP, DELETE, UPDATE) are present
**And** validation metrics are returned: `{passed: boolean, checks: array, warnings: array}`

**Prerequisites:** Story 1.2 (backend API must exist)

**Technical Notes:** Use regex-based validation (basic approach for POC). Check for client_id presence, single client enforcement, read-only operations.

---

### Story 1.4: React Frontend with Visualization

As a **market researcher (end user)**,
I want **a clean web interface where I can select a client, enter a natural language query, and see results with visualizations**,
So that **I can query data without writing SQL**.

**Acceptance Criteria:**

**Given** the React application is running
**When** I load the page
**Then** I see a client dropdown selector and query input field

**And** when I select a client and enter a query
**And** click Search
**Then** I see:
- Loading indicator during API call
- Recharts visualization (bar/line/pie based on data type)
- MUI data table with query results
- Generated SQL query display
- Validation metrics (color-coded chips: green=PASS, red=FAIL)

**And** I can switch clients and run new queries

**Prerequisites:** Stories 1.2 and 1.3 (backend API + validation must exist)

**Technical Notes:** Use Material-UI 6.3.0 for components, Recharts 2.15.0 for charts, Axios for API calls. Implement auto-detect chart type based on result structure.

---

### Story 1.5: Integration Testing and Demo Preparation

As a **product team member preparing for client demo**,
I want **end-to-end tested demo queries with polished UI and error handling**,
So that **we can confidently present the POC to stakeholders**.

**Acceptance Criteria:**

**Given** all previous stories are complete
**When** I test each of 5-8 prepared demo queries
**Then** each query completes successfully within 5 seconds

**And** multi-client switching works without data leakage
**And** validation correctly shows PASS for valid queries
**And** error handling displays user-friendly messages for failures
**And** UI is polished (loading states, proper spacing, professional colors)

**And** I have a demo script documenting:
- Which client to select for each query
- Expected results for each query
- Key talking points about validation and security

**Prerequisites:** Stories 1.1, 1.2, 1.3, 1.4 (entire system must be complete)

**Technical Notes:** Prepare 5-8 realistic market research queries. Test edge cases (API timeout, SQL errors, validation failures). Create demo script checklist.

---

## Implementation Timeline - Epic 1

**Total Stories:** 5

**Story Points Distribution:**
- Story 1.1 (Database): 3 points
- Story 1.2 (Backend API): 5 points
- Story 1.3 (Validator): 3 points
- Story 1.4 (Frontend): 5 points
- Story 1.5 (Integration): 3 points

**Total Story Points:** 19 points

**Implementation Approach:** Sequential bottom-up development with testing at each layer.

---

_Epic breakdown complete. Individual story files created in sprint_artifacts/ directory._

_Next: DEV agent to implement stories sequentially, starting with Story 1.1._
