# Story: Planning Agent & Tool Infrastructure

**Story ID:** STORY-AGENT-2  
**Epic:** EPIC-AGENTIC-001 (Agentic Text-to-SQL Enhancement)  
**Priority:** Must Have  
**Status:** Ready for Development  
**Estimate:** 3 days  
**Dependencies:** STORY-AGENT-1  

---

## User Story

**As a** developer  
**I want** to implement the planning agent and modular tool infrastructure  
**So that** the system can intelligently decide which actions to take and execute them through reusable tools

---

## Description

Implement the core intelligence of the agentic system: a planning agent that analyzes the current state and decides what action to take next (get schema, generate SQL, execute query, validate, complete). Also create the modular tool pattern that allows the planning agent to execute specific actions.

This story establishes the decision-making brain of the agentic system.

---

## Acceptance Criteria

### Must Have

1. **Planning Node Implemented**
   - [ ] `_plan_node(state)` function makes intelligent routing decisions
   - [ ] Decision logic:
     - If no schema → next_action = "get_schema"
     - If no SQL generated → next_action = "generate_sql"
     - If SQL not executed → next_action = "execute_sql"
     - If results not validated → next_action = "validate_results"
     - If max_iterations exceeded → next_action = "complete"
     - Otherwise → next_action = "complete"
   - [ ] Increments iteration counter
   - [ ] Returns dict with next_action and updated iteration

2. **Tool Base Class Created**
   - [ ] `Tool` class in `backend/services/agent_tools.py`
   - [ ] Properties: name, description, function
   - [ ] Method: `execute(**kwargs) -> Dict`
   - [ ] Returns standardized format: {success: bool, tool: str, result: Any, error: Optional[str]}
   - [ ] Error handling in execute method

3. **Core Tools Implemented**
   - [ ] **get_schema Tool:**
     - Retrieves database schema from db_manager
     - Simple direct retrieval (no hybrid search)
     - Returns schema as string
   - [ ] **execute_sql Tool:**
     - Executes SQL query safely
     - Uses existing query_executor
     - Returns {success, data, columns, row_count, error}
   - [ ] **validate_results Tool:**
     - Basic validation logic
     - Checks: has_results, row_count > 0, no errors
     - Returns {is_valid, has_results, row_count, issues: []}

4. **Execute Tools Node Implemented**
   - [ ] `_execute_tools_node(state)` function
   - [ ] Maps next_action to appropriate tool
   - [ ] Executes tool with correct parameters
   - [ ] Updates state with tool results
   - [ ] Appends tool call to tool_calls list
   - [ ] Returns state updates

5. **State Machine Routing**
   - [ ] Add conditional edge from plan to execute_tools or complete
   - [ ] Add edge from execute_tools back to plan (loop)
   - [ ] Conditional function `_should_execute_tool(state)` implemented
   - [ ] Workflow can loop: plan → execute_tools → plan → ...

### Nice to Have

- [ ] Tool execution timing/metrics
- [ ] Tool call logging for debugging
- [ ] Schema caching to avoid redundant calls

### Architecture Validation

- [ ] Planning decision tree matches Architecture Section 5.3.2
- [ ] Tool base class matches Architecture Section 6.1
- [ ] All tools follow standardized interface (Architecture Section 6.1)
- [ ] Tool error handling returns success/error format
- [ ] Logging follows Architecture Section 13.3 patterns

---

## Architecture References

**See Architecture Document:** `docs/architecture-agentic-text2sql.md`
- **Section 5.3.2:** Planning Node Design (decision tree logic)
- **Section 6.1:** Tool Base Class (standardized tool interface)
- **Section 6.2:** Tool Catalog (all 4 tools defined)
- **Section 6.3:** Tool Implementation Details

**Key Architecture Patterns:**
- Tool execute() returns standardized dict: `{success, tool, result/error}`
- Planning node uses decision tree: schema → SQL → execute → validate → reflect
- Tools are stateless, reusable components
- Planning node increments iteration counter as guard

**Performance Targets (Architecture Section 13.1):**
- get_schema: ≤100ms
- execute_sql: ≤500ms
- validate_results: ≤100ms

---

