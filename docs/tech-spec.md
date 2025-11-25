# text-to-sql-poc - Technical Specification

**Author:** DS
**Date:** 2025-11-25
**Project Level:** Simple (Quick Flow)
**Change Type:** New Feature - POC Development
**Development Context:** Greenfield - Client Proposal Demo

---

## Context

### Available Documents

**Loaded Documents:**
- ✅ **Product Brief** (product-brief-text-to-sql-poc-2025-11-25.md)
  - Comprehensive POC vision and requirements
  - Architecture overview and security guardrails
  - MVP scope with 6 core features
  - Success criteria and risk assessment

**Key Insights from Brief:**
- **Strategic Goal:** Build vs. buy decision - prove technical feasibility as Number Station alternative
- **Target Users:** Market researchers (non-technical) needing self-service SQL access
- **Critical Requirement:** Multi-client data isolation (cannot access other clients' data)
- **Demo Focus:** 5-8 prepared queries, local deployment, professional UI

### Project Stack

**Current Environment:**
- Python 3.13.9 (latest stable)
- Node.js 24.10.0 (latest LTS)
- No existing dependencies (greenfield)

**Technology Decisions (Data-Driven):**

Based on 2025 research for rapid POC development:
- **Backend Framework:** Flask (chosen over FastAPI for faster MVP prototyping - "easier to build MVPs and prototypes using Flask")
- **Frontend UI:** Material-UI/MUI (chosen over Ant Design for simpler setup, better docs, smaller bundle)
- **Charting:** Recharts (chosen over Chart.js for React-native components, single-package install)
- **Database:** SQLite (single-file simplicity for local demo)
- **LLM:** Claude 4.5 Sonnet via Anthropic Python SDK

### Existing Codebase Structure

Greenfield project - establishing new codebase structure.

**Planned Structure:**
```
text-to-sql-poc/
├── backend/           # Python Flask API
│   ├── app.py        # Main Flask application
│   ├── database/     # SQLite setup and data generation
│   ├── services/     # Claude integration, SQL validator
│   └── requirements.txt
├── frontend/         # React + MUI application
│   ├── src/
│   │   ├── components/  # Search, Results, Charts
│   │   ├── services/    # API client
│   │   └── App.js
│   └── package.json
├── data/            # SQLite database file
└── docs/            # Documentation and diagrams
```

---

## The Change

### Problem Statement

The client serves market researchers across multiple industries who currently depend on Number Station (external text-to-SQL service) for data access. This creates:

**Business Problems:**
- High licensing costs that don't scale with multi-domain business model
- Performance latency impacting researcher productivity
- Vendor lock-in limiting customization and integration
- No control over feature roadmap or model improvements

**Technical Gap:**
- Need to prove that in-house text-to-SQL solution is technically feasible
- Must demonstrate comparable functionality to Number Station
- Must show data isolation can be enforced (critical security requirement)
- Must run 100% locally (data privacy advantage)

**User Pain:**
Market researchers without SQL expertise face bottlenecks:
- Wait for data engineers to write queries
- Slow response times from external service
- Cannot customize queries for specific analysis needs
- Limited by vendor's feature set

### Proposed Solution

Build a proof-of-concept text-to-SQL system that demonstrates:

1. **Core Capability:** Natural language → SQL → Results → Visualizations
2. **Security:** Client data isolation through validation layer
3. **Performance:** Local deployment for faster response times
4. **Transparency:** Display generated SQL and validation metrics
5. **Professional UX:** Clean interface suitable for stakeholder demo

**Solution Architecture:**
```
User Input (NL Query + Client Selection)
  ↓
React Frontend (MUI Search Interface)
  ↓
Flask Backend API (/query endpoint)
  ↓
Claude 4.5 Sonnet (SQL Generation with schema context)
  ↓
SQL Validator (Client isolation checks)
  ↓
SQLite Database (Sample retail data)
  ↓
Results + Metrics
  ↓
Frontend Display (Recharts + Data Table + SQL + Validation)
```

**Implementation Approach:** Bottom-up
- Story 1: Database foundation
- Story 2: Backend API + LLM
- Story 3: Security validation
- Story 4: Frontend + visualization
- Story 5: Integration + demo polish

### Scope

**In Scope:**

1. **Database & Sample Data**
   - SQLite database setup
   - 5-10 sample retail clients
   - ~200 realistic product records (electronics, apparel, home goods)
   - ~2000 synthetic sales records with temporal patterns
   - Customer segment data
   - Schema: clients, products, sales, customer_segments

2. **Backend API**
   - Flask REST API with /query endpoint
   - Claude 4.5 Sonnet integration for SQL generation
   - Schema context injection in LLM prompts
   - Client_id enforcement in prompts

3. **SQL Validation Layer**
   - Basic string/regex validation for client_id presence
   - Validation metrics: correctness, safety, performance
   - Visual validation indicators for demo

4. **Frontend Application**
   - React + Material-UI search interface
   - Client dropdown selector (multi-client switching)
   - Query input field
   - Results display: Recharts visualizations + data table
   - Generated SQL display
   - Validation metrics display

5. **Demo Preparation**
   - 5-8 prepared demo queries
   - Multi-client demonstration capability
   - Professional UI polish
   - Error handling and loading states

**Out of Scope:**

- Multi-turn conversational queries
- Query history or persistence
- User authentication system
- Production deployment infrastructure
- Advanced visualizations (heatmaps, geo maps)
- Query result export functionality
- Performance optimization for large datasets
- Multi-database support
- Real-time data connections
- Advanced SQL parsing (AST-based validation)
- Query refinement features
- Natural language result explanations

---

## Implementation Details

### Source Tree Changes

**CREATE - Backend Structure:**
```
backend/
├── app.py                          # Flask application entry point
├── config.py                       # Configuration (Claude API key, DB path)
├── requirements.txt                # Python dependencies
├── database/
│   ├── __init__.py
│   ├── schema.py                   # SQLAlchemy models
│   ├── seed_data.py               # Sample data generation script
│   └── db_manager.py              # Database initialization and queries
├── services/
│   ├── __init__.py
│   ├── claude_service.py          # Claude API integration
│   ├── sql_validator.py           # Client isolation validation
│   └── query_executor.py          # Safe SQL execution
└── routes/
    ├── __init__.py
    └── query_routes.py            # /query endpoint handler
```

**CREATE - Frontend Structure:**
```
frontend/
├── package.json                    # Node dependencies
├── public/
│   └── index.html
└── src/
    ├── App.js                      # Main application component
    ├── index.js                    # React entry point
    ├── components/
    │   ├── SearchBar.js           # Query input + client selector
    │   ├── ResultsDisplay.js      # Main results container
    │   ├── DataVisualization.js   # Recharts component
    │   ├── DataTable.js           # MUI table for raw data
    │   ├── SqlDisplay.js          # Generated SQL viewer
    │   └── ValidationMetrics.js   # Security validation indicators
    ├── services/
    │   └── api.js                 # Axios backend API client
    └── styles/
        └── theme.js               # MUI theme configuration
```

**CREATE - Data Directory:**
```
data/
└── text_to_sql_poc.db             # SQLite database file (generated)
```

### Technical Approach

**Backend Implementation:**

1. **Flask API Setup**
   - Flask 3.1.0 for REST API
   - Flask-CORS for frontend communication
   - Single POST /query endpoint accepting: `{query: string, client_id: int}`
   - Returns: `{sql: string, results: array, validation: object, metrics: object}`

2. **Claude Integration**
   - Anthropic Python SDK 0.40.0+
   - Model: claude-4-5-sonnet-20250929
   - Prompt structure:
     ```
     System: You are a SQL expert. Generate SQLite queries for retail market research data.

     Schema: [inject full schema with table definitions]

     Rules:
     - ALWAYS include WHERE client_id = {client_id} in queries
     - Use JOIN when querying across tables
     - Return only the SQL query, no explanations

     User Query: {natural_language_query}
     Client Context: client_id = {client_id}
     ```
   - Timeout: 10 seconds
   - Error handling: Catch API errors, return user-friendly messages

3. **SQL Validation (Basic)**
   - Regex pattern: `WHERE\s+.*client_id\s*=\s*\d+`
   - Additional checks:
     - No multiple client_id values (prevent OR conditions)
     - No DROP/DELETE/UPDATE statements (read-only)
     - Validate against schema (table/column existence)
   - Validation result: `{passed: boolean, checks: array, warnings: array}`

4. **Query Execution**
   - SQLAlchemy 2.0+ for safe parameterized queries
   - Execute as read-only transaction
   - Limit results to 1000 rows (demo safety)
   - Capture execution time for metrics
   - Error handling: SQL errors → user-friendly messages

**Frontend Implementation:**

1. **Material-UI Setup**
   - @mui/material 6.3.0+
   - @emotion/react and @emotion/styled (MUI dependencies)
   - Theme: Professional blue/gray palette
   - Responsive layout (desktop-focused for demo)

2. **Search Interface**
   - MUI Select dropdown for client selection (populated from /clients endpoint)
   - MUI TextField for query input (multiline, placeholder with examples)
   - MUI Button for submit
   - Loading state with CircularProgress

3. **Results Display**
   - Recharts 2.15.0+ for visualizations
     - Auto-detect chart type from data structure:
       - Time series → LineChart
       - Comparisons → BarChart
       - Proportions → PieChart
     - Responsive width, fixed height (400px)
   - MUI TableContainer + Table for raw data
     - Sortable columns
     - Pagination for > 50 rows
   - SQL display in MUI Card with syntax highlighting (simple)
   - Validation metrics as MUI Chip components with color coding

4. **State Management**
   - React hooks (useState, useEffect)
   - No Redux/Context needed for POC simplicity

### Existing Patterns to Follow

Greenfield project - establishing new patterns:

**Code Style:**
- Python: PEP 8 (Black formatter)
- JavaScript: ES6+, functional components, arrow functions
- Naming: snake_case (Python), camelCase (JavaScript)

**Error Handling:**
- Backend: Try/except with logging, return error status codes
- Frontend: Try/catch in async calls, display MUI Alert on errors

**Testing Pattern (to be established):**
- Backend: pytest for unit tests
- Frontend: Jest + React Testing Library
- Manual testing for POC demo validation

### Integration Points

**Internal Integrations:**

1. **Frontend → Backend API**
   - Endpoint: POST http://localhost:5000/query
   - Headers: Content-Type: application/json
   - Request: `{query: string, client_id: number}`
   - Response: `{sql, results, validation, metrics, error?}`

2. **Backend → Claude API**
   - Anthropic API: https://api.anthropic.com/v1/messages
   - Authentication: API key in headers (x-api-key)
   - Model: claude-4-5-sonnet-20250929
   - Max tokens: 1000 (sufficient for SQL queries)

3. **Backend → SQLite Database**
   - Connection: SQLAlchemy engine
   - Path: ../data/text_to_sql_poc.db
   - Read-only mode for query execution
   - Connection pooling: disabled (single-user demo)

**External Dependencies:**
- Claude API (Anthropic) - requires API key
- No other external services

---

## Development Context

### Relevant Existing Code

N/A - Greenfield project. No existing code to reference.

### Dependencies

**Framework/Libraries:**

**Backend (Python 3.13.9):**
- Flask==3.1.0 - Web framework
- flask-cors==5.0.0 - CORS support for frontend
- anthropic==0.40.0 - Claude API SDK
- sqlalchemy==2.0.36 - Database ORM
- python-dotenv==1.0.1 - Environment variable management
- Faker==33.1.0 - Realistic product data generation

**Frontend (Node.js 24.10.0):**
- react==18.3.1 - UI framework
- react-dom==18.3.1 - React DOM renderer
- @mui/material==6.3.0 - Material-UI component library
- @emotion/react==11.14.0 - MUI styling dependency
- @emotion/styled==11.14.0 - MUI styling dependency
- recharts==2.15.0 - Charting library
- axios==1.7.9 - HTTP client for API calls

**Dev Dependencies:**
- Backend: pytest==8.3.4, black==24.10.0, flake8==7.1.1
- Frontend: @vitejs/plugin-react==4.3.4, vite==6.0.7

### Internal Modules

**Backend Modules:**
- `database.schema` - SQLAlchemy models (Client, Product, Sale, CustomerSegment)
- `database.seed_data` - Data generation logic using Faker
- `database.db_manager` - Database initialization and query helpers
- `services.claude_service` - Claude API wrapper with prompt engineering
- `services.sql_validator` - Validation logic for client_id enforcement
- `services.query_executor` - Safe SQL execution with error handling
- `routes.query_routes` - Flask route handlers

**Frontend Modules:**
- `services/api` - Axios client for backend communication
- `components/*` - Reusable React components
- `styles/theme` - MUI theme configuration

### Configuration Changes

**Environment Variables (.env file):**
```
# Backend configuration
ANTHROPIC_API_KEY=sk-ant-xxx...  # Claude API key (user must provide)
DATABASE_PATH=../data/text_to_sql_poc.db
FLASK_ENV=development
FLASK_DEBUG=True
CORS_ORIGINS=http://localhost:5173  # Vite dev server

# Frontend configuration (in .env for Vite)
VITE_API_URL=http://localhost:5000
```

**Configuration Files to Create:**
- backend/config.py - Load environment variables, set Flask config
- frontend/vite.config.js - Vite build configuration
- backend/.env.example - Template for required environment variables

**No package.json/requirements.txt yet** - will be created in Story 1 and 2.

### Existing Conventions (Brownfield)

N/A - Greenfield project.

**Establishing Conventions:**
- File naming: lowercase with underscores (Python), PascalCase for components (React)
- Module organization: Feature-based (services, routes, components)
- Import order: Standard library → Third-party → Local modules
- Documentation: Docstrings for Python functions, JSDoc for complex React functions
- Logging: Python logging module with INFO level for development

### Test Framework & Standards

**Test Framework Selection:**

**Backend:**
- pytest 8.3.4 - Python testing framework
- Coverage target: 70%+ for core services (claude_service, sql_validator)
- Test file naming: test_*.py
- Test location: backend/tests/

**Frontend:**
- Jest 29.7.0 (bundled with React)
- React Testing Library 16.1.0
- Coverage target: 60%+ for components
- Test file naming: *.test.js
- Test location: frontend/src/__tests__/

**Testing Standards:**
- Unit tests for business logic (Claude prompts, validation rules, data generation)
- Integration tests for API endpoints
- Component tests for React UI
- Manual testing for end-to-end demo scenarios
- NO E2E automation for POC (manual testing sufficient)

---

## Implementation Stack

**Runtime Environment:**
- Python 3.13.9
- Node.js 24.10.0
- SQLite 3.x (bundled with Python)

**Backend Stack:**
- Flask 3.1.0 (Web framework)
- Anthropic SDK 0.40.0 (Claude API)
- SQLAlchemy 2.0.36 (ORM)
- Flask-CORS 5.0.0 (CORS handling)
- python-dotenv 1.0.1 (Config management)
- Faker 33.1.0 (Data generation)

**Frontend Stack:**
- React 18.3.1 (UI framework)
- Material-UI 6.3.0 (Component library)
- Recharts 2.15.0 (Charting)
- Axios 1.7.9 (HTTP client)
- Vite 6.0.7 (Build tool)
- @emotion 11.14.0 (Styling)

**Development Tools:**
- pytest 8.3.4 (Backend testing)
- Jest 29.7.0 (Frontend testing)
- Black 24.10.0 (Python formatting)
- ESLint 9.x (JavaScript linting)

**Database:**
- SQLite 3.x (File-based, zero-config)

**External Services:**
- Anthropic Claude API (Claude 4.5 Sonnet)

---

## Technical Details

### Database Schema Design

**Table: clients**
```sql
CREATE TABLE clients (
    client_id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_name TEXT NOT NULL,
    industry TEXT NOT NULL
);
```

**Table: products**
```sql
CREATE TABLE products (
    product_id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    product_name TEXT NOT NULL,
    category TEXT NOT NULL,  -- electronics, apparel, home_goods
    brand TEXT NOT NULL,
    price REAL NOT NULL,
    FOREIGN KEY (client_id) REFERENCES clients(client_id)
);
```

**Table: sales**
```sql
CREATE TABLE sales (
    sale_id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    region TEXT NOT NULL,  -- North, South, East, West
    date TEXT NOT NULL,    -- ISO format: YYYY-MM-DD
    quantity INTEGER NOT NULL,
    revenue REAL NOT NULL,
    FOREIGN KEY (client_id) REFERENCES clients(client_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);
```

**Table: customer_segments**
```sql
CREATE TABLE customer_segments (
    segment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    segment_name TEXT NOT NULL,  -- Premium, Standard, Budget
    demographics TEXT,            -- JSON string: {"age_range": "25-34", "income": "high"}
    FOREIGN KEY (client_id) REFERENCES clients(client_id)
);
```

**Indexes (for demo performance):**
```sql
CREATE INDEX idx_sales_client_date ON sales(client_id, date);
CREATE INDEX idx_products_client_category ON products(client_id, category);
```

### Data Generation Logic

**Client Data:**
- 5-10 retail companies with industry variations
- Industries: Retail, Consumer Goods, E-commerce, Fashion, Electronics
- Names: Mix of realistic company names (using Faker)

**Product Data:**
- ~200 products total (~20-40 per client)
- Categories: electronics (40%), apparel (30%), home_goods (30%)
- Realistic product names: "Samsung Galaxy S24", "Nike Air Max", "Dyson V15"
- Price ranges: Electronics ($50-$2000), Apparel ($20-$300), Home Goods ($30-$800)
- Brands: Mix of real brand names

**Sales Data:**
- ~2000 sales records total
- Date range: 2023-01-01 to 2024-12-31 (2 years)
- Temporal patterns: Higher volume in Q4 (holiday season)
- Regional distribution: Varied across North, South, East, West
- Quantity: 1-50 units per sale
- Revenue: quantity * product price

**Customer Segments:**
- 3 segments per client: Premium, Standard, Budget
- Demographics as JSON: age ranges, income levels

### Claude Prompt Engineering

**System Prompt Template:**
```python
SYSTEM_PROMPT = """You are an expert SQL query generator for SQLite databases.
You specialize in retail market research data analysis.

DATABASE SCHEMA:
{schema_definition}

CRITICAL RULES:
1. ALWAYS include "WHERE client_id = {client_id}" in your queries
2. Use ONLY the tables and columns defined in the schema
3. Generate valid SQLite syntax
4. Return ONLY the SQL query - no explanations or markdown
5. Use appropriate JOINs when querying multiple tables
6. For aggregations, use GROUP BY and appropriate aggregate functions
7. Limit results to 100 rows unless explicitly requested otherwise

EXAMPLE QUERIES:
- "Top 10 products by revenue for client 3":
  SELECT product_name, SUM(revenue) as total_revenue
  FROM sales s JOIN products p ON s.product_id = p.product_id
  WHERE s.client_id = 3
  GROUP BY product_name
  ORDER BY total_revenue DESC
  LIMIT 10
"""

USER_PROMPT_TEMPLATE = """
Client Context: client_id = {client_id}, client_name = "{client_name}"

Natural Language Query: {user_query}

Generate the SQL query:
"""
```

**Error Handling:**
- API timeout: Return error after 10 seconds
- Invalid response: Fallback to error message, log for debugging
- Rate limiting: Implement exponential backoff (not needed for POC demo)

### SQL Validation Algorithm

**Basic Validation Steps:**

```python
def validate_sql_for_client_isolation(sql_query, expected_client_id):
    """
    Basic string-based validation for POC demonstration.
    Returns: {passed: bool, checks: list, warnings: list}
    """
    checks = []
    warnings = []
    passed = True

    # Check 1: Contains WHERE clause with client_id
    client_id_pattern = rf"WHERE\s+.*client_id\s*=\s*{expected_client_id}"
    if not re.search(client_id_pattern, sql_query, re.IGNORECASE):
        passed = False
        checks.append({"name": "Client ID Filter", "status": "FAIL",
                      "message": f"Missing WHERE client_id = {expected_client_id}"})
    else:
        checks.append({"name": "Client ID Filter", "status": "PASS"})

    # Check 2: No multiple client IDs (prevent OR leakage)
    other_clients_pattern = r"client_id\s*=\s*(?!" + str(expected_client_id) + r")\d+"
    if re.search(other_clients_pattern, sql_query):
        passed = False
        checks.append({"name": "Single Client", "status": "FAIL",
                      "message": "Query references multiple client IDs"})
    else:
        checks.append({"name": "Single Client", "status": "PASS"})

    # Check 3: No destructive operations (read-only)
    destructive_keywords = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER"]
    for keyword in destructive_keywords:
        if keyword in sql_query.upper():
            passed = False
            checks.append({"name": "Read-Only", "status": "FAIL",
                          "message": f"Destructive keyword detected: {keyword}"})
            break
    else:
        checks.append({"name": "Read-Only", "status": "PASS"})

    # Warning: Multiple WHERE conditions (informational)
    where_count = sql_query.upper().count("WHERE")
    if where_count > 1:
        warnings.append("Multiple WHERE clauses detected - verify JOIN logic")

    return {
        "passed": passed,
        "checks": checks,
        "warnings": warnings
    }
```

### Chart Type Selection Logic

**Auto-detect visualization type from query results:**

```javascript
function selectChartType(results, query) {
  // If results contain date/time column → Line Chart
  const hasDateColumn = results.columns.some(col =>
    col.toLowerCase().includes('date') ||
    col.toLowerCase().includes('month') ||
    col.toLowerCase().includes('quarter')
  );
  if (hasDateColumn) return 'line';

  // If results have 2 columns with numeric aggregation → Bar Chart
  if (results.columns.length === 2 &&
      typeof results.data[0][results.columns[1]] === 'number') {
    return 'bar';
  }

  // If results show proportions/percentages → Pie Chart
  if (results.columns.some(col =>
    col.toLowerCase().includes('percent') ||
    col.toLowerCase().includes('share')
  )) {
    return 'pie';
  }

  // Default: Bar Chart for comparisons
  return 'bar';
}
```

### Performance Considerations

**POC Performance Targets:**
- Claude API response: < 3 seconds (typical: 1-2 seconds)
- SQL execution: < 500ms (dataset is small)
- Frontend render: < 100ms (2000 rows max)
- Total query time: < 5 seconds (POC acceptable)

**Optimizations:**
- Database indexes on frequently queried columns
- Limit query results to 1000 rows
- No complex query optimization (SQLite handles small datasets well)
- Frontend: React.memo for chart components (prevent unnecessary re-renders)

**Not Optimized (Out of Scope):**
- Caching of queries or results
- Query result pagination on backend
- Claude API response streaming
- Frontend virtualization for large tables

### Security Considerations

**POC Security Scope:**

**Implemented:**
- Client ID validation (basic string checks)
- Read-only SQL execution (no writes)
- API key security (environment variables)
- CORS restrictions (localhost only)

**NOT Implemented (Out of Scope for POC):**
- SQL injection protection (parameterization would be production requirement)
- Authentication/authorization
- Rate limiting
- Input sanitization beyond validation
- Audit logging
- API key rotation

**Demo Security Focus:**
- Showcase client isolation concept
- Display validation metrics visually
- Demonstrate that architecture CAN enforce security

---

## Development Setup

**Prerequisites:**
- Python 3.13.9 installed
- Node.js 24.10.0 installed
- Claude API key (from Anthropic console)
- Git (for version control)
- Code editor (VS Code recommended)

**Initial Setup Steps:**

1. **Clone Repository (if not already done)**
   ```bash
   git clone <repository-url>
   cd text-to-sql-poc
   ```

2. **Backend Setup**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Create Environment File**
   ```bash
   cp .env.example .env
   # Edit .env and add your ANTHROPIC_API_KEY
   ```

4. **Initialize Database**
   ```bash
   python -m database.seed_data
   ```

5. **Frontend Setup**
   ```bash
   cd ../frontend
   npm install
   ```

6. **Run Development Servers**
   ```bash
   # Terminal 1 - Backend
   cd backend
   source venv/bin/activate
   flask run --port 5000

   # Terminal 2 - Frontend
   cd frontend
   npm run dev
   ```

7. **Access Application**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:5000

**Development Workflow:**
- Backend changes: Flask auto-reloads on file changes
- Frontend changes: Vite hot-reloads in browser
- Database changes: Re-run seed_data script

---

## Implementation Guide

### Setup Steps

**Pre-Implementation Checklist:**

1. ✅ Verify Python 3.13.9 installed: `python3 --version`
2. ✅ Verify Node.js 24.10.0 installed: `node --version`
3. ✅ Obtain Claude API key from Anthropic console
4. ✅ Create project directory structure
5. ✅ Initialize git repository: `git init`
6. ✅ Create .gitignore (ignore venv/, node_modules/, .env, *.db)

### Implementation Steps

**Story-by-Story Implementation Order:**

**Story 1: Database Foundation**
1. Create backend/ directory structure
2. Set up SQLAlchemy models (schema.py)
3. Implement data generation script (seed_data.py using Faker)
4. Generate SQLite database with sample data
5. Verify data: Query database to confirm realistic products, synthetic sales

**Story 2: Backend API + Claude**
1. Initialize Flask application (app.py)
2. Create requirements.txt with Flask, anthropic, sqlalchemy, flask-cors
3. Implement Claude service (claude_service.py) with prompt engineering
4. Create /query endpoint (query_routes.py)
5. Test Claude integration manually with curl/Postman
6. Verify SQL generation for sample queries

**Story 3: SQL Validator**
1. Implement sql_validator.py with regex-based validation
2. Integrate validator into /query endpoint
3. Return validation metrics in API response
4. Test with valid and invalid client_id scenarios
5. Verify validation catches missing client_id filters

**Story 4: Frontend + Visualization**
1. Initialize React app with Vite
2. Create package.json with MUI, Recharts, Axios
3. Implement SearchBar component (client selector + query input)
4. Implement ResultsDisplay component container
5. Implement DataVisualization (Recharts with auto-detect logic)
6. Implement DataTable (MUI Table)
7. Implement SqlDisplay and ValidationMetrics components
8. Connect to backend API via Axios
9. Test with backend running

**Story 5: Integration + Demo Polish**
1. Prepare 5-8 demo queries with expected results
2. Test end-to-end flow for each demo query
3. Add loading states and error handling
4. Polish UI (spacing, colors, responsiveness)
5. Add client context display ("Viewing as: Client X")
6. Verify multi-client switching works correctly
7. Test validation failure scenarios
8. Create demo script/checklist for presentation

### Testing Strategy

**Unit Testing:**
- Backend:
  - test_claude_service.py: Test prompt generation, API mocking
  - test_sql_validator.py: Test validation logic with various SQL patterns
  - test_seed_data.py: Verify data generation produces expected schema
- Frontend:
  - SearchBar.test.js: Test input handling and client selection
  - DataVisualization.test.js: Test chart type selection logic
  - api.test.js: Test API client with mocked responses

**Integration Testing:**
- test_query_endpoint.py: Test /query endpoint end-to-end
- Mock Claude API responses to avoid API costs during testing
- Verify validation integration with query execution

**Manual Testing (Critical for Demo):**
- Test each of 5-8 prepared demo queries
- Verify client switching works without data leakage
- Test error scenarios: Invalid query, API timeout, validation failure
- Verify UI displays correctly on demo machine (browser, screen resolution)
- Test performance: Ensure < 5 second response times

**Coverage Goals:**
- Backend core services: 70%+ (claude_service, sql_validator)
- Frontend components: 60%+
- Manual testing: 100% coverage of demo scenarios

### Acceptance Criteria

**Story 1 - Database Complete:**
- ✅ SQLite database file created at data/text_to_sql_poc.db
- ✅ 5-10 clients with realistic names and industries
- ✅ ~200 products with realistic names, categories, prices
- ✅ ~2000 sales records with temporal patterns (2023-2024)
- ✅ Customer segments for each client
- ✅ Can query database manually and see data

**Story 2 - Backend API Complete:**
- ✅ Flask server runs on localhost:5000
- ✅ POST /query endpoint accepts {query, client_id}
- ✅ Claude API integration generates SQL from natural language
- ✅ Returns SQL query in response
- ✅ Handles errors gracefully (API timeouts, invalid queries)
- ✅ Can test via curl/Postman

**Story 3 - Validator Complete:**
- ✅ Validation logic checks for client_id presence
- ✅ Validation metrics returned in API response
- ✅ Validation PASS for correct queries
- ✅ Validation FAIL for queries without client_id
- ✅ Read-only check prevents DROP/DELETE/UPDATE

**Story 4 - Frontend Complete:**
- ✅ React app runs on localhost:5173
- ✅ Client dropdown populated with database clients
- ✅ Query input field accepts natural language
- ✅ Submit button triggers API call
- ✅ Results display shows: Chart + Table + SQL + Validation
- ✅ Loading state during API call
- ✅ Error alerts for API failures

**Story 5 - Demo Ready:**
- ✅ 5-8 prepared demo queries documented
- ✅ Each demo query works reliably end-to-end
- ✅ Multi-client switching works without errors
- ✅ UI is polished and professional for presentation
- ✅ Response times < 5 seconds for all demo queries
- ✅ Validation metrics display correctly
- ✅ Can run demo without internet (except Claude API)

**Overall POC Success Criteria:**
- ✅ Demonstrates "yes, we can build this" to stakeholders
- ✅ Natural language → SQL → Results flow works
- ✅ Client isolation concept proven through validation
- ✅ Local deployment working
- ✅ Professional UI suitable for client presentation

---

## Developer Resources

### File Paths Reference

**Backend Files:**
```
backend/
├── app.py                          # Flask application entry
├── config.py                       # Configuration loader
├── requirements.txt                # Python dependencies
├── .env                           # Environment variables (git ignored)
├── .env.example                   # Environment template
├── database/
│   ├── __init__.py
│   ├── schema.py                  # SQLAlchemy models
│   ├── seed_data.py              # Data generation
│   └── db_manager.py             # Database utilities
├── services/
│   ├── __init__.py
│   ├── claude_service.py         # Claude API wrapper
│   ├── sql_validator.py          # Validation logic
│   └── query_executor.py         # SQL execution
├── routes/
│   ├── __init__.py
│   └── query_routes.py           # API endpoints
└── tests/
    ├── __init__.py
    ├── test_claude_service.py
    ├── test_sql_validator.py
    └── test_query_endpoint.py
```

**Frontend Files:**
```
frontend/
├── package.json                   # Node dependencies
├── vite.config.js                # Vite configuration
├── index.html                    # HTML entry point
├── .env                          # Frontend env vars (git ignored)
└── src/
    ├── App.js                    # Main React component
    ├── index.js                  # React entry point
    ├── components/
    │   ├── SearchBar.js          # Query input + client selector
    │   ├── ResultsDisplay.js     # Results container
    │   ├── DataVisualization.js  # Recharts component
    │   ├── DataTable.js          # MUI data table
    │   ├── SqlDisplay.js         # SQL query display
    │   └── ValidationMetrics.js  # Validation indicators
    ├── services/
    │   └── api.js                # Axios API client
    ├── styles/
    │   └── theme.js              # MUI theme config
    └── __tests__/
        ├── SearchBar.test.js
        ├── DataVisualization.test.js
        └── api.test.js
```

**Data Files:**
```
data/
└── text_to_sql_poc.db           # SQLite database (generated)
```

**Documentation:**
```
docs/
├── product-brief-text-to-sql-poc-2025-11-25.md  # Product brief
├── tech-spec.md                                   # This document
└── diagrams/
    └── diagram-text-to-sql-poc-architecture.excalidraw  # Architecture diagram
```

### Key Code Locations

**Backend Entry Points:**
- Flask app initialization: `backend/app.py:10-30`
- Main query endpoint: `backend/routes/query_routes.py:15-60`
- Claude API call: `backend/services/claude_service.py:40-80`
- SQL validation: `backend/services/sql_validator.py:20-70`
- Database models: `backend/database/schema.py:10-50`

**Frontend Entry Points:**
- React app root: `frontend/src/App.js:10-150`
- API client setup: `frontend/src/services/api.js:5-30`
- Search component: `frontend/src/components/SearchBar.js:10-100`
- Chart logic: `frontend/src/components/DataVisualization.js:50-120`

**Configuration:**
- Backend config: `backend/config.py:5-30`
- Environment template: `backend/.env.example`
- MUI theme: `frontend/src/styles/theme.js:5-50`

### Testing Locations

**Backend Tests:**
```
backend/tests/
├── test_claude_service.py        # Claude integration tests
├── test_sql_validator.py         # Validation logic tests
├── test_query_endpoint.py        # API endpoint tests
└── test_seed_data.py            # Data generation tests
```

**Frontend Tests:**
```
frontend/src/__tests__/
├── SearchBar.test.js             # Search component tests
├── DataVisualization.test.js     # Chart component tests
├── DataTable.test.js            # Table component tests
└── api.test.js                  # API client tests
```

**Test Execution:**
```bash
# Backend tests
cd backend
pytest tests/ -v

# Frontend tests
cd frontend
npm test

# Coverage reports
pytest --cov=. tests/           # Backend
npm test -- --coverage          # Frontend
```

### Documentation to Update

**As Implementation Progresses:**

1. **README.md** (Create in project root)
   - Project overview
   - Setup instructions
   - How to run locally
   - Demo queries list
   - Troubleshooting guide

2. **API.md** (Optional - for reference)
   - POST /query endpoint documentation
   - Request/response examples
   - Error codes

3. **DEMO_SCRIPT.md** (Create for presentation)
   - Step-by-step demo walkthrough
   - Which client to select
   - Which queries to run
   - Expected results for each query
   - Talking points about validation

4. **CHANGELOG.md** (Optional)
   - Track story completion
   - Note any deviations from tech-spec

**Post-POC Documentation (If Moving to Production):**
- Architecture decision records (ADRs)
- Deployment guide
- Production configuration guide
- Security assessment document

---

## UX/UI Considerations

**UI Components Affected:**

This POC has significant UI impact - the entire frontend is new.

**Primary UI Components:**

1. **Client Selector (Dropdown)**
   - MUI Select component
   - Populated from /clients API endpoint
   - Display format: "Client Name (Industry)"
   - Sticky at top of page during scrolling

2. **Query Input (Text Field)**
   - MUI TextField (multiline, 3 rows)
   - Placeholder text with example: "e.g., Show me top 10 products by revenue"
   - Character limit: 500 (prevent overly long queries)
   - Submit button (MUI Button, primary color)

3. **Results Container (Card)**
   - MUI Card component wrapping all result sections
   - Sections: Chart, Table, SQL, Validation
   - Collapsible sections (MUI Accordion) for better organization

4. **Data Visualization (Chart)**
   - Recharts component (Line/Bar/Pie based on auto-detect)
   - Responsive width: 100% of container
   - Fixed height: 400px
   - Tooltips on hover
   - Legend below chart

5. **Data Table (Grid)**
   - MUI Table with TableContainer
   - Sortable columns (click header to sort)
   - Pagination: 50 rows per page
   - Alternating row colors for readability

6. **SQL Display (Code Block)**
   - MUI Card with monospace font
   - Syntax highlighting (simple: keywords in blue)
   - Copy button (MUI IconButton with ContentCopy icon)
   - Collapsible/expandable

7. **Validation Metrics (Chips)**
   - MUI Chip components
   - Color coding: Green (PASS), Red (FAIL), Yellow (WARNING)
   - Icons: CheckCircle, Error, Warning
   - Tooltip on hover for details

**UX Flow:**

```
User lands on page
  ↓
Select client from dropdown (required)
  ↓
Enter natural language query
  ↓
Click "Search" button
  ↓
Loading spinner appears (MUI CircularProgress)
  ↓
Results display:
  - Chart section (expanded by default)
  - Data table section (expanded)
  - SQL section (collapsed, expandable)
  - Validation section (expanded if any warnings/failures)
  ↓
User can:
  - Sort table columns
  - Expand/collapse sections
  - Copy SQL query
  - Switch client and run new query
  - See validation status clearly
```

**Visual Design Patterns:**

- **Color Palette:**
  - Primary: Blue (#1976d2) - buttons, links
  - Secondary: Gray (#757575) - text, borders
  - Success: Green (#4caf50) - validation pass
  - Error: Red (#f44336) - validation fail
  - Warning: Orange (#ff9800) - validation warnings
  - Background: White (#ffffff)
  - Surface: Light Gray (#f5f5f5) - cards

- **Typography:**
  - Headings: Roboto Bold
  - Body: Roboto Regular
  - Code: Monaco, Menlo, monospace

- **Spacing:**
  - Component padding: 16px
  - Section margins: 24px
  - Card elevation: 2 (subtle shadow)

**Responsive Design:**

POC is **desktop-focused** (demo on laptop), but basic responsive principles:
- Minimum width: 1024px (laptop screen)
- Chart scales to container width
- Table horizontal scroll on smaller screens
- No mobile optimization needed for POC

**Accessibility (Basic):**

- Semantic HTML elements (header, main, section)
- Alt text for any icons
- Keyboard navigation (tab through inputs)
- Focus indicators on interactive elements
- Color contrast meets WCAG AA standards (MUI defaults)

**NOT Implemented (Out of Scope):**
- Screen reader optimization
- ARIA labels for complex interactions
- Keyboard shortcuts
- High contrast mode
- Font size adjustments

**User Feedback Mechanisms:**

- **Loading State:** CircularProgress spinner while API call in progress
- **Success State:** Results display with green validation checks
- **Error State:** MUI Alert (red) with error message at top of results
- **Empty State:** Friendly message if no results returned
- **Validation Warnings:** Yellow chips with warning icons

---

## Testing Approach

**Test Framework Info:**

**Backend:**
- Framework: pytest 8.3.4
- Coverage tool: pytest-cov
- Mocking: unittest.mock (standard library)
- Fixture location: backend/tests/conftest.py

**Frontend:**
- Framework: Jest 29.7.0 (bundled with React)
- Testing library: React Testing Library 16.1.0
- Mocking: jest.mock()
- Setup file: frontend/src/setupTests.js

**Testing Philosophy for POC:**
- **Unit tests:** Business logic and utilities (validators, data generators)
- **Integration tests:** API endpoints with mocked dependencies
- **Component tests:** React components with user interactions
- **Manual tests:** End-to-end demo scenarios (most critical for POC success)

**Test Coverage Targets:**
- Backend core services: 70%+ (claude_service, sql_validator)
- Backend routes: 60%+
- Frontend components: 60%+
- **Manual test coverage:** 100% of demo queries

### Testing Strategy by Story

**Story 1 - Database Tests:**
```python
# backend/tests/test_seed_data.py
def test_generate_clients():
    """Verify 5-10 clients created with realistic data"""
    clients = generate_clients()
    assert 5 <= len(clients) <= 10
    assert all(c.industry in VALID_INDUSTRIES for c in clients)

def test_generate_products():
    """Verify ~200 products with realistic names and prices"""
    products = generate_products(client_ids=[1,2,3])
    assert 180 <= len(products) <= 220
    assert all(p.price > 0 for p in products)
    assert all(p.category in ['electronics', 'apparel', 'home_goods'] for p in products)

def test_generate_sales():
    """Verify ~2000 sales with temporal patterns"""
    sales = generate_sales(product_ids=range(1,201), years=2)
    assert 1800 <= len(sales) <= 2200
    # Q4 should have higher volume
    q4_sales = [s for s in sales if s.date.month in [10,11,12]]
    assert len(q4_sales) > len(sales) / 5  # More than 20%
```

**Story 2 - Claude API Tests:**
```python
# backend/tests/test_claude_service.py
from unittest.mock import patch, MagicMock

@patch('anthropic.Anthropic')
def test_generate_sql_success(mock_anthropic):
    """Test successful SQL generation from natural language"""
    mock_client = MagicMock()
    mock_client.messages.create.return_value.content[0].text = "SELECT * FROM products WHERE client_id = 1"
    mock_anthropic.return_value = mock_client

    service = ClaudeService(api_key="test")
    sql = service.generate_sql("Show me all products", client_id=1)

    assert "SELECT" in sql
    assert "client_id = 1" in sql

@patch('anthropic.Anthropic')
def test_generate_sql_timeout(mock_anthropic):
    """Test handling of API timeout"""
    mock_client = MagicMock()
    mock_client.messages.create.side_effect = TimeoutError()
    mock_anthropic.return_value = mock_client

    service = ClaudeService(api_key="test")
    with pytest.raises(SQLGenerationError):
        service.generate_sql("test query", client_id=1)
```

**Story 3 - Validator Tests:**
```python
# backend/tests/test_sql_validator.py
def test_validation_pass_with_client_id():
    """Validator should pass for query with correct client_id"""
    sql = "SELECT * FROM products WHERE client_id = 5"
    result = validate_sql_for_client_isolation(sql, expected_client_id=5)
    assert result['passed'] == True
    assert len([c for c in result['checks'] if c['status'] == 'PASS']) == 3

def test_validation_fail_missing_client_id():
    """Validator should fail if client_id missing"""
    sql = "SELECT * FROM products"
    result = validate_sql_for_client_isolation(sql, expected_client_id=5)
    assert result['passed'] == False
    assert any('Missing WHERE client_id' in c['message'] for c in result['checks'] if c['status'] == 'FAIL')

def test_validation_fail_wrong_client_id():
    """Validator should fail if wrong client_id"""
    sql = "SELECT * FROM products WHERE client_id = 3"
    result = validate_sql_for_client_isolation(sql, expected_client_id=5)
    assert result['passed'] == False

def test_validation_fail_destructive():
    """Validator should block DROP/DELETE/UPDATE"""
    sql = "DELETE FROM products WHERE client_id = 5"
    result = validate_sql_for_client_isolation(sql, expected_client_id=5)
    assert result['passed'] == False
    assert any('Destructive keyword' in c['message'] for c in result['checks'] if c['status'] == 'FAIL')
```

**Story 4 - Frontend Component Tests:**
```javascript
// frontend/src/__tests__/SearchBar.test.js
import { render, screen, fireEvent } from '@testing-library/react';
import SearchBar from '../components/SearchBar';

test('renders client selector and query input', () => {
  const clients = [{id: 1, name: 'TestCorp', industry: 'Retail'}];
  render(<SearchBar clients={clients} onSubmit={jest.fn()} />);

  expect(screen.getByLabelText(/select client/i)).toBeInTheDocument();
  expect(screen.getByLabelText(/enter query/i)).toBeInTheDocument();
});

test('submit button disabled without client selection', () => {
  render(<SearchBar clients={[]} onSubmit={jest.fn()} />);
  const submitBtn = screen.getByRole('button', {name: /search/i});
  expect(submitBtn).toBeDisabled();
});

test('calls onSubmit with correct data', () => {
  const mockSubmit = jest.fn();
  const clients = [{id: 1, name: 'TestCorp', industry: 'Retail'}];
  render(<SearchBar clients={clients} onSubmit={mockSubmit} />);

  fireEvent.change(screen.getByLabelText(/select client/i), {target: {value: '1'}});
  fireEvent.change(screen.getByLabelText(/enter query/i), {target: {value: 'test query'}});
  fireEvent.click(screen.getByRole('button', {name: /search/i}));

  expect(mockSubmit).toHaveBeenCalledWith({clientId: 1, query: 'test query'});
});
```

**Story 5 - Integration Tests:**
```python
# backend/tests/test_query_endpoint.py
def test_query_endpoint_success(client, mock_claude, sample_db):
    """Test /query endpoint with mocked Claude API"""
    mock_claude.return_value = "SELECT product_name FROM products WHERE client_id = 1 LIMIT 10"

    response = client.post('/query', json={
        'query': 'Show me 10 products',
        'client_id': 1
    })

    assert response.status_code == 200
    data = response.json
    assert 'sql' in data
    assert 'results' in data
    assert 'validation' in data
    assert data['validation']['passed'] == True

def test_query_endpoint_validation_failure(client, mock_claude):
    """Test endpoint with invalid SQL (missing client_id)"""
    mock_claude.return_value = "SELECT * FROM products"

    response = client.post('/query', json={
        'query': 'test',
        'client_id': 1
    })

    assert response.status_code == 400  # Bad request
    data = response.json
    assert data['validation']['passed'] == False
```

**Manual Testing Checklist (Critical):**

```markdown
## Demo Query Manual Tests

For each of 5-8 prepared queries:

- [ ] Query 1: "Show me top 10 products by revenue for Q3 2024"
  - [ ] Select Client 1
  - [ ] Enter query
  - [ ] Click Search
  - [ ] Verify results returned within 5 seconds
  - [ ] Verify bar chart displays correctly
  - [ ] Verify data table shows 10 rows
  - [ ] Verify SQL includes "WHERE client_id = 1"
  - [ ] Verify validation shows all PASS

- [ ] Query 2: "Compare electronics vs apparel sales across regions"
  - [ ] Select Client 2
  - [ ] Enter query
  - [ ] Verify grouped bar chart
  - [ ] Verify SQL has JOINs and GROUP BY
  - [ ] Verify validation PASS

[... repeat for all 5-8 demo queries]

## Multi-Client Switching Tests

- [ ] Run query for Client 1, verify results
- [ ] Switch to Client 2, run same query
- [ ] Verify results are DIFFERENT (no data leakage)
- [ ] Verify validation shows correct client_id in both cases

## Error Scenario Tests

- [ ] Submit query with no client selected → Error message
- [ ] Submit empty query → Error message
- [ ] Simulate Claude API timeout → Graceful error display
- [ ] Submit intentionally bad query → SQL error handled gracefully
- [ ] Kill backend server, submit query → Connection error displayed

## UI/UX Tests

- [ ] All components render correctly
- [ ] Loading spinner appears during API call
- [ ] Chart renders without errors for each type (line, bar, pie)
- [ ] Table pagination works (if >50 rows)
- [ ] SQL display is collapsible/expandable
- [ ] Copy SQL button works
- [ ] Validation chips colored correctly (green=PASS, red=FAIL)
```

**Coverage Execution:**

```bash
# Generate coverage reports before demo
cd backend
pytest --cov=. --cov-report=html tests/
open htmlcov/index.html  # Review coverage

cd frontend
npm test -- --coverage
open coverage/lcov-report/index.html
```

---

## Deployment Strategy

### Deployment Steps

**POC Deployment = Local Development Setup**

This POC is designed to run locally on a laptop for client demo. No production deployment infrastructure needed.

**Pre-Demo Setup (On Demo Machine):**

1. **Clone Repository**
   ```bash
   git clone <repository-url>
   cd text-to-sql-poc
   ```

2. **Backend Setup**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Configure Environment**
   ```bash
   cp .env.example .env
   # Add ANTHROPIC_API_KEY
   ```

4. **Generate Database**
   ```bash
   python -m database.seed_data
   # Verify: data/text_to_sql_poc.db created
   ```

5. **Frontend Setup**
   ```bash
   cd ../frontend
   npm install
   ```

6. **Test Run (Pre-Demo)**
   ```bash
   # Terminal 1: Backend
   cd backend
   source venv/bin/activate
   flask run --port 5000

   # Terminal 2: Frontend
   cd frontend
   npm run dev

   # Browser: http://localhost:5173
   # Test each demo query once
   ```

**Demo Day Checklist:**

- [ ] Demo machine has stable internet (for Claude API)
- [ ] Both terminals ready (backend + frontend)
- [ ] Browser bookmarked to http://localhost:5173
- [ ] Demo queries list printed or on second screen
- [ ] Backup: Screen recording of successful demo run
- [ ] Backup: Screenshots of expected results for each query

**Post-Demo (If Moving to Production):**

This is out of scope for POC, but high-level steps would include:
1. Containerize with Docker (backend + frontend)
2. Set up cloud hosting (AWS/GCP/Azure)
3. Add authentication layer
4. Configure production database (PostgreSQL)
5. Set up CI/CD pipeline
6. Add monitoring and logging

### Rollback Plan

**For POC Demo:**

Rollback is simple since everything runs locally:

1. **If Demo Breaks Mid-Presentation:**
   - Show pre-recorded demo video (backup plan)
   - OR restart both servers and retry
   - OR show screenshots of working demo

2. **If Database Corrupted:**
   ```bash
   rm data/text_to_sql_poc.db
   python -m database.seed_data  # Regenerate
   ```

3. **If Code Changes Break Demo:**
   ```bash
   git log  # Find last working commit
   git checkout <commit-hash>  # Revert to stable version
   ```

**Version Control Strategy:**

- Tag stable demo version: `git tag demo-v1.0`
- Always test from tagged commit before demo
- Keep main branch stable throughout POC development

**Production Rollback (Future):**
If this moves to production, implement:
- Blue-green deployment
- Database migration rollback scripts
- Feature flags for risky changes
- Automated health checks

### Monitoring Approach

**POC Monitoring = Manual Observation**

During demo, watch for:
- Flask terminal logs for errors
- Browser console for JavaScript errors
- API response times (visible in browser dev tools)
- Visual: Validation metrics on screen

**Logs to Monitor:**

**Backend (Flask):**
```
INFO: Query received: client_id=1, query="Show me top products"
INFO: Claude API call: 1.2s
INFO: SQL generated: SELECT...
INFO: Validation: PASS
INFO: Query executed: 0.3s, 10 rows returned
```

**Frontend (Browser Console):**
```
API call started...
API response received: 200 OK (1.5s)
Chart rendered: bar chart, 10 data points
```

**Metrics to Track (Informally):**
- API response time per query (aim: < 5 seconds)
- Validation pass rate (should be 100% for demo queries)
- Any errors or warnings

**Post-Demo Analysis:**

- Review Flask logs for any errors during demo
- Note any performance issues
- Document any unexpected behavior for improvement

**Production Monitoring (Future):**

If moving to production, implement:
- Application Performance Monitoring (APM): DataDog, New Relic
- Error tracking: Sentry
- Logging: CloudWatch, ELK stack
- Metrics: Prometheus + Grafana
- Alerting: PagerDuty for critical errors

**Health Checks (Future):**
- Endpoint: GET /health → returns {status: "ok", version: "1.0"}
- Claude API connectivity check
- Database connectivity check
- Response time monitoring (< 3s threshold)

---

_End of Technical Specification_

_This document provides comprehensive, definitive technical guidance for implementing the Text-to-SQL POC. All technology choices are final and specific. All implementation steps are actionable. Proceed directly to Story 1 implementation._

_Next Steps: Generate Epic + 5 Stories based on this tech-spec._
