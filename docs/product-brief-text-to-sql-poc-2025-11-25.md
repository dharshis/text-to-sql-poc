# Product Brief: Text-to-SQL POC

**Date:** 2025-11-25
**Author:** DS
**Context:** Client Proposal / Proof of Concept

---

## Executive Summary

**Project Type:** Client Proposal - Proof of Concept
**Strategic Context:** Build vs. Buy Decision
**Current State:** Client uses Number Station (external text-to-SQL service) with pain points around cost and performance latency
**POC Goal:** Demonstrate "yes, we can build this" - technical feasibility of an in-house alternative

This POC will showcase a locally-deployable, LLM-powered text-to-SQL solution that converts natural language queries into structured SQL, executes them against a sample retail market research database, and presents results through automatic visualizations and data tables. The demo will prove technical feasibility and strategic advantages (ownership, customization, data privacy, cost optimization potential) of building an in-house solution rather than continuing vendor dependency on Number Station.

**Technology Approach:**
- **Frontend:** React search interface (simple, focused)
- **Backend:** Python + Claude API for SQL generation
- **Database:** Local SQLite with moderate retail dataset (5-10 clients, 200 products, 2000 sales records)
- **Deployment:** 100% local - no cloud hosting required

**POC Scope:** Feature-focused demo with 5-8 prepared queries showcasing text-to-SQL capabilities, visualizations, and the intelligence of SQL generation. Not production-ready, but sufficient to validate the build approach and support a strategic decision.

**Success Definition:** If client stakeholders see this and say "yes, this proves we can build it - let's discuss the full implementation," the POC has succeeded.

---

## Core Vision

### Problem Statement

The client currently serves market researchers across multiple industries who rely on an external third-party product for text-to-SQL capabilities. While the external solution provides basic functionality, the client lacks ownership and control over this critical data access capability. This dependency creates strategic risk, limits customization potential, and prevents the client from fully integrating the text-to-SQL capability into their broader platform and workflow.

Market researchers from diverse industries need to query complex datasets about markets, competitors, trends, and consumer behavior - but without SQL expertise. The current external solution works, but creates vendor lock-in and doesn't offer the flexibility needed for the client's multi-domain business model.

### Problem Impact

**Financial Impact:** Number Station's licensing costs are creating budget pressure, especially given the client's need to serve multiple industries and scale their market research platform.

**Operational Impact:** Performance latency in query processing slows down researchers' workflows, creating frustration when analysts need quick insights to support client deliverables or respond to time-sensitive market questions.

### Why Existing Solutions Fall Short

**Current Solution:** Number Station (external text-to-SQL service)

**Key Pain Points:**
1. **Cost:** Expensive licensing model that doesn't align with the client's multi-domain scaling strategy
2. **Performance Latency:** Slow query generation and execution times impact researcher productivity and user experience

**Strategic Concerns:**
- Vendor dependency limits ability to customize for specific market research data patterns
- External service creates potential data security and sovereignty considerations
- Cannot optimize for the client's specific database schemas and query patterns
- Limited control over model improvements and feature roadmap

### Proposed Solution

Build a lightweight, locally-deployable text-to-SQL solution powered by Claude LLM that demonstrates technical feasibility as an alternative to Number Station. The POC will showcase the complete flow: natural language input → SQL generation → query execution → structured data output → automatic visualization.

**Core Architecture:**
- **Frontend:** React-based simple search interface (search bar, not full chatbot)
- **Backend:** Python service handling LLM orchestration, SQL generation, and query execution
- **LLM:** Claude API for natural language to SQL translation
- **Deployment:** Fully local - no cloud hosting required
- **Demo Data:** Sample retail market research dataset

**User Flow:**
1. User enters natural language question in search bar (e.g., "Show me top performing products in Q3")
2. Backend sends query to Claude with database schema context
3. Claude generates SQL query
4. Backend executes SQL against local database
5. Frontend displays results as both:
   - Basic visualizations (bar/line/pie charts as appropriate)
   - Raw data table

### Key Differentiators

**vs. Number Station:**
- **Ownership & Control:** Full control over the solution, model behavior, and feature roadmap
- **Cost Model:** Pay-per-use API costs vs. expensive licensing; potential for cost optimization
- **Data Privacy:** Local deployment means sensitive market research data never leaves client infrastructure
- **Customization:** Can tune prompts, schema definitions, and query logic for client's specific data patterns
- **Integration:** Native integration potential with client's existing platform and workflows

