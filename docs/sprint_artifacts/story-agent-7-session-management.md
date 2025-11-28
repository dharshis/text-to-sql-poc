# Story: Session Management & Conversation Context

**Story ID:** STORY-AGENT-7  
**Epic:** EPIC-AGENTIC-001 (Agentic Text-to-SQL Enhancement)  
**Priority:** Must Have  
**Status:** Ready for Development  
**Estimate:** 2 days  
**Dependencies:** STORY-AGENT-1  

---

## User Story

**As a** market researcher  
**I want** to ask follow-up questions that reference previous queries  
**So that** I can explore data conversationally without repeating context

---

## Description

Implement session management and conversation context handling that allows the system to maintain memory across queries. Users can ask follow-up questions like "What about Q4?" or "Show me by region" and the system understands the context from previous queries.

This enables natural conversational data exploration.

---

## Acceptance Criteria

### Must Have

1. **Session Storage Implemented**
   - [ ] In-memory dictionary for POC: `chat_sessions = {}`
   - [ ] Structure: `{session_id: [query_history]}`
   - [ ] Each entry: `{user_query, resolved_query, sql, results_summary, timestamp}`
   - [ ] Methods: `_get_chat_history(session_id)`, `_add_to_history(session_id, entry)`
   - [ ] Keep last 5-10 queries per session

2. **Query Resolution with History**
   - [ ] `_resolve_query_with_history(user_query, chat_history)` method
   - [ ] Detects follow-up queries (keywords: "what about", "show me", "that", "this", "same but")
   - [ ] Uses Claude to resolve follow-ups into standalone queries
   - [ ] Examples:
     - "Top 10 products in Q3" → [stores context]
     - "What about Q4?" → resolved to "Top 10 products in Q4"
     - "Show me by region" → resolved to "Top 10 products in Q3 by region"

3. **Context Resolution Prompt**
   - [ ] System prompt: "You are a query resolution assistant"
   - [ ] Includes last 2-3 queries from history
   - [ ] Instructions: resolve follow-ups into standalone queries
   - [ ] If not a follow-up, return unchanged
   - [ ] Output: resolved standalone query

4. **Integration with Workflow**
   - [ ] Session management in AgenticText2SQLService.__init__
   - [ ] Get history at start of generate_sql_with_agent
   - [ ] Resolve query before initializing state
   - [ ] Store resolved_query in state
   - [ ] Add to history after successful generation
   - [ ] Display context indicator in response

5. **Session Lifecycle**
   - [ ] Session created on first query with session_id
   - [ ] Session persists across queries (in-memory for POC)
   - [ ] Session expires after server restart (acceptable for POC)
   - [ ] No cleanup needed (limited to demo scenarios)

### Nice to Have

- [ ] Session persistence (Redis, database)
- [ ] Session expiry logic (TTL)
- [ ] Session cleanup
- [ ] Multi-user session isolation (authentication)

### Architecture Validation

- [ ] In-memory storage structure matches Architecture Section 7.1
- [ ] Query resolution for follow-ups works (Section 7.2)
- [ ] History retention: last 10 queries
- [ ] Session lifecycle documented
- [ ] Production path noted (Redis upgrade, Section 7.3)

---

## Architecture References

**See Architecture Document:** `docs/architecture-agentic-text2sql.md`
- **Section 7.1:** Session Architecture (in-memory storage)
- **Section 7.2:** Query Resolution (follow-up detection)
- **Section 7.3:** Production Path (Redis upgrade)

**Session Structure (Architecture Section 7.1):**
```python
{
    "session-id": [
        {
            "user_query": "original query",
            "resolved_query": "standalone query",
            "sql": "SELECT...",
            "results_summary": "10 rows, columns: ...",
            "timestamp": "ISO-8601"
        }
    ]
}
```

**Follow-up Keywords:** "what about", "show me", "that", "this", "same but"

**Retention:** Last 10 queries per session (Architecture Section 7.1)

---

## Technical Implementation

