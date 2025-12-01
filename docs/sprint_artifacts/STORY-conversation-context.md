# User Story: Conversation Context for Follow-Up Queries

**Story ID:** STORY-001
**Feature:** Conversation Memory
**Priority:** High
**Estimate:** 3 points

---

## User Story

**As a** business analyst using the text-to-SQL application
**I want** my follow-up queries to remember the context from previous queries in the same session
**So that** I can drill down into data without repeating filters each time

---

## Background

Currently, when users ask follow-up questions like "break it down by month" after querying "show market trend in 2024", the system returns ALL monthly data (2020-present) instead of just 2024 data. This breaks the natural conversation flow and forces users to repeat filters.

**Current State:**
- Frontend stores conversation history in React state
- Backend stores session history in memory (`self.chat_sessions`)
- Session history is NOT passed to Claude when generating SQL
- Each query is treated independently without context

**Desired State:**
- Follow-up queries inherit filters from previous queries
- Context window of last 5 queries passed to Claude
- Natural drill-down conversations without filter repetition

---

## Acceptance Criteria

### AC1: Context Formatting
**Given** a session with previous query history
**When** the system prepares to generate SQL for a new query
**Then** it should format the last 5 queries into structured context including:
- User's original query
- Resolved/interpreted query
- Key filters applied (dimensions, metrics, time)
- Results summary

### AC2: Context Injection
**Given** formatted conversation context exists
**When** calling Claude API to generate SQL
**Then** the context should be appended to the system prompt
**And** a log message should confirm context was added

### AC3: Basic Context Inheritance
**Given** Query 1: "Show me the market trend in 2024"
**When** Query 2 is submitted: "Break it down by month"
**Then** the generated SQL should filter to `fiscal_year = 2024`
**And** should NOT include data from 2020-2023

### AC4: Multi-Level Drilldown
**Given** a sequence of queries:
1. "Show sales for AB InBev in 2023"
2. "By quarter"
3. "Just Q1"
4. "By month"
5. "Show top brands"

**Then**:
- All queries maintain corp_id filter for AB InBev
- Queries 2-5 maintain fiscal_year=2023
- Queries 3-5 filter to Q1 2023

### AC5: Explicit Context Override
**Given** Query 1: "Market trend in 2024"
**When** Query 2 explicitly overrides: "Show me 2023 instead"
**Then** the generated SQL should use fiscal_year = 2023
**And** should ignore the previous 2024 filter

### AC6: Clear Conversation Resets Context
**Given** Query 1: "Show 2024 data"
**When** user clicks "Clear Conversation"
**And** submits Query 2: "By month"
**Then** Query 2 should NOT have 2024 context
**And** should either ask for clarification or default to all available years

### AC7: Context Window Limit
**Given** a session with 7 previous queries
**When** preparing context for Query 8
**Then** only queries 3-7 (last 5) should be included in context
**And** queries 1-2 should be excluded

### AC8: Performance
**Given** any query with conversation context
**When** measuring end-to-end query time
**Then** context formatting should add < 200ms
**And** total latency increase should be < 500ms

---

## Technical Implementation

### Files to Modify

1. **`backend/services/agentic_text2sql_service.py`**
   - Add `_format_conversation_context()` method (after line 136)
   - Update `_generate_sql_node()` to retrieve and pass context (lines 890-916)
   - Verify `session_id` in initial_state (line ~1340)

2. **`backend/services/claude_service.py`**
   - Add `conversation_context` parameter to `generate_sql()` (line 215)
   - Inject context into system prompt (lines 248-276)

### Key Design Decisions

- **Context Window:** Last 5 queries (matches typical user workflow)
- **Token Cost:** ~750 tokens per request (5 queries × 150 tokens)
- **Storage:** Use existing in-memory `self.chat_sessions` dictionary
- **Format:** Structured markdown with clear sections for each query

---

## Test Scenarios

### Scenario 1: Basic Drill-Down
```
User: "Show me the market trend in 2024"
Assistant: [Returns 2024 data with trend chart]

User: "Break it down by month"
Assistant: [Returns monthly breakdown for 2024 ONLY]
```

### Scenario 2: Entity Context
```
User: "Sales for AB InBev in 2023"
Assistant: [Returns AB InBev sales for 2023]

User: "By quarter"
Assistant: [Returns quarterly breakdown for AB InBev in 2023]

User: "Top performing brands"
Assistant: [Returns top brands within AB InBev portfolio for 2023]
```

### Scenario 3: Override Previous Filter
```
User: "Market data for 2024"
Assistant: [Returns 2024 market data]

User: "Actually, show me 2023"
Assistant: [Returns 2023 data, ignoring previous 2024 filter]
```

---

## Definition of Done

- [ ] `_format_conversation_context()` method implemented and tested
- [ ] `_generate_sql_node()` retrieves and passes conversation context
- [ ] `claude_service.generate_sql()` accepts and injects context
- [ ] All 8 acceptance criteria pass
- [ ] Unit tests added for context formatting
- [ ] Integration test confirms end-to-end context flow
- [ ] Performance benchmark shows < 500ms latency increase
- [ ] Code reviewed and merged
- [ ] Backend restarted and deployed

---

## Non-Functional Requirements

### Performance
- Context formatting: < 200ms
- Total latency increase: < 500ms
- Token overhead: ~750 tokens per request (acceptable)

### Scalability
- In-memory storage sufficient for POC
- Consider Redis for production multi-instance deployments

### Maintainability
- Clear separation: format context → pass to Claude → inject into prompt
- Configurable context window size (`max_entries=5`)
- Easy rollback: set `max_entries=0` to disable

---

## Dependencies

- Existing session management infrastructure (already implemented)
- `chat_sessions` dictionary with history storage
- Claude API access with sufficient token quota

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Token cost increase | Medium | Monitor usage; acceptable for 5-query window |
| Context confuses Claude | High | Clear formatting with "IMPORTANT" instruction |
| Performance degradation | Medium | Benchmark and optimize formatting logic |
| Memory growth over time | Low | Existing 10-query limit per session prevents unbounded growth |

---

## Future Enhancements

- **Smart Context Pruning:** Only include queries with relevant entities
- **Persistent Storage:** Move from in-memory to Redis for production
- **Context Summarization:** Compress older queries to save tokens
- **User Control:** Allow users to manually exclude specific queries from context
