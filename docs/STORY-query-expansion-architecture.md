# User Stories: Query Expansion Architecture

**Epic:** Simplify Conversation Context with Pure LLM Query Expansion  
**Created:** December 1, 2024  
**Status:** Draft  

---

## Epic Description

Replace the current hardcoded filter extraction approach with a clean, LLM-native query expansion system that works at the natural language level, not the SQL level.

**Current Problems:**
- ❌ Hardcoded regex patterns for filter extraction (region_name, brand_name, etc.)
- ❌ Dataset-specific code that needs maintenance
- ❌ Working at SQL level instead of user intent level
- ❌ Corp_id filter sometimes missing, causing security validation failures

**New Approach:**
- ✅ Expand incomplete queries at natural language level
- ✅ No SQL parsing or filter extraction
- ✅ Dataset agnostic
- ✅ Trust Claude to understand conversational context
- ✅ Clear security layer for mandatory filters

---

## Story 1: Natural Language Query Expansion

**As a** business analyst  
**I want** my follow-up questions to be understood in context  
**So that** I don't have to repeat myself in every query

### Acceptance Criteria

**AC1: Fragment Query Expansion**
- Given a conversation with previous query: "Show market trend in 2023"
- When I ask: "by region"
- Then the system expands it to: "Show market trend in 2023 by region"
- And generates SQL from the expanded query

**AC2: Complete Query Pass-Through**
- Given any previous conversation context
- When I ask a complete question: "Show total sales for all brands in Q4 2024"
- Then the system recognizes it as complete
- And uses it as-is without expansion

**AC3: Additive Context**
- Given conversation: 
  - Q1: "Show market trend in 2023"
  - Q2: "by region"
- When I ask: "for Africa only"
- Then system expands to: "Show market trend in 2023 by region for Africa only"
- And maintains the cumulative context

**AC4: Context Window Limit**
- Given a long conversation (10+ queries)
- When expanding a new query
- Then use only the last 3-5 queries as context
- To prevent token bloat and maintain relevance

**AC5: No SQL Dependencies**
- When expanding queries
- Then use ONLY previous user queries (natural language)
- And NOT previous SQL queries
- To remain dataset-agnostic

### Implementation Notes

```python
def expand_query_with_context(user_query: str, chat_history: List[Dict]) -> str:
    """
    Expand fragment queries using conversation context.
    Works at natural language level - no SQL needed.
    
    Args:
        user_query: Current user input (may be fragment or complete)
        chat_history: Previous queries in conversation
        
    Returns:
        Expanded, standalone natural language query
    """
    # Get last N user queries (just NL, not SQL)
    recent_queries = [entry['user_query'] for entry in chat_history[-3:]]
    
    prompt = f"""
Previous conversation:
{format_queries(recent_queries)}

Current user input: "{user_query}"

Task: If this is a fragment or follow-up, expand it into a complete query.
If it's already complete, return unchanged.

Output only the expanded query.
"""
    
    return call_claude(prompt)
```

### Test Scenarios

| Previous Queries | User Input | Expected Expansion |
|-----------------|------------|-------------------|
| "Show sales in 2023" | "by region" | "Show sales in 2023 by region" |
| "Show sales in 2023", "by region" | "for Africa" | "Show sales in 2023 by region for Africa" |
| "Show sales in 2023" | "Show brand performance" | "Show brand performance" (complete query) |
| None (first query) | "by region" | "by region" (unchanged, may need clarification) |

---

## Story 2: Ambiguous Query Resolution

**As a** business analyst  
**I want** the system to intelligently handle ambiguous follow-ups  
**So that** natural conversation patterns work as expected

### Acceptance Criteria

**AC1: Time Period Replacement**
- Given conversation: "Show market trend in 2023 by region"
- When I ask: "what about 2024?"
- Then system should expand to: "Show market trend in 2024 by region"
- And maintain the drill-down structure (by region) while replacing the time period

**AC2: Scope Expansion**
- Given conversation: "Show sales for Le Creuset brand"
- When I ask: "how did it perform in Q4?"
- Then expand to: "Show sales for Le Creuset brand in Q4"
- And add the time filter while maintaining brand scope

**AC3: Explicit Context Reset**
- Given any previous conversation
- When user asks: "Show me something completely different: brand performance"
- Then recognize this as a new topic
- And expand minimally or not at all

**AC4: Ambiguity Detection**
- Given conversation: "Show sales"
- When I ask: "for 2024"
- Then system may expand to: "Show sales for 2024"
- OR recognize ambiguity and ask clarification
- Based on context sufficiency