## Technical Implementation

### Files to Create

```
backend/services/agent_tools.py
```

### Files to Modify

```
backend/services/agentic_text2sql_service.py (add nodes, edges, tools)
```

### Key Code Structure

```python
# backend/services/agent_tools.py

from typing import Callable, Dict
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class Tool:
    """
    Base tool class for agentic workflow.
    Architecture Reference: Section 6.1 (Tool Base Class)
    """
    
    def __init__(self, name: str, description: str, function: Callable):
        self.name = name
        self.description = description
        self.function = function
        logger.info(f"Tool initialized: {name}")
    
    def execute(self, **kwargs) -> Dict:
        """
        Execute the tool with standardized error handling.
        Architecture Reference: Section 6.1
        Returns: {success: bool, tool: str, result/error: Any}
        """
        start_time = datetime.now()
        logger.info(f"Executing tool '{self.name}' with params: {list(kwargs.keys())}")
        
        try:
            result = self.function(**kwargs)
            
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(f"Tool '{self.name}' succeeded in {elapsed:.3f}s")
            
            return {
                "success": True,
                "tool": self.name,
                "result": result,
                "elapsed": elapsed
            }
            
        except Exception as e:
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.error(f"Tool '{self.name}' failed after {elapsed:.3f}s: {e}", exc_info=True)
            
            return {
                "success": False,
                "tool": self.name,
                "error": str(e),
                "elapsed": elapsed
            }


# backend/services/agentic_text2sql_service.py (additions)

def _initialize_tools(self) -> Dict[str, Tool]:
    """Initialize available tools"""
    
    tools = {}
    
    # Tool: Get Schema
    tools['get_schema'] = Tool(
        name="get_schema",
        description="Retrieves database schema",
        function=self._get_schema_tool
    )
    
    # Tool: Execute SQL
    tools['execute_sql'] = Tool(
        name="execute_sql",
        description="Executes SQL query",
        function=self._execute_sql_tool
    )
    
    # Tool: Validate Results
    tools['validate_results'] = Tool(
        name="validate_results",
        description="Validates query results",
        function=self._validate_results_tool
    )
    
    return tools

def _plan_node(self, state: AgentState) -> Dict:
    """
    Intelligent workflow routing based on state.
    Architecture Reference: Section 5.3.2 (Planning Node Design)
    
    Decision Tree:
    1. No schema → get_schema
    2. Has schema, no SQL → generate_sql
    3. Has SQL, not executed → execute_sql
    4. Has results, not validated → validate_results
    5. Max iterations OR all complete → complete
    """
    iteration = state["iteration"] + 1
    logger.info(f"Planning iteration {iteration}/{state['max_iterations']}")
    
    updates = {"iteration": iteration}
    
    # Max iteration guard (Architecture Section 13.1)
    if iteration > state["max_iterations"]:
        logger.warning(f"Max iterations reached: {iteration}")
        updates["next_action"] = "complete"
        updates["is_complete"] = True
        return updates
    
    # Decision tree (Architecture Section 5.3.2)
    if state["schema"] is None:
        next_action = "get_schema"
    elif state["sql_query"] is None:
        next_action = "generate_sql"
    elif state["execution_result"] is None:
        next_action = "execute_sql"
    elif state["validation_result"] is None:
        next_action = "validate_results"
    else:
        next_action = "complete"
        updates["is_complete"] = True
    
    logger.info(f"Planning decision: {next_action} (iteration {iteration})")
    updates["next_action"] = next_action
    
    return updates

def _execute_tools_node(self, state: AgentState) -> Dict:
    """
    Execute the tool specified by planning node.
    Architecture Reference: Section 6.2 (Tool Catalog)
    """
    action = state["next_action"]
    logger.info(f"Execute tools node: action={action}")
    
    # Map actions to tools with parameters
    tool_mapping = {
        "get_schema": ("get_schema", {"query": state["resolved_query"]}),
        "execute_sql": ("execute_sql", {"sql": state["sql_query"]}),
        "validate_results": ("validate_results", {
            "query": state["resolved_query"],
            "sql": state["sql_query"],
            "results": state["execution_result"]
        })
    }
    
    updates = {}
    
    if action not in tool_mapping:
        logger.warning(f"Unknown action '{action}', skipping tool execution")
        return updates
    
    # Execute tool (Architecture Section 6.1)
    tool_name, params = tool_mapping[action]
    logger.info(f"Executing tool: {tool_name}")
    
    tool_result = self.tools[tool_name].execute(**params)
    updates["tool_calls"] = [tool_result]
    
    # Update state based on tool (Architecture Section 6.2)
    if tool_result.get("success"):
        result = tool_result.get("result")
        
        if tool_name == "get_schema":
            updates["schema"] = result
            logger.info(f"Schema retrieved: {len(result)} chars")
        elif tool_name == "execute_sql":
            updates["execution_result"] = result
            row_count = len(result.get("data", []))
            logger.info(f"SQL executed: {row_count} rows returned")
        elif tool_name == "validate_results":
            updates["validation_result"] = result
            logger.info(f"Validation complete: valid={result.get('is_valid')}")
    else:
        # Tool failed (Architecture Section 6.1)
        error = tool_result.get("error", "Unknown error")
        logger.error(f"Tool '{tool_name}' failed: {error}")
        updates["error"] = f"Tool {tool_name}: {error}"
    
    return updates

def _should_execute_tool(self, state: AgentState) -> str:
    """Decide if should execute tool or complete"""
    action = state.get("next_action", "")
    if action == "complete":
        return "complete"
    else:
        return "execute_tools"

# Update workflow building
def _build_workflow(self) -> StateGraph:
    """Build LangGraph workflow"""
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("plan", self._plan_node)
    workflow.add_node("execute_tools", self._execute_tools_node)
    workflow.add_node("complete", self._complete_node)
    
    # Set entry point
    workflow.set_entry_point("plan")
    
    # Add edges
    workflow.add_conditional_edges(
        "plan",
        self._should_execute_tool,
        {
            "execute_tools": "execute_tools",
            "complete": "complete"
        }
    )
    workflow.add_edge("execute_tools", "plan")  # Loop back
    workflow.add_edge("complete", END)
    
    return workflow.compile()

# Tool implementation methods
def _get_schema_tool(self, query: str = None) -> str:
    """
    Tool: Get database schema.
    Architecture Reference: Section 6.2 (get_schema tool)
    Performance Target: ≤100ms
    """
    logger.info("Retrieving database schema...")
    
    try:
        # Use existing ClaudeService schema (Architecture Section 11.1)
        schema = self.claude_service.get_schema_info()
        logger.info(f"Schema retrieved: {len(schema)} characters")
        return schema
        
    except Exception as e:
        logger.error(f"Schema retrieval failed: {e}", exc_info=True)
        raise  # Re-raise for Tool class to handle

def _execute_sql_tool(self, sql: str) -> Dict:
    """
    Tool: Execute SQL query safely.
    Architecture Reference: Section 6.2 (execute_sql tool)
    Performance Target: ≤500ms
    """
    logger.info(f"Executing SQL: {sql[:100]}...")
    
    try:
        # Use existing QueryExecutor (Architecture Section 11.2)
        from services.query_executor import QueryExecutor
        executor = QueryExecutor()
        result = executor.execute_query(sql)
        
        row_count = len(result.get("data", []))
        logger.info(f"SQL executed successfully: {row_count} rows")
        
        return result
        
    except Exception as e:
        logger.error(f"SQL execution failed: {e}", exc_info=True)
        raise  # Re-raise for Tool class to handle

def _validate_results_tool(self, query: str, sql: str, results: Dict) -> Dict:
    """
    Tool: Validate SQL results.
    Architecture Reference: Section 6.2 (validate_results tool)
    Performance Target: ≤100ms
    """
    logger.info("Validating results...")
    
    try:
        validation = {
            "is_valid": True,
            "has_results": bool(results.get("data")),
            "row_count": len(results.get("data", [])),
            "issues": []
        }
        
        # Check for results (informational, not critical)
        if not validation["has_results"]:
            validation["issues"].append("No results returned")
            logger.info("Validation: No results (might be correct)")
        
        # Check for execution errors
        if not results.get("success", True):
            validation["issues"].append(f"Execution error: {results.get('error')}")
            logger.warning(f"Validation: Execution error detected")
        
        logger.info(f"Validation complete: {len(validation['issues'])} issue(s)")
        
        return validation
        
    except Exception as e:
        logger.error(f"Validation failed: {e}", exc_info=True)
        raise  # Re-raise for Tool class to handle
```

