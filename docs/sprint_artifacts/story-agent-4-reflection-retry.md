# Story: Reflection Agent & Retry Logic

**Story ID:** STORY-AGENT-4  
**Epic:** EPIC-AGENTIC-001 (Agentic Text-to-SQL Enhancement)  
**Priority:** Must Have  
**Status:** Ready for Development  
**Estimate:** 2 days  
**Dependencies:** STORY-AGENT-3  

---

## User Story

**As a** system  
**I want** to evaluate generated SQL quality and retry if critical errors are detected  
**So that** the system can self-correct and improve accuracy without user intervention

---

## Description

Implement the reflection agent that evaluates SQL quality after execution and validation. If critical errors are detected (syntax errors, unknown tables/columns), the system should reset state and retry generation. This is the key self-correction capability that differentiates the agentic system.

---

## Acceptance Criteria

### Must Have

1. **Reflection Node Implemented**
   - [ ] `_reflect_node(state)` function created
   - [ ] Analyzes: sql_query, execution_result, validation_result
   - [ ] Detects critical errors requiring retry
   - [ ] Detects acceptable results (proceed to complete)
   - [ ] Returns {reflection_result: Dict, should_refine: bool}

2. **Error Detection Logic**
   - [ ] **Critical Errors (trigger retry):**
     - SQL syntax errors
     - Unknown table or column errors
     - Parse errors from database
   - [ ] **Non-Critical Issues (proceed):**
     - Empty results (might be correct)
     - Performance warnings
     - Data quality issues
   - [ ] Clear classification of error severity

3. **Retry Logic Implemented**
   - [ ] If should_refine=True AND iteration < max_iterations:
     - Reset sql_query to None
     - Reset execution_result to None
     - Reset validation_result to None
     - Loop back to planning
   - [ ] If max_iterations reached: complete (stop retrying)
   - [ ] Reflection result stored in state for transparency

4. **Conditional Routing**
   - [ ] `_should_refine(state)` function implemented
   - [ ] Conditional edge from reflect node
   - [ ] Routes to "plan" for refinement or "complete" for done
   - [ ] State machine: generate_sql → reflect → [refine back to plan] OR [complete]

5. **Reflection Result Format**
   - [ ] Structure: {is_acceptable: bool, should_refine: bool, issues: List[str], reasoning: str}
   - [ ] Clear explanation of decision
   - [ ] List of detected issues
   - [ ] Transparent reasoning

### Nice to Have

- [ ] Quality scoring (0-100 scale)
- [ ] Suggested improvements for next iteration
- [ ] Pattern learning from successful/failed queries

### Architecture Validation

- [ ] Reflection logic matches Architecture Section 5.3.3
- [ ] Critical error keywords from architecture
- [ ] Retry flow matches Section 10.3
- [ ] State reset on retry (sql_query, execution_result, validation_result)
- [ ] Max iteration check prevents infinite loops

---

## Architecture References

**See Architecture Document:** `docs/architecture-agentic-text2sql.md`
- **Section 5.3.3:** Reflection Node Design (quality evaluation)
- **Section 10.3:** Retry Flow (complete retry workflow)
- **Section 13.1:** Performance (max 3 iterations)
- **Section 4.2:** Conditional Edges (routing logic)

**Critical Error Keywords (Architecture Section 5.3.3):**
- syntax error, parse error, invalid sql
- unknown column, unknown table, no such table, no such column

**Retry Pattern:**
1. Reflection detects critical error → should_refine=True
2. Check iteration < max_iterations → Reset state
3. Route back to plan → Regenerate SQL with context
4. Max iterations reached → Complete (stop retrying)

**Performance:** Max 3 iterations (Architecture Section 13.1)

---

## Technical Implementation

### Files to Modify

```
backend/services/agentic_text2sql_service.py (add reflect_node, update workflow)
```

### Key Code Structure

