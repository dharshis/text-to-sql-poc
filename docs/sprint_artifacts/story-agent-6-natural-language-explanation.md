# Story: Natural Language Explanation Generator

**Story ID:** STORY-AGENT-6  
**Epic:** EPIC-AGENTIC-001 (Agentic Text-to-SQL Enhancement)  
**Priority:** Must Have  
**Status:** Ready for Development  
**Estimate:** 2 days  
**Dependencies:** STORY-AGENT-3  

---

## User Story

**As a** market researcher  
**I want** to see natural language explanations of query results  
**So that** I immediately understand key insights without manually analyzing data

---

## Description

Implement the explanation generator that transforms raw SQL results into human-readable insights using Claude. This is a major value-add feature that positions the system as an "insights engine" not just a query tool. The explanation should highlight key findings, trends, comparisons, and anomalies in plain English.

---

## Acceptance Criteria

### Must Have

1. **Explanation Generation Node Implemented**
   - [ ] `_generate_explanation_node(state)` function created
   - [ ] Called after successful query execution and validation
   - [ ] Sends results + context to Claude
   - [ ] Receives natural language explanation
   - [ ] Updates state with explanation text
   - [ ] Returns {explanation: str}

2. **Explanation Prompt Engineering**
   - [ ] System prompt: "You are a data insights analyst"
   - [ ] Includes: original user query, SQL query, result data, column names
   - [ ] Instructions: write clear, concise insights
   - [ ] Should highlight:
     - Top items/values
     - Trends and patterns
     - Comparisons
     - Notable findings or anomalies
   - [ ] Tone: professional but accessible
   - [ ] Length: 2-4 sentences

3. **Data Formatting for Explanation**
   - [ ] Limit result data sent to Claude (max 100 rows)
   - [ ] Include column names and data types
   - [ ] Format numbers appropriately (currency, percentages)
   - [ ] Handle empty results gracefully
   - [ ] Handle large datasets (summary stats only)

4. **Workflow Integration**
   - [ ] Planning node routes to "generate_explanation" after validation
   - [ ] Explanation generated before completing workflow
   - [ ] Workflow: ... → validate → reflect → generate_explanation → complete
   - [ ] Explanation included in final response

5. **Error Handling**
   - [ ] If explanation generation fails, workflow continues
   - [ ] Return results without explanation (graceful degradation)
   - [ ] Log explanation errors
   - [ ] No retry for explanation failures

### Nice to Have

- [ ] Explanation quality scoring
- [ ] Multiple explanation styles (brief vs. detailed)
- [ ] Comparison to previous results (if conversation context)
- [ ] Customizable explanation templates

### Architecture Validation

- [ ] Explanation quality: 2-4 sentences, plain English (Architecture Section 5.3.4)
- [ ] Data sample limited to 20 rows for performance
- [ ] Graceful fallback if generation fails
- [ ] Performance target ≤2s (Architecture Section 13.1)
- [ ] Highlights key insights (top items, trends, comparisons)

---

## Architecture References

**See Architecture Document:** `docs/architecture-agentic-text2sql.md`
- **Section 5.3.4:** Explanation Generation Node (complete design)
- **Section 13.1:** Performance Budget (≤2s for explanation)
- **Section 9.1:** Frontend Integration (InsightCard display)

**Explanation Quality Criteria (Architecture):**
- 2-4 sentences, plain English
- Highlights: top values, trends, comparisons, anomalies
- Business-focused, not technical
- Professional but accessible tone

**Key Patterns:**
- Called after validation, before complete
- Uses result data (limited sample for performance)
- Graceful degradation if generation fails
- No retry on failure (non-critical)

**Performance Target:** ≤2s (Architecture Section 13.1)

---

## Technical Implementation

### Files to Modify

```
backend/services/agentic_text2sql_service.py (add generate_explanation_node, update workflow)
```

### Key Code Structure

