# Story: Clarification Detection Agent

**Story ID:** STORY-AGENT-5  
**Epic:** EPIC-AGENTIC-001 (Agentic Text-to-SQL Enhancement)  
**Priority:** Must Have  
**Status:** Ready for Development  
**Estimate:** 3 days  
**Dependencies:** STORY-AGENT-2  

---

## User Story

**As a** market researcher  
**I want** the system to ask for clarification when my query is ambiguous  
**So that** I get accurate results without having to guess what information to provide upfront

---

## Description

Implement the clarification detection agent that analyzes user queries before SQL generation and determines if critical information is missing. When ambiguity is detected, the system asks specific questions instead of blindly generating potentially incorrect SQL.

This is a key UX differentiator that demonstrates intelligence.

---

## Acceptance Criteria

### Must Have

1. **Clarification Detection Node Implemented**
   - [ ] `_detect_clarification_node(state)` function created
   - [ ] Inserted as first node after entry (before planning)
   - [ ] Analyzes user query for ambiguity
   - [ ] Has access to schema context for better detection
   - [ ] Returns {clarification_needed: bool, clarification_questions: List[str]}

2. **Ambiguity Detection Logic**
   - [ ] Uses Claude to analyze query against schema
   - [ ] Detects missing critical context:
     - Time periods not specified ("show sales trends" → which period?)
     - Vague metrics ("show performance" → revenue? quantity? growth?)
     - Ambiguous entities ("top products" → by what measure? how many?)
     - Missing filters (region, category, etc.)
   - [ ] Returns 2-4 specific, helpful clarification questions

3. **Clarification Prompt Engineering**
   - [ ] System prompt: "You are a query analysis expert"
   - [ ] Includes schema context in analysis
   - [ ] Includes business context (if available)
   - [ ] Instructions: only ask if truly ambiguous
   - [ ] Output format: JSON with needs_clarification and questions array

4. **Workflow Routing with Clarification**
   - [ ] Entry point: detect_clarification (NEW)
   - [ ] Conditional edge: clarify OR proceed
   - [ ] If clarification_needed=True → route to "complete" (return questions to user)
   - [ ] If clarification_needed=False → route to "plan" (continue workflow)
   - [ ] `_should_clarify(state)` function implemented

5. **Response Format for Clarification**
   - [ ] When clarification needed, workflow returns immediately
   - [ ] Response: {success: False, needs_clarification: True, questions: [...], method: "agentic"}
   - [ ] Frontend can display questions to user
   - [ ] User provides answers, resubmits with additional context

### Nice to Have

- [ ] Clarification quality scoring
- [ ] Learn from which queries needed clarification
- [ ] Suggest query templates to avoid ambiguity

### Architecture Validation

- [ ] Entry point routing (workflow starts with detect_clarification)
- [ ] Schema context provided to Claude for analysis
- [ ] Fail-safe: proceeds if detection fails (Architecture Section 5.3.1)
- [ ] Performance target ≤3s (Architecture Section 13.1)
- [ ] Questions are specific and actionable (2-4 questions max)

---

## Architecture References

**See Architecture Document:** `docs/architecture-agentic-text2sql.md`
- **Section 5.3.1:** Clarification Detection Node (complete design)
- **Section 10.2:** Clarification Flow (complete workflow with questions)
- **Section 4.2:** State Machine (entry point routing)
- **Section 13.1:** Performance Budget (≤3s for clarification)

**Clarification Triggers (Architecture Section 5.3.1):**
- Missing time periods ("show trends" → which period?)
- Vague metrics ("show performance" → revenue? quantity?)
- Ambiguous entities ("top products" → by what measure?)
- Missing filters (category, region, etc.)

**Key Patterns:**
- Entry point of workflow (first node after invoke)
- Uses schema context for better detection
- Fail-safe: proceeds if detection fails
- Returns immediately if clarification needed

**Performance Target:** ≤3s (Architecture Section 13.1)

---

## Technical Implementation