```python
# backend/services/agentic_text2sql_service.py

from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def _reflect_node(self, state: AgentState) -> Dict:
    """
    Evaluate SQL quality and decide if retry needed.
    Architecture Reference: Section 5.3.3 (Reflection Node Design)
    Performance Target: ≤200ms (Section 13.1)
    """
    start_time = datetime.now()
    
    sql = state.get("sql_query")
    execution_result = state.get("execution_result")
    validation_result = state.get("validation_result")
    iteration = state.get("iteration", 0)
    
    logger.info(f"Reflecting on SQL quality (iteration {iteration})...")
    logger.info(f"  SQL: {sql[:100] if sql else 'None'}...")
    
    should_refine = False
    issues = []
    
    # Critical error detection (Architecture Section 5.3.3)
    if execution_result and not execution_result.get("success"):
        error_msg = execution_result.get("error", "").lower()
        
        # Critical keywords from architecture
        critical_keywords = [
            "syntax error", "parse error", "invalid sql",
            "unknown column", "unknown table",
            "no such table", "no such column"
        ]
        
        # Check if critical error
        if any(kw in error_msg for kw in critical_keywords):
            should_refine = True
            issues.append(f"Critical SQL error: {error_msg}")
            logger.warning(f"Critical error detected: {error_msg}")
        else:
            # Non-critical error, proceed
            issues.append(f"Non-critical error: {error_msg}")
            logger.info(f"Non-critical error (proceeding): {error_msg}")
    
    # Empty results check (informational, not critical)
    if validation_result and not validation_result.get("has_results"):
        issues.append("Query returned no results")
        logger.info("Empty results - might be correct, proceeding")
    
    # Build reflection result
    reflection = {
        "is_acceptable": not should_refine,
        "should_refine": should_refine,
        "issues": issues,
        "reasoning": "SQL has critical errors requiring retry" if should_refine else "SQL quality acceptable"
    }
    
    elapsed = (datetime.now() - start_time).total_seconds()
    logger.info(f"Reflection complete in {elapsed:.3f}s: acceptable={reflection['is_acceptable']}, refine={should_refine}, issues={len(issues)}")
    
    return {"reflection_result": reflection}

def _should_refine(self, state: AgentState) -> str:
    """
    Conditional routing: refine or complete.
    Architecture Reference: Section 4.2 (Conditional Edges), Section 10.3 (Retry Flow)
    """
    reflection = state.get("reflection_result", {})
    iteration = state.get("iteration", 0)
    max_iterations = state.get("max_iterations", 3)
    
    should_refine = reflection.get("should_refine", False)
    
    # Refinement decision (Architecture Section 10.3)
    if should_refine and iteration < max_iterations:
        logger.info(f"Refining SQL (iteration {iteration}/{max_iterations})")
        
        # Reset state for retry (Architecture Section 10.3)
        state["sql_query"] = None
        state["execution_result"] = None
        state["validation_result"] = None
        
        return "refine"
    
    logger.info("Reflection complete, proceeding to finish")
    return "complete"

# Update workflow building
def _build_workflow(self) -> StateGraph:
    """Build LangGraph workflow"""
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("plan", self._plan_node)
    workflow.add_node("execute_tools", self._execute_tools_node)
    workflow.add_node("generate_sql", self._generate_sql_node)
    workflow.add_node("reflect", self._reflect_node)  # NEW
    workflow.add_node("complete", self._complete_node)
    
    # Set entry point
    workflow.set_entry_point("plan")
    
    # Add edges
    workflow.add_conditional_edges(
        "plan",
        self._should_execute_or_generate,
        {
            "execute_tools": "execute_tools",
            "generate_sql": "generate_sql",
            "complete": "complete"
        }
    )
    workflow.add_edge("execute_tools", "plan")
    workflow.add_edge("generate_sql", "plan")  # Generate → plan → validate → reflect
    
    # NEW: After validation, go to reflection
    # (Plan node will route to reflect when validation is done)
    # Reflection decides: refine (back to plan) or complete
    workflow.add_conditional_edges(
        "reflect",
        self._should_refine,
        {
            "refine": "plan",  # Try again
            "complete": "complete"  # Done
        }
    )
    
    workflow.add_edge("complete", END)
    
    return workflow.compile()

# Update planning node to route to reflection
def _plan_node(self, state: AgentState) -> Dict:
    """Planning node - decides next action"""
    iteration = state["iteration"] + 1
    updates = {"iteration": iteration}
    
    # Check iteration limit
    if iteration > state["max_iterations"]:
        updates["next_action"] = "complete"
        updates["is_complete"] = True
        return updates
    
    # Decision logic
    if state["schema"] is None:
        updates["next_action"] = "get_schema"
    elif state["sql_query"] is None:
        updates["next_action"] = "generate_sql"
    elif state["execution_result"] is None:
        updates["next_action"] = "execute_sql"
    elif state["validation_result"] is None:
        updates["next_action"] = "validate_results"
    elif state["reflection_result"] is None:  # NEW: Go to reflection after validation
        updates["next_action"] = "reflect"
    else:
        updates["next_action"] = "complete"
        updates["is_complete"] = True
    
    return updates

# Update routing to include reflection
def _should_execute_or_generate(self, state: AgentState) -> str:
    """Routing: execute_tools, generate_sql, reflect, or complete"""
    action = state.get("next_action", "")
    
    if action == "generate_sql":
        return "generate_sql"
    elif action == "reflect":
        return "reflect"  # NEW
    elif action == "complete":
        return "complete"
    else:
        return "execute_tools"
```