### Testing Strategy

**Unit Tests:**
```python
# backend/tests/test_planning_tools.py

def test_tool_execution():
    """Test tool can execute successfully"""
    def mock_function(**kwargs):
        return "test_result"
    
    tool = Tool("test_tool", "Test description", mock_function)
    result = tool.execute()
    
    assert result["success"] == True
    assert result["result"] == "test_result"

def test_tool_error_handling():
    """Test tool handles errors gracefully"""
    def failing_function(**kwargs):
        raise ValueError("Test error")
    
    tool = Tool("failing_tool", "Fails", failing_function)
    result = tool.execute()
    
    assert result["success"] == False
    assert "Test error" in result["error"]

def test_planning_logic():
    """Test planning node makes correct decisions"""
    service = AgenticText2SQLService()
    
    # Test: No schema -> get_schema
    state = {**initial_state, "schema": None}
    updates = service._plan_node(state)
    assert updates["next_action"] == "get_schema"
    
    # Test: Has schema, no SQL -> generate_sql
    state = {**initial_state, "schema": "schema", "sql_query": None}
    updates = service._plan_node(state)
    assert updates["next_action"] == "generate_sql"

def test_execute_tools_node():
    """Test execute_tools node executes correct tool"""
    service = AgenticText2SQLService()
    
    state = {
        **initial_state,
        "next_action": "get_schema",
        "resolved_query": "test"
    }
    
    updates = service._execute_tools_node(state)
    assert "schema" in updates
    assert len(updates["tool_calls"]) == 1

def test_workflow_loops():
    """Test workflow can loop through multiple tools"""
    service = AgenticText2SQLService()
    
    initial_state = {...}
    final_state = service.workflow.invoke(initial_state)
    
    # Should have called multiple tools
    assert len(final_state["tool_calls"]) >= 2
    assert final_state["is_complete"] == True
```

