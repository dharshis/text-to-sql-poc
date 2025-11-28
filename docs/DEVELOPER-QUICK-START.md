# Developer Quick-Start Guide: Agentic Enhancement

**Architect:** Winston 🏗️  
**For:** Development Team  
**Purpose:** Get started implementing the agentic enhancement immediately  

---

## 🚀 Start Here

You're about to implement a sophisticated multi-agent system. This guide gives you everything you need to start coding **today**.

---

## 📚 Prerequisites - Read These First

**Required Reading (30 minutes):**

1. **Product Brief** (`docs/product-brief-agentic-text2sql-enhancement.md`)
   - Why we're building this
   - Key features: clarification, reflection, conversation context, explanations
   - Success criteria

2. **Architecture Document** (`docs/architecture-agentic-text2sql.md`) - **CRITICAL**
   - Section 4: LangGraph State Machine (AgentState, workflow)
   - Section 5: Agent Nodes (all node designs)
   - Section 6: Tool Infrastructure
   - Skim rest for context

3. **Inspiration Code** (`docs/inspiration/agentic_text2sql.py`)
   - Working reference implementation
   - Study the patterns, don't copy-paste
   - Note: We're simplifying (no hybrid retrieval)

**Optional (but helpful):**
- Story Validation Summary (`docs/STORY-VALIDATION-SUMMARY.md`)
- Implementation Roadmap (`docs/IMPLEMENTATION-ROADMAP.md`)

---

## 🎯 What You're Building

**In Simple Terms:**

Transform this:
```
User query → Claude → SQL → Execute → Display
```

Into this:
```
User query → Clarification Check → Planning Loop:
  [Get Schema → Generate SQL → Execute → Validate → Reflect → Retry if needed]
  → Generate Explanation → Display with Insights
```

**Key Capabilities:**
1. **Clarification:** "Show trends" → Ask "Which time period?"
2. **Reflection:** Bad SQL → Automatic retry
3. **Context:** "Top products in Q3" then "What about Q4?" → Understands
4. **Explanation:** Raw data → "Samsung Galaxy led Q3 with $45K revenue..."

---

## 📋 Implementation Order

### Week 1: Foundation

**Day 1-3: STORY-AGENT-1**
✅ Set up LangGraph infrastructure
✅ Define AgentState (20+ fields)
✅ Create basic workflow (plan → complete)
✅ Test state transitions

**Day 4-5: STORY-AGENT-2 & STORY-AGENT-3**
✅ Add planning node (decision tree)
✅ Create tools (get_schema, execute_sql, validate_results)
✅ Add SQL generation node

**Checkpoint:** Basic flow works: query → get schema → generate SQL → execute → results

### Week 2: Intelligence

**Day 6-7: STORY-AGENT-4**
✅ Add reflection node
✅ Implement retry logic
✅ Test error recovery

**Day 8-9: STORY-AGENT-6**
✅ Add explanation generation
✅ Test explanation quality

**Day 8-10: STORY-AGENT-5**
✅ Add clarification detection (entry point)
✅ Test ambiguity detection

**Checkpoint:** Intelligent flow works with self-correction and insights

### Week 3: Context & UI

**Day 11-12: STORY-AGENT-7**
✅ Session management
✅ Query resolution for follow-ups

**Day 13-15: STORY-AGENT-8**
✅ Frontend components
✅ API integration
✅ End-to-end UI testing

**Checkpoint:** Complete system with conversation and UI

### Week 4: Polish

**Day 16-20:**
✅ Integration testing
✅ Performance tuning
✅ Demo preparation

---

## 🛠️ Development Setup

### Install Dependencies

```bash
cd backend
source venv/bin/activate  # Or venv\Scripts\activate on Windows

# Add to requirements.txt:
echo "langgraph>=0.0.20" >> requirements.txt

pip install langgraph>=0.0.20
```

### Verify Existing Services

```python
# Test existing Claude service
from services.claude_service import ClaudeService

claude = ClaudeService()
sql = claude.generate_sql("Top 10 products", client_id=1)
print(sql)  # Should generate SQL
```

### Create Project Structure

```bash
cd backend/services
touch agentic_text2sql_service.py
touch agent_tools.py

cd ../tests
touch test_agentic_foundation.py
```

---

## 💻 Code Patterns

### Pattern 1: Agent Node Structure

```python
def _node_name(self, state: AgentState) -> Dict:
    """
    Brief description of what this node does.
    
    Architecture Reference: Section X.X
    Performance Target: ≤Xs
    """
    logger.info("Starting node_name...")
    start_time = datetime.now()
    
    try:
        # Extract from state
        field1 = state["field1"]
        field2 = state.get("field2")  # Optional field
        
        # Perform logic
        result = do_something(field1, field2)
        
        # Log success
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"node_name completed in {elapsed:.2f}s")
        
        # Return state updates
        return {
            "field_to_update": result,
            "other_field": value
        }
        
    except Exception as e:
        logger.error(f"node_name failed: {e}", exc_info=True)
        return {
            "error": str(e),
            "is_complete": True  # Optional: stop workflow
        }
```

