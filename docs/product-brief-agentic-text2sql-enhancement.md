# Product Brief: Agentic Text-to-SQL Enhancement

**Date:** 2025-11-27
**Author:** Mary (Business Analyst) with DS
**Project Type:** Enhancement / POC Evolution
**Status:** Draft for Review

---

## Executive Summary

**Enhancement Vision:** Transform the current single-shot Text-to-SQL POC into an intelligent agentic system that can plan, reflect, iterate, and self-correct to generate more accurate SQL queries and handle complex, multi-step analytical requests.

**Current State:** The text-to-sql-poc successfully demonstrates basic LLM-powered SQL generation with a simple flow: user query → Claude API → SQL generation → execution → display results. This proves technical feasibility but lacks the intelligence to handle ambiguous queries, iteratively refine poor results, or break down complex questions into manageable steps.

**Proposed Enhancement:** Implement an agentic AI architecture using LangGraph that introduces autonomous decision-making through specialized agent nodes:
- **Clarification Agent:** Detects ambiguous queries and proactively asks for clarification
- **Planning Agent:** Decides which tools to invoke and in what order
- **Execution Agent:** Orchestrates tool calls (schema retrieval, SQL generation, query execution, validation)
- **Reflection Agent:** Evaluates SQL quality and decides whether to iterate or complete
- **Explanation Agent:** Transforms raw results into natural language insights (KEY DIFFERENTIATOR)
- **Conversation Agent:** Maintains session context for follow-up queries

**Key Value Proposition:** Move from "one-shot SQL generation" to "intelligent insights engine" that not only generates accurate SQL but explains what the results mean in plain English. The system can handle real-world complexity, recover from errors, learn from conversation context, and most importantly, transform data into actionable insights—demonstrating a significant competitive advantage over simple text-to-SQL tools like Number Station.

**Strategic Impact:** This enhancement proves the organization can build not just comparable but superior functionality to external vendors, with sophisticated multi-agent intelligence that can be continuously improved and customized for domain-specific needs.

---

## Problem Statement

### Current System Limitations

The existing Text-to-SQL POC has proven technical feasibility but reveals several limitations when handling real-world market research queries:

**1. No Ambiguity Detection**
- System blindly generates SQL even when user query is vague or ambiguous
- Cannot detect when critical context is missing (date ranges, specific metrics, filtering criteria)
- Researchers must perfectly phrase questions or risk getting incorrect results
- Example: "Show me sales trends" → System guesses a time period rather than asking for clarification

**2. No Iterative Refinement**
- Single-shot generation with no ability to self-correct
- If generated SQL has errors or returns empty results, system has no mechanism to try again
- Poor results are presented to user with no reflection on quality
- Example: SQL syntax error → user sees error message with no automated retry

**3. No Conversation Context**
- Each query is independent; cannot handle follow-up questions
- Researchers must repeat context in every query
- Natural conversational patterns ("Now show me by region", "What about Q3?") fail
- Lost opportunity for researchers to iteratively explore data

**4. Limited Intelligence in Query Planning**
- No decision-making about which tools or data sources to use
- Cannot break complex questions into sub-queries
- All queries follow the same rigid pattern regardless of complexity
- Example: "Compare this quarter to last quarter" → Should intelligently fetch data for both periods

**5. No Self-Evaluation**
- System cannot assess whether generated SQL is correct or optimal
- No validation of result quality (empty results, unexpected patterns, performance issues)
- Researchers bear full burden of verifying correctness
- Missed opportunity to learn and improve

### Business Impact

**For Market Researchers:**
- **Productivity Loss:** Time wasted rephrasing queries or manually fixing SQL
- **Trust Issues:** Uncertainty about result correctness reduces tool adoption
- **Cognitive Load:** Must maintain all context mentally across multiple queries
- **Missed Insights:** Cannot explore data conversationally; limited to pre-planned questions

**For Strategic Build vs. Buy Decision:**
- Current POC demonstrates parity with Number Station but not superiority
- Lacks the intelligence needed to justify build investment
- Does not showcase the customization and improvement potential of in-house solution
- Fails to demonstrate advanced AI capabilities that differentiate from vendors

### Why This Enhancement Matters Now

**Technical Opportunity:** LangGraph and agentic AI patterns are mature and proven in production systems. The inspiration code (`agentic_text2sql.py`) demonstrates a working architecture that can be adapted to this POC.

**Strategic Timing:** Before committing to a full production build, proving that an agentic approach is feasible strengthens the business case for ownership over vendor dependency.

**Competitive Differentiation:** Agentic capabilities (clarification, reflection, conversation context) are not standard in text-to-SQL tools. Demonstrating these positions the in-house solution as technically superior, not just cost-competitive.