### Implementation Notes

**Prompt Engineering:**
```python
expansion_prompt = f"""
You are helping a user having a conversation about data analysis.

Conversation so far:
1. User: "Show market trend in 2023"
2. User: "by region"
3. User: "what about 2024?"

Your task:
- If query 3 is a fragment/follow-up, expand it into a complete query
- Consider: Is user modifying previous query or asking something new?
- "what about 2024?" likely means: replace 2023 with 2024, keep other aspects
- Be smart about intent: maintain scope unless user explicitly changes it

Expanded query:
"""
```

**Decision Logic:**
- Replacement phrases: "what about", "how about", "show me", "instead"
- Additive phrases: "also", "for", "in", "only"
- Reset phrases: "now show", "instead show", "something different"

### Test Scenarios

| Previous Context | User Input | Expected Behavior | Expanded Query |
|-----------------|------------|-------------------|----------------|
| "Show 2023 trends by region" | "what about 2024?" | Replace year, keep structure | "Show 2024 trends by region" |
| "Show 2023 trends" | "what about 2024?" | Replace year | "Show 2024 trends" |
| "Show sales for Africa" | "and for Europe?" | Add parallel scope | "Show sales for Europe" OR ask clarification |
| "Show 2023 data" | "Show brand performance" | New topic | "Show brand performance" (no expansion) |

---

## Story 3: Mandatory Security Filter (Corp ID)

**As a** system administrator  
**I want** every query to be filtered to the correct client/corporation  
**So that** data isolation is guaranteed

### Acceptance Criteria

**AC1: Corp ID Always Present**
- Given any user query
- When SQL is generated
- Then the SQL MUST include: `WHERE corp_id = {client_id}`
- Or the query must be rejected

**AC2: Explicit Corp ID in System Prompt**
- When calling Claude to generate SQL
- Then system prompt must explicitly state:
  ```
  CRITICAL: Every query MUST filter to corp_id = {client_id}
  This is mandatory for data security. Never omit this filter.
  ```

**AC3: Auto-Injection Safety Net (Optional)**
- Given SQL generated by Claude
- When corp_id filter is missing
- Then system MAY auto-inject the filter
- And log a warning for monitoring
- (Decision: Auto-inject for demo, or reject for production?)

**AC4: Validation Layer**
- Given any generated SQL
- When security validation runs
- Then it must verify corp_id filter exists
- And reject query if missing (even with auto-inject as backup)

**AC5: Corp ID in Conversation Context**
- When formatting conversation history for Claude
- Then include reminder: "All queries are filtered to corp_id = {client_id}"
- To reinforce this requirement

### Implementation Notes

**System Prompt Enhancement:**
```python
system_prompt = f"""
You are a SQL query generator for a business analytics system.

🚨 CRITICAL SECURITY REQUIREMENT 🚨
Corporation Isolation: corp_id = {client_id}

EVERY query you generate MUST include this WHERE clause:
WHERE corp_id = {client_id}

Even for follow-up queries.
Even if the user doesn't mention it.
This is NON-NEGOTIABLE for data security.

Failure to include this will result in query rejection.
"""
```

**Auto-Injection (if approved):**
```python
def ensure_corp_id_filter(sql: str, client_id: int) -> str:
    """
    Safety net: Ensure corp_id filter exists.
    """
    if f"corp_id = {client_id}" not in sql.lower():
        logger.warning(f"Corp ID missing from SQL, auto-injecting for client {client_id}")
        # Inject into WHERE clause
        sql = inject_where_condition(sql, f"corp_id = {client_id}")
    return sql
```

### Test Scenarios

| User Query | Expected SQL Must Include |
|-----------|--------------------------|
| "Show sales in 2023" | `WHERE corp_id = 105` |
| "by region" (follow-up) | `WHERE corp_id = 105 AND ...` |
| "Show market trends" | `WHERE corp_id = 105` |

### Decision Required

**Do we auto-inject corp_id or reject?**

**Option A: Auto-Inject (Pragmatic)**
- Pro: Demo won't break
- Pro: User experience is smooth
- Con: Masks prompt engineering problems
- **Recommendation:** Use for demo/MVP

**Option B: Reject (Strict)**
- Pro: Forces proper prompt engineering
- Pro: Clean, no SQL manipulation
- Con: May break during demo
- **Recommendation:** Use for production after prompts are perfected

