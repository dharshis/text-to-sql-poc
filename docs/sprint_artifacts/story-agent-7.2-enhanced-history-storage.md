# Story 7.2: Enhanced History Storage with Entity Tracking

**Story ID:** STORY-AGENT-7.2  
**Epic:** EPIC-AGENTIC-001 (Agentic Text-to-SQL Enhancement)  
**Priority:** Must Have  
**Status:** Ready for Development  
**Estimate:** 1 day  
**Dependencies:** STORY-AGENT-7.1  

---

## User Story

**As a** system  
**I want** to store rich context about each query (entities, filters, dimensions)  
**So that** follow-up resolution has better information to work with

---

## Description

Enhance the current basic history storage to include structured entity information. This enables smarter follow-up resolution by providing Claude with semantic understanding of what each query was about.

**Current storage:**
```python
{
    "user_query": "Top products",
    "sql": "SELECT...",
    "timestamp": "..."
}
```

**Enhanced storage:**
```python
{
    "user_query": "Top products",
    "resolved_query": "Top 5 products by revenue",
    "sql": "SELECT...",
    "results_summary": "5 rows: Le Creuset ($X)...",
    "key_entities": {
        "dimensions": ["product"],
        "metrics": ["revenue"],
        "filters": [{"client_id": 1}],
        "time_period": "all time",
        "grouping": ["product_name"],
        "limit": 5
    },
    "timestamp": "2025-11-27T...",
    "is_followup": false
}
```

---

## Acceptance Criteria

### AC1: Update History Entry Structure

- [ ] Modify `_add_to_history()` to accept enhanced entry format
- [ ] New structure includes:
  ```python
  {
      "user_query": str,              # Original query
      "resolved_query": str,          # After follow-up resolution
      "sql": str,                     # Generated SQL
      "results_summary": str,         # "5 rows: Le Creuset ($X)..."
      "key_entities": {
          "dimensions": List[str],    # ["product", "region"]
          "metrics": List[str],       # ["revenue", "quantity"]
          "filters": List[Dict],      # [{"client_id": 1}, {"category": "electronics"}]
          "time_period": str,         # "Q4 2024", "last 6 months", "all time"
          "grouping": List[str],      # ["product_name", "region"]
          "limit": int                # 5, 10, etc.
      },
      "timestamp": str,               # ISO format
      "is_followup": bool            # Was this a follow-up query?
  }
  ```
- [ ] Backward compatible with existing sessions (handle missing fields)

---

### AC2: Entity Extraction from Query State

- [ ] Create `_extract_entities()` method in `AgenticText2SQLService`
- [ ] **Input:** `state: AgentState` (after SQL generation)
- [ ] **Output:** `key_entities: Dict`
- [ ] Parse generated SQL to extract:
  
  **Dimensions** (from SELECT and GROUP BY):
  ```sql
  SELECT p.product_name, r.region, ...
  GROUP BY p.product_name, r.region
  → dimensions: ["product", "region"]
  ```
  
  **Metrics** (from SELECT aggregations):
  ```sql
  SELECT SUM(s.revenue), COUNT(s.quantity), ...
  → metrics: ["revenue", "quantity"]
  ```
  
  **Filters** (from WHERE clause):
  ```sql
  WHERE s.client_id = 1 AND p.category = 'electronics'
  → filters: [{"client_id": 1}, {"category": "electronics"}]
  ```
  
  **Time Period** (from date filters):
  ```sql
  WHERE s.date >= '2024-10-01' AND s.date <= '2024-12-31'
  → time_period: "Q4 2024"
  
  WHERE s.date >= date('now', '-6 months')
  → time_period: "last 6 months"
  
  No date filter
  → time_period: "all time"
  ```
  
  **Grouping** (from GROUP BY):
  ```sql
  GROUP BY p.product_name, r.region
  → grouping: ["product_name", "region"]
  ```
  
  **Limit** (from LIMIT clause):
  ```sql
  LIMIT 5
  → limit: 5
  ```

- [ ] Use regex patterns for parsing (POC-level, not full SQL parser)
- [ ] If extraction fails for a field → use empty/null default
- [ ] Log extraction results

---

### AC3: Results Summarization

- [ ] Create `_summarize_results()` method in `AgenticText2SQLService`
- [ ] **Input:** `execution_result: Dict`
- [ ] **Output:** `results_summary: str`
- [ ] Summary format:
  ```python
  # If no results:
  "0 rows"
  
  # If 1-5 rows:
  "3 rows: Le Creuset ($12K), Dyson ($8K), Apple Watch ($6K)"
  
  # If 6+ rows:
  "25 rows: Le Creuset ($12K) (top)"
  ```
- [ ] Extract first value from first row as "top" item
- [ ] Truncate to 100 chars max
- [ ] Handle empty/null results gracefully

---

### AC4: Integration with Workflow

- [ ] Update `generate_sql_with_agent()` to call entity extraction:
  ```python
  # After workflow completes successfully
  if final_state.get("sql_query") and not final_state.get("clarification_needed"):
      # Extract entities from state
      key_entities = self._extract_entities(final_state)
      
      # Summarize results
      results_summary = self._summarize_results(final_state.get("execution_result"))
      
      # Add enhanced history entry
      self._add_to_history(session_id, {
          "user_query": user_query,
          "resolved_query": resolved_query,
          "sql": final_state.get("sql_query"),
          "results_summary": results_summary,
          "key_entities": key_entities,
          "timestamp": datetime.now().isoformat(),
          "is_followup": is_followup
      })
  ```
