# Story 7.1: Follow-up Detection & Query Resolution

**Story ID:** STORY-AGENT-7.1  
**Epic:** EPIC-AGENTIC-001 (Agentic Text-to-SQL Enhancement)  
**Priority:** Must Have  
**Status:** Ready for Development  
**Estimate:** 2 days  
**Dependencies:** STORY-AGENT-1, STORY-AGENT-6  

---

## User Story

**As a** market researcher  
**I want** the system to detect when I'm asking a follow-up question  
**So that** I don't have to repeat context from my previous query

---

## Description

Implement the core intelligence for detecting follow-up questions and resolving them into complete, standalone queries using Claude. This is the foundational backend work that enables conversational analytics.

**Example:**
```
User: "Top products by revenue"
User: "What about Q4?"
System: Detects follow-up → Resolves to "Top products by revenue in Q4"
```

---

## Acceptance Criteria

### AC1: Follow-up Detection Method

- [ ] Create `_detect_followup()` method in `AgenticText2SQLService`
- [ ] **Input:** `user_query: str`, `chat_history: List[Dict]`
- [ ] **Output:** `(is_followup: bool, confidence: float)`
- [ ] Detection logic:
  ```python
  # Keyword patterns
  followup_keywords = [
      "what about", "show me", "same but", "also show",
      "compare", "versus", "by", "for", "in", "only",
      "just", "filter", "more", "less", "that", "it",
      "them", "this", "these", "previous", "last", "next"
  ]
  
  # Scoring rules:
  # - Has keywords + short query (≤4 words) + no entity = 0.9 confidence
  # - Has keywords only = 0.7 confidence
  # - Short + no entity = 0.6 confidence
  # - Otherwise = not follow-up
  ```
- [ ] If no history exists → always return `False, 1.0`
- [ ] Log detection decision with reasoning

**Test Cases:**
```python
# Should detect as follow-up (True)
"What about Q4?" → (True, 0.9)
"Show me by region" → (True, 0.7)
"Same but for electronics" → (True, 0.9)
"Compare to Q3" → (True, 0.8)
"That" → (True, 0.6)

# Should NOT detect as follow-up (False)
"Top products by revenue" → (False, 0.8)
"Show me all clients" → (False, 0.8)
```

---

### AC2: Query Resolution with Claude

- [ ] Create `_resolve_query_with_history()` method in `AgenticText2SQLService`
- [ ] **Input:** `user_query: str`, `chat_history: List[Dict]`
- [ ] **Output:** Dict with:
  ```python
  {
      "resolved_query": str,        # Complete standalone query
      "confidence": float,           # 0-1
      "is_followup": bool,
      "interpretation": str,         # Human-readable explanation
      "entities_inherited": Dict     # What was inherited from history
  }
  ```
- [ ] Use last 2-3 queries from history for context
- [ ] Claude prompt structure:
  ```
  Previous conversation context:
  1. Query: "Top products by revenue"
     Resolved to: "Top 5 products by revenue for all time"
     Context: {dimensions: ["product"], metrics: ["revenue"]}
  
  New user query: "What about Q4?"
  
  Task: Resolve into complete standalone query
  - Inherit relevant context
  - Resolve pronouns
  - Expand implicit references
  
  Respond in JSON: {resolved_query, confidence, is_followup, interpretation, entities_inherited}
  ```
- [ ] Temperature: 0.3 (consistent, precise)
- [ ] Max tokens: 500
- [ ] Handle JSON parse errors → fallback to original query
- [ ] Performance target: ≤2s

**Test Cases:**
```python
History: ["Top products by revenue"]
Query: "What about Q4?" 
→ resolved_query: "Top products by revenue in Q4"

History: ["Sales by product"]
Query: "Show me by region"
→ resolved_query: "Sales by product grouped by region"

History: ["Revenue by category"]
Query: "Compare to last year"
→ resolved_query: "Revenue by category compared to last year"
```

---

### AC3: Integration with Workflow

- [ ] Update `generate_sql_with_agent()` method:
  ```python
  def generate_sql_with_agent(...):
      # 1. Get chat history
      chat_history = self._get_chat_history(session_id)
      
      # 2. Detect if follow-up
      is_followup, confidence = self._detect_followup(user_query, chat_history)
      
      # 3. Resolve query if needed
      if is_followup:
          resolution = self._resolve_query_with_history(user_query, chat_history)
          resolved_query = resolution['resolved_query']
          
          # Low confidence → could trigger clarification (future)
          if resolution['confidence'] < 0.8:
              logger.warning(f"Low confidence: {resolution['confidence']}")
      else:
          resolved_query = user_query
          resolution = None
      
      # 4. Initialize state with resolution info
      initial_state = {
          "user_query": user_query,
          "resolved_query": resolved_query,
          "is_followup": is_followup,
          "resolution_info": resolution,
          # ... rest of state
      }
      
      # 5. Run workflow
      final_state = self.workflow.invoke(initial_state)
      
      # 6. Format response with follow-up info
      response = self._format_response(final_state)
      response["is_followup"] = is_followup
      if resolution:
          response["resolution_info"] = {
              "interpreted_as": resolution['resolved_query'],
              "confidence": resolution['confidence']
          }
      
      return response
  ```