**POC Strategic Goal:** Demonstrate "this can be done" with comparable functionality, paving the way for a build vs. buy decision that favors in-house development.

---

## Target Users

### Primary Users: Market Researchers

**Who they are:**
- Market research analysts and consultants working across multiple industries (retail, consumer goods, technology, healthcare, etc.)
- Non-technical professionals who understand business questions but lack SQL expertise
- Need quick access to data insights to support client deliverables, competitive analysis, and market trend reports

**Their Current Workflow:**
- Today: Rely on Number Station or request data from technical teams
- Pain: Waiting for queries to process or depending on data engineers creates bottlenecks
- Need: Self-service data access that "just works" - ask questions in plain English, get answers immediately

**What they need from this solution:**
- Intuitive search interface - no technical knowledge required
- Fast, accurate query results
- Visual representation of data for quick pattern recognition
- Raw data access for deeper analysis or export
- Confidence that the SQL query generated is correct for their question

### Secondary Users: Client Stakeholders (Demo Audience)

**Who they are:**
- Technical decision-makers evaluating build vs. buy options
- Product managers assessing feasibility of in-house solution
- Finance stakeholders concerned about Number Station costs

**What they need to see:**
- Technical feasibility proof - "yes, we can build this"
- Comparable functionality to current solution
- Clear path to cost savings and strategic control
- Local deployment demonstrating data privacy advantage

---

## MVP Scope

### Core Features

**1. Natural Language Search Interface**
- Clean, simple search bar (React frontend)
- Single input field for natural language queries
- Submit button to trigger query processing
- No complex chatbot UI - keep it minimal and focused

**2. LLM-Powered SQL Generation**
- Claude API integration for natural language to SQL translation
- Database schema context injection (clients, products, sales, customer_segments tables)
- Prompt engineering to ensure accurate SQL generation for market research queries
- Display the generated SQL query to users for transparency and demo credibility

**3. Local Database with Sample Retail Dataset**
- SQLite or PostgreSQL local database
- **Moderate dataset scope:**
  - 5-10 sample retail clients
  - ~200 products across various categories (electronics, apparel, home goods, etc.)
  - ~2000 sales records with temporal data (quarters, regions)
  - Customer segment data

- **Schema:**
  - `clients`: client_id, client_name, industry
  - `products`: product_id, client_id, product_name, category, brand, price
  - `sales`: sale_id, client_id, product_id, region, date, quantity, revenue
  - `customer_segments`: segment_id, client_id, segment_name, demographics

**4. Query Execution Engine**
- Python backend service to execute generated SQL safely
- Query validation and sanitization
- Error handling for malformed queries
- Return structured results to frontend

**5. Dual Data Display**
- **Visualizations:** Automatic chart generation (bar, line, pie) based on query results
  - Smart chart selection based on data type (time series → line chart, comparisons → bar chart, proportions → pie chart)
  - Basic but clean visualization using charting library (e.g., Chart.js, Recharts)
- **Raw Data Table:** Sortable, formatted table showing query results
- Both displays shown simultaneously on results page

**6. Sample Demo Queries**
- Pre-populated example queries to showcase capabilities:
  - "Show me top 10 products by revenue in Q3 2024"
  - "Compare electronics sales vs apparel across all regions"
  - "What are the average transaction values by customer segment?"
  - "Which clients had the highest year-over-year growth?"

### Out of Scope for MVP

**Explicitly NOT included in POC:**
- Multi-turn conversational interface
- Query history or saved queries
- User authentication or multi-user support
- Real-time database connections to client production data
- Advanced visualizations (heatmaps, geographic maps, complex dashboards)
- Query result export functionality
- Performance optimization for large datasets
- Multi-database support
- Natural language explanations of results
- Query refinement or follow-up questions

### MVP Success Criteria

**POC Demo Success = "Yes, we can build this"**

The POC will be considered successful if it demonstrates:

1. **Technical Feasibility:**
   - Natural language input correctly translates to valid SQL queries
   - Queries execute and return accurate results
   - System runs entirely locally without cloud dependencies

2. **Comparable Functionality:**
   - Performs text-to-SQL at a level that shows parity potential with Number Station
   - Handles realistic market research questions (aggregations, comparisons, filtering)
   - Visualizations are clear and appropriate for the data