**Option C: Hybrid**
- Auto-inject but log loudly
- Monitor logs to track how often it happens
- Goal: Reduce to zero over time
- **Recommendation:** Best of both worlds

---

## Story 4: Conversation History Storage

**As a** system  
**I want** to store minimal, relevant conversation history  
**So that** query expansion works efficiently

### Acceptance Criteria

**AC1: Store User Queries Only**
- When storing conversation history
- Then store: `user_query`, `expanded_query`, `sql_query`, `timestamp`
- And remove: filter extraction, results_summary, key_entities
- To simplify the data model

**AC2: Limit History Length**
- When storing conversation history per session
- Then keep only last 10 queries
- To prevent unbounded memory growth

**AC3: Use Last N for Expansion**
- When expanding a new query
- Then use last 3-5 queries for context
- Not the entire history
- To keep prompts focused and token-efficient

**AC4: Clear Session Support**
- When user starts a new conversation
- Then create new session_id
- And start fresh history
- To support explicit context reset

### Data Model

```python
# Simplified history entry
{
    "user_query": "by region",  # Original user input
    "expanded_query": "Show market trend in 2023 by region",  # After expansion
    "sql_query": "SELECT ...",  # Generated SQL
    "timestamp": "2024-12-01T10:00:00",
    "is_followup": true  # Detected as fragment/follow-up
}
```

**Removed fields:**
- ❌ `results_summary` - Not needed for query expansion
- ❌ `key_entities` - No more entity extraction
- ❌ `execution_result` in history - Too much data

---

## Story 5: Pivot vs Drill-Down Detection

**As a** business analyst  
**I want** the system to understand when I'm pivoting vs drilling down  
**So that** conversation flow feels natural

### Acceptance Criteria

**AC1: Drill-Down Preservation**
- Given conversation establishing scope: "Show sales for Africa"
- When I ask additive question: "What about Q4?"
- Then system maintains Africa scope: "Show sales for Africa in Q4"
- And treats it as drill-down, not pivot

**AC2: Explicit Pivot Recognition**
- Given any conversation context
- When I ask: "Now show me brand performance instead"
- Then system recognizes this as a pivot
- And starts fresh analysis without previous scope

**AC3: Natural Pivot Indicators**
- When user input contains phrases like:
  - "instead", "now show", "what about [different topic]", "forget that"
- Then system should recognize potential pivot
- And either: (a) start fresh, or (b) ask for confirmation

**AC4: Organic Demarcation (Demo Requirement)**
- Given the demo requirement: "clear demarcation of drill-down vs new conversation"
- When using query expansion
- Then drill-downs naturally persist (context maintained)
- And pivots naturally break (user explicitly changes topic)
- Without needing hardcoded enforcement

### Implementation Notes

**LLM-Based Detection:**
```python
expansion_prompt = f"""
Previous queries:
1. "Show sales for Africa"
2. "break down by brand"

Current input: "what about Europe?"

Is this:
A) A DRILL-DOWN: Maintaining Africa context, adding new dimension
B) A PIVOT: Switching from Africa to Europe

Answer: PIVOT (user explicitly said "Europe" not "also Europe")

Expanded query: "Show sales for Europe"
```

**Heuristics (optional guidance to LLM):**
- Same entity + new dimension = Drill-down
- Different entity + explicit change word = Pivot
- Ambiguous case = Ask Claude's judgement

### Test Scenarios

| Previous Context | User Input | Classification | Expected Expansion |
|-----------------|------------|----------------|-------------------|
| "Sales for Africa" | "break down by brand" | Drill-down | "Sales for Africa by brand" |
| "Sales for Africa" | "what about Europe?" | Pivot | "Sales for Europe" |
| "Sales by region" | "focus on Africa" | Drill-down | "Sales by region for Africa" |
| "2023 trends" | "show 2024 instead" | Pivot/Replace | "2024 trends" |

---

## Story 6: Remove Filter Extraction Code

**As a** developer  
**I want** to remove all hardcoded filter extraction logic  
**So that** the codebase is clean and dataset-agnostic

### Acceptance Criteria

**AC1: Remove Extraction Functions**
- Delete: `_extract_filters_from_sql()` method
- Delete: All regex patterns for region_name, brand_name, category_name, etc.
- Delete: Dataset-specific filter logic

**AC2: Remove Enhanced Instructions**
- Remove: Hardcoded "PRESERVE ALL FILTERS" instructions
- Remove: Concrete examples like "If Africa then 2024 = Africa 2024"
- Replace with: Simple "maintain context" instruction