---

## Proposed Solution

### Agentic Architecture Overview

Transform the current linear SQL generation flow into an intelligent multi-agent system powered by LangGraph state machine:

**Current Flow (Linear):**
```
User Query → Claude API → SQL Generated → Execute → Display Results
```

**Agentic Flow (Intelligent Loop):**
```
User Query 
  ↓
Clarification Agent (detect ambiguity with schema/metadata context)
  ↓
  ├─ IF ambiguous → Ask User for Clarification → Return questions
  └─ IF clear → Continue
       ↓
Planning Agent (decide next action based on state)
  ↓
  ├─ Need schema? → Execute Tools (get_schema)
  ├─ Need metadata? → Execute Tools (search_metadata)  
  ├─ Ready to generate? → SQL Generation Agent
  ├─ SQL generated? → Execute Tools (execute_sql)
  └─ Results ready? → Execute Tools (validate_results)
       ↓
Reflection Agent (evaluate quality)
  ↓
  ├─ Critical errors detected? → Loop back to Planning (retry)
  └─ Acceptable quality? → Continue
       ↓
Natural Language Explanation (explain results in plain English)
       ↓
Session Memory (store for follow-up queries)
       ↓
Display Results with Explanation + Context
```

### Core Agentic Capabilities

**1. Clarification Detection Agent**
- **Purpose:** Proactively identify when user query is ambiguous or missing critical context
- **How:** Use Claude to analyze query against available schema and metadata before SQL generation
- **Benefits:** 
  - Reduces incorrect SQL generation
  - Improves user trust through intelligent interaction
  - Demonstrates system "understands" when it needs more information

**2. Planning Agent**
- **Purpose:** Intelligent decision-making about what action to take next
- **How:** State machine logic that decides: get schema → search metadata → generate SQL → execute → validate → complete
- **Benefits:**
  - Flexible workflow that adapts to query complexity
  - Can skip unnecessary steps (e.g., if schema already cached)
  - Foundation for future multi-step query planning

**3. Execution Agent with Tools**
- **Purpose:** Orchestrate specific actions through modular tools
- **Tools:**
  - `get_schema`: Retrieve database schema (simplified, no hybrid retrieval)
  - `search_metadata`: Optional business rules lookup (static file or simple keyword search)
  - `execute_sql`: Safe SQL execution with error handling
  - `validate_results`: Quality checks on query results
- **Benefits:**
  - Modular design for easy testing and improvement
  - Clear separation of concerns
  - Reusable tools across different agent workflows

**4. Reflection Agent**
- **Purpose:** Self-evaluate SQL quality and decide whether to iterate
- **How:** Check for critical errors (syntax errors, wrong tables/columns, empty results when data should exist)
- **Benefits:**
  - Automatic retry for fixable errors
  - Learns from mistakes within a single query session
  - Reduces user frustration with failed queries

**5. Conversation Context Manager**
- **Purpose:** Maintain session memory for follow-up queries
- **How:** Store recent queries and results; resolve follow-ups into standalone queries
- **Benefits:**
  - Natural conversational interface
  - Researchers can iteratively explore data
  - Demonstrates advanced UX compared to simple tools

**6. Natural Language Results Explainer**
- **Purpose:** Transform raw SQL results into human-readable insights
- **How:** Send results + query context to Claude with explanation prompt; generate summary highlighting key findings
- **Benefits:**
  - Non-technical users immediately understand what data means
  - Highlights patterns, trends, and anomalies automatically
  - Reduces cognitive load on market researchers
  - Major differentiation from tools that only show raw data

### Simplified Approach (Per Your Constraint)

**Excluded from Inspiration Code:**
- ❌ Hybrid retrieval (Vector + BM25 for schema/metadata)
- ❌ Advanced sample data retrieval with embeddings
- ❌ Complex metadata search with vector similarity

**Simplified Alternatives:**
- ✅ Direct schema retrieval from `database/db_manager.py` (already have schema access)
- ✅ Simple keyword-based metadata search (or static business rules file if needed)
- ✅ Basic sample data queries using SQL (no embeddings required)
- ✅ In-memory session storage (dictionary) instead of Redis

### Key Differentiators vs. Current POC

| Feature | Current POC | Agentic Enhancement |
|---------|-------------|---------------------|
| Query Handling | Single-shot | Iterative with retry |
| Ambiguity | Blindly generates SQL | Detects and asks for clarification |
| Error Recovery | Shows error to user | Attempts self-correction |
| Follow-up Queries | Not supported | Conversation context aware |
| Tool Orchestration | Fixed flow | Intelligent planning |
| Quality Assessment | None | Self-reflection and validation |
| Results Presentation | Raw data + charts | Natural language explanations + data + charts |
| User Experience | Basic tool | Intelligent assistant with insights |