3. **Demo Readiness:**
   - Works reliably for 5-8 prepared demo queries
   - UI is clean and professional enough for client presentation
   - Response time is reasonable (< 5 seconds per query)
   - Generated SQL display demonstrates translation intelligence

4. **Strategic Advantages Visible:**
   - Local deployment proves data privacy benefit
   - Customization potential is evident (schema-specific prompting)
   - Path to full ownership is clear

**What this POC is NOT trying to prove:**
- Production readiness
- Feature completeness vs Number Station
- Scalability to thousands of users
- Cost savings calculations (though can be discussed)

### Future Vision

**If POC succeeds and client greenlights development:**

**Phase 2 - Production MVP:**
- User authentication and role-based access
- Connection to actual client databases
- Query history and saved queries
- Export functionality (CSV, Excel, PDF reports)
- Enhanced error handling and query refinement
- Performance optimization

**Phase 3 - Advanced Features:**
- Multi-turn conversational queries
- Query suggestions based on schema and user behavior
- Advanced visualizations and dashboard creation
- Natural language insights generation
- Integration with client's existing platform
- Multi-database and cross-client analytics

**Phase 4 - Enterprise Scale:**
- Support for complex schemas across multiple industries
- Fine-tuned models for domain-specific terminology
- Audit logging and compliance features
- API for programmatic access
- Real-time data refresh capabilities

---

## Technical Preferences

**Architecture Stack:**
- **Frontend:** React (JavaScript/TypeScript)
  - Component library: Material-UI or Ant Design for professional look
  - Charting: Chart.js or Recharts for visualizations
  - State management: React hooks (keep it simple for POC)

- **Backend:** Python
  - Framework: Flask or FastAPI for REST API
  - Database: SQLite (simplest for local POC) or PostgreSQL (if preferring production-like setup)
  - ORM: SQLAlchemy for database interactions
  - LLM Integration: Anthropic Python SDK for Claude API

- **LLM:** Claude API (Sonnet 3.5 or later)
  - Leveraging existing access
  - Suitable for complex SQL generation tasks
  - Good balance of speed and accuracy

**Deployment Model:**
- **100% Local execution** - no cloud hosting
- Can run on laptop/local machine for demo
- All data processing happens locally
- Only external call is Claude API for SQL generation

**Development Approach:**
- Minimal dependencies to reduce complexity
- Focus on core functionality over polish
- Modular design for easy iteration
- Well-commented code for handoff potential

