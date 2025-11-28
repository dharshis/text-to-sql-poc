# Architecture Document: Agentic Text-to-SQL Enhancement

**Project:** Text-to-SQL POC - Agentic Enhancement  
**Architect:** Winston  
**Date:** 2025-11-27  
**Version:** 1.0  
**Status:** Design - Ready for Implementation  

---

## Executive Summary

This document defines the architecture for enhancing the existing Text-to-SQL POC with agentic AI capabilities powered by LangGraph. The enhancement transforms a simple single-shot SQL generation system into an intelligent multi-agent workflow that can detect ambiguity, plan actions, self-correct errors, maintain conversation context, and explain results in natural language.

**Key Architectural Decisions:**
- **State Machine Pattern:** LangGraph StateGraph for workflow orchestration
- **Modular Agents:** Specialized nodes for clarification, planning, generation, reflection, explanation
- **Tool-Based Execution:** Reusable tools for schema retrieval, SQL execution, validation
- **Session-Based Context:** In-memory conversation management for POC
- **Backward Compatibility:** Existing `/query` endpoint unchanged; new `/query-agentic` endpoint

**Strategic Goals:**
- Demonstrate technical superiority over external vendors (Number Station)
- Position system as "insights engine" not just "query tool"
- Prove sophisticated AI capabilities justify build vs. buy decision

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Architecture Principles](#2-architecture-principles)
3. [Component Architecture](#3-component-architecture)
4. [LangGraph State Machine](#4-langgraph-state-machine)
5. [Agent Nodes](#5-agent-nodes)
6. [Tool Infrastructure](#6-tool-infrastructure)
7. [Session Management](#7-session-management)
8. [API Design](#8-api-design)
9. [Frontend Architecture](#9-frontend-architecture)
10. [Data Flow](#10-data-flow)
11. [Integration Patterns](#11-integration-patterns)
12. [Security Architecture](#12-security-architecture)
13. [Performance Architecture](#13-performance-architecture)
14. [Deployment Architecture](#14-deployment-architecture)
15. [Testing Strategy](#15-testing-strategy)
16. [Implementation Roadmap](#16-implementation-roadmap)

---

## 1. System Overview

### 1.1 Current State (Baseline)

**Existing Architecture:**
```
User → React Frontend → Flask API (/query) → Claude Service → SQL Generation
                                          ↓
                                    SQL Validator
                                          ↓
                                    Query Executor
                                          ↓
                                    Results → Frontend Display
```

**Current Capabilities:**
- Single-shot SQL generation from natural language
- Basic client isolation validation
- SQL execution and result display
- Simple visualization (charts + tables)

**Limitations:**
- No ambiguity detection
- No error recovery (retry mechanism)
- No conversation context
- No results explanation
- Linear, non-adaptive workflow

### 1.2 Target State (Enhanced)

**Agentic Architecture:**
```
User → React Frontend → Flask API (/query-agentic) → AgenticText2SQLService
                                                              ↓
                                                      LangGraph Workflow
                                                              ↓
                    ┌─────────────────────────────────────────┴─────────────────────────────────────────┐
                    │                         STATE MACHINE ORCHESTRATION                                │
                    └─────────────────────────────────────────┬─────────────────────────────────────────┘
                                                              ↓
        ┌──────────────────────────────────────────────────────────────────────────────────────────┐
        │                                    AGENT NODES                                            │
        │  Clarification → Planning → Tool Execution → SQL Generation → Reflection → Explanation   │
        └──────────────────────────────────────────────────────────────────────────────────────────┘
                                                              ↓
                    ┌─────────────────────────────────────────┴─────────────────────────────────────────┐
                    │                              TOOLS & SERVICES                                      │
                    │  Schema Retrieval │ SQL Executor │ Validator │ Session Manager │ Claude API       │
                    └─────────────────────────────────────────┬─────────────────────────────────────────┘
                                                              ↓
                                      Results + Explanation + Metadata
                                                              ↓
                                      React Frontend (Enhanced Components)
```

**Enhanced Capabilities:**
- ✅ Ambiguity detection with clarification questions
- ✅ Iterative SQL generation with self-correction (reflection)
- ✅ Conversation context for follow-up queries
- ✅ Natural language result explanations
- ✅ Transparent workflow with iteration tracking
- ✅ Intelligent planning and tool orchestration

---

## 2. Architecture Principles

### 2.1 Design Principles

**1. State-Driven Workflow**
- All agent behavior driven by immutable state (AgentState TypedDict)
- State transitions are explicit and testable
- State carries full context through entire workflow

**2. Modular Agent Pattern**
- Each agent node has single, clear responsibility
- Nodes are independently testable
- Loose coupling through state interface

**3. Tool-Based Execution**
- Reusable tools with consistent interface
- Tool execution isolated from planning logic
- Easy to add new tools without changing agents

**4. Progressive Enhancement**
- Existing `/query` endpoint remains unchanged
- New `/query-agentic` endpoint for enhanced flow
- Frontend backward compatible

**5. Fail-Safe Design**
- Graceful degradation (e.g., explanation fails → show results without explanation)
- Max iteration limits prevent infinite loops
- Clear error messages for debugging

**6. Observable Workflow**
- All decisions logged
- State transitions visible
- Tool calls tracked
- Iteration counter exposed

### 2.2 Technology Alignment

**Chosen Technologies:**
- **LangGraph:** State machine orchestration (proven pattern from inspiration code)
- **TypedDict:** State structure (Python 3.8+ standard, no Pydantic dependency)
- **operator.add:** State field accumulation (built-in, no extra deps)
- **In-Memory Storage:** Session management for POC (Redis path for production)

**Rationale:**
- Minimize new dependencies
- Use proven patterns (inspiration code validation)
- Keep complexity appropriate for POC timeline
- Clear upgrade path to production

### 2.3 Non-Functional Requirements

**Performance:**
- Total response time ≤10 seconds (including retries + explanation)
- Individual agent nodes ≤2 seconds each
- Claude API calls ≤2 seconds (typical)
- Max 3 iterations per query

**Scalability:**
- POC: Single-instance, in-memory sessions
- Production path: Stateless agents + Redis sessions + horizontal scaling

**Reliability:**
- Graceful error handling at every node
- No crashes on invalid input or API failures
- Clear error messages for debugging

**Observability:**
- Structured logging for all agent decisions
- State snapshots at key transitions
- Tool execution tracking
- Performance timing per node

---

## 3. Component Architecture

### 3.1 High-Level Components

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                               FRONTEND LAYER                                         │
│  ┌─────────────┐  ┌──────────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │ InsightCard │  │ ClarificationDlg │  │ IterIndicator│  │ ReflectionSummary│   │
│  └─────────────┘  └──────────────────┘  └──────────────┘  └──────────────────┘   │
│  ┌──────────────┐  ┌─────────────────────────────────────────────────────────┐   │
│  │ ContextBadge │  │          Existing Components (Chart, Table, etc.)       │   │
│  └──────────────┘  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────┬───────────────────────────────────────────┘
                                          │ HTTP/JSON
┌─────────────────────────────────────────┴───────────────────────────────────────────┐
│                                API LAYER                                             │
│  ┌──────────────────────┐                ┌────────────────────────┐                │
│  │  /query (existing)   │                │  /query-agentic (new)  │                │
│  │  Simple flow         │                │  Agentic workflow      │                │
│  └──────────────────────┘                └────────────────────────┘                │
└─────────────────────────────────────────┬───────────────────────────────────────────┘
                                          │
┌─────────────────────────────────────────┴───────────────────────────────────────────┐
│                           SERVICE LAYER                                              │
│  ┌───────────────────────────────────────────────────────────────────────────┐     │
│  │                     AgenticText2SQLService                                 │     │
│  │  - Workflow orchestration                                                  │     │
│  │  - Session management                                                      │     │
│  │  - Response formatting                                                     │     │
│  └───────────────────────────────────────────────────────────────────────────┘     │
│  ┌───────────────────────────────────────────────────────────────────────────┐     │
│  │                     LangGraph StateGraph                                   │     │
│  │  - State machine execution                                                 │     │
│  │  - Node routing                                                            │     │
│  │  - State management                                                        │     │
│  └───────────────────────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────┬───────────────────────────────────────────┘
                                          │
┌─────────────────────────────────────────┴───────────────────────────────────────────┐
│                          AGENT NODES LAYER                                           │
│  ┌──────────────┐  ┌──────────┐  ┌───────────────┐  ┌────────────┐  ┌────────────┐│
│  │Clarification │  │ Planning │  │ SQL Generation│  │ Reflection │  │Explanation ││
│  │    Node      │  │   Node   │  │     Node      │  │    Node    │  │    Node    ││
│  └──────────────┘  └──────────┘  └───────────────┘  └────────────┘  └────────────┘│
│  ┌──────────────┐  ┌──────────┐                                                    │
│  │ Execute Tools│  │ Complete │                                                    │
│  │    Node      │  │   Node   │                                                    │
│  └──────────────┘  └──────────┘                                                    │
└─────────────────────────────────────────┬───────────────────────────────────────────┘
                                          │
┌─────────────────────────────────────────┴───────────────────────────────────────────┐
│                           TOOL LAYER                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐  ┌──────────────────┐   │
│  │ get_schema   │  │ execute_sql  │  │ validate_results│  │ search_metadata  │   │
│  │    Tool      │  │    Tool      │  │      Tool       │  │      Tool        │   │
│  └──────────────┘  └──────────────┘  └─────────────────┘  └──────────────────┘   │
└─────────────────────────────────────────┬───────────────────────────────────────────┘
                                          │
┌─────────────────────────────────────────┴───────────────────────────────────────────┐
│                      INFRASTRUCTURE LAYER                                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ ClaudeService│  │  DBManager   │  │ SessionStore │  │  QueryExecutor       │  │
│  │  (existing)  │  │  (existing)  │  │   (new)      │  │  (existing)          │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Component Responsibilities

**Frontend Layer:**
- InsightCard: Display natural language explanations
- ClarificationDialog: Show clarification questions, collect user responses
- IterationIndicator: Display retry counter
- ReflectionSummary: Show quality assessment results
- ContextBadge: Indicate follow-up query context

**API Layer:**
- `/query`: Existing simple flow (backward compatible)
- `/query-agentic`: New agentic workflow endpoint

**Service Layer:**
- AgenticText2SQLService: Main orchestrator, manages workflow lifecycle
- LangGraph StateGraph: State machine execution engine

**Agent Nodes Layer:**
- Individual agent functions (clarification, planning, generation, reflection, explanation)
- Stateless, pure functions (input: state, output: state updates)

**Tool Layer:**
- Modular, reusable tools with consistent interface
- Error handling and logging

**Infrastructure Layer:**
- Existing services (Claude, DB, QueryExecutor)
- New: SessionStore for conversation context

---

## 4. LangGraph State Machine

### 4.1 AgentState Structure

```python
class AgentState(TypedDict):
    """Complete state for agentic workflow"""
    
    # ===== CORE QUERY INFO =====
    user_query: str                    # Original user question
    session_id: str                    # Session identifier for context
    resolved_query: str                # Query with history context resolved
    
    # ===== CONVERSATION CONTEXT =====
    chat_history: Annotated[List[Dict], operator.add]  # Previous queries/results
    
    # ===== ITERATION TRACKING =====
    iteration: int                     # Current iteration count
    max_iterations: int                # Maximum retry limit (default: 3)
    
    # ===== RETRIEVED CONTEXT =====
    schema: Optional[str]              # Database schema
    sample_data: Dict[str, str]        # Sample data per table
    metadata_context: Annotated[List[Dict], operator.add]  # Business rules
    
    # ===== GENERATED ARTIFACTS =====
    sql_query: Optional[str]           # Generated SQL
    execution_result: Optional[Dict]   # Query execution results
    validation_result: Optional[Dict]  # Validation checks
    explanation: Optional[str]         # Natural language explanation
    
    # ===== REFLECTION & CLARIFICATION =====
    reflection_result: Optional[Dict]  # Quality assessment
    clarification_needed: bool         # Whether to ask user for clarification
    clarification_questions: Annotated[List[str], operator.add]
    
    # ===== TOOL TRACKING =====
    tool_calls: Annotated[List[Dict], operator.add]  # Record of tool executions
    
    # ===== FLOW CONTROL =====
    next_action: str                   # Next action to take
    is_complete: bool                  # Workflow completion flag
    error: Optional[str]               # Error message if failed
```

**Design Rationale:**
- **TypedDict:** Clear contract, IDE support, no Pydantic dependency
- **Annotated[List, operator.add]:** Accumulate history/tool_calls across nodes
- **Optional fields:** Not all fields populated at all times
- **Flat structure:** Easy to access, no nested complexity

### 4.2 State Machine Graph

```
                                    START
                                      ↓
                          ┌───────────────────────┐
                          │ detect_clarification  │ (Entry Point)
                          └───────────┬───────────┘
                                      ↓
                              ┌───────┴────────┐
                              │  Clarification  │
                              │    needed?      │
                              └───┬─────────┬───┘
                                  │         │
                         Yes ─────┘         └───── No
                          ↓                        ↓
                  ┌───────────────┐        ┌──────────────┐
                  │   complete    │        │     plan     │
                  │(return Qs to  │        │   (decide    │
                  │     user)     │        │  next action)│
                  └───────────────┘        └──────┬───────┘
                                                  ↓
                                          ┌───────┴────────┐
                                          │  Next Action?  │
                                          └────────────────┘
                                     ┌────────┼────────┬─────────┐
                                     │        │        │         │
                              execute_tools  generate  reflect complete
                                     │        sql      │         │
                                     ↓        ↓        ↓         ↓
                          ┌──────────────┐ ┌─────┐ ┌────────┐ END
                          │  Tool Exec   │ │ SQL │ │Reflect │
                          │ get_schema   │ │Gen  │ │Quality │
                          │ execute_sql  │ └──┬──┘ └───┬────┘
                          │ validate     │    │        │
                          └──────┬───────┘    │        │
                                 │            │        │
                                 └────────────┴────────┘
                                              ↓
                                    ┌─────────┴────────┐
                                    │ Should refine?   │
                                    └──────────────────┘
                                       │            │
                                 Yes ──┘            └── No
                                  ↓                    ↓
                            Back to plan        generate_explanation
                         (reset SQL state)              ↓
                                                   ┌─────────────┐
                                                   │ Explanation │
                                                   └──────┬──────┘
                                                          ↓
                                                    Back to plan
                                                  (then complete)
```

### 4.3 Node Routing Logic

**Conditional Edges:**

1. **From detect_clarification:**
   - If `clarification_needed == True` → complete (return questions)
   - Else → plan

2. **From plan:**
   - If `next_action == "generate_sql"` → generate_sql
   - If `next_action == "reflect"` → reflect
   - If `next_action == "generate_explanation"` → generate_explanation
   - If `next_action == "complete"` → complete
   - Else → execute_tools

3. **From reflect:**
   - If `should_refine == True` AND `iteration < max_iterations` → plan (retry)
   - Else → plan (proceed to explanation)

**Loop Points:**
- execute_tools → plan (tool results trigger replanning)
- generate_sql → plan (SQL generated, proceed to execution)
- generate_explanation → plan (explanation done, complete)
- reflect (refine) → plan (reset SQL, retry)

---

## 5. Agent Nodes

### 5.1 Node Catalog

| Node Name | Purpose | Input Dependencies | Output Updates |
|-----------|---------|-------------------|----------------|
| detect_clarification | Detect ambiguous queries | user_query, schema (optional) | clarification_needed, questions, schema |
| plan | Decide next action | All state fields | next_action, iteration |
| execute_tools | Execute specific tool | next_action, query params | schema/results/validation, tool_calls |
| generate_sql | Generate SQL with Claude | schema, user_query | sql_query |
| reflect | Evaluate SQL quality | sql_query, execution_result | reflection_result |
| generate_explanation | Explain results | execution_result, query | explanation |
| complete | Finalize workflow | All state | is_complete |

### 5.2 Node Implementation Patterns

**Standard Node Signature:**
```python
def _node_name(self, state: AgentState) -> Dict:
    """
    Node function processes state and returns updates.
    
    Args:
        state: Current AgentState
        
    Returns:
        Dict with fields to update in state
    """
    # 1. Extract needed fields from state
    # 2. Perform node logic
    # 3. Return state updates (partial dict)
    pass
```

**Error Handling Pattern:**
```python
def _node_name(self, state: AgentState) -> Dict:
    try:
        # Node logic
        result = perform_operation()
        return {"field": result}
    except Exception as e:
        logger.error(f"Node failed: {e}")
        return {
            "error": str(e),
            "is_complete": True  # Stop workflow on critical errors
        }
```

### 5.3 Detailed Node Designs

#### 5.3.1 Clarification Detection Node

**Purpose:** Analyze query for ambiguity before SQL generation

**Algorithm:**
```python
def _detect_clarification_node(self, state: AgentState) -> Dict:
    """Detect if query needs clarification"""
    
    query = state["resolved_query"]
    
    # Retrieve schema for context
    schema_result = self.tools['get_schema'].execute(query=query)
    schema = schema_result.get("result") if schema_result.get("success") else None
    
    # Build clarification prompt
    prompt = f"""
    Analyze this query for ambiguity:
    Query: {query}
    Schema: {schema[:1000]}
    
    Is clarification needed? Consider:
    - Missing time periods, metrics, filters
    - Vague terms
    - Multiple interpretations
    
    Return JSON:
    {{"needs_clarification": bool, "questions": ["q1", "q2"]}}
    """
    
    # Call Claude for analysis
    response = claude_api_call(prompt)
    result = json.loads(response)
    
    return {
        "clarification_needed": result["needs_clarification"],
        "clarification_questions": result["questions"],
        "schema": schema  # Cache for later use
    }
```

**Decision Criteria:**
- Needs clarification: Missing critical context (dates, metrics, entities)
- Proceeds: Query has sufficient context given schema

**Error Handling:**
- If detection fails → proceed without clarification (fail-safe)

#### 5.3.2 Planning Node

**Purpose:** Intelligent workflow routing based on current state

**Algorithm:**
```python
def _plan_node(self, state: AgentState) -> Dict:
    """Plan next action based on state"""
    
    iteration = state["iteration"] + 1
    
    # Check iteration limit
    if iteration > state["max_iterations"]:
        return {"next_action": "complete", "is_complete": True, "iteration": iteration}
    
    # Decision tree
    if state["schema"] is None:
        next_action = "get_schema"
    elif state["sql_query"] is None:
        next_action = "generate_sql"
    elif state["execution_result"] is None:
        next_action = "execute_sql"
    elif state["validation_result"] is None:
        next_action = "validate_results"
    elif state["reflection_result"] is None:
        next_action = "reflect"
    elif state["explanation"] is None and state["execution_result"].get("success"):
        next_action = "generate_explanation"
    else:
        next_action = "complete"
        is_complete = True
    
    return {"next_action": next_action, "iteration": iteration}
```

**Decision Tree:**
1. Schema not retrieved? → get_schema
2. SQL not generated? → generate_sql
3. SQL not executed? → execute_sql
4. Results not validated? → validate_results
5. Quality not reflected? → reflect
6. Results not explained? → generate_explanation
7. All done? → complete

#### 5.3.3 Reflection Node

**Purpose:** Evaluate SQL quality, decide if retry needed

**Algorithm:**
```python
def _reflect_node(self, state: AgentState) -> Dict:
    """Reflect on SQL quality"""
    
    execution_result = state.get("execution_result")
    should_refine = False
    issues = []
    
    # Check for critical errors
    if execution_result and not execution_result.get("success"):
        error_msg = execution_result.get("error", "").lower()
        
        critical_keywords = [
            "syntax error", "parse error", "invalid sql",
            "unknown column", "unknown table", "no such table"
        ]
        
        if any(kw in error_msg for kw in critical_keywords):
            should_refine = True
            issues.append(f"Critical error: {error_msg}")
    
    reflection = {
        "is_acceptable": not should_refine,
        "should_refine": should_refine,
        "issues": issues
    }
    
    return {"reflection_result": reflection}
```

**Retry Decision:**
- **Retry:** Critical SQL errors (syntax, unknown tables/columns)
- **Proceed:** Empty results, performance warnings, data issues
- **Max iterations:** Stop retrying after max_iterations

#### 5.3.4 Explanation Generation Node

**Purpose:** Transform results into natural language insights

**Algorithm:**
```python
def _generate_explanation_node(self, state: AgentState) -> Dict:
    """Generate natural language explanation"""
    
    query = state["user_query"]
    sql = state["sql_query"]
    results = state["execution_result"]
    
    # Handle empty results
    if not results or not results.get("data"):
        return {"explanation": "No results found for this query."}
    
    # Prepare data for Claude
    data = results["data"][:20]  # Limit sample
    columns = results["columns"]
    
    prompt = f"""
    Explain these results in 2-4 sentences:
    
    User Question: {query}
    SQL: {sql}
    Results: {format_data(data, columns)}
    
    Highlight: top values, trends, comparisons, anomalies
    Write for business users, not technical.
    """
    
    explanation = claude_api_call(prompt)
    
    return {"explanation": explanation}
```

**Explanation Quality:**
- 2-4 sentences
- Plain English, no jargon
- Highlights key insights (top items, trends, comparisons)
- Actionable for business users

---

## 6. Tool Infrastructure

### 6.1 Tool Base Class

```python
class Tool:
    """Base tool class for agentic workflow"""
    
    def __init__(self, name: str, description: str, function: Callable):
        self.name = name
        self.description = description
        self.function = function
    
    def execute(self, **kwargs) -> Dict:
        """Execute tool with error handling"""
        try:
            result = self.function(**kwargs)
            return {
                "success": True,
                "tool": self.name,
                "result": result
            }
        except Exception as e:
            logger.error(f"Tool {self.name} failed: {e}")
            return {
                "success": False,
                "tool": self.name,
                "error": str(e)
            }
```

**Tool Contract:**
- Input: Keyword arguments (flexible per tool)
- Output: Standardized dict with success/result/error
- Error handling: Catch all exceptions, return error structure
- Logging: Log all executions and errors

### 6.2 Tool Catalog

| Tool Name | Purpose | Parameters | Returns |
|-----------|---------|------------|---------|
| get_schema | Retrieve database schema | query (optional) | Schema string |
| execute_sql | Execute SQL query | sql (required) | {success, data, columns, row_count} |
| validate_results | Validate query results | query, sql, results | {is_valid, has_results, row_count, issues} |
| search_metadata | Search business rules | query, top_k | List of relevant documents |

### 6.3 Tool Implementation Details

**get_schema Tool:**
```python
def _get_schema_tool(self, query: str = None) -> str:
    """Retrieve database schema directly"""
    # Simplified: no hybrid retrieval per requirements
    return self.claude_service.get_schema_info()
```

**execute_sql Tool:**
```python
def _execute_sql_tool(self, sql: str) -> Dict:
    """Execute SQL safely"""
    executor = QueryExecutor()
    return executor.execute_query(sql)
```

**validate_results Tool:**
```python
def _validate_results_tool(self, query: str, sql: str, results: Dict) -> Dict:
    """Basic validation"""
    return {
        "is_valid": True,
        "has_results": bool(results.get("data")),
        "row_count": len(results.get("data", [])),
        "issues": []
    }
```

---

## 7. Session Management

### 7.1 Session Architecture

**Storage:** In-memory dictionary for POC
```python
self.chat_sessions = {
    "session-123": [
        {
            "user_query": "Top 10 products in Q3",
            "resolved_query": "Top 10 products in Q3",
            "sql": "SELECT...",
            "results_summary": "10 rows, columns: product_name, revenue",
            "timestamp": "2024-01-01T00:00:00"
        }
    ]
}
```

**Session Lifecycle:**
- Created: On first query with session_id
- Updated: After each successful query
- Retained: Last 10 queries per session
- Expires: On server restart (POC limitation)

### 7.2 Query Resolution

**Follow-Up Detection:**
Keywords: "what about", "show me", "that", "this", "same but"

**Resolution Process:**
1. Retrieve last 3 queries from session
2. Build history context string
3. Call Claude to resolve follow-up into standalone query
4. Return resolved query or original if not a follow-up

```python
def _resolve_query_with_history(self, user_query: str, chat_history: List[Dict]) -> str:
    """Resolve follow-up queries"""
    if not chat_history:
        return user_query
    
    history_str = format_history(chat_history[-3:])
    
    prompt = f"""
    History: {history_str}
    New query: {user_query}
    
    If follow-up, rewrite as standalone. Else return unchanged.
    """
    
    resolved = claude_api_call(prompt)
    return resolved
```

### 7.3 Production Path

**Future Enhancements:**
- Redis for session persistence
- Session expiry (TTL: 1 hour)
- Session cleanup cron job
- Multi-server session sharing

---

## 8. API Design

### 8.1 Endpoint Specifications

#### `/query-agentic` (POST)

**Request:**
```json
{
  "query": "Show me top 10 products by revenue in Q3",
  "session_id": "uuid-v4-string",
  "client_id": 1,
  "max_iterations": 3
}
```

**Response (Success):**
```json
{
  "success": true,
  "sql": "SELECT p.product_name, SUM(s.revenue) as total_revenue...",
  "results": {
    "data": [...],
    "columns": ["product_name", "total_revenue"],
    "row_count": 10
  },
  "explanation": "Samsung Galaxy S24 led Q3 2024 with $45,230 in revenue...",
  "validation": {
    "passed": true,
    "checks": [...]
  },
  "reflection": {
    "is_acceptable": true,
    "issues": []
  },
  "method": "agentic",
  "session_id": "uuid-v4-string",
  "iterations": 1,
  "tool_calls": 4,
  "is_followup": false
}
```

**Response (Clarification Needed):**
```json
{
  "success": false,
  "needs_clarification": true,
  "questions": [
    "Which time period would you like to analyze? (Q1, Q2, Q3, Q4, or full year)",
    "Should this include all products or specific categories?"
  ],
  "method": "agentic",
  "session_id": "uuid-v4-string"
}
```

**Response (Error):**
```json
{
  "success": false,
  "error": "Max iterations exceeded. Unable to generate valid SQL.",
  "method": "agentic",
  "iterations": 3
}
```

### 8.2 Backward Compatibility

**Existing `/query` endpoint:** Unchanged
- Routes to simple ClaudeService flow
- No breaking changes
- Existing frontend code continues to work

**Migration Path:**
- Frontend can detect agentic endpoint availability
- Graceful fallback to simple endpoint if needed
- Feature flag for agentic mode

---

## 9. Frontend Architecture

### 9.1 Component Hierarchy

```
App.jsx
├── SearchBar.jsx
│   ├── ClientSelector (existing)
│   ├── QueryInput (existing)
│   ├── SubmitButton (existing)
│   └── IterationIndicator (NEW)
│
├── ContextBadge (NEW - below search bar)
│
├── ClarificationDialog (NEW - modal)
│
└── ResultsDisplay.jsx
    ├── InsightCard (NEW - PROMINENT TOP POSITION)
    ├── DataVisualization.jsx (existing)
    ├── DataTable.jsx (existing)
    ├── SqlDisplay.jsx (existing)
    ├── ValidationMetrics.jsx (existing)
    └── ReflectionSummary (NEW - collapsible)
```

### 9.2 Component Specifications

**InsightCard (Priority #1):**
```jsx
<Card sx={{ mb: 2, backgroundColor: '#f0f8ff' }}>
  <CardContent>
    <Box display="flex" alignItems="center">
      <Lightbulb sx={{ color: '#ffc107', mr: 1 }} />
      <Typography variant="h6">Key Insights</Typography>
    </Box>
    <Typography variant="body1" sx={{ mt: 2, fontSize: '16px' }}>
      {explanation}
    </Typography>
  </CardContent>
</Card>
```

**ClarificationDialog:**
```jsx
<Dialog open={needsClarification} maxWidth="sm">
  <DialogTitle>Need More Information</DialogTitle>
  <DialogContent>
    <List>
      {questions.map((q, idx) => (
        <ListItem key={idx}>{idx + 1}. {q}</ListItem>
      ))}
    </List>
    <TextField 
      multiline 
      rows={3} 
      value={response} 
      onChange={...}
      label="Your Response"
    />
  </DialogContent>
  <DialogActions>
    <Button onClick={handleSubmit}>Submit</Button>
  </DialogActions>
</Dialog>
```

### 9.3 State Management

**Session State:**
```javascript
const [sessionId, setSessionId] = useState(() => uuidv4());
```

**Query State:**
```javascript
const [queryState, setQueryState] = useState({
  loading: false,
  results: null,
  explanation: null,
  needsClarification: false,
  questions: [],
  iteration: 0,
  error: null
});
```

**API Integration:**
```javascript
const executeAgenticQuery = async (query, sessionId, clientId) => {
  const response = await axios.post('/query-agentic', {
    query,
    session_id: sessionId,
    client_id: clientId
  });
  
  if (response.data.needs_clarification) {
    // Show clarification dialog
    setQueryState({
      needsClarification: true,
      questions: response.data.questions
    });
  } else {
    // Show results with explanation
    setQueryState({
      results: response.data.results,
      explanation: response.data.explanation,
      iteration: response.data.iterations,
      // ...
    });
  }
};
```

---

## 10. Data Flow

### 10.1 Happy Path Flow

```
User submits query
    ↓
Frontend: Generate/use session_id
    ↓
POST /query-agentic {query, session_id, client_id}
    ↓
Backend: AgenticText2SQLService.generate_sql_with_agent()
    ↓
Retrieve chat_history(session_id)
    ↓
Resolve query with history
    ↓
Initialize AgentState
    ↓
workflow.invoke(initial_state)
    ↓
┌─────────────────────────────────────┐
│ detect_clarification                │
│ - Get schema                        │
│ - Analyze query                     │
│ - Decision: proceed (no clarification)│
└────────────┬────────────────────────┘
             ↓
┌─────────────────────────────────────┐
│ plan (iteration=1)                  │
│ - Decision: get_schema              │
└────────────┬────────────────────────┘
             ↓
┌─────────────────────────────────────┐
│ execute_tools                       │
│ - Execute get_schema tool           │
│ - Update state: schema=...          │
└────────────┬────────────────────────┘
             ↓
┌─────────────────────────────────────┐
│ plan (iteration=1)                  │
│ - Decision: generate_sql            │
└────────────┬────────────────────────┘
             ↓
┌─────────────────────────────────────┐
│ generate_sql                        │
│ - Call Claude with schema           │
│ - Extract clean SQL                 │
│ - Update state: sql_query=...       │
└────────────┬────────────────────────┘
             ↓
┌─────────────────────────────────────┐
│ plan (iteration=1)                  │
│ - Decision: execute_sql             │
└────────────┬────────────────────────┘
             ↓
┌─────────────────────────────────────┐
│ execute_tools                       │
│ - Execute execute_sql tool          │
│ - Update state: execution_result=...│
└────────────┬────────────────────────┘
             ↓
┌─────────────────────────────────────┐
│ plan (iteration=1)                  │
│ - Decision: validate_results        │
└────────────┬────────────────────────┘
             ↓
┌─────────────────────────────────────┐
│ execute_tools                       │
│ - Execute validate_results tool     │
│ - Update state: validation_result=...│
└────────────┬────────────────────────┘
             ↓
┌─────────────────────────────────────┐
│ plan (iteration=1)                  │
│ - Decision: reflect                 │
└────────────┬────────────────────────┘
             ↓
┌─────────────────────────────────────┐
│ reflect                             │
│ - Evaluate SQL quality              │
│ - Decision: acceptable (no refine)  │
│ - Update state: reflection_result=...│
└────────────┬────────────────────────┘
             ↓
┌─────────────────────────────────────┐
│ plan (iteration=1)                  │
│ - Decision: generate_explanation    │
└────────────┬────────────────────────┘
             ↓
┌─────────────────────────────────────┐
│ generate_explanation                │
│ - Call Claude with results          │
│ - Generate insights                 │
│ - Update state: explanation=...     │
└────────────┬────────────────────────┘
             ↓
┌─────────────────────────────────────┐
│ plan (iteration=1)                  │
│ - Decision: complete                │
└────────────┬────────────────────────┘
             ↓
┌─────────────────────────────────────┐
│ complete                            │
│ - Mark is_complete=True             │
└────────────┬────────────────────────┘
             ↓
workflow returns final_state
    ↓
Add to session history
    ↓
Format response with all fields
    ↓
Return JSON to frontend
    ↓
Frontend displays:
    - InsightCard (explanation)
    - Chart (visualization)
    - Table (data)
    - SQL (generated query)
    - Reflection (quality check)
```

**Total Steps:** 9 nodes executed, 1 iteration
**Typical Time:** 6-8 seconds

### 10.2 Clarification Flow

```
User submits vague query: "Show me sales trends"
    ↓
Backend: detect_clarification
    - Analyzes query + schema
    - Decision: ambiguous (missing time period, product category)
    - Returns: clarification_needed=True, questions=["Which time period?", ...]
    ↓
Workflow completes immediately (no SQL generation)
    ↓
Frontend receives clarification response
    ↓
ClarificationDialog opens with questions
    ↓
User provides response: "Q3 2024, electronics only"
    ↓
Frontend resubmits: "Show me sales trends for electronics in Q3 2024"
    ↓
Backend: detect_clarification
    - Decision: clear (proceeds)
    ↓
... (continue with normal flow)
```

### 10.3 Retry Flow

```
... (normal flow until SQL execution)
    ↓
execute_tools: execute_sql
    - SQL has syntax error: "SELCT * FROM products"
    - Returns: success=False, error="syntax error near SELCT"
    ↓
plan: route to reflect
    ↓
reflect:
    - Detects critical error
    - Decision: should_refine=True
    ↓
Conditional routing: refine → plan
    - Resets: sql_query=None, execution_result=None, validation_result=None
    ↓
plan (iteration=2):
    - Decision: generate_sql (retry)
    ↓
generate_sql:
    - Calls Claude again with same context
    - Generates corrected SQL: "SELECT * FROM products"
    ↓
... (continue execution with corrected SQL)
    ↓
reflect:
    - Decision: acceptable (no more errors)
    - Proceeds to explanation
```

**Max Retries:** 3 iterations
**Retry Trigger:** Critical SQL errors only

---

## 11. Integration Patterns

### 11.1 Integration with Existing Services

**ClaudeService Integration:**
```python
# AgenticText2SQLService uses existing ClaudeService
self.claude_service = ClaudeService()

# Reuse for SQL generation
sql = self.claude_service.generate_sql(query, client_id)

# Reuse system prompts and schema info
schema = self.claude_service.get_schema_info()
```

**DBManager Integration:**
```python
# Tools leverage existing DB manager
def _get_schema_tool(self, query: str = None) -> str:
    return self.db_manager.get_schema()
```

**QueryExecutor Integration:**
```python
# execute_sql tool uses existing executor
def _execute_sql_tool(self, sql: str) -> Dict:
    executor = QueryExecutor()
    return executor.execute_query(sql)
```

### 11.2 Service Boundaries

```
┌─────────────────────────────────────────────────────────────┐
│           AgenticText2SQLService (NEW)                      │
│                                                              │
│  Owns:                                                       │
│  - LangGraph workflow                                        │
│  - Agent nodes                                               │
│  - Tools (wrappers)                                          │
│  - Session management                                        │
│                                                              │
│  Delegates to:                                               │
│  - ClaudeService (SQL generation, clarification, explanation)│
│  - QueryExecutor (SQL execution)                            │
│  - SQLValidator (validation logic)                          │
│  - DBManager (schema retrieval)                             │
└─────────────────────────────────────────────────────────────┘
```

**Design Principle:** Composition over modification
- AgenticText2SQLService orchestrates
- Existing services unchanged
- Clean separation of concerns

---

## 12. Security Architecture

### 12.1 Session Security

**Session ID Generation:**
```python
import uuid
session_id = str(uuid.uuid4())  # Cryptographically random
```

**Session Isolation:**
- Each session_id maps to isolated history
- No cross-session data leakage
- Dictionary key-based isolation

**Production Enhancements:**
- Add user authentication
- Tie session to authenticated user
- Implement session hijacking prevention

### 12.2 SQL Injection Prevention

**Current:** Basic validation (client_id checks)

**Agentic Enhancement:** Same validation applied
- Existing sql_validator.py checks maintained
- Client_id filtering enforced
- Read-only query validation

**No New Vulnerabilities:** Tools use existing safe execution paths

### 12.3 API Security

**Rate Limiting (Production):**
```python
# Per-session rate limit
if request_count(session_id) > 10/minute:
    return {"error": "Rate limit exceeded"}, 429
```

**Input Validation:**
```python
# Validate all inputs
if not user_query or len(user_query) > 1000:
    return {"error": "Invalid query"}, 400

if max_iterations < 1 or max_iterations > 5:
    return {"error": "Invalid max_iterations"}, 400
```

---

## 13. Performance Architecture

### 13.1 Performance Budget

**Total Response Time: ≤10 seconds**

Breakdown:
- detect_clarification: ≤3s (Claude API call)
- get_schema: ≤100ms (cached or direct retrieval)
- generate_sql: ≤2s (Claude API call)
- execute_sql: ≤500ms (SQLite query)
- validate_results: ≤100ms (simple checks)
- reflect: ≤200ms (logic only)
- generate_explanation: ≤2s (Claude API call)
- Overhead (state transitions, logging): ≤500ms

**Total (1 iteration):** ~8.4 seconds
**With retry (2 iterations):** ~10-12 seconds (acceptable for POC)

### 13.2 Optimization Strategies

**Schema Caching:**
```python
# Cache schema in state after first retrieval
if state["schema"] is None:
    schema = get_schema()
    state["schema"] = schema  # Reuse in subsequent iterations
```

**Prompt Optimization:**
- Keep prompts concise
- Limit data samples sent to Claude (max 20 rows)
- Use focused system prompts

**Iteration Limits:**
- Max 3 iterations (prevent slow endless loops)
- Only retry on critical errors

**Async Opportunities (Future):**
- Parallel tool execution where independent
- Async Claude API calls
- Stream explanation generation

### 13.3 Performance Monitoring

**Metrics to Track:**
```python
{
    "total_time": 8.2,
    "node_times": {
        "detect_clarification": 2.8,
        "plan": 0.1,
        "generate_sql": 1.9,
        "execute_sql": 0.4,
        "reflect": 0.2,
        "generate_explanation": 2.1
    },
    "iterations": 1,
    "tool_calls": 4
}
```

**Logging:**
```python
logger.info(f"Query completed in {total_time:.2f}s, {iteration} iterations")
```

---

## 14. Deployment Architecture

### 14.1 POC Deployment

**Environment:** Local development
```
Laptop/Workstation
├── Backend (Flask on port 5001)
│   └── In-memory sessions
├── Frontend (Vite dev server on port 5173)
└── SQLite database (file-based)
```

**No Infrastructure Required:**
- Single-server deployment
- No Redis, no load balancer
- Suitable for demo only

### 14.2 Production Deployment Path

**Recommended Architecture:**
```
                        ┌──────────────┐
                        │  CloudFront  │ (CDN for frontend)
                        └──────┬───────┘
                               │
                ┌──────────────┴──────────────┐
                │                             │
        ┌───────┴────────┐          ┌────────┴────────┐
        │   S3 Bucket    │          │  Load Balancer  │
        │  (React build) │          └────────┬────────┘
        └────────────────┘                   │
                                    ┌────────┴────────┐
                                    │                 │
                            ┌───────┴──────┐  ┌──────┴──────┐
                            │  Flask App 1 │  │ Flask App 2 │
                            │  (ECS/K8s)   │  │  (ECS/K8s)  │
                            └───────┬──────┘  └──────┬──────┘
                                    │                │
                            ┌───────┴────────────────┴──────┐
                            │        Redis Cluster          │
                            │   (Session persistence)       │
                            └───────────────────────────────┘
                                    │
                            ┌───────┴──────────────────┐
                            │   RDS PostgreSQL         │
                            │   (Replace SQLite)       │
                            └──────────────────────────┘
```

**Scalability:**
- Stateless Flask apps (horizontal scaling)
- Redis for shared session state
- RDS for production database
- Auto-scaling based on traffic

---

## 15. Testing Strategy

### 15.1 Testing Pyramid

```
                    ┌────────────────┐
                    │   E2E Tests    │
                    │  (Demo scenarios)│
                    └────────────────┘
                  ┌──────────────────────┐
                  │  Integration Tests   │
                  │ (Workflow execution) │
                  └──────────────────────┘
              ┌──────────────────────────────┐
              │       Unit Tests             │
              │ (Nodes, Tools, Functions)    │
              └──────────────────────────────┘
```

### 15.2 Test Coverage

**Unit Tests (70% backend coverage):**
- Each agent node function
- Each tool implementation
- State management functions
- Query resolution logic
- Session management

**Integration Tests:**
- Full workflow execution (happy path)
- Clarification flow
- Retry flow
- Follow-up query flow
- Error scenarios

**Manual Tests (Critical for Demo):**
- 5-8 demo scenarios end-to-end
- UI component interactions
- Performance validation

### 15.3 Test Examples

**Node Test:**
```python
def test_reflect_node_detects_syntax_error():
    service = AgenticText2SQLService()
    state = {
        "execution_result": {
            "success": False,
            "error": "syntax error near SELCT"
        }
    }
    updates = service._reflect_node(state)
    assert updates["reflection_result"]["should_refine"] == True
```

**Workflow Test:**
```python
def test_workflow_completes_successfully():
    service = AgenticText2SQLService()
    result = service.generate_sql_with_agent(
        user_query="Top 10 products",
        session_id="test-123"
    )
    assert result["success"] == True
    assert result["sql"] is not None
    assert result["explanation"] is not None
```

---

## 16. Implementation Roadmap

### 16.1 4-Week Plan

**Week 1: Foundation**
- Story 1: LangGraph infrastructure
- Story 2: Planning + Tools
- Story 3: SQL Generation
- Milestone: Basic workflow works

**Week 2: Intelligence**
- Story 4: Reflection + Retry
- Story 5: Clarification
- Story 6: Explanation
- Milestone: All agent capabilities working

**Week 3: Integration**
- Story 7: Session Management
- Story 8: Frontend Components + API
- Milestone: Complete system integrated

**Week 4: Polish**
- Integration testing
- Demo preparation
- Performance tuning
- Documentation

### 16.2 Risk Mitigation

**Technical Risks:**
1. **LangGraph learning curve**
   - Mitigation: Study inspiration code first, allocate buffer time
2. **Performance issues**
   - Mitigation: Set max_iterations=2 initially, tune prompts
3. **Clarification quality**
   - Mitigation: Test with 20+ sample queries, iterate prompts

**Project Risks:**
1. **Scope creep**
   - Mitigation: Strict adherence to story acceptance criteria
2. **Timeline slip**
   - Mitigation: Weekly checkpoints, buffer in Week 4

---

## Appendix A: Glossary

**Agent Node:** Stateless function that processes state and returns updates
**AgentState:** TypedDict containing all workflow state
**Clarification:** Process of asking user for missing query context
**LangGraph:** State machine orchestration library
**Reflection:** Process of evaluating SQL quality and deciding if retry needed
**Session:** Conversation context identified by session_id
**State Machine:** Graph of nodes with conditional routing
**Tool:** Reusable component for specific action (schema retrieval, SQL execution)

---

## Appendix B: Architecture Decisions

### ADR-001: LangGraph for State Machine
**Decision:** Use LangGraph StateGraph for workflow orchestration
**Rationale:** Proven pattern from inspiration code, declarative node/edge definition, built-in state management
**Alternatives Considered:** Custom state machine, AWS Step Functions
**Status:** Accepted

### ADR-002: In-Memory Sessions for POC
**Decision:** Use dictionary-based in-memory session storage
**Rationale:** Simplest for POC, no infrastructure dependency, clear upgrade path to Redis
**Alternatives Considered:** Redis (over-engineering for POC), SQLite sessions
**Status:** Accepted

### ADR-003: TypedDict for State
**Decision:** Use TypedDict (not Pydantic) for AgentState
**Rationale:** Standard library, matches inspiration code, sufficient for use case
**Alternatives Considered:** Pydantic (extra dependency), dataclass (less flexible)
**Status:** Accepted

### ADR-004: Backward Compatible API
**Decision:** Keep existing `/query` endpoint unchanged, add new `/query-agentic`
**Rationale:** No breaking changes, gradual migration path, fallback option
**Alternatives Considered:** Replace existing endpoint (risky), version entire API (overkill)
**Status:** Accepted

---

## Appendix C: References

- **Product Brief:** `docs/product-brief-agentic-text2sql-enhancement.md`
- **Epic:** `docs/epic-agentic-text2sql-enhancement.md`
- **Stories:** `docs/sprint_artifacts/story-agent-*.md`
- **Inspiration Code:** `docs/inspiration/agentic_text2sql.py`
- **LangGraph Docs:** https://langchain-ai.github.io/langgraph/

---

**Document Status:** ✅ Complete - Ready for Implementation

**Next Steps:**
1. Review architecture with development team
2. Validate technical approach
3. Begin Story 1 (LangGraph Foundation)
4. Schedule architecture review checkpoints

---

*This architecture document provides complete technical guidance for implementing the Agentic Text-to-SQL enhancement. All design decisions are documented, patterns are established, and implementation path is clear.*

**Architect:** Winston 🏗️  
**Date:** 2025-11-27  
**Version:** 1.0