---

## Target Users

### Primary Users: Market Researchers (Enhanced Experience)

**Current Pain Points Addressed:**
- **Ambiguous Query Frustration:** Now system asks clarifying questions instead of guessing
- **Error Recovery Burden:** System attempts to fix errors automatically before showing results
- **Context Repetition:** Can ask follow-up questions naturally without repeating context
- **Trust in Results:** Validation metrics and reflection results increase confidence
- **Data Interpretation Burden:** Natural language explanations eliminate need to manually analyze raw results

**New Capabilities Enabled:**
- **Instant insights:** See "Samsung Galaxy S24 led Q3 sales with 45% market share" instead of just raw numbers
- **Conversational data exploration:** "Show me Q3 sales" → "What about Q4?" → "Compare them by region"
- **Guided query refinement:** Through clarification questions
- **Automatic error recovery:** From common SQL generation mistakes
- **Transparent intelligence:** View system's decision-making process
- **Pattern detection:** System automatically highlights trends, anomalies, and key findings

### Secondary Users: Stakeholders Evaluating Build vs. Buy

**What This Demonstrates:**
- **Technical Superiority:** Agentic capabilities beyond what Number Station offers
- **Customization Potential:** Architecture designed for domain-specific improvements
- **AI Innovation:** Cutting-edge multi-agent approach showing R&D capability
- **Investment Justification:** Clear path from POC → Production with intelligent features

**Success Metric for This Audience:**
If stakeholders see this and say "this is more sophisticated than Number Station, we should build this," the enhancement has succeeded.

---

## Goals & Success Metrics

### Business Objectives

1. **Demonstrate Technical Superiority** 
   - Metric: Agentic system handles ≥3 query types that current POC fails on (ambiguous queries, error recovery, follow-ups)
   - Target: 100% success rate on prepared demo scenarios

2. **Prove Iterative Refinement Value**
   - Metric: Track queries that succeed on 2nd/3rd attempt after reflection-driven retry
   - Target: ≥30% of complex queries benefit from self-correction

3. **Validate Conversation Context Utility**
   - Metric: Demonstrate 3-5 follow-up query sequences that work seamlessly
   - Target: Context resolution accuracy ≥90% (correct interpretation of "that", "this", "what about")

4. **Strengthen Build vs. Buy Case**
   - Metric: Stakeholder feedback survey post-demo
   - Target: ≥80% agreement that agentic approach justifies build investment

### User Success Metrics

1. **Reduced Query Errors**
   - Current: ~30% of queries fail or return unexpected results (estimated)
   - Target: ≤10% final failure rate with agentic retry mechanism

2. **Improved Clarity Through Clarification**
   - Metric: % of ambiguous queries caught before bad SQL generation
   - Target: System correctly identifies ≥80% of intentionally ambiguous test queries

3. **Conversational Flow Adoption**
   - Metric: Track follow-up queries in user sessions
   - Target: ≥50% of demo sessions include successful follow-up queries

### Key Performance Indicators (KPIs)

- **Clarification Detection Accuracy:** 80% of ambiguous queries flagged before SQL generation
- **Self-Correction Success Rate:** 70% of retries result in successful SQL execution
- **Context Resolution Accuracy:** 90% of follow-up queries correctly interpreted
- **Total Query Success Rate:** 90% of queries produce valid, expected results (up from ~70%)
- **Explanation Quality:** ≥85% of explanations rated as "clear and helpful" in user testing
- **Insight Detection:** Explanations successfully highlight key insights (top items, trends, anomalies) in ≥80% of results
- **Response Time:** ≤10 seconds per query including retries + explanation generation
- **Iteration Efficiency:** Average 1.5 iterations per query (most succeed on first or second attempt)

---

## MVP Scope

### Core Features (Must Have for Agentic POC)

**1. LangGraph State Machine Foundation**
- **Description:** Implement LangGraph StateGraph with AgentState TypedDict for workflow orchestration
- **Rationale:** Core infrastructure enabling all agentic behaviors; proven pattern from inspiration code
- **Acceptance:** State transitions work correctly: clarification → plan → execute_tools → generate_sql → reflect → complete

**2. Clarification Detection Agent**
- **Description:** Node that analyzes query against schema/metadata and determines if clarification needed
- **Rationale:** Highest-value UX improvement; demonstrates intelligence over simple tools
- **Acceptance:** 
  - Correctly flags ≥3 types of ambiguous queries in demo
  - Returns clear, helpful clarification questions
  - Bypasses when query is sufficiently clear

