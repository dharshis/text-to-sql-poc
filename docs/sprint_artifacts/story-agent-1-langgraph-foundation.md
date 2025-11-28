# Story: LangGraph Foundation & State Machine

**Story ID:** STORY-AGENT-1  
**Epic:** EPIC-AGENTIC-001 (Agentic Text-to-SQL Enhancement)  
**Priority:** Must Have  
**Status:** Ready for Development  
**Estimate:** 3 days  
**Dependencies:** None  

---

## User Story

**As a** developer  
**I want** to set up the LangGraph state machine foundation  
**So that** we can build agentic workflows with intelligent state management and conditional routing

---

## Description

Implement the core LangGraph infrastructure that will power the agentic text-to-SQL system. This includes defining the AgentState TypedDict, creating the StateGraph, and establishing basic node/edge patterns that all subsequent stories will build upon.

This is the foundational story that enables all other agentic capabilities.

---

## Acceptance Criteria

### Must Have

1. **AgentState TypedDict Defined**
   - [ ] Create `AgentState` TypedDict with all required fields:
     - user_query, session_id, resolved_query
     - chat_history (Annotated with operator.add)
     - iteration, max_iterations
     - schema, sample_data, metadata_context
     - sql_query, execution_result, validation_result
     - reflection_result, explanation
     - clarification_needed, clarification_questions
     - tool_calls, next_action, is_complete, error
   - [ ] Type annotations are correct
   - [ ] All fields documented with clear descriptions

2. **StateGraph Created**
   - [ ] LangGraph StateGraph initialized with AgentState
   - [ ] Basic nodes added: `plan_node`, `complete_node`
   - [ ] Entry point set to `plan_node`
   - [ ] Edges connect nodes correctly
   - [ ] Graph compiles without errors

3. **Basic Workflow Tested**
   - [ ] Create simple test: user_query → plan → complete
   - [ ] State transitions work correctly
   - [ ] State updates persist across nodes
   - [ ] Workflow invokes and returns final state

4. **AgenticText2SQLService Created**
   - [ ] New service class `AgenticText2SQLService` in `backend/services/agentic_text2sql_service.py`
   - [ ] Inherits from or composes with existing services (ClaudeService, db_manager)
   - [ ] Method `generate_sql_with_agent(user_query, session_id, max_iterations=3)` implemented
   - [ ] Returns response with full state information

5. **Integration with Existing Code**
   - [ ] Can import and use existing `ClaudeService`
   - [ ] Can access database schema via existing `db_manager`
   - [ ] No breaking changes to existing `/query` endpoint
   - [ ] LangGraph dependencies installed in requirements.txt

### Nice to Have

- [ ] Logging framework set up for agent decisions
- [ ] State visualization helper for debugging
- [ ] Performance timing for node execution

### Architecture Validation

- [ ] AgentState matches architecture Section 4.1 exactly (20+ fields)
- [ ] Workflow pattern matches Section 4.2 state machine design
- [ ] Service structure follows Section 3.1 component architecture
- [ ] Logging follows Section 13.3 performance monitoring patterns

---

## Architecture References

**See Architecture Document:** `docs/architecture-agentic-text2sql.md`
- **Section 4.1:** AgentState Structure (complete field definitions)
- **Section 4.2:** State Machine Graph (workflow overview)
- **Section 3.1:** Component Architecture (service layer design)
- **Section 2.1:** Design Principles (state-driven workflow)

**Key Architecture Decisions:**
- **ADR-003:** TypedDict for AgentState (not Pydantic)
- State carries full context through entire workflow
- Nodes are pure functions: input state → output updates

---

## Technical Implementation

### Files to Create

```
backend/services/agentic_text2sql_service.py
```

### Files to Modify

```
backend/requirements.txt  (add langgraph>=0.0.20)
```

### Key Code Structure