**Key Technical Decisions:**
1. **Database choice:** SQLite recommended for POC simplicity (single file, no server setup)
2. **API design:** RESTful with single endpoint `/query` accepting natural language input
3. **Error handling:** Graceful degradation - show user-friendly errors if SQL generation fails
4. **Security:** Basic SQL injection prevention via parameterized queries (even though it's demo data)

---

## Security & Data Isolation Guardrails

### Critical Requirement: Multi-Client Data Isolation

**Client Concern:** Market researchers must NEVER be able to access other clients' data through natural language queries - even accidentally.

**POC Demonstration Approach:**

**1. Client Context Enforcement**
- Every query requires a `client_id` parameter (simulated user session context)
- LLM prompts are engineered to ALWAYS include client filtering:
  ```
  "Generate SQL for client_id = {X} ONLY.
  ALL queries MUST include WHERE client_id = {X} clause.
  NEVER return data from other clients."
  ```
- System automatically validates generated SQL contains correct client_id filter

**2. SQL Query Validation & Post-Processing**

**Pre-Execution Validation:**
- Parse generated SQL to verify it includes `WHERE client_id = {expected_client_id}`
- Reject queries that:
  - Reference multiple client_ids
  - Omit client_id filtering entirely
  - Use OR conditions that could leak data across clients
  - Attempt JOINs without client_id filters on all tables

**Post-Processing Showcase:**
- Display validation results to demonstrate safety checks:
  - ✅ Client isolation verified
  - ✅ Query scope: Client X data only
  - ✅ No cross-client data access detected
  - ✅ SQL safety checks passed

**3. Demo Safety Indicators**

**Visual Guardrail Display in UI:**
- Show current user's client context: "Viewing as: Client XYZ Corp"
- Display SQL validation status before execution
- Highlight client_id clauses in generated SQL for transparency

**Example POC Query Flow:**
```
User Input: "Show me top 10 products by revenue"
↓
LLM Generates: SELECT product_name, SUM(revenue)
                FROM sales s JOIN products p ON s.product_id = p.product_id
                WHERE s.client_id = 123
                GROUP BY product_name
                ORDER BY SUM(revenue) DESC
                LIMIT 10
↓
Validation Check:
  ✅ Client filter present (client_id = 123)
  ✅ All joined tables filtered by client_id
  ✅ No cross-client risk detected
↓
Execute & Display Results + Validation Summary
```

**4. Query Evaluation Metrics**

**Demonstrate Quality Assessment:**
- **Correctness Score:** Did SQL return expected results for test queries?
- **Safety Score:** Does query properly enforce client isolation?
- **Performance:** Query execution time
- **Schema Adherence:** Uses correct tables and columns

**POC Implementation:**
- Create validation dashboard showing these metrics for each demo query
- Pre-calculate scores for prepared queries to showcase during presentation
- Demonstrate how system would flag problematic queries in real-time

### Production Considerations (Not in POC)

**What full production would add:**
- Row-level security policies at database level
- Audit logging of all queries with client context
- Rate limiting per client to prevent data mining
- Anomaly detection for suspicious query patterns
- Fine-grained access control by user role within client
- Encrypted query logs for compliance

**POC Demonstration Goal:**
Show that the architecture CAN enforce data isolation through LLM prompt engineering + SQL validation, proving this isn't an inherent limitation of the text-to-SQL approach.

---

## Risks and Assumptions

### Key Assumptions

1. **Claude API Performance:**
   - Assuming Claude API will consistently generate accurate SQL from natural language
   - Assuming API response times will be acceptable for demo purposes (< 3 seconds)
   - Assuming Claude has sufficient capability for market research query patterns

2. **Dataset Representativeness:**
   - Sample retail dataset will be sufficient to demonstrate real-world applicability
   - Client will accept synthetic data for POC demonstration
   - Demo queries will align with actual researcher needs

3. **Client Context:**
   - Client stakeholders understand POC limitations vs production system
   - Technical team can evaluate architecture and approach from POC
   - Client has budget/appetite for build option if POC succeeds

4. **Technical Feasibility:**
   - Local deployment is acceptable for production (or cloud migration path is understood)
   - Claude API costs at scale are acceptable vs Number Station licensing
   - Integration with client's existing systems is technically viable

### Potential Risks

**Technical Risks:**
- **SQL Accuracy:** Claude may generate incorrect SQL for complex queries (Mitigation: Test extensively, have fallback examples)
- **Performance:** API latency may be slower than expected (Mitigation: Set realistic expectations, optimize prompt size)
- **Schema Complexity:** Real client schemas may be far more complex than POC (Mitigation: Acknowledge in presentation, plan for schema engineering work)
- **Edge Cases:** Unusual query patterns may break (Mitigation: Scope demo to proven query types)

**Business Risks:**
- **Expectations Gap:** Client may expect production-ready solution from POC (Mitigation: Clear communication about POC scope and next phases)
- **Cost Comparison:** API costs at scale may not be compelling vs Number Station (Mitigation: Present cost model scenarios, emphasize other benefits)
- **Build Commitment:** Client may not commit to full build after POC (Mitigation: This is exploratory - manage expectations)

**Demo Risks:**
- **Live Demo Failures:** API issues, network problems during presentation (Mitigation: Have video recording backup, test extensively beforehand)
- **Query Examples:** Pre-selected queries may not impress stakeholders (Mitigation: Collaborate with client on relevant query examples)

### Critical Success Factors

For this POC to achieve its goal:

1. **Accurate SQL Generation:** Must get core demo queries right - this is non-negotiable
2. **Professional UI:** Even though it's basic, must look polished enough for client presentation
3. **Clear Value Proposition:** Must articulate ownership, cost, and customization benefits clearly
4. **Realistic Scoping:** Must manage expectations about what POC proves vs what production requires
5. **Strong Follow-up Plan:** Must have clear roadmap from POC to production if client approves

---

_This Product Brief captures the vision and requirements for the Text-to-SQL POC project._

_It was created through collaborative discovery and reflects the unique needs of this client proposal proof-of-concept._

_Next steps: Use this brief to guide development of the POC demo, ensuring clear alignment between implementation and strategic objectives. Consider following up with a PRD if the client greenlights full production development._