**3. Planning Agent with Tool Orchestration**
- **Description:** Decision-making node that determines next action: get_schema, generate_sql, execute_sql, validate_results, complete
- **Rationale:** Demonstrates intelligent workflow adaptation vs. rigid pipeline
- **Acceptance:**
  - Routes to appropriate tools based on state
  - Avoids redundant tool calls (e.g., schema retrieval cached)
  - Handles iteration loops correctly

**4. Execution Tools (Simplified)**
- **get_schema Tool:** Retrieve database schema directly from db_manager (no hybrid retrieval)
- **execute_sql Tool:** Execute generated SQL safely with error handling
- **validate_results Tool:** Basic validation (has results, row count, no errors)
- **Rationale:** Modular tools enable planning agent flexibility
- **Acceptance:** Each tool returns consistent result format; errors handled gracefully

**5. Reflection Agent with Retry Logic**
- **Description:** Node that evaluates SQL quality and decides whether to retry or complete
- **Rationale:** Self-correction capability differentiates from simple systems
- **Acceptance:**
  - Detects critical errors (syntax errors, unknown tables/columns)
  - Triggers retry for fixable issues (max 2-3 iterations)
  - Completes when acceptable or max iterations reached

**6. Conversation Context Management**
- **Description:** Session-based memory storing recent queries and results; query resolution for follow-ups
- **Rationale:** Enables natural conversational interaction
- **Acceptance:**
  - Maintains last 5-10 query/result pairs per session
  - Resolves follow-up queries ("what about Q4?") into standalone queries
  - Works across multiple demo sequences

**7. Enhanced API Endpoint**
- **Description:** New `/query-agentic` endpoint that accepts session_id and returns richer response
- **Rationale:** Backend support for agentic workflow
- **Acceptance:**
  - Returns: {sql, results, **explanation**, validation, reflection, iterations, clarification_questions?, context_used}
  - **explanation** field contains natural language summary of results
  - Handles session management
  - Maintains backward compatibility with existing `/query` endpoint

**8. Natural Language Results Explanation**
- **Description:** Generate human-readable explanations of query results using Claude
- **Rationale:** Transform raw data into insights; highest-value UX feature for non-technical users
- **Implementation:**
  - After successful query execution, send results to Claude with prompt: "Explain these results in plain English"
  - Include context: original query, column meanings, key patterns
  - Display explanation prominently above or alongside visualization
- **Acceptance:**
  - Explanations are clear, accurate, and relevant
  - Highlights key insights (top items, trends, comparisons, anomalies)
  - Reads naturally, not robotic
  - Generated within 2-3 seconds

**9. Enhanced Frontend Display**
- **Description:** UI updates to show agentic workflow transparency and results explanations
- **Components:**
  - **Natural Language Insight Card** (NEW - primary display)
  - Clarification Questions dialog (when needed)
  - Iteration counter display
  - Reflection results summary
  - Context indicator ("Following up on: [previous query]")
- **Rationale:** Demonstrate intelligent behavior visually + make results immediately understandable
- **Acceptance:**
  - Explanation displayed prominently at top of results
  - Clarification flow works end-to-end
  - Users can see system's thinking process
  - Professional appearance suitable for demo

### Out of Scope for MVP

**Explicitly NOT included in Agentic POC:**
- ❌ Hybrid retrieval (Vector + BM25) for schema/metadata
- ❌ Advanced sample data retrieval with embeddings
- ❌ Complex metadata knowledge base (keep simple or skip)
- ❌ Multi-database support
- ❌ Query plan optimization across multiple SQL queries
- ❌ Advanced visualization based on agentic insights (basic charts remain)
- ❌ User authentication for session persistence
- ❌ Production-grade session storage (Redis, database)
- ❌ Fine-tuned models for SQL generation
- ❌ Comprehensive error taxonomy and specialized retry strategies
- ❌ Performance optimization for large-scale usage

### MVP Success Criteria

**The Agentic POC will be considered successful if:**

1. **Natural Language Explanations Work:**
   - Demo includes ≥3 queries with clear, accurate explanations
   - Explanations highlight key insights (top items, trends, comparisons)
   - Non-technical stakeholders immediately understand results without looking at data
   - Explanations feel natural, not robotic

2. **Clarification Works:**
   - Demo includes ≥2 scenarios where system asks for clarification before generating SQL
   - Clarification questions are relevant and helpful
   - After user responds, system generates correct SQL

3. **Reflection & Retry Works:**
   - Demo includes ≥1 scenario where initial SQL fails but system self-corrects on retry
   - Reflection accurately identifies issue
   - Second attempt succeeds

4. **Conversation Context Works:**
   - Demo includes ≥2 follow-up query sequences
   - Context is correctly maintained and referenced
   - Follow-ups generate appropriate SQL and coherent explanations