```python
from typing import TypedDict, Annotated, List, Dict, Optional
from langgraph.graph import StateGraph, END
import operator
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    """State for the agentic workflow"""
    # Core query info
    user_query: str
    session_id: str
    resolved_query: str
    
    # Conversation context
    chat_history: Annotated[List[Dict], operator.add]
    
    # Iteration tracking
    iteration: int
    max_iterations: int
    
    # Retrieved context
    schema: Optional[str]
    sample_data: Dict[str, str]
    metadata_context: Annotated[List[Dict], operator.add]
    
    # Generated artifacts
    sql_query: Optional[str]
    execution_result: Optional[Dict]
    validation_result: Optional[Dict]
    explanation: Optional[str]
    
    # Reflection and clarification
    reflection_result: Optional[Dict]
    clarification_needed: bool
    clarification_questions: Annotated[List[str], operator.add]
    
    # Tool tracking
    tool_calls: Annotated[List[Dict], operator.add]
    
    # Flow control
    next_action: str
    is_complete: bool
    error: Optional[str]


class AgenticText2SQLService:
    """Agentic Text2SQL with LangGraph orchestration"""
    
    def __init__(self):
        self.claude_service = ClaudeService()
        self.db_manager = DBManager()
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """Build LangGraph workflow"""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("plan", self._plan_node)
        workflow.add_node("complete", self._complete_node)
        
        # Set entry point
        workflow.set_entry_point("plan")
        
        # Add edges
        workflow.add_edge("plan", "complete")
        workflow.add_edge("complete", END)
        
        return workflow.compile()
    
    def _plan_node(self, state: AgentState) -> Dict:
        """Planning node - decides next action"""
        return {
            "next_action": "complete",
            "is_complete": True
        }
    
    def _complete_node(self, state: AgentState) -> Dict:
        """Complete the workflow"""
        return {"is_complete": True}
    
    def generate_sql_with_agent(
        self,
        user_query: str,
        session_id: str,
        max_iterations: int = 3
    ) -> Dict:
        """
        Generate SQL using agentic approach with LangGraph orchestration.
        
        Args:
            user_query: Natural language query from user
            session_id: Session identifier for conversation context
            max_iterations: Maximum retry attempts (default: 3)
            
        Returns:
            Dict with SQL, results, and workflow metadata
            
        Architecture Reference: Section 4.1 (AgentState), Section 10.1 (Data Flow)
        """
        start_time = datetime.now()
        logger.info(f"Starting agentic workflow: session={session_id}, query='{user_query[:100]}'")
        
        try:
            # Initialize state (Architecture Section 4.1)
            initial_state: AgentState = {
            "user_query": user_query,
            "session_id": session_id,
            "resolved_query": user_query,
            "chat_history": [],
            "iteration": 0,
            "max_iterations": max_iterations,
            "schema": None,
            "sample_data": {},
            "metadata_context": [],
            "sql_query": None,
            "execution_result": None,
            "validation_result": None,
            "explanation": None,
            "reflection_result": None,
            "clarification_needed": False,
            "clarification_questions": [],
            "tool_calls": [],
            "next_action": "plan",
            "is_complete": False,
            "error": None
        }
        
            # Run workflow (Architecture Section 4.2)
            final_state = self.workflow.invoke(initial_state)
            
            # Performance tracking (Architecture Section 13.3)
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(f"Workflow completed in {elapsed:.2f}s, {final_state.get('iteration', 0)} iterations")
            
            return self._format_response(final_state)
            
        except Exception as e:
            logger.error(f"Agentic workflow failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "method": "agentic",
                "session_id": session_id
            }
    
    def _format_response(self, state: AgentState) -> Dict:
        """Format the final response"""
        return {
            "success": True,
            "sql": state.get("sql_query"),
            "method": "agentic",
            "session_id": state["session_id"],
            "iterations": state.get("iteration", 0),
            "tool_calls": len(state.get("tool_calls", [])),
            "clarification_needed": state.get("clarification_needed", False)
        }
```

### Testing Strategy

**Unit Tests:**
```python
# backend/tests/test_agentic_foundation.py

def test_agent_state_creation():
    """Test AgentState can be instantiated with all fields"""
    state: AgentState = {
        "user_query": "test",
        "session_id": "123",
        # ... all required fields
    }
    assert state["user_query"] == "test"

def test_workflow_compiles():
    """Test LangGraph workflow compiles successfully"""
    service = AgenticText2SQLService()
    assert service.workflow is not None

def test_simple_workflow_execution():
    """Test basic workflow execution"""
    service = AgenticText2SQLService()
    result = service.generate_sql_with_agent(
        user_query="test query",
        session_id="test-123"
    )
    assert result["success"] == True
    assert result["method"] == "agentic"
```

---

## Dependencies

### Prerequisites
- Existing ClaudeService must be functional
- Existing database schema access
- Python environment ready

### Install Required Packages
```bash
pip install langgraph>=0.0.20
```

---

## Definition of Done

### Code Complete
- [ ] All code written and self-reviewed
- [ ] No syntax errors or type errors
- [ ] Code follows project conventions (PEP 8)

### Tests Pass
- [ ] Unit tests written and passing
- [ ] Manual test: workflow executes without errors
- [ ] State transitions work as expected

### Documentation
- [ ] Code is well-commented
- [ ] AgentState fields documented
- [ ] README updated with LangGraph dependency

### Review
- [ ] Code reviewed by peer
- [ ] All review comments addressed

---

## Notes & Considerations

**Why This Story First:**
- Foundation for all other agentic features
- Validates LangGraph works in our environment
- Establishes patterns for subsequent stories

**Key Decisions:**
- Using TypedDict (not Pydantic) to match inspiration code
- Using operator.add for list fields that accumulate
- Keeping workflow simple initially (just plan → complete)

**Risks:**
- LangGraph API may differ from inspiration code version
- State management could be tricky with nested structures
- Mitigation: Study LangGraph docs thoroughly before implementation

---

## Related Stories

**Depends On:** None (foundational story)

**Blocks:**
- STORY-AGENT-2 (Planning Agent)
- STORY-AGENT-7 (Session Management)

**Related:**
- All stories in EPIC-AGENTIC-001

---

**Story Status:** ✅ Ready for Development

**Assigned To:** [Developer Name]

**Sprint:** Sprint X

**Started:** [Date]

**Completed:** [Date]