### Pattern 2: Tool Structure

```python
class Tool:
    """Reusable tool for agent actions"""
    
    def __init__(self, name: str, description: str, function: Callable):
        self.name = name
        self.description = description
        self.function = function
    
    def execute(self, **kwargs) -> Dict:
        """Execute with standardized error handling"""
        logger.info(f"Executing tool: {self.name}")
        
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

### Pattern 3: Conditional Routing

```python
def _should_do_action(self, state: AgentState) -> str:
    """
    Conditional edge function for routing.
    
    Returns:
        String matching edge destination in workflow
    """
    action = state.get("next_action", "")
    
    if action == "option_a":
        return "node_a"
    elif action == "option_b":
        return "node_b"
    else:
        return "default_node"
```

### Pattern 4: Logging Standards

```python
import logging

logger = logging.getLogger(__name__)

# Info: Normal operations
logger.info(f"Processing query: '{query[:100]}'")
logger.info(f"Retrieved {count} items from cache")

# Warning: Issues but continuing
logger.warning(f"Max iterations reached: {iteration}")
logger.warning(f"Query exceeded 10s target: {elapsed:.2f}s")

# Error: Failures
logger.error(f"Tool execution failed: {e}", exc_info=True)
logger.error(f"API timeout: {e}")
```

---

## 🧪 Testing Patterns

### Unit Test Template

```python
import pytest
from services.agentic_text2sql_service import AgenticText2SQLService, AgentState


def test_node_basic_functionality():
    """Test node with valid input"""
    service = AgenticText2SQLService()
    
    state = {
        "user_query": "test query",
        "session_id": "test-123",
        # ... other required fields
    }
    
    result = service._node_name(state)
    
    assert "expected_field" in result
    assert result["expected_field"] is not None


def test_node_error_handling():
    """Test node handles errors gracefully"""
    service = AgenticText2SQLService()
    
    # Create state that will trigger error
    state = {"invalid": "state"}
    
    result = service._node_name(state)
    
    assert "error" in result or result.get("is_complete") == True
```

### Integration Test Template

```python
def test_workflow_end_to_end():
    """Test complete workflow execution"""
    service = AgenticText2SQLService()
    
    result = service.generate_sql_with_agent(
        user_query="Top 10 products by revenue",
        session_id="test-integration-123"
    )
    
    assert result["success"] == True
    assert result["sql"] is not None
    assert result["explanation"] is not None
    assert result["iterations"] >= 1
```

---

## 🎯 Key Implementation Tips

### Tip 1: Start Simple

Don't implement everything at once:
1. Get workflow compiling and running (even if nodes do nothing)
2. Add one node at a time
3. Test each node independently before integration
4. Integrate incrementally

### Tip 2: Follow the Architecture

The architecture document has **complete code examples** for:
- AgentState structure (Section 4.1)
- Every agent node (Section 5.3)
- Tools (Section 6)
- Session management (Section 7)

**Copy these patterns, don't reinvent.**

### Tip 3: Use the Inspiration Code

The `agentic_text2sql.py` file is a **working reference**. When stuck:
1. Find the equivalent section in inspiration code
2. Understand the pattern
3. Adapt (don't copy) to our simplified approach

**Key differences:**
- ❌ No hybrid retrieval (Vector + BM25)
- ✅ Direct schema access
- ✅ Simpler metadata (or skip)

### Tip 4: Log Everything

Good logging = easy debugging:
```python
logger.info(f"Planning iteration {iteration}/{max_iterations}")
logger.info(f"Decision: {next_action}")
logger.info(f"Completed in {elapsed:.2f}s")
```

### Tip 5: Test Incrementally

After each node:
```python
# Quick manual test
service = AgenticText2SQLService()
result = service.generate_sql_with_agent("test query", "test-session")
print(result)
```

---

## ⚠️ Common Pitfalls

### Pitfall 1: Forgetting operator.add

```python
# ❌ WRONG - this won't accumulate
chat_history: List[Dict]

# ✅ RIGHT - this accumulates across nodes
chat_history: Annotated[List[Dict], operator.add]
```

### Pitfall 2: Mutating State Directly

```python
# ❌ WRONG - don't modify state in place
def _node(self, state: AgentState):
    state["field"] = "new value"  # Don't do this!
    return {}

# ✅ RIGHT - return updates
def _node(self, state: AgentState) -> Dict:
    return {"field": "new value"}
```

### Pitfall 3: Missing Error Handling

```python
# ❌ WRONG - errors crash workflow
def _node(self, state: AgentState):
    result = risky_operation()
    return {"field": result}