5. **Performance Acceptable:**
   - Response times ≤10 seconds including iterations and explanation generation
   - System feels responsive, not sluggish
   - Iterations converge (don't loop indefinitely)

6. **Stakeholder Impact:**
   - Demo audience recognizes sophistication beyond simple text-to-SQL
   - Natural language insights identified as major differentiator
   - Clear articulation: "This doesn't just answer questions, it provides insights"
   - Build vs. Buy case strengthened

---

## Post-MVP Vision

### Phase 2: Production-Ready Agentic System

**If POC succeeds, next phase would include:**

**Advanced Planning:**
- Multi-query decomposition (break complex questions into multiple SQL queries)
- Cross-table relationship inference
- Query optimization recommendations

**Enhanced Tools:**
- Advanced metadata search with business glossary
- Sample data smart fetching based on query patterns
- Query result caching and reuse

**Improved Reflection:**
- Sophisticated error taxonomy with specialized retry strategies
- Learning from successful query patterns
- Performance-based reflection (query too slow? suggest indexes)

**Enhanced Explanations:**
- Deeper insights with statistical analysis (significance testing, correlation detection)
- Comparative explanations (vs. previous period, vs. benchmarks)
- Anomaly detection and highlighting
- Customizable explanation depth (summary vs. detailed)

**Session Management:**
- Persistent storage (Redis, database)
- User-specific conversation history
- Export conversation transcripts

### Phase 3: AI-Native Features

**Proactive Suggestions:**
- "You might also want to see..."
- "This data shows an anomaly, investigate?"
- "Based on this query, consider these related insights"

**Collaborative Refinement:**
- User can provide feedback on SQL quality
- System learns from corrections
- Adaptive prompt tuning based on user patterns

**Domain Intelligence:**
- Market research specific terminology understanding
- Industry-specific query templates
- Automated insight generation from results

### Phase 4: Enterprise Intelligence Platform

**Multi-Domain Support:**
- Agentic routing across multiple databases/domains
- Cross-client analytics with proper isolation
- Federated query planning

**Advanced Workflows:**
- Scheduled queries and monitoring
- Alert generation based on query results
- Integration with BI tools and reporting systems

**AI Governance:**
- Audit trail of all agentic decisions
- Explainability for SQL generation choices
- Compliance and security validation

---

## Technical Considerations

### Platform Requirements

- **Target Platform:** Continue local deployment for POC; cloud-ready architecture for future
- **Browser Support:** Modern browsers (Chrome, Firefox, Edge) - same as current POC
- **Performance Requirements:** 
  - Agentic workflow: ≤8 seconds end-to-end including retries
  - Clarification detection: ≤3 seconds
  - Individual agent nodes: ≤2 seconds each
  - Session context lookup: ≤100ms

### Technology Preferences

**Backend (Python):**
- **Framework:** Continue with Flask (existing)
- **Agentic Framework:** LangGraph (from langgraph library)
- **State Management:** LangGraph StateGraph with TypedDict
- **LLM Integration:** Continue Anthropic Claude API
- **Session Storage:** In-memory dictionary for POC (Redis path for production)
- **New Dependencies:**
  - `langgraph>=0.0.20` - State machine orchestration
  - `operator` - Built-in, for state annotations

**Frontend (React):**
- **Framework:** Continue with React + Material-UI
- **New Components:**
  - **InsightCard.jsx** - Display natural language explanation prominently (PRIMARY NEW FEATURE)
  - ClarificationDialog.jsx - Display clarification questions
  - IterationIndicator.jsx - Show retry counter
  - ReflectionSummary.jsx - Display agent's self-assessment
  - ContextBadge.jsx - Indicate follow-up query context
- **State Management:** Continue with React hooks (useState, useEffect)

**Database:**
- **Continue:** SQLite for POC
- **No Changes:** Existing schema remains the same
- **New:** Optional metadata table or JSON file for business rules (if needed)

### Architecture Considerations

**Repository Structure:**
```
text-to-sql-poc/
├── backend/
│   ├── services/
│   │   ├── claude_service.py (existing - may need minor updates)
│   │   ├── agentic_text2sql_service.py (NEW - main agentic orchestration)
│   │   ├── agent_tools.py (NEW - tool implementations)
│   │   └── session_manager.py (NEW - conversation context)
│   └── routes/
│       └── query_routes.py (UPDATE - add /query-agentic endpoint)
├── frontend/
│   └── src/
│       └── components/
│           ├── InsightCard.jsx (NEW - Natural Language Explanation)
│           ├── ClarificationDialog.jsx (NEW)
│           ├── IterationIndicator.jsx (NEW)
│           ├── ReflectionSummary.jsx (NEW)
│           └── ContextBadge.jsx (NEW)
└── docs/
    └── inspiration/
        └── agentic_text2sql.py (reference only)
```

**Service Architecture:**
- **Existing `/query` endpoint:** Keep unchanged for backward compatibility
- **New `/query-agentic` endpoint:** Route to AgenticText2SQLService
- **Shared resources:** Both endpoints use same database, schema, validation
- **Explanation Generation:** New service method `generate_explanation(query, sql, results)` calls Claude

**Integration Requirements:**
- LangGraph integrates with existing Claude service
- Agent tools call existing query_executor, sql_validator services
- Explanation generator calls Claude with results context
- Frontend backward compatible with existing `/query` endpoint
- Graceful fallback: if agentic fails, fall back to simple mode; if explanation fails, show results without explanation

**Security Considerations:**
- **Session Management:** Generate secure session_ids (UUID)
- **Session Isolation:** Ensure sessions don't leak across users
- **Rate Limiting:** Consider per-session limits to prevent abuse
- **Client Isolation:** Maintain existing client_id validation in all SQL queries
- **No New Security Risks:** Agentic logic is server-side; no client-side execution

---

## Constraints & Assumptions

### Constraints

**Budget:**
- POC enhancement budget: Time-boxed to 2-3 weeks of development effort
- Claude API costs: Expect 2-3x API calls per query due to iterations; acceptable for POC

**Timeline:**
- Target: 2-3 weeks for implementation and testing
- Milestone 1 (Week 1): LangGraph foundation + Planning agent + Tools
- Milestone 2 (Week 2): Clarification + Reflection + Session management
- Milestone 3 (Week 3): Frontend updates + Integration testing + Demo prep

**Resources:**
- Single developer for backend implementation
- Frontend developer (or same person) for UI updates
- No additional infrastructure required (local deployment)

**Technical:**
- Must work with existing SQLite database (no schema changes)
- Must maintain backward compatibility with existing `/query` endpoint
- Must exclude hybrid retrieval (simplified approach only)
- Must fit within current Python/React stack

### Key Assumptions

1. **LangGraph Suitability:** LangGraph is appropriate for this use case and can be learned/implemented within timeline
2. **Claude API Performance:** Claude API can handle multiple calls per query without unacceptable latency (assumes <2s per call)
3. **Simplified Approach Sufficient:** Agentic benefits are demonstrable even without hybrid retrieval and advanced tools
4. **Session Storage:** In-memory session storage is acceptable for POC demo (no persistence between server restarts)
5. **Demo Focus:** POC will be demoed locally with prepared scenarios, not deployed for production use
6. **Iteration Convergence:** Most queries will converge within 2-3 iterations; infinite loops are rare
7. **Clarification Coverage:** Claude can effectively detect ambiguity in 70-80% of genuinely ambiguous queries
8. **User Acceptance:** Market researchers will understand and appreciate agentic behavior (not find it confusing)

---

## Risks & Open Questions

### Key Risks

**1. Technical Complexity Risk**
- **Risk:** LangGraph learning curve delays implementation; state machine logic harder than expected
- **Impact:** High - Could miss timeline or deliver incomplete functionality
- **Mitigation:** 
  - Study inspiration code (`agentic_text2sql.py`) thoroughly before starting
  - Build incrementally: start with simplest state machine, add complexity
  - Allocate buffer time in week 3 for troubleshooting

**2. Iteration Performance Risk**
- **Risk:** Multi-step agentic workflow is too slow; users perceive it as sluggish
- **Impact:** Medium - Reduces demo impact if response times >10 seconds
- **Mitigation:**
  - Set max_iterations=2 for POC (limit retry loops)
  - Optimize prompts to reduce Claude API latency
  - Cache schema retrieval to avoid redundant calls
  - Display iteration progress to users so wait feels purposeful

**3. Clarification Quality Risk**
- **Risk:** Clarification detection is too aggressive (asks unnecessary questions) or too lenient (misses ambiguity)
- **Impact:** Medium - Poor UX reduces demo effectiveness
- **Mitigation:**
  - Tune clarification prompts carefully with test queries
  - Provide schema/metadata context to clarification agent to reduce false positives
  - Demo only with well-tested query scenarios

**4. Context Resolution Accuracy Risk**
- **Risk:** Follow-up query resolution misinterprets user intent ("what about Q4?" resolves incorrectly)
- **Impact:** Medium - Conversation feature fails to work in demo
- **Mitigation:**
  - Test extensively with prepared follow-up sequences
  - Keep conversation history short (last 5 queries) to reduce complexity
  - Have fallback: if resolution uncertain, ask for clarification

**5. Scope Creep Risk**
- **Risk:** Temptation to add features from inspiration code (hybrid retrieval, advanced tools) exceeds timeline
- **Impact:** High - Could derail POC completion
- **Mitigation:**
  - Strict adherence to MVP scope defined above
  - Defer any "nice-to-haves" to Phase 2
  - Regular check-ins on progress vs. timeline

**6. Stakeholder Expectation Risk**
- **Risk:** Demo audience expects production-ready system or confuses POC with full solution
- **Impact:** Medium - Could undermine build vs. buy case if expectations mismanaged
- **Mitigation:**
  - Clear communication before demo about POC scope
  - Frame as "proof of concept for agentic approach" not "final product"
  - Prepare slide deck explaining POC limitations and production roadmap

### Open Questions

1. **LangGraph Version:** Which version of LangGraph should be used? (Latest stable vs. specific version from inspiration code)
2. **Session Expiry:** How long should in-memory sessions persist? (1 hour? Until server restart?)
3. **Error Messaging:** For queries that fail after max iterations, what error message should users see?
4. **Metadata Source:** Do we need a business rules/metadata file, or can we skip this tool for POC?
5. **Frontend Backward Compatibility:** Should frontend support both agentic and non-agentic modes with toggle, or default to agentic only?
6. **Demo Script:** Which specific query scenarios should be prepared for demo? (Need 5-8 prepared examples)
7. **Reflection Criteria:** What specific checks define "acceptable" SQL quality in reflection agent?
8. **Logging:** How verbose should agentic workflow logging be? (Helpful for debugging but could be noisy)

### Areas Needing Further Research

**Before Implementation Starts:**
- Review LangGraph documentation and best practices (1-2 days)
- Analyze `agentic_text2sql.py` in detail to understand all state transitions (1 day)
- Research conversation context resolution patterns in LLM applications (1 day)

**During Implementation:**
- Test clarification detection effectiveness with 20-30 sample queries
- Benchmark iteration performance to validate <8 second target
- Gather informal feedback on UX of clarification flow from 2-3 colleagues

**For Production Roadmap:**
- Evaluate Vector DB options for future hybrid retrieval (Pinecone, Weaviate, ChromaDB)
- Research session persistence patterns (Redis vs. PostgreSQL vs. DynamoDB)
- Investigate query plan optimization algorithms for multi-query decomposition

---

## Appendices

### A. Inspiration Code Analysis Summary

**Source:** `docs/inspiration/agentic_text2sql.py`

**Key Architecture Patterns Adopted:**
1. **StateGraph with AgentState TypedDict** - Core state machine structure
2. **Node Functions** - Modular agent functions for each workflow step
3. **Conditional Edges** - Decision logic for routing between nodes
4. **Tool Pattern** - Reusable tool classes with execute() method
5. **Session Management** - Dictionary-based conversation history

**Key Patterns Simplified/Excluded:**
1. ~~Hybrid Retrieval (Vector + BM25)~~ → Direct schema retrieval
2. ~~Advanced Sample Data Retrieval~~ → Simple SQL queries if needed
3. ~~Complex Metadata Search~~ → Static file or skip entirely
4. ~~Redis Session Storage~~ → In-memory dictionary

**State Machine Nodes Implemented:**
- `detect_clarification_node`: Analyzes query for ambiguity
- `plan_node`: Decides next action based on state
- `execute_tools_node`: Executes tools (get_schema, execute_sql, validate_results)
- `generate_sql_node`: Generates SQL using Claude with context
- `reflect_node`: Evaluates quality and decides to retry or complete
- `complete_node`: Finalizes workflow

**Workflow Edges:**
- `detect_clarification` → [clarify | proceed]
- `plan` → [generate_sql | execute_tools | complete]
- `execute_tools` → `plan` (loop)
- `generate_sql` → `reflect`
- `reflect` → [refine | complete]

### B. Stakeholder Considerations

**Stakeholder Concerns to Address in Demo:**

1. **"How is this better than Number Station?"**
   - Answer: Agentic capabilities (clarification, reflection, context, **natural language insights**) are not standard features
   - Natural language explanations transform this from a query tool into an insights engine
   - Demonstrates AI sophistication and customization potential
   - Market researchers get answers, not just data

2. **"What's the cost impact of multiple API calls?"**
   - Answer: For POC, costs are manageable; production would optimize with caching and smarter routing
   - Long-term cost still likely lower than Number Station licensing

3. **"Is this production-ready?"**
   - Answer: This is POC demonstrating feasibility; production would require 3-6 months of hardening
   - Roadmap is clear and achievable

4. **"What if Claude is unavailable?"**
   - Answer: Fallback to simple mode (existing `/query` endpoint); production would add redundancy

5. **"How do we know SQL is correct?"**
   - Answer: Reflection and validation provide quality checks; production would add automated testing suite

### C. Demo Script Planning

**Recommended Demo Flow (8-10 minutes):**

1. **Introduction (1 min):**
   - Briefly recap current POC capabilities
   - Introduce agentic enhancement vision
   - Emphasize "intelligent assistant, not just a query tool"

2. **Scenario 1: Natural Language Insights (2 min):**
   - Submit query: "Top 10 products by revenue in Q3 2024"
   - **Highlight explanation card first:** 
     - "Samsung Galaxy S24 led Q3 2024 with $45,230 in revenue, representing 18% of total electronics sales. The top 3 products accounted for 42% of revenue, indicating strong concentration..."
   - Then show chart and data table
   - **Key message:** System doesn't just show data, it explains what it means

3. **Scenario 2: Clarification (2 min):**
   - Submit intentionally ambiguous query: "Show me sales trends"
   - System asks: "Which time period? Which region? All products or specific category?"
   - Provide clarification: "Q3 2024, all regions, electronics only"
   - System generates correct SQL and displays results with explanation

4. **Scenario 3: Error Recovery (1.5 min):**
   - Submit query that generates initially faulty SQL (designed to trigger reflection)
   - Show iteration counter incrementing
   - Display reflection result: "Detected syntax error, retrying..."
   - Show successful second attempt with explanation

5. **Scenario 4: Conversation Context (2.5 min):**
   - Initial query: "Top 10 products by revenue in Q3"
   - See explanation of Q3 results
   - Follow-up 1: "What about Q4?" → System maintains context, generates comparison
   - Follow-up 2: "Which products improved?" → Explanation highlights growth patterns
   - Demonstrate conversational flow throughout

6. **Wrap-up (1 min):**
   - Highlight key differentiators: insights, intelligence, conversation
   - Show system transparency (iterations, reflection results, context indicators)
   - Briefly mention production roadmap

### D. References

**Technical Documentation:**
- LangGraph Documentation: https://langchain-ai.github.io/langgraph/
- Anthropic Claude API Docs: https://docs.anthropic.com/claude/reference
- Existing Project Docs: `docs/product-brief-text-to-sql-poc-2025-11-25.md`, `docs/tech-spec.md`

**Inspiration Code:**
- `docs/inspiration/agentic_text2sql.py` (reference implementation)

**Related Research:**
- ReAct Pattern (Reasoning + Acting): https://arxiv.org/abs/2210.03629
- Multi-Agent Systems for LLM Applications: Various blog posts and papers

---

## Next Steps

### Immediate Actions

1. **Review & Refine This Brief** (1-2 days)
   - Team review session to validate approach
   - Gather feedback from stakeholders on priorities
   - Finalize MVP scope and demo scenarios

2. **Technical Preparation** (2-3 days)
   - Study LangGraph documentation thoroughly
   - Set up development branch: `feature/agentic-enhancement`
   - Install dependencies: `pip install langgraph`
   - Review inspiration code in detail

3. **Create Implementation Plan** (1 day)
   - Break down MVP into implementable tasks/stories
   - Create GitHub issues or task list
   - Assign timeline estimates to each task

4. **Begin Development** (Week 1)
   - Start with LangGraph foundation and Planning agent
   - Implement core state machine with 2-3 simple nodes
   - Test state transitions thoroughly

### Handoff to Development Team

**For Architect:**
This Project Brief provides full context for the Agentic Text-to-SQL enhancement. Please:
- Review technical approach and validate LangGraph architecture fit
- Design detailed state machine diagram showing all nodes and edges
- Identify any technical risks or concerns not captured here
- Create technical specification document if needed

**For Developer:**
Once architecture is validated:
- Implement in order: Planning Agent → Tools → Reflection → Clarification → Session Management
- Follow modular pattern from inspiration code
- Test each node independently before integration
- Maintain backward compatibility with existing `/query` endpoint throughout

**For PM/Product Owner:**
- Schedule stakeholder demo for end of Week 3
- Prepare demo scenarios aligned with business case
- Create slides explaining agentic approach benefits
- Plan feedback collection mechanism for post-demo

---

**Project Brief Status:** ✅ Complete - Ready for Review

**Next Document:** Technical Specification (Architecture Detail) or Epic Breakdown (Implementation Stories)

---

*This Project Brief was created collaboratively by Business Analyst Mary and DS using the BMAD Method framework. It captures the vision and requirements for enhancing the Text-to-SQL POC with agentic AI capabilities to demonstrate technical superiority in the build vs. buy decision.*