### Files to Modify

```
backend/services/agentic_text2sql_service.py (add detect_clarification_node, update workflow)
```

### Key Code Structure

```python
# backend/services/agentic_text2sql_service.py

from datetime import datetime
import logging
import json

logger = logging.getLogger(__name__)


def _detect_clarification_node(self, state: AgentState) -> Dict:
    """
    Detect if query needs clarification before SQL generation.
    Architecture Reference: Section 5.3.1, Section 10.2
    Performance Target: ≤3s (Section 13.1)
    """
    query = state["resolved_query"]
    logger.info(f"Analyzing query for ambiguity: '{query}'")
    start_time = datetime.now()
    
    # Retrieve schema for context (Architecture Section 5.3.1)
    schema_context = None
    try:
        schema_result = self.tools['get_schema'].execute(query=query)
        if schema_result.get("success"):
            schema_context = schema_result.get("result")
            logger.info("Schema retrieved for clarification context")
    except Exception as e:
        logger.warning(f"Could not retrieve schema for clarification: {e}")
    
    # Build clarification detection prompt
    schema_str = schema_context[:1000] if schema_context else "Schema not available"
    
    clarification_prompt = f"""Analyze this database query for ambiguity:

Query: {query}

Available Schema:
{schema_str}

Determine if this query needs clarification before generating SQL. Consider:
1. Is the intent clear and unambiguous given the schema?
2. Are there multiple valid interpretations?
3. Is critical context missing (date ranges, specific entities, metrics)?
4. Are there vague terms that could mean different things?
5. Can you identify the relevant tables/columns from the schema?

Respond in JSON format:
{{
    "needs_clarification": true/false,
    "reason": "explanation",
    "questions": ["clarifying question 1", "clarifying question 2"]
}}

Only request clarification if absolutely necessary - if the schema provides sufficient context, proceed without clarification.
Return ONLY the JSON."""
    
    try:
        response = self.claude_service.client.messages.create(
            model=self.claude_service.model,
            max_tokens=500,
            system="You are a query analysis expert. Detect ambiguous queries that need clarification.",
            messages=[{"role": "user", "content": clarification_prompt}]
        )
        
        # Parse response
        result = json.loads(response.content[0].text)
        
        clarification_needed = result.get("needs_clarification", False)
        questions = result.get("questions", [])
        
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"Clarification analysis in {elapsed:.2f}s: needed={clarification_needed}, questions={len(questions)}")
        
        # Performance warning (Architecture Section 13.1)
        if elapsed > 3.0:
            logger.warning(f"Clarification detection exceeded 3s target: {elapsed:.2f}s")
        
        return {
            "clarification_needed": clarification_needed,
            "clarification_questions": questions,
            "schema": schema_context,  # Cache schema for later use
            "tool_calls": [{"tool": "detect_clarification", "success": True}]
        }
        
    except Exception as e:
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.error(f"Clarification detection failed after {elapsed:.2f}s: {e}", exc_info=True)
        
        # Fail-safe: proceed without clarification (Architecture Section 5.3.1)
        logger.warning("Proceeding without clarification due to detection failure")
        return {
            "clarification_needed": False,
            "clarification_questions": []
        }

def _should_clarify(self, state: AgentState) -> str:
    """Decide if clarification is needed"""
    if state.get("clarification_needed", False):
        logger.info("Clarification needed, returning questions to user")
        return "clarify"
    logger.info("Query is clear, proceeding with workflow")
    return "proceed"

# Update workflow building
def _build_workflow(self) -> StateGraph:
    """Build LangGraph workflow"""
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("detect_clarification", self._detect_clarification_node)  # NEW
    workflow.add_node("plan", self._plan_node)
    workflow.add_node("execute_tools", self._execute_tools_node)
    workflow.add_node("generate_sql", self._generate_sql_node)
    workflow.add_node("reflect", self._reflect_node)
    workflow.add_node("complete", self._complete_node)
    
    # Set entry point
    workflow.set_entry_point("detect_clarification")  # NEW: Start with clarification
    
    # Add edges
    workflow.add_conditional_edges(
        "detect_clarification",
        self._should_clarify,
        {
            "clarify": "complete",  # Return clarification questions
            "proceed": "plan"  # Continue workflow
        }
    )
    
    workflow.add_conditional_edges(
        "plan",
        self._should_execute_or_generate,
        {
            "execute_tools": "execute_tools",
            "generate_sql": "generate_sql",
            "reflect": "reflect",
            "complete": "complete"
        }
    )
    workflow.add_edge("execute_tools", "plan")
    workflow.add_edge("generate_sql", "plan")
    workflow.add_conditional_edges(
        "reflect",
        self._should_refine,
        {
            "refine": "plan",
            "complete": "complete"
        }
    )
    workflow.add_edge("complete", END)
    
    return workflow.compile()

# Update response formatting
def _format_response(self, state: AgentState) -> Dict:
    """Format the final response"""
    
    # If clarification needed, return questions
    if state.get("clarification_needed"):
        return {
            "success": False,
            "needs_clarification": True,
            "questions": state.get("clarification_questions", []),
            "method": "agentic"
        }
    
    # Normal response
    return {
        "success": True,
        "sql": state.get("sql_query"),
        "results": state.get("execution_result"),
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
# backend/tests/test_clarification.py

def test_clarification_detects_vague_query():
    """Test clarification node detects ambiguous query"""
    service = AgenticText2SQLService()
    
    state = {
        **initial_state,
        "resolved_query": "Show me sales trends"  # Vague: which period?
    }
    
    updates = service._detect_clarification_node(state)
    
    assert updates["clarification_needed"] == True
    assert len(updates["clarification_questions"]) >= 1

def test_clarification_allows_clear_query():
    """Test clarification node allows clear query"""
    service = AgenticText2SQLService()
    
    state = {
        **initial_state,
        "resolved_query": "Show me top 10 products by revenue in Q3 2024"  # Clear
    }
    
    updates = service._detect_clarification_node(state)
    
    assert updates["clarification_needed"] == False

def test_workflow_returns_clarification_questions():
    """Integration: workflow returns questions when clarification needed"""
    service = AgenticText2SQLService()
    
    result = service.generate_sql_with_agent(
        user_query="Show me trends",
        session_id="test"
    )
    
    assert result["needs_clarification"] == True
    assert "questions" in result
    assert len(result["questions"]) > 0

def test_workflow_proceeds_without_clarification():
    """Integration: workflow proceeds when query is clear"""
    service = AgenticText2SQLService()
    
    result = service.generate_sql_with_agent(
        user_query="Show me top 10 products by revenue",
        session_id="test"
    )
    
    assert result.get("needs_clarification", False) == False
    assert "sql" in result
```

---

## Dependencies

### Prerequisites
- STORY-AGENT-2 must be complete (tools for schema retrieval)
- ClaudeService must be functional

---

## Definition of Done

### Code Complete
- [ ] Clarification detection node implemented
- [ ] Ambiguity detection logic working
- [ ] Workflow routing with clarification works
- [ ] Response format handles clarification

### Tests Pass
- [ ] Unit tests for clarification detection
- [ ] Integration tests for clarification workflow
- [ ] Test cases: vague queries vs. clear queries
- [ ] All tests passing

### Documentation
- [ ] Clarification logic documented
- [ ] State machine diagram updated
- [ ] Example clarification scenarios documented

### Review
- [ ] Code reviewed by peer

---

## Notes & Considerations

**Demo Scenarios:**
- "Show me sales trends" → needs clarification (period?)
- "Top products" → needs clarification (by what measure? how many?)
- "Electronics sales by region in Q3 2024" → no clarification needed

**Tuning Required:**
- Balance between being helpful vs. annoying
- Should ask 2-4 questions max
- Questions should be specific and actionable

---

**Story Status:** ✅ Ready for Development