# ✅ RIGHT - errors handled gracefully
def _node(self, state: AgentState):
    try:
        result = risky_operation()
        return {"field": result}
    except Exception as e:
        logger.error(f"Node failed: {e}")
        return {"error": str(e), "is_complete": True}
```

### Pitfall 4: Infinite Loops

```python
# ❌ WRONG - can loop forever
if should_retry:
    return "retry"

# ✅ RIGHT - max iterations check
if should_retry and iteration < max_iterations:
    return "retry"
else:
    return "complete"
```

---

## 🔍 Debugging Tips

### Tip 1: State Inspection

```python
# Add to nodes during development
logger.info(f"State snapshot: iteration={state['iteration']}, "
            f"schema={'Yes' if state['schema'] else 'No'}, "
            f"sql={'Yes' if state['sql_query'] else 'No'}")
```

### Tip 2: Workflow Visualization

```python
# After building workflow
print(workflow.get_graph().draw_ascii())
```

### Tip 3: Step-by-Step Execution

```python
# Test individual nodes
state = {...}  # Create test state
result = service._plan_node(state)
print(result)
```

### Tip 4: Mock External Calls

```python
# Mock Claude API during testing
from unittest.mock import Mock

service.claude_service.generate_sql = Mock(return_value="SELECT * FROM products")
```

---

## 📊 Performance Targets

**Keep These in Mind:**

| Component | Target Time |
|-----------|-------------|
| detect_clarification | ≤3s |
| get_schema | ≤100ms |
| generate_sql | ≤2s |
| execute_sql | ≤500ms |
| validate_results | ≤100ms |
| reflect | ≤200ms |
| generate_explanation | ≤2s |
| **Total (1 iteration)** | **≤8s** |
| **Max (3 iterations)** | **≤10s** |

**Log if exceeded:**
```python
if elapsed > target_time:
    logger.warning(f"Exceeded {target_time}s target: {elapsed:.2f}s")
```

---

## 🎓 Learning Resources

### LangGraph

- Official Docs: https://langchain-ai.github.io/langgraph/
- Key concepts: StateGraph, nodes, edges, conditional routing
- Focus on: Basic state machines (don't need advanced features)

### Our Codebase

- **Start:** `backend/services/claude_service.py` (existing, understand this first)
- **Study:** `docs/inspiration/agentic_text2sql.py` (working reference)
- **Follow:** Architecture document sections 4-6

---

## ✅ Pre-Implementation Checklist

Before writing code:

- [ ] Read product brief (understand the "why")
- [ ] Read architecture sections 4-6 (understand the "how")
- [ ] Review inspiration code (understand the patterns)
- [ ] Verify existing services work (Claude, DB, QueryExecutor)
- [ ] Install LangGraph dependency
- [ ] Set up test file structure
- [ ] Choose Story 1 to start

---

## 🚦 Ready to Code?

### Your First Task: STORY-AGENT-1

**Goal:** Get basic workflow running

**Steps:**
1. Open `docs/sprint_artifacts/story-agent-1-langgraph-foundation.md`
2. Create `backend/services/agentic_text2sql_service.py`
3. Copy AgentState structure from architecture Section 4.1
4. Create basic workflow with 2 nodes (plan, complete)
5. Test: `workflow.invoke(initial_state)` returns final_state

**Success:** Workflow compiles and executes without errors

**Time estimate:** Day 1 (setup) + Days 2-3 (implementation + testing)

---

## 💬 Need Help?

### Quick References

**"How do I...?"**
- ...define AgentState? → Architecture Section 4.1
- ...create a node? → Architecture Section 5.3 + Pattern 1 above
- ...add a tool? → Architecture Section 6 + Pattern 2 above
- ...handle errors? → Pattern 1 try/except + STORY-VALIDATION-SUMMARY.md
- ...add logging? → Pattern 4 above
- ...test my code? → Testing Patterns section above

### Document Index

- **Product Brief:** docs/product-brief-agentic-text2sql-enhancement.md
- **Architecture:** docs/architecture-agentic-text2sql.md ⭐
- **Stories:** docs/sprint_artifacts/story-agent-*.md
- **Validation:** docs/STORY-VALIDATION-SUMMARY.md
- **Roadmap:** docs/IMPLEMENTATION-ROADMAP.md
- **Inspiration:** docs/inspiration/agentic_text2sql.py

---

## 🎉 You're Ready!

You have:
- ✅ Complete architecture
- ✅ Detailed stories
- ✅ Code patterns
- ✅ Testing strategies
- ✅ Working reference code
- ✅ Performance targets
- ✅ Common pitfalls documented

**Start with Story 1 and build incrementally. You've got this!** 🏗️

---

**Document Status:** ✅ Ready for Development

**Architect:** Winston  
**Date:** 2025-11-27  
**Version:** 1.0

---

*This guide is your companion throughout implementation. Refer back frequently as you progress through the stories.*