- [ ] Ensure history is added ONLY for successful queries
- [ ] Skip history for clarification requests

---

### AC5: Use Entities in Resolution

- [ ] Update `_resolve_query_with_history()` to include entities in prompt:
  ```python
  context_lines = []
  for i, entry in enumerate(recent_history, 1):
      context_lines.append(f"{i}. Query: \"{entry['user_query']}\"")
      context_lines.append(f"   Resolved to: \"{entry['resolved_query']}\"")
      
      # NEW: Include entity context
      if entry.get('key_entities'):
          entities = entry['key_entities']
          context_lines.append(f"   Dimensions: {entities.get('dimensions', [])}")
          context_lines.append(f"   Metrics: {entities.get('metrics', [])}")
          context_lines.append(f"   Time period: {entities.get('time_period', 'all time')}")
          context_lines.append(f"   Filters: {entities.get('filters', [])}")
  ```
- [ ] This gives Claude more structured context for resolution

---

## Technical Notes

### Files to Modify

**Backend:**
- `backend/services/agentic_text2sql_service.py`:
  - Add `_extract_entities()` method
  - Add `_summarize_results()` method
  - Modify `_add_to_history()` to use enhanced structure
  - Update `_resolve_query_with_history()` to include entities
  - Update `generate_sql_with_agent()` integration

### SQL Parsing Patterns (POC-Level)

```python
# Dimensions - extract from SELECT and GROUP BY
dimensions_pattern = r'(?:SELECT|GROUP BY)\s+(?:.*?\b(product|region|category|client|customer|segment)\b)'

# Metrics - extract from SELECT aggregations
metrics_pattern = r'(SUM|COUNT|AVG|MAX|MIN)\s*\(\s*\w+\.(\w+)\s*\)'

# Filters - extract from WHERE
filters_pattern = r'WHERE\s+.*?(\w+)\s*=\s*[\'"]?(\w+)[\'"]?'

# Time period - detect date ranges
time_pattern = r'date\s*>=\s*[\'"](\d{4}-\d{2}-\d{2})[\'"]'

# Grouping - extract from GROUP BY
grouping_pattern = r'GROUP BY\s+([\w., ]+)'

# Limit
limit_pattern = r'LIMIT\s+(\d+)'
```

### Performance

- Entity extraction: <50ms (regex parsing)
- Results summarization: <10ms (simple string formatting)
- Total overhead: <100ms per query

---

## Testing

### Test Case 1: Simple Query
```python
SQL: "SELECT product_name, SUM(revenue) FROM sales WHERE client_id = 1 GROUP BY product_name LIMIT 5"

Expected entities:
{
    "dimensions": ["product"],
    "metrics": ["revenue"],
    "filters": [{"client_id": 1}],
    "time_period": "all time",
    "grouping": ["product_name"],
    "limit": 5
}
```

### Test Case 2: Complex Query with Time Filter
```python
SQL: "SELECT p.product_name, r.region, SUM(s.revenue), COUNT(s.quantity) 
      FROM sales s 
      JOIN products p ON s.product_id = p.product_id 
      JOIN regions r ON s.region_id = r.region_id 
      WHERE s.client_id = 1 
        AND s.date >= '2024-10-01' 
        AND s.date <= '2024-12-31'
        AND p.category = 'electronics'
      GROUP BY p.product_name, r.region 
      LIMIT 10"

Expected entities:
{
    "dimensions": ["product", "region"],
    "metrics": ["revenue", "quantity"],
    "filters": [
        {"client_id": 1},
        {"category": "electronics"}
    ],
    "time_period": "Q4 2024",
    "grouping": ["product_name", "region"],
    "limit": 10
}
```

### Test Case 3: Results Summarization
```python
Results: [
    {"product_name": "Le Creuset", "total_revenue": 12000},
    {"product_name": "Dyson", "total_revenue": 8000},
    {"product_name": "Apple Watch", "total_revenue": 6000}
]

Expected summary: "3 rows: Le Creuset ($12000) (top)"
```

### Test Case 4: Empty Results
```python
Results: []

Expected summary: "0 rows"
```

### Test Case 5: Large Result Set
```python
Results: [25 rows of data]

Expected summary: "25 rows: [first value] (top)"
```

---

## Definition of Done

- [ ] `_extract_entities()` method implemented
- [ ] `_summarize_results()` method implemented
- [ ] Enhanced history structure in use
- [ ] All 5 test cases pass
- [ ] Entity extraction works for simple and complex queries
- [ ] Results summarization handles all edge cases
- [ ] Integration with `generate_sql_with_agent()` complete
- [ ] Resolution prompt includes entity context
- [ ] Performance targets met (<100ms overhead)
- [ ] Backward compatible with existing sessions
- [ ] Logging added for entity extraction
- [ ] Code reviewed and follows standards
- [ ] No linter errors

---

## Success Metrics

- **Extraction success rate**: % of queries with successfully extracted entities (target: >90%)
- **Resolution improvement**: % better resolution accuracy with entity context vs without (measure via A/B test if possible)
- **Storage size**: Average bytes per history entry (monitor for memory usage)

---

**Story Status:** ✅ Ready for Development  
**Assigned To:** Dev Agent  
**Started:** TBD  
**Completed:** TBD


