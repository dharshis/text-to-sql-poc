# Story: SQL Generation with Tools

**Story ID:** STORY-AGENT-3  
**Epic:** EPIC-AGENTIC-001 (Agentic Text-to-SQL Enhancement)  
**Priority:** Must Have  
**Status:** Ready for Development  
**Estimate:** 2 days  
**Dependencies:** STORY-AGENT-2  

---

## User Story

**As a** system  
**I want** to generate SQL queries using collected context from tools  
**So that** the agentic workflow can produce accurate SQL based on schema and query information

---

## Description

Implement the SQL generation node that uses Claude to generate SQL queries. This node is invoked by the planning agent when it's time to generate SQL, using the schema and other context collected by previous tool executions.

---

## Acceptance Criteria

### Must Have

1. **Generate SQL Node Implemented**
   - [ ] `_generate_sql_node(state)` function created
   - [ ] Uses schema from state (collected by get_schema tool)
   - [ ] Calls Claude API with enhanced prompt
   - [ ] Includes user query and client context
   - [ ] Extracts clean SQL from Claude response
   - [ ] Updates state with generated SQL
   - [ ] Returns {sql_query: str}

2. **Enhanced SQL Generation Prompt**
   - [ ] Includes database schema from state
   - [ ] Includes user's natural language query
   - [ ] Includes client_id context (if available)
   - [ ] Maintains existing SQL generation rules
   - [ ] Leverages existing ClaudeService system prompt

3. **SQL Extraction Logic**
   - [ ] Removes markdown code blocks if present
   - [ ] Strips extra whitespace
   - [ ] Handles multi-line SQL
   - [ ] Returns clean, executable SQL string

4. **Planning Integration**
   - [ ] Planning node recognizes "generate_sql" action
   - [ ] Routing logic: plan → generate_sql → plan → execute_sql
   - [ ] State machine workflow includes generate_sql node
   - [ ] Conditional edge from plan to generate_sql works

5. **Error Handling**
   - [ ] Claude API errors caught and logged
   - [ ] Invalid response handled gracefully
   - [ ] Error stored in state.error field
   - [ ] Workflow can recover or complete on error

### Nice to Have

- [ ] SQL formatting/prettification
- [ ] Metadata context inclusion (business rules)
- [ ] Sample data context (if needed for complex queries)

### Architecture Validation

- [ ] SQL generation node matches Architecture Section 5.3
- [ ] Uses schema from state (collected by tools)
- [ ] Performance target ≤2s (Architecture Section 13.1)
- [ ] Error handling stops workflow appropriately
- [ ] Logging includes query snippet and timing

---

## Architecture References

**See Architecture Document:** `docs/architecture-agentic-text2sql.md`
- **Section 5.3:** SQL Generation Node (implementation details)
- **Section 8.1:** API Design (Claude integration)
- **Section 11.1:** Integration with ClaudeService
- **Section 13.1:** Performance Budget (≤2s for SQL generation)

**Key Patterns:**
- SQL generation called when planning node sets `next_action="generate_sql"`
- Uses schema from state (already retrieved by get_schema tool)
- Cleans markdown code blocks from Claude response
- Returns to planning node after generation (loop back)

**Performance Target:** ≤2s (Architecture Section 13.1)

---

## Technical Implementation

### Files to Modify

```
backend/services/agentic_text2sql_service.py (add generate_sql_node, update workflow)
```

### Key Code Structure

```python
# backend/services/agentic_text2sql_service.py

from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def _generate_sql_node(self, state: AgentState) -> Dict:
    """
    Generate SQL using Claude with collected context.
    Architecture Reference: Section 5.3 (SQL Generation Node)
    Performance Target: ≤2s (Section 13.1)
    """
    query = state["user_query"]
    schema = state.get("schema")
    
    logger.info(f"Generating SQL for: '{query[:100]}'")
    logger.info(f"Using schema: {'Yes' if schema else 'No (using default)'}")
    
    start_time = datetime.now()
    
    try:
        # Call existing ClaudeService (Architecture Section 11.1)
        sql_query = self.claude_service.generate_sql(
            natural_language_query=query,
            client_id=state.get("client_id", 1),
            client_name=state.get("client_name")
        )
        
        # Extract clean SQL (Architecture Section 5.3)
        sql = self._extract_sql(sql_query)
        
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"SQL generated in {elapsed:.2f}s: {sql[:100]}...")
        
        # Performance warning (Architecture Section 13.1)
        if elapsed > 2.0:
            logger.warning(f"SQL generation exceeded 2s target: {elapsed:.2f}s")
        
        return {"sql_query": sql}
        
    except Exception as e:
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.error(f"SQL generation failed after {elapsed:.2f}s: {e}", exc_info=True)
        
        return {
            "error": f"SQL generation failed: {str(e)}",
            "is_complete": True  # Stop workflow on generation failure (Architecture Section 5.3)
        }

def _extract_sql(self, sql_response: str) -> str:
    """
    Extract clean SQL from Claude response.
    Removes markdown code blocks and extra whitespace.
    Architecture Reference: Section 5.3
    """
    logger.debug(f"Extracting SQL from response: {sql_response[:100]}...")
    
    sql = sql_response.strip()
    
    # Remove markdown code blocks (```sql ... ``` or ``` ... ```)
    if sql.startswith('```'):
        lines = sql.split('\n')
        # Filter out lines that are just backticks or language tags
        sql_lines = []
        for line in lines:
            if line.strip() in ['```', '```sql', '```SQL']:
                continue
            sql_lines.append(line)
        sql = '\n'.join(sql_lines).strip()
    
    logger.debug(f"Extracted SQL: {sql[:100]}...")
    
    return sql