---

## Dependencies

### Prerequisites
- STORY-AGENT-1 must be complete (LangGraph foundation)
- Existing query_executor and db_manager must be functional

### Required Services
- ClaudeService (for schema info)
- query_executor (for SQL execution)
- db_manager (for database access)

---

## Definition of Done

### Code Complete
- [ ] All code written and self-reviewed
- [ ] Planning logic implemented and tested
- [ ] All three core tools working
- [ ] Execute tools node working
- [ ] Workflow loops correctly

### Tests Pass
- [ ] Unit tests for Tool class
- [ ] Unit tests for each tool implementation
- [ ] Unit tests for planning logic
- [ ] Integration test: full workflow with tools
- [ ] All tests passing

### Documentation
- [ ] Tool class documented
- [ ] Planning logic documented
- [ ] State machine flow diagram updated

### Review
- [ ] Code reviewed by peer
- [ ] All review comments addressed

---

## Notes & Considerations

**Key Decisions:**
- Using simple direct schema retrieval (no hybrid search per requirements)
- Tool pattern matches inspiration code for consistency
- Planning logic is straightforward state-based routing

**Why This Order:**
- Get schema first (needed for SQL generation)
- Generate SQL second (core functionality)
- Execute SQL third (produce results)
- Validate results last (quality check)

**Risks:**
- Planning logic could become complex as features grow
- Tool error handling needs to be robust
- Mitigation: Keep planning logic simple, clear error messages

---

## Related Stories

**Depends On:** STORY-AGENT-1

**Blocks:**
- STORY-AGENT-3 (SQL Generation)
- STORY-AGENT-5 (Clarification)

**Related:**
- STORY-AGENT-4 (Reflection uses similar patterns)

---

**Story Status:** ✅ Ready for Development

**Assigned To:** [Developer Name]

**Sprint:** Sprint X

**Started:** [Date]

**Completed:** [Date]