```python
# backend/services/agentic_text2sql_service.py

from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def _generate_explanation_node(self, state: AgentState) -> Dict:
    """
    Generate natural language explanation of results.
    Architecture Reference: Section 5.3.4
    Performance Target: ≤2s (Section 13.1)
    """
    query = state["user_query"]
    sql = state["sql_query"]
    results = state["execution_result"]
    
    logger.info("Generating natural language explanation...")
    start_time = datetime.now()
    
    # Handle no results
    if not results or not results.get("data"):
        return {
            "explanation": f"The query returned no results. This might indicate that no data matches the specified criteria."
        }
    
    # Prepare data for explanation
    data = results.get("data", [])
    columns = results.get("columns", [])
    row_count = len(data)
    
    # Limit data sent to Claude (performance + cost)
    sample_data = data[:20] if row_count > 20 else data
    
    # Build explanation prompt
    explanation_prompt = f"""Analyze these query results and provide a clear, insightful explanation in plain English.

User's Question: {query}

Generated SQL: {sql}

Results ({row_count} rows total, showing first {len(sample_data)}):
Columns: {', '.join(columns)}

Data:
{self._format_data_for_explanation(sample_data, columns)}

Provide a 2-4 sentence explanation that:
1. Directly answers the user's question
2. Highlights the most important findings (top values, trends, patterns)
3. Notes any interesting comparisons or anomalies
4. Uses plain English (no technical jargon)

Write the explanation as if speaking to a business stakeholder who needs quick insights."""
    
    try:
        response = self.claude_service.client.messages.create(
            model=self.claude_service.model,
            max_tokens=300,
            temperature=0.7,
            system="You are a data insights analyst. Transform query results into clear, actionable insights for business users.",
            messages=[{"role": "user", "content": explanation_prompt}]
        )
        
        explanation = response.content[0].text.strip()
        logger.info(f"Generated explanation: {explanation[:100]}...")
        
        return {"explanation": explanation}
        
    except Exception as e:
        logger.error(f"Explanation generation failed: {e}")
        # Graceful fallback
        return {
            "explanation": f"Found {row_count} result(s) for your query."
        }

def _format_data_for_explanation(self, data: List[Dict], columns: List[str]) -> str:
    """Format data rows for explanation prompt"""
    
    if not data:
        return "No data"
    
    # Create simple table format
    lines = []
    for row in data[:10]:  # Max 10 rows in prompt
        row_str = " | ".join([str(row.get(col, 'N/A')) for col in columns])
        lines.append(row_str)
    
    return "\n".join(lines)

# Update planning node to route to explanation
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
    elif state["reflection_result"] is None:
        updates["next_action"] = "reflect"
    elif state["explanation"] is None and state["execution_result"].get("success"):  # NEW
        updates["next_action"] = "generate_explanation"
    else:
        updates["next_action"] = "complete"
        updates["is_complete"] = True
    
    return updates

# Update workflow
def _build_workflow(self) -> StateGraph:
    """Build LangGraph workflow"""
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("detect_clarification", self._detect_clarification_node)
    workflow.add_node("plan", self._plan_node)
    workflow.add_node("execute_tools", self._execute_tools_node)
    workflow.add_node("generate_sql", self._generate_sql_node)
    workflow.add_node("reflect", self._reflect_node)
    workflow.add_node("generate_explanation", self._generate_explanation_node)  # NEW
    workflow.add_node("complete", self._complete_node)
    
    # Set entry point
    workflow.set_entry_point("detect_clarification")
    
    # Add edges
    workflow.add_conditional_edges(
        "detect_clarification",
        self._should_clarify,
        {
            "clarify": "complete",
            "proceed": "plan"
        }
    )
    
    workflow.add_conditional_edges(
        "plan",
        self._should_execute_or_generate,
        {
            "execute_tools": "execute_tools",
            "generate_sql": "generate_sql",
            "reflect": "reflect",
            "generate_explanation": "generate_explanation",  # NEW
            "complete": "complete"
        }
    )
    
    workflow.add_edge("execute_tools", "plan")
    workflow.add_edge("generate_sql", "plan")
    workflow.add_edge("generate_explanation", "plan")  # NEW: Loop back after explanation
    
    workflow.add_conditional_edges(
        "reflect",
        self._should_refine,
        {
            "refine": "plan",
            "complete": "plan"  # Go back to plan for explanation generation
        }
    )
    
    workflow.add_edge("complete", END)
    
    return workflow.compile()

# Update routing
def _should_execute_or_generate(self, state: AgentState) -> str:
    """Enhanced routing including explanation"""
    action = state.get("next_action", "")
    
    if action == "generate_sql":
        return "generate_sql"
    elif action == "reflect":
        return "reflect"
    elif action == "generate_explanation":  # NEW
        return "generate_explanation"
    elif action == "complete":
        return "complete"
    else:
        return "execute_tools"

# Update response format to include explanation
def _format_response(self, state: AgentState) -> Dict:
    """Format the final response"""
    
    # If clarification needed
    if state.get("clarification_needed"):
        return {
            "success": False,
            "needs_clarification": True,
            "questions": state.get("clarification_questions", []),
            "method": "agentic"
        }
    
    # Normal response with explanation
    return {
        "success": True,
        "sql": state.get("sql_query"),
        "results": state.get("execution_result"),
        "explanation": state.get("explanation"),  # NEW: Include explanation
        "validation": state.get("validation_result"),
        "reflection": state.get("reflection_result"),
        "method": "agentic",
        "session_id": state["session_id"],
        "iterations": state.get("iteration", 0),
        "tool_calls": len(state.get("tool_calls", []))
    }
```