- [ ] Update `AgentState` TypedDict to include:
  - `is_followup: bool`
  - `resolution_info: Optional[Dict]`
- [ ] Pass `is_followup` flag in API response

---

### AC4: Logging & Observability

- [ ] Log follow-up detection:
  ```python
  logger.info(f"Follow-up detected: '{user_query}' (confidence: {confidence})")
  ```
- [ ] Log resolution:
  ```python
  logger.info(f"Query resolved: '{user_query}' → '{resolved_query}' (confidence: {resolution_confidence})")
  ```
- [ ] Log low confidence warnings:
  ```python
  logger.warning(f"Low resolution confidence: {resolution_confidence}, may need clarification")
  ```
- [ ] Include resolution details in error logs if workflow fails

---

## Technical Notes

### Files to Modify

**Backend:**
- `backend/services/agentic_text2sql_service.py`:
  - Add `_detect_followup()` method
  - Add `_resolve_query_with_history()` method
  - Modify `generate_sql_with_agent()` to integrate resolution
  - Update `AgentState` TypedDict

### Performance Targets

- Follow-up detection: <100ms (local logic)
- Query resolution: ≤2s (Claude API call)
- Total overhead: ≤2.5s for follow-up queries

### Error Handling

- If Claude API fails → return original query with confidence 0.5
- If JSON parsing fails → return original query with confidence 0.5
- Log all failures with full context

---

## Testing

### Manual Test Cases

**Test 1: Time Period Follow-ups**
```
1. Query: "Top products by revenue"
   → is_followup: False
   
2. Query: "What about Q4?"
   → is_followup: True, confidence: 0.9
   → resolved: "Top products by revenue in Q4"
   
3. Query: "And Q3?"
   → is_followup: True, confidence: 0.8
   → resolved: "Top products by revenue in Q3"
```

**Test 2: Dimension Changes**
```
1. Query: "Sales by product"
   → is_followup: False
   
2. Query: "Show me by region"
   → is_followup: True, confidence: 0.7
   → resolved: "Sales by product grouped by region"
```

**Test 3: Filtering**
```
1. Query: "Show all sales"
   → is_followup: False
   
2. Query: "Only electronics"
   → is_followup: True, confidence: 0.9
   → resolved: "Show sales for electronics category only"
```

**Test 4: Pronouns**
```
1. Query: "Top 5 products by revenue"
   → is_followup: False
   
2. Query: "Show me that by region"
   → is_followup: True, confidence: 0.8
   → resolved: "Top 5 products by revenue grouped by region"
```

**Test 5: Not a Follow-up**
```
1. Query: "Top products"
   → is_followup: False
   
2. Query: "Show me all clients"
   → is_followup: False (topic change, has entity)
```

### Unit Tests

Create `backend/tests/test_followup_detection.py`:
```python
def test_detect_followup_with_keywords():
    """Test keyword-based detection"""
    # Test implementation
    
def test_detect_followup_short_query():
    """Test short query detection"""
    
def test_not_followup_has_entity():
    """Test queries with entities are not flagged"""
    
def test_resolve_time_period():
    """Test resolving time period changes"""
    
def test_resolve_dimension():
    """Test resolving dimension changes"""
    
def test_resolve_with_pronoun():
    """Test pronoun resolution"""
```

---

## Definition of Done

- [ ] `_detect_followup()` method implemented and tested
- [ ] `_resolve_query_with_history()` method implemented and tested
- [ ] Integration with `generate_sql_with_agent()` complete
- [ ] `AgentState` updated with new fields
- [ ] API response includes `is_followup` and `resolution_info`
- [ ] All 5 manual test cases pass
- [ ] Logging added for all resolution steps
- [ ] Performance targets met (<2.5s overhead)
- [ ] Error handling covers all failure modes
- [ ] Code reviewed and follows standards
- [ ] No linter errors
- [ ] Documentation updated

---

## Success Metrics

After deployment, track:
- **Detection accuracy**: % of true follow-ups correctly identified (target: >85%)
- **False positive rate**: % of non-follow-ups incorrectly flagged (target: <10%)
- **Resolution accuracy**: % of follow-ups correctly resolved (target: >80%)
- **Resolution time**: Average time for Claude resolution (target: <2s)

---

**Story Status:** ✅ Ready for Development  
**Assigned To:** Dev Agent  
**Started:** TBD  
**Completed:** TBD