### Testing Strategy

**Unit Tests:**
```python
# backend/tests/test_reflection.py

def test_reflect_node_success():
    """Test reflection accepts good SQL"""
    service = AgenticText2SQLService()
    
    state = {
        **initial_state,
        "sql_query": "SELECT * FROM products",
        "execution_result": {"success": True, "data": [...]},
        "validation_result": {"is_valid": True, "has_results": True}
    }
    
    updates = service._reflect_node(state)
    
    assert updates["reflection_result"]["is_acceptable"] == True
    assert updates["reflection_result"]["should_refine"] == False

def test_reflect_node_syntax_error():
    """Test reflection detects syntax error and triggers retry"""
    service = AgenticText2SQLService()
    
    state = {
        **initial_state,
        "sql_query": "SELCT * FROM products",  # Typo
        "execution_result": {"success": False, "error": "syntax error near SELCT"},
        "validation_result": None
    }
    
    updates = service._reflect_node(state)
    
    assert updates["reflection_result"]["should_refine"] == True
    assert len(updates["reflection_result"]["issues"]) > 0

def test_reflect_node_unknown_table():
    """Test reflection detects unknown table error"""
    service = AgenticText2SQLService()
    
    state = {
        **initial_state,
        "execution_result": {"success": False, "error": "no such table: wrong_table"}
    }
    
    updates = service._reflect_node(state)
    
    assert updates["reflection_result"]["should_refine"] == True

def test_should_refine_with_iterations_left():
    """Test retry logic when iterations remain"""
    service = AgenticText2SQLService()
    
    state = {
        **initial_state,
        "reflection_result": {"should_refine": True},
        "iteration": 1,
        "max_iterations": 3
    }
    
    result = service._should_refine(state)
    
    assert result == "refine"
    assert state["sql_query"] is None  # Reset for retry

def test_should_refine_max_iterations():
    """Test stops retrying at max iterations"""
    service = AgenticText2SQLService()
    
    state = {
        **initial_state,
        "reflection_result": {"should_refine": True},
        "iteration": 3,
        "max_iterations": 3
    }
    
    result = service._should_refine(state)
    
    assert result == "complete"  # Give up

def test_workflow_retries_on_error():
    """Integration: workflow retries after SQL error"""
    service = AgenticText2SQLService()
    
    # Mock: first attempt fails, second succeeds
    mock_attempts = [
        {"success": False, "error": "syntax error"},
        {"success": True, "data": [...]}
    ]
    
    # ... (complex test setup with mocking)
    
    final_state = service.workflow.invoke(initial_state)
    
    assert final_state["iteration"] == 2  # Took 2 attempts
    assert final_state["sql_query"] is not None
    assert final_state["reflection_result"]["is_acceptable"] == True
```

---

## Dependencies

### Prerequisites
- STORY-AGENT-3 must be complete (SQL generation)
- Validation tool must be working

---

## Definition of Done

### Code Complete
- [ ] Reflection node implemented
- [ ] Error detection logic working
- [ ] Retry logic implemented
- [ ] Conditional routing working
- [ ] Planning node routes to reflection

### Tests Pass
- [ ] Unit tests for reflection logic
- [ ] Unit tests for retry logic
- [ ] Integration test: workflow retries on error
- [ ] Integration test: workflow stops at max iterations
- [ ] All tests passing

### Documentation
- [ ] Reflection logic documented
- [ ] Error classification documented
- [ ] State machine diagram updated

### Review
- [ ] Code reviewed by peer

---

## Notes & Considerations

**Key Decisions:**
- Simple reflection: only retry on critical errors
- Max 2-3 iterations to avoid infinite loops
- Empty results don't trigger retry (might be valid)

**Demo Impact:**
- This is a showpiece feature (self-correction)
- Demo should include intentional error scenario
- Transparency in reflection result is important

**Risks:**
- Retry might generate same bad SQL
- Max iterations might be too low/high
- Mitigation: Tune max_iterations based on testing

---

## Related Stories

**Depends On:** STORY-AGENT-3

**Blocks:** STORY-AGENT-8 (Frontend needs reflection display)

---

**Story Status:** ✅ Ready for Development

