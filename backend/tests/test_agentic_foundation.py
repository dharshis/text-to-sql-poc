"""
Unit tests for LangGraph foundation and AgenticText2SQLService.

Tests cover:
- AgentState TypedDict instantiation
- Workflow compilation
- Basic workflow execution
- State transitions

Architecture Reference: docs/architecture-agentic-text2sql.md Section 4.1, 4.2
"""

import pytest
from services.agentic_text2sql_service import AgenticText2SQLService, AgentState


def test_agent_state_creation():
    """
    Test AgentState can be instantiated with all required fields.
    AC1: AgentState TypedDict Defined
    """
    state: AgentState = {
        "user_query": "test query",
        "session_id": "test-123",
        "resolved_query": "test query",
        "chat_history": [],
        "iteration": 0,
        "max_iterations": 3,
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
    
    assert state["user_query"] == "test query"
    assert state["session_id"] == "test-123"
    assert state["iteration"] == 0
    assert state["max_iterations"] == 3
    assert state["is_complete"] is False


def test_workflow_compiles():
    """
    Test LangGraph workflow compiles successfully.
    AC2: StateGraph Created - Graph compiles without errors
    """
    service = AgenticText2SQLService()
    
    assert service.workflow is not None
    # Workflow should be compiled (has invoke method)
    assert hasattr(service.workflow, 'invoke')


def test_simple_workflow_execution():
    """
    Test basic workflow execution.
    AC3: Basic Workflow Tested - workflow invokes and returns final state
    """
    service = AgenticText2SQLService()
    
    result = service.generate_sql_with_agent(
        user_query="test query",
        session_id="test-123"
    )
    
    # AC4: Returns response with full state information
    assert result["success"] is True
    assert result["method"] == "agentic"
    assert result["session_id"] == "test-123"
    assert "iterations" in result
    assert "tool_calls" in result
    assert "clarification_needed" in result


def test_state_transitions():
    """
    Test state updates persist across nodes.
    AC3: State transitions work correctly
    """
    service = AgenticText2SQLService()
    
    result = service.generate_sql_with_agent(
        user_query="Show me top products",
        session_id="test-456",
        max_iterations=5
    )
    
    # Workflow should complete
    assert result["success"] is True
    assert result["session_id"] == "test-456"
    
    # State should have been initialized and processed
    assert "iterations" in result


def test_max_iterations_respected():
    """
    Test max_iterations parameter is passed to state.
    AC1: AgentState includes max_iterations field
    """
    service = AgenticText2SQLService()
    
    result = service.generate_sql_with_agent(
        user_query="test",
        session_id="test-789",
        max_iterations=5
    )
    
    assert result["success"] is True
    # Future stories will validate iteration counting works


def test_error_handling():
    """
    Test workflow handles errors gracefully.
    AC5: Integration - error handling
    """
    service = AgenticText2SQLService()
    
    # Test with empty query (should not crash)
    result = service.generate_sql_with_agent(
        user_query="",
        session_id="test-error"
    )
    
    # Should return success (even if query is empty, workflow completes)
    assert "success" in result
    assert "method" in result