### Files to Modify

```
backend/services/agentic_text2sql_service.py (add session management)
```

### Key Code Structure

```python
# backend/services/agentic_text2sql_service.py

class AgenticText2SQLService:
    """Agentic Text2SQL with conversation context"""
    
    def __init__(self):
        self.claude_service = ClaudeService()
        self.db_manager = DBManager()
        self.tools = self._initialize_tools()
        self.workflow = self._build_workflow()
        
        # Session storage (in-memory for POC)
        self.chat_sessions = {}  # NEW
    
    def generate_sql_with_agent(
        self,
        user_query: str,
        session_id: str,
        max_iterations: int = 3
    ) -> Dict:
        """Generate SQL using agentic approach with conversation context"""
        
        logger.info(f"Processing query: '{user_query}', session: {session_id}")
        
        # Get conversation history
        chat_history = self._get_chat_history(session_id)
        logger.info(f"Retrieved {len(chat_history)} previous queries from session")
        
        # Resolve query with history
        resolved_query = self._resolve_query_with_history(user_query, chat_history)
        is_followup = resolved_query != user_query
        
        if is_followup:
            logger.info(f"Follow-up detected. Resolved: '{resolved_query}'")
        
        # Initialize agent state
        initial_state: AgentState = {
            "user_query": user_query,
            "session_id": session_id,
            "resolved_query": resolved_query,  # Use resolved query
            "chat_history": chat_history,
            # ... other fields
        }
        
        # Run workflow
        final_state = self.workflow.invoke(initial_state)
        
        # Add to history if SQL was generated successfully
        if final_state.get("sql_query") and not final_state.get("clarification_needed"):
            self._add_to_history(session_id, {
                "user_query": user_query,
                "resolved_query": resolved_query,
                "sql": final_state["sql_query"],
                "results_summary": self._summarize_results(final_state.get("execution_result")),
                "timestamp": datetime.now().isoformat()
            })
        
        # Format response
        response = self._format_response(final_state)
        
        # Add context indicator if follow-up
        if is_followup:
            response["resolved_query"] = resolved_query
            response["is_followup"] = True
        
        return response
    
    def _get_chat_history(self, session_id: str) -> List[Dict]:
        """Retrieve conversation history for a session"""
        return self.chat_sessions.get(session_id, [])
    
    def _add_to_history(self, session_id: str, entry: Dict):
        """Add entry to conversation history"""
        if session_id not in self.chat_sessions:
            self.chat_sessions[session_id] = []
        
        self.chat_sessions[session_id].append(entry)
        
        # Keep only last 10 exchanges
        if len(self.chat_sessions[session_id]) > 10:
            self.chat_sessions[session_id] = self.chat_sessions[session_id][-10:]
        
        logger.info(f"Added to session {session_id}. Total queries: {len(self.chat_sessions[session_id])}")
    
    def _resolve_query_with_history(self, user_query: str, chat_history: List[Dict]) -> str:
        """Resolve follow-up queries using conversation history"""
        
        if not chat_history:
            return user_query  # No history, use as-is
        
        # Build history context
        history_str = "\n".join([
            f"Q: {entry.get('user_query', '')}\nSQL: {entry.get('sql', '')}"
            for entry in chat_history[-3:]  # Last 3 exchanges
        ])
        
        resolve_prompt = f"""Given this conversation history:

{history_str}

User's new query: {user_query}

If this is a follow-up query that references previous context (e.g., "what about...", "show me more", "filter that by...", "what about Q4?", "by region"),
rewrite it as a standalone query that includes all necessary context.

If it's already a standalone query, return it unchanged.

Return ONLY the resolved query, nothing else."""
        
        try:
            resolved = self.claude_service.client.messages.create(
                model=self.claude_service.model,
                max_tokens=200,
                system="You are a query resolution assistant. Resolve follow-up queries into standalone queries.",
                messages=[{"role": "user", "content": resolve_prompt}]
            )
            
            resolved_query = resolved.content[0].text.strip()
            logger.info(f"Query resolution: '{user_query}' → '{resolved_query}'")
            
            return resolved_query
            
        except Exception as e:
            logger.error(f"Query resolution failed: {e}")
            return user_query  # Fallback to original
    
    def _summarize_results(self, execution_result: Optional[Dict]) -> str:
        """Create brief summary of results for history"""
        if not execution_result or not execution_result.get("success"):
            return "No results"
        
        row_count = len(execution_result.get("data", []))
        columns = execution_result.get("columns", [])
        
        return f"{row_count} rows, columns: {', '.join(columns[:3])}"
```