# Update workflow building
def _build_workflow(self) -> StateGraph:
    """Build LangGraph workflow"""
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("plan", self._plan_node)
    workflow.add_node("execute_tools", self._execute_tools_node)
    workflow.add_node("generate_sql", self._generate_sql_node)  # NEW
    workflow.add_node("complete", self._complete_node)
    
    # Set entry point
    workflow.set_entry_point("plan")
    
    # Add edges
    workflow.add_conditional_edges(
        "plan",
        self._should_execute_or_generate,  # Updated routing
        {
            "execute_tools": "execute_tools",
            "generate_sql": "generate_sql",  # NEW
            "complete": "complete"
        }
    )
    workflow.add_edge("execute_tools", "plan")  # Loop back
    workflow.add_edge("generate_sql", "plan")   # NEW: Loop back after generation
    workflow.add_edge("complete", END)
    
    return workflow.compile()

def _should_execute_or_generate(self, state: AgentState) -> str:
    """Routing: execute_tools, generate_sql, or complete"""
    action = state.get("next_action", "")
    
    if action == "generate_sql":
        return "generate_sql"
    elif action == "complete":
        return "complete"
    else:
        return "execute_tools"
```

### Testing Strategy

**Unit Tests:**
```python
# backend/tests/test_sql_generation.py

def test_generate_sql_node_success():
    """Test SQL generation node with valid query"""
    service = AgenticText2SQLService()
    
    state = {
        **initial_state,
        "user_query": "Show me top 10 products",
        "schema": "CREATE TABLE products...",
        "client_id": 1
    }
    
    updates = service._generate_sql_node(state)
    
    assert "sql_query" in updates
    assert "SELECT" in updates["sql_query"]
    assert updates["sql_query"] is not None

def test_sql_extraction_with_markdown():
    """Test SQL extraction removes markdown"""
    service = AgenticText2SQLService()
    
    response = "```sql\nSELECT * FROM products\n```"
    sql = service._extract_sql(response)
    
    assert sql == "SELECT * FROM products"
    assert "```" not in sql

def test_sql_extraction_clean():
    """Test SQL extraction with clean input"""
    service = AgenticText2SQLService()
    
    response = "SELECT * FROM products"
    sql = service._extract_sql(response)
    
    assert sql == "SELECT * FROM products"

def test_generate_sql_node_error_handling():
    """Test SQL generation handles errors gracefully"""
    service = AgenticText2SQLService()
    
    # Mock Claude service to raise error
    service.claude_service.generate_sql = Mock(side_effect=Exception("API Error"))
    
    state = {**initial_state, "user_query": "test"}
    updates = service._generate_sql_node(state)
    
    assert "error" in updates
    assert updates["is_complete"] == True

def test_workflow_generates_sql():
    """Integration test: workflow generates SQL"""
    service = AgenticText2SQLService()
    
    initial_state = {
        "user_query": "Top 10 products by revenue",
        "session_id": "test",
        # ... other required fields
    }
    
    final_state = service.workflow.invoke(initial_state)
    
    assert final_state["sql_query"] is not None
    assert "SELECT" in final_state["sql_query"]
```

---

## Dependencies

### Prerequisites
- STORY-AGENT-2 must be complete (planning and tools)
- ClaudeService must be functional
- Schema retrieval tool working

### Required Services
- ClaudeService for SQL generation
- Existing system prompt from claude_service.py

---

## Definition of Done

### Code Complete
- [ ] Generate SQL node implemented
- [ ] SQL extraction logic working
- [ ] Workflow routing updated
- [ ] Planning logic includes generate_sql action

### Tests Pass
- [ ] Unit tests for SQL generation node
- [ ] Unit tests for SQL extraction
- [ ] Integration test: full workflow generates SQL
- [ ] All tests passing

### Documentation
- [ ] SQL generation node documented
- [ ] State machine diagram updated with generate_sql node

### Review
- [ ] Code reviewed by peer
- [ ] All review comments addressed

---

## Notes & Considerations

**Key Decisions:**
- Reuse existing ClaudeService.generate_sql method
- SQL generation happens after schema is collected
- Generation failures stop the workflow (is_complete=True)

**Integration Points:**
- Uses schema from get_schema tool result
- SQL output fed to execute_sql tool in next iteration
- Planning node decides when to invoke generation

**Risks:**
- Claude API could generate invalid SQL
- Markdown cleanup might miss edge cases
- Mitigation: STORY-AGENT-4 (Reflection) will handle retry logic

---

## Related Stories

**Depends On:** 
- STORY-AGENT-1 (Foundation)
- STORY-AGENT-2 (Planning & Tools)

**Blocks:**
- STORY-AGENT-4 (Reflection needs SQL to evaluate)
- STORY-AGENT-6 (Explanation needs results from executed SQL)

**Related:**
- STORY-AGENT-5 (Clarification can affect SQL generation)

---

**Story Status:** ✅ Ready for Development

**Assigned To:** [Developer Name]

**Sprint:** Sprint X

**Started:** [Date]

**Completed:** [Date]