### Testing Strategy

**Unit Tests:**
```python
# backend/tests/test_explanation.py

def test_generate_explanation_with_results():
    """Test explanation generation with valid results"""
    service = AgenticText2SQLService()
    
    state = {
        **initial_state,
        "user_query": "Top 10 products by revenue",
        "sql_query": "SELECT...",
        "execution_result": {
            "success": True,
            "data": [{"product_name": "Product A", "revenue": 10000}, ...],
            "columns": ["product_name", "revenue"]
        }
    }
    
    updates = service._generate_explanation_node(state)
    
    assert "explanation" in updates
    assert len(updates["explanation"]) > 50  # Reasonable length
    assert "Product A" in updates["explanation"]  # Mentions data

def test_generate_explanation_empty_results():
    """Test explanation handles empty results"""
    service = AgenticText2SQLService()
    
    state = {
        **initial_state,
        "execution_result": {"success": True, "data": []}
    }
    
    updates = service._generate_explanation_node(state)
    
    assert "explanation" in updates
    assert "no results" in updates["explanation"].lower()

def test_explanation_graceful_failure():
    """Test explanation generation failure doesn't break workflow"""
    service = AgenticText2SQLService()
    
    # Mock Claude to fail
    service.claude_service.client.messages.create = Mock(side_effect=Exception("API Error"))
    
    state = {...}  # Valid state
    
    updates = service._generate_explanation_node(state)
    
    assert "explanation" in updates  # Fallback explanation provided
    # Workflow should continue

def test_workflow_includes_explanation():
    """Integration: full workflow generates explanation"""
    service = AgenticText2SQLService()
    
    result = service.generate_sql_with_agent(
        user_query="Top 10 products by revenue",
        session_id="test"
    )
    
    assert "explanation" in result
    assert result["explanation"] is not None
    assert len(result["explanation"]) > 20
```

---

## Dependencies

### Prerequisites
- STORY-AGENT-3 complete (SQL generation and execution)
- ClaudeService functional

---

## Definition of Done

### Code Complete
- [ ] Explanation generation node implemented
- [ ] Prompt engineering complete
- [ ] Data formatting logic working
- [ ] Workflow integration complete
- [ ] Response format includes explanation

### Tests Pass
- [ ] Unit tests for explanation generation
- [ ] Tests for empty results handling
- [ ] Tests for error handling
- [ ] Integration test: full workflow with explanation
- [ ] All tests passing

### Documentation
- [ ] Explanation logic documented
- [ ] Prompt template documented
- [ ] State machine diagram updated

### Review
- [ ] Code reviewed by peer

---

## Notes & Considerations

**This is a KEY DIFFERENTIATOR:**
- Transforms system from "query tool" to "insights engine"
- Major UX improvement for non-technical users
- Should be featured prominently in demo

**Prompt Tuning:**
- May need iteration to get tone right
- Balance detail vs. brevity
- Should feel natural, not robotic

**Performance:**
- Adds 1-2 seconds to response time
- Worth it for value provided
- Can be optimized later if needed

---

**Story Status:** ✅ Ready for Development