### Testing Strategy

**Unit Tests:**
```python
# backend/tests/test_session_management.py

def test_get_empty_history():
    """Test getting history for new session"""
    service = AgenticText2SQLService()
    
    history = service._get_chat_history("new-session")
    
    assert history == []

def test_add_to_history():
    """Test adding query to history"""
    service = AgenticText2SQLService()
    
    entry = {
        "user_query": "test query",
        "sql": "SELECT * FROM products",
        "timestamp": "2024-01-01T00:00:00"
    }
    
    service._add_to_history("test-session", entry)
    history = service._get_chat_history("test-session")
    
    assert len(history) == 1
    assert history[0]["user_query"] == "test query"

def test_history_limit():
    """Test history keeps only last 10 queries"""
    service = AgenticText2SQLService()
    
    # Add 15 queries
    for i in range(15):
        service._add_to_history("test", {"query": f"query-{i}"})
    
    history = service._get_chat_history("test")
    
    assert len(history) == 10  # Limited to 10
    assert history[0]["query"] == "query-5"  # Oldest kept

def test_resolve_query_standalone():
    """Test standalone query unchanged"""
    service = AgenticText2SQLService()
    
    resolved = service._resolve_query_with_history(
        "Top 10 products by revenue",
        []
    )
    
    assert resolved == "Top 10 products by revenue"

def test_resolve_query_followup():
    """Test follow-up query resolved"""
    service = AgenticText2SQLService()
    
    history = [{
        "user_query": "Top 10 products in Q3",
        "sql": "SELECT..."
    }]
    
    resolved = service._resolve_query_with_history(
        "What about Q4?",
        history
    )
    
    assert "Q4" in resolved
    assert "products" in resolved
    # Should be standalone

def test_workflow_with_followup():
    """Integration: workflow handles follow-up query"""
    service = AgenticText2SQLService()
    
    # First query
    result1 = service.generate_sql_with_agent(
        "Top 10 products in Q3",
        session_id="test-123"
    )
    
    # Follow-up query
    result2 = service.generate_sql_with_agent(
        "What about Q4?",
        session_id="test-123"
    )
    
    assert result2.get("is_followup") == True
    assert result2.get("resolved_query") is not None
    assert "Q4" in result2["resolved_query"]
```

---

## Dependencies

### Prerequisites
- STORY-AGENT-1 complete (foundation)
- ClaudeService functional

---

## Definition of Done

### Code Complete
- [ ] Session storage implemented
- [ ] History management methods working
- [ ] Query resolution logic working
- [ ] Integration with workflow complete

### Tests Pass
- [ ] Unit tests for session management
- [ ] Unit tests for query resolution
- [ ] Integration test: follow-up queries work
- [ ] All tests passing

### Documentation
- [ ] Session management documented
- [ ] Query resolution logic documented
- [ ] Example follow-up scenarios documented

### Review
- [ ] Code reviewed by peer

---

## Notes & Considerations

**Session Design:**
- In-memory is fine for POC (single server, demo only)
- Production would need Redis or database
- Session isolation not critical for demo

**Query Resolution:**
- Claude is good at understanding context
- Should work for most common follow-up patterns
- May need tuning for edge cases

**Demo Value:**
- Showcases conversational intelligence
- Natural UX for data exploration
- Clear differentiation from static tools

---

**Story Status:** ✅ Ready for Development