**AC3: Simplify Context Formatting**
- Format conversation context as:
  ```
  Previous queries:
  1. User: "Show sales in 2023"
  2. User: "by region"
  
  Current query: "for Africa"
  ```
- No filter extraction, no SQL parsing
- Just user queries in sequence

**AC4: Update Tests**
- Remove: `test_drilldown_context_fix.py` (tests removed functionality)
- Update: Integration tests to test query expansion instead

**AC5: Update Documentation**
- Archive: `DRILLDOWN-CONTEXT-BUG-FIX.md` (obsolete approach)
- Create: New architecture documentation for query expansion

### Files to Modify

```
Modified:
  backend/services/agentic_text2sql_service.py
  - Remove _extract_filters_from_sql() method
  - Simplify _format_conversation_context()
  - Add _expand_query_with_context() method

Deleted:
  backend/test_drilldown_context_fix.py
  DRILLDOWN-CONTEXT-BUG-FIX.md
  QUICK-TEST-DRILLDOWN-FIX.md

Created:
  docs/STORY-query-expansion-architecture.md (this file)
  backend/tests/test_query_expansion.py (new tests)
```

---

## Story 7: Performance & Token Efficiency

**As a** system operator  
**I want** query expansion to be fast and token-efficient  
**So that** the system remains responsive

### Acceptance Criteria

**AC1: Single Claude Call for Expansion**
- When expanding a query
- Then make only ONE Claude API call
- Not multiple calls for detection + expansion

**AC2: Small Prompt Size**
- When building expansion prompt
- Then include only last 3-5 queries
- Keep prompt under 500 tokens
- To minimize latency and cost

**AC3: Cache Previous Expansions**
- When expanding queries
- Then reuse expanded queries from history
- Don't re-expand them for context

**AC4: Fast Fallback**
- When expansion fails or times out
- Then use original query as-is
- And log the failure for monitoring

**AC5: Performance Target**
- Query expansion should complete in < 1 second
- Total query processing (expand + generate SQL + execute) < 5 seconds

---

## Implementation Priority

### Phase 1: Core Query Expansion (MVP)
- ✅ Story 1: Natural Language Query Expansion
- ✅ Story 3: Mandatory Security Filter (with auto-inject safety net)
- ✅ Story 4: Conversation History Storage (simplified)
- ✅ Story 6: Remove Filter Extraction Code

**Goal:** Replace current approach with clean LLM-native expansion

### Phase 2: Intelligent Context Handling
- ✅ Story 2: Ambiguous Query Resolution
- ✅ Story 5: Pivot vs Drill-Down Detection

**Goal:** Handle edge cases and improve user experience

### Phase 3: Optimization
- ✅ Story 7: Performance & Token Efficiency

**Goal:** Ensure production-ready performance

---

## Open Questions

### Q1: Corp ID Security - Auto-inject or Reject?
**Options:**
- A) Auto-inject as safety net (good for demo)
- B) Reject and force prompt fix (cleaner long-term)
- C) Hybrid: Auto-inject but log loudly

**Decision needed from:** Product Owner / System Admin

### Q2: When to ask clarification vs expand?
**Scenario:** User says "by region" as first query (no context)
- Option A: Expand to "by region" and let SQL generation ask clarification
- Option B: Detect insufficient context at expansion stage and ask

**Decision:** Probably Option A (let existing clarification flow handle it)

### Q3: Store expanded queries in history?
**Options:**
- A) Store both user_query and expanded_query
- B) Store only expanded_query (what was actually processed)

**Recommendation:** Store both (helps debugging and user understanding)

---

## Success Metrics

### Functional Metrics
- ✅ 100% of queries have corp_id filter (security)
- ✅ 90%+ drill-down queries maintain scope correctly
- ✅ 0% dataset-specific code in query expansion logic

### Performance Metrics
- ⚡ Query expansion: < 1 second
- ⚡ End-to-end query: < 5 seconds
- 📉 Token usage: 50% reduction (no SQL in expansion context)

### User Experience Metrics
- 😊 Users don't need to repeat themselves
- 😊 Natural conversation patterns work
- 😊 Clear when drill-down vs pivot occurs

---

## Related Documents
- `docs/architecture-agentic-text2sql.md` - Overall architecture (needs update)
- `STORY-conversation-context.md` - Original conversation context story (superseded)
- `backend/services/agentic_text2sql_service.py` - Main implementation file

