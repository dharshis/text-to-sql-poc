# Story: Enhanced Session Memory with Context-Aware Follow-ups

**Story ID:** STORY-AGENT-7-ENHANCED  
**Epic:** EPIC-AGENTIC-001 (Agentic Text-to-SQL Enhancement)  
**Priority:** Must Have  
**Status:** Ready for Development  
**Estimate:** 1 week (5 days)  
**Dependencies:** STORY-AGENT-1, STORY-AGENT-6, STORY-AGENT-8  

---

## User Story

**As a** market researcher or data analyst  
**I want** to have natural conversations with the system using follow-up questions  
**So that** I can explore data efficiently without repeating context, enabling progressive refinement, exploratory analysis, and comparative insights

---

## Description

Implement comprehensive session memory that enables **context-aware conversational analytics**. The system will intelligently understand follow-up questions like "What about Q4?", "Show me by region", or "Compare to last year" by maintaining conversation context and resolving implicit references.

This transforms the tool from a single-query interface into an intelligent analytics assistant that remembers your conversation and helps you explore data naturally.

### Key Capabilities

1. **Context-Aware Intelligence** - Understands pronouns, implicit references, and relative terms
2. **All Scenario Support** - Handles exploratory, refinement, and comparative analysis patterns
3. **Analyst-Focused UI** - Professional dashboard with collapsible conversation history
4. **Smart Clarification** - Asks for clarification only when truly ambiguous
5. **Query Suggestions** - Proposes relevant follow-up questions

---

## Target User Scenarios

### Scenario A: Exploratory Analysis
```
User: "Show me top products by revenue"
      [sees Le Creuset is #1]
User: "What about Q4 specifically?"
      [system resolves: "Top products by revenue in Q4"]
User: "Compare that to Q3"
      [system resolves: "Top products by revenue Q4 vs Q3"]
User: "Show me by region"
      [system resolves: "Top products by revenue in Q4 by region"]
```

### Scenario B: Progressive Refinement
```
User: "Show me all sales"
User: "Just electronics"
      [system adds filter: category='electronics']
User: "Only in North region"
      [system adds filter: region='North']
User: "Last 6 months"
      [system adds filter: date >= 6 months ago]
```

### Scenario C: Comparative Analysis
```
User: "Revenue by product category"
User: "Same thing but for last year"
      [system changes time period]
User: "Show me the difference"
      [system generates year-over-year comparison]
```

---

## Acceptance Criteria

### Phase 1: Core Follow-up Resolution (Week 1 - Must Have)

#### AC1: Follow-up Detection
- [ ] **`_detect_followup()` method** in agentic service
- [ ] Detects keyword patterns: "what about", "show me", "same but", "also", "compare"
- [ ] Detects pronouns: "it", "that", "them", "this", "these"
- [ ] Detects implicit references: "Q4", "by region", "electronics"
- [ ] Detects relative terms: "previous", "next", "last", "more"
- [ ] Returns `is_followup: bool` and `confidence: float`
- [ ] Logs detection decision with reasoning

#### AC2: Query Resolution with Claude
- [ ] **`_resolve_query_with_history()` method** in agentic service
- [ ] Takes: `user_query`, `chat_history` (last 3 queries)
- [ ] Sends to Claude with structured prompt (see Technical Details)
- [ ] Claude returns: `resolved_query`, `confidence`, `entities_extracted`
- [ ] If confidence < 80%: triggers clarification
- [ ] If confidence >= 80%: proceeds with resolved query
- [ ] Logs resolution: original → resolved query
- [ ] Performance target: ≤2s for resolution

#### AC3: Enhanced History Storage
- [ ] Update history structure to include:
  ```python
  {
      "user_query": str,
      "resolved_query": str,
      "sql": str,
      "results_summary": str,
      "key_entities": {
          "dimensions": List[str],      # e.g., ["product", "region"]
          "metrics": List[str],          # e.g., ["revenue", "quantity"]
          "filters": List[Dict],         # e.g., [{"client_id": 1}]
          "time_period": str,            # e.g., "Q4 2024", "all time"
          "grouping": List[str],         # e.g., ["product_name"]
          "limit": int                   # e.g., 5
      },
      "timestamp": str,
      "iteration": int,
      "is_followup": bool
  }
  ```
- [ ] Keep last 10 queries per session
- [ ] Use last 2-3 for resolution context

#### AC4: Workflow Integration
- [ ] Modify `generate_sql_with_agent()` to:
  1. Get chat history
  2. Detect if follow-up
  3. Resolve query if needed
  4. Pass resolved_query + is_followup to state
  5. Add to history after successful execution
- [ ] Update `AgentState` with `is_followup: bool`
- [ ] Pass `is_followup` flag in API response

#### AC5: Basic Frontend Display
- [ ] **Enhanced ContextBadge** shows follow-up indicator
- [ ] When `is_followup=true`:
  - Display: "Following up on: [previous query]"
  - Show [×] button to clear context
- [ ] Clicking [×] creates new session ID
- [ ] Badge auto-hides if not a follow-up

### Phase 2: Conversation UI (Week 1 - Must Have)

#### AC6: Conversation History Panel
- [ ] Create **`ConversationPanel.jsx`** component
- [ ] Slide-out panel from right side (300px wide)
- [ ] Triggered by button in top-right: `[💬 History ({count})]`
- [ ] Shows last 10 queries in reverse chronological order
- [ ] Each query item displays:
  - 🔍 Query text (truncated to 50 chars)
  - ↪️ Indentation if follow-up
  - ✅ Result count / ⚠️ Error indicator
  - Timestamp (relative: "3 min ago", "Just now")
  - ⚡ Current query highlight
- [ ] Click query to view its results (nice-to-have for Phase 2)
- [ ] "Clear Conversation" button at bottom
- [ ] Keyboard shortcut: Cmd/Ctrl + H

#### AC7: Query Resolution Indicator
- [ ] Create **`ResolutionIndicator.jsx`** component
- [ ] Shows after follow-up is resolved:
  ```
  🤖 I understood: "Top 5 products by revenue in Q4"
  [✓ Correct] [⚠️ Let me clarify]
  ```
- [ ] Auto-dismisses after 5 seconds
- [ ] [✓ Correct] button: hides immediately
- [ ] [⚠️ Let me clarify] button: opens clarification dialog with pre-filled context
- [ ] Fades in/out smoothly

### Phase 3: Smart Features (Week 2 - Should Have)

#### AC8: Query Suggestions
- [ ] After results displayed, show suggested follow-ups
- [ ] Generate 3-4 suggestions based on:
  - Current query context
  - Available data dimensions
  - Common analyst patterns
- [ ] Examples:
  - "What about Q3?"
  - "Show me by region"
  - "Compare to last year"
  - "Filter for electronics"
- [ ] Click suggestion fills search bar
- [ ] Position below results (collapsible)

#### AC9: Topic Change Detection
- [ ] Detect when user changes topics completely
- [ ] Use Claude to check: "Is query related to previous context?"
- [ ] If unrelated: automatically soft-reset context
- [ ] Log: "Topic change detected, starting new thread"
- [ ] Keep session ID but mark as new conversation thread

#### AC10: Clarification Intelligence
- [ ] Enhanced clarification dialog for ambiguous follow-ups
- [ ] When confidence < 80%, show multiple interpretations:
  ```
  💬 Need More Information
  
  I'm not sure what you mean by "Show me more"
  
  Did you mean:
  1. More products (show top 10 instead of 5)?
  2. More details (add columns)?
  3. More time periods (add monthly breakdown)?
  
  [Your clarification...] [Submit]
  ```
- [ ] User's clarification gets appended to query
- [ ] Retry resolution with clarification

---

## Technical Implementation

### Backend Changes

#### File: `backend/services/agentic_text2sql_service.py`

**New Methods:**

```python
def _detect_followup(self, user_query: str, chat_history: List[Dict]) -> Tuple[bool, float]:
    """
    Detect if query is a follow-up using keyword and context analysis.
    
    Returns:
        (is_followup, confidence) - bool and float 0-1
    """
    query_lower = user_query.lower()
    
    # No history = not a follow-up
    if not chat_history:
        return False, 1.0
    
    # Keyword patterns
    followup_keywords = [
        "what about", "show me", "same but", "also show",
        "compare", "versus", "by", "for", "in", "only",
        "just", "filter", "more", "less", "that", "it",
        "them", "this", "these", "previous", "last", "next"
    ]
    
    # Check for keywords
    has_keywords = any(kw in query_lower for kw in followup_keywords)
    
    # Check for very short queries (likely follow-ups)
    is_short = len(user_query.split()) <= 4
    
    # Check for incomplete queries (no main entity)
    has_entity = any(word in query_lower for word in 
                     ["product", "sales", "revenue", "client", "region", "category"])
    
    # Scoring
    if has_keywords and is_short and not has_entity:
        return True, 0.9  # High confidence follow-up
    elif has_keywords:
        return True, 0.7  # Medium confidence
    elif is_short and not has_entity:
        return True, 0.6  # Lower confidence
    else:
        return False, 0.8  # Probably not a follow-up
```

```python
def _resolve_query_with_history(
    self, 
    user_query: str, 
    chat_history: List[Dict]
) -> Dict:
    """
    Resolve follow-up query into standalone query using Claude.
    
    Returns:
        {
            "resolved_query": str,
            "confidence": float,
            "entities": Dict,
            "interpretation": str
        }
    """
    # Use last 2-3 queries for context
    recent_history = chat_history[-3:] if len(chat_history) > 3 else chat_history
    
    # Build context string
    context_lines = []
    for i, entry in enumerate(recent_history, 1):
        context_lines.append(f"{i}. Query: \"{entry['user_query']}\"")
        context_lines.append(f"   Resolved to: \"{entry['resolved_query']}\"")
        if entry.get('key_entities'):
            entities = entry['key_entities']
            context_lines.append(f"   Context: {entities}")
    
    context = "\n".join(context_lines)
    
    # Claude resolution prompt
    resolution_prompt = f"""You are a query resolution assistant for a text-to-SQL system.

Previous conversation context:
{context}

New user query: "{user_query}"

Your task: Resolve this query into a complete, standalone natural language query that can be converted to SQL.

If it's a follow-up:
- Inherit relevant context from previous queries
- Resolve pronouns (it, that, them) to specific entities
- Expand implicit references (Q4 → "in Q4 2024", by region → "grouped by region")
- Keep the user's intent but make it standalone

If it's NOT a follow-up:
- Return the query unchanged

Respond in JSON format:
{{
    "resolved_query": "complete standalone query",
    "confidence": 0.95,
    "is_followup": true,
    "interpretation": "User wants to see same data but for Q4",
    "entities_inherited": {{"time_period": "Q4", "metrics": ["revenue"], "dimensions": ["product"]}}
}}
"""
    
    try:
        response = self.claude_service.client.messages.create(
            model=self.claude_service.model,
            max_tokens=500,
            temperature=0.3,  # Lower temp for consistency
            system="You are a precise query resolution assistant. Always respond in valid JSON.",
            messages=[{"role": "user", "content": resolution_prompt}]
        )
        
        result_text = response.content[0].text.strip()
        result = json.loads(result_text)
        
        logger.info(f"Query resolved: '{user_query}' → '{result['resolved_query']}' (confidence: {result['confidence']})")
        
        return result
        
    except Exception as e:
        logger.error(f"Query resolution failed: {e}", exc_info=True)
        # Fallback: return original query
        return {
            "resolved_query": user_query,
            "confidence": 0.5,
            "is_followup": False,
            "interpretation": "Resolution failed, using original query"
        }
```

**Modified Method:**

```python
def generate_sql_with_agent(
    self,
    user_query: str,
    session_id: str,
    client_id: int = 1,
    max_iterations: int = 3
) -> Dict:
    """Enhanced with follow-up resolution"""
    
    start_time = datetime.now()
    logger.info(f"Starting agentic workflow: session={session_id}, query='{user_query[:100]}'")
    
    # Get conversation history
    chat_history = self._get_chat_history(session_id)
    
    # Detect and resolve follow-ups
    is_followup, confidence = self._detect_followup(user_query, chat_history)
    
    if is_followup:
        logger.info(f"Follow-up detected (confidence: {confidence})")
        resolution = self._resolve_query_with_history(user_query, chat_history)
        resolved_query = resolution['resolved_query']
        resolution_confidence = resolution['confidence']
        
        # If low confidence, might need clarification
        if resolution_confidence < 0.8:
            logger.warning(f"Low resolution confidence: {resolution_confidence}")
            # Could trigger clarification here in future
    else:
        resolved_query = user_query
        resolution = None
    
    try:
        # Initialize state with resolution info
        initial_state: AgentState = {
            "user_query": user_query,
            "session_id": session_id,
            "resolved_query": resolved_query,
            "is_followup": is_followup,
            "resolution_info": resolution,
            "client_id": client_id,
            # ... rest of state ...
        }
        
        # Run workflow
        final_state = self.workflow.invoke(initial_state)
        
        # Add to history if successful
        if final_state.get("sql_query") and not final_state.get("clarification_needed"):
            self._add_enhanced_history(session_id, {
                "user_query": user_query,
                "resolved_query": resolved_query,
                "sql": final_state.get("sql_query"),
                "results_summary": self._summarize_results(final_state.get("execution_result")),
                "key_entities": self._extract_entities(final_state),
                "timestamp": datetime.now().isoformat(),
                "is_followup": is_followup
            })
        
        # Format response with follow-up info
        response = self._format_response(final_state)
        response["is_followup"] = is_followup
        if resolution:
            response["resolution_info"] = {
                "interpreted_as": resolution['resolved_query'],
                "confidence": resolution['confidence']
            }
        
        return response
        
    except Exception as e:
        logger.error(f"Agentic workflow failed: {e}", exc_info=True)
        return {"success": False, "error": str(e), "method": "agentic"}
```

**Helper Methods:**

```python
def _extract_entities(self, state: AgentState) -> Dict:
    """Extract key entities from query state for history"""
    # Parse SQL to extract dimensions, metrics, filters
    # This is a simplified version - can be enhanced
    sql = state.get("sql_query", "")
    
    return {
        "dimensions": [],  # Extract from GROUP BY
        "metrics": [],     # Extract from SELECT aggregations
        "filters": [],     # Extract from WHERE
        "time_period": "", # Extract from date filters
        "grouping": [],    # Extract from GROUP BY
        "limit": None      # Extract from LIMIT
    }

def _summarize_results(self, execution_result: Dict) -> str:
    """Create short summary of results for history"""
    if not execution_result:
        return "No results"
    
    results = execution_result.get("results", [])
    columns = execution_result.get("columns", [])
    
    if not results:
        return "0 rows"
    
    # Short summary with first row highlight
    row_count = len(results)
    if row_count > 0 and results[0]:
        first_val = list(results[0].values())[0] if results[0] else "N/A"
        return f"{row_count} rows: {first_val} (top)"
    
    return f"{row_count} rows"
```

---

### Frontend Changes

#### New Component: `frontend/src/components/ConversationPanel.jsx`

```jsx
import React from 'react';
import {
  Drawer,
  Box,
  Typography,
  List,
  ListItem,
  ListItemText,
  IconButton,
  Button,
  Chip,
  Divider
} from '@mui/material';
import {
  Close as CloseIcon,
  Search as SearchIcon,
  SubdirectoryArrowRight as FollowUpIcon,
  CheckCircle as SuccessIcon,
  Error as ErrorIcon
} from '@mui/icons-material';
import { formatDistanceToNow } from 'date-fns';

const ConversationPanel = ({ 
  open, 
  onClose, 
  history = [], 
  currentQueryIndex,
  onClearConversation,
  onQueryClick 
}) => {
  return (
    <Drawer
      anchor="right"
      open={open}
      onClose={onClose}
      PaperProps={{
        sx: { width: 350, p: 2 }
      }}
    >
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Box>
          <Typography variant="h6">💬 Conversation</Typography>
          <Typography variant="caption" color="text.secondary">
            Session: {history.length} queries
          </Typography>
        </Box>
        <IconButton onClick={onClose} size="small">
          <CloseIcon />
        </IconButton>
      </Box>

      <Divider sx={{ mb: 2 }} />

      {/* Query List */}
      <List sx={{ flexGrow: 1, overflow: 'auto' }}>
        {history.map((query, index) => (
          <ListItem
            key={index}
            sx={{
              flexDirection: 'column',
              alignItems: 'flex-start',
              backgroundColor: index === currentQueryIndex ? 'action.selected' : 'transparent',
              borderRadius: 1,
              mb: 1,
              cursor: 'pointer',
              '&:hover': { backgroundColor: 'action.hover' },
              pl: query.is_followup ? 4 : 2  // Indent follow-ups
            }}
            onClick={() => onQueryClick && onQueryClick(index)}
          >
            {/* Query Text */}
            <Box display="flex" alignItems="center" gap={1} width="100%">
              {query.is_followup ? (
                <FollowUpIcon fontSize="small" color="action" />
              ) : (
                <SearchIcon fontSize="small" color="primary" />
              )}
              <Typography 
                variant="body2" 
                sx={{ 
                  flexGrow: 1,
                  fontWeight: index === currentQueryIndex ? 600 : 400
                }}
              >
                {query.user_query}
              </Typography>
            </Box>

            {/* Metadata */}
            <Box display="flex" gap={0.5} mt={0.5} flexWrap="wrap">
              {/* Result indicator */}
              {query.success ? (
                <Chip 
                  icon={<SuccessIcon />}
                  label={query.results_summary || 'Success'}
                  size="small"
                  color="success"
                  variant="outlined"
                />
              ) : (
                <Chip 
                  icon={<ErrorIcon />}
                  label="Error"
                  size="small"
                  color="error"
                  variant="outlined"
                />
              )}

              {/* Timestamp */}
              <Chip 
                label={formatDistanceToNow(new Date(query.timestamp), { addSuffix: true })}
                size="small"
                variant="outlined"
              />

              {/* Current indicator */}
              {index === currentQueryIndex && (
                <Chip 
                  label="Viewing"
                  size="small"
                  color="primary"
                />
              )}
            </Box>
          </ListItem>
        ))}
      </List>

      <Divider sx={{ my: 2 }} />

      {/* Footer */}
      <Button 
        fullWidth
        variant="outlined"
        color="error"
        onClick={onClearConversation}
        disabled={history.length === 0}
      >
        Clear Conversation
      </Button>
    </Drawer>
  );
};

export default ConversationPanel;
```

#### New Component: `frontend/src/components/ResolutionIndicator.jsx`

```jsx
import React, { useState, useEffect } from 'react';
import { Alert, Button, Collapse } from '@mui/material';

const ResolutionIndicator = ({ 
  resolution, 
  onConfirm, 
  onClarify 
}) => {
  const [show, setShow] = useState(true);

  useEffect(() => {
    if (resolution) {
      setShow(true);
      const timer = setTimeout(() => setShow(false), 5000);
      return () => clearTimeout(timer);
    }
  }, [resolution]);

  if (!resolution) return null;

  return (
    <Collapse in={show}>
      <Alert 
        severity="info"
        sx={{ mb: 2 }}
        action={
          <>
            <Button size="small" onClick={() => { onConfirm(); setShow(false); }}>
              ✓ Correct
            </Button>
            <Button size="small" onClick={() => { onClarify(); setShow(false); }}>
              ⚠️ Clarify
            </Button>
          </>
        }
      >
        <strong>🤖 I understood:</strong> "{resolution.interpreted_as}"
        {resolution.confidence < 0.9 && (
          <> (Confidence: {Math.round(resolution.confidence * 100)}%)</>
        )}
      </Alert>
    </Collapse>
  );
};

export default ResolutionIndicator;
```

#### Update: `frontend/src/App.jsx`

```jsx
// Add state for conversation
const [conversationHistory, setConversationHistory] = useState([]);
const [conversationPanelOpen, setConversationPanelOpen] = useState(false);
const [currentQueryIndex, setCurrentQueryIndex] = useState(-1);
const [resolutionInfo, setResolutionInfo] = useState(null);

// Enhance handleQuerySubmit
const handleQuerySubmit = async (query, clientId) => {
  setLoading(true);
  setError(null);
  setResults(null);
  setAgenticData(null);
  setResolutionInfo(null);

  try {
    let data;
    
    if (agenticMode) {
      data = await executeAgenticQuery(query, sessionId, clientId, 10);
      
      // Handle clarification
      if (data.needs_clarification) {
        // ... existing clarification logic ...
        return;
      }
      
      // Store resolution info for display
      if (data.resolution_info) {
        setResolutionInfo(data.resolution_info);
      }
      
      // Add to conversation history
      const historyEntry = {
        user_query: query,
        resolved_query: data.resolution_info?.interpreted_as || query,
        timestamp: new Date().toISOString(),
        success: data.success,
        results_summary: data.results?.row_count ? `${data.results.row_count} rows` : 'No results',
        is_followup: data.is_followup || false
      };
      
      setConversationHistory(prev => [...prev, historyEntry]);
      setCurrentQueryIndex(conversationHistory.length);
      
      // ... rest of existing logic ...
    } else {
      // ... classic mode ...
    }
  } catch (err) {
    // ... error handling ...
  } finally {
    setLoading(false);
  }
};

// Clear conversation handler
const handleClearConversation = () => {
  const newSessionId = `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  setSessionId(newSessionId);
  setConversationHistory([]);
  setCurrentQueryIndex(-1);
  setAgenticData(null);
  console.log(`Conversation cleared. New session: ${newSessionId}`);
};

// Add to JSX
<Box sx={{ position: 'relative' }}>
  {/* History button in header */}
  <IconButton 
    onClick={() => setConversationPanelOpen(true)}
    sx={{ position: 'absolute', top: 16, right: 16 }}
  >
    <Badge badgeContent={conversationHistory.length} color="primary">
      💬
    </Badge>
  </IconButton>

  {/* Resolution indicator */}
  <ResolutionIndicator
    resolution={resolutionInfo}
    onConfirm={() => setResolutionInfo(null)}
    onClarify={() => {
      // Open clarification dialog with context
      setClarificationDialog({
        open: true,
        questions: ["Please clarify what you meant..."],
        originalQuery: lastQuery,
        clientId: currentClientId,
      });
    }}
  />

  {/* Conversation panel */}
  <ConversationPanel
    open={conversationPanelOpen}
    onClose={() => setConversationPanelOpen(false)}
    history={conversationHistory}
    currentQueryIndex={currentQueryIndex}
    onClearConversation={handleClearConversation}
    onQueryClick={(index) => {
      // Future: load that query's results
      console.log('Query clicked:', index);
    }}
  />
</Box>
```

---

## Testing Scenarios

### Test Case 1: Time Period Follow-ups
```
1. "Top products by revenue" → Show all-time
2. "What about Q4?" → Q4 only
3. "And Q3?" → Q3 only
4. "Compare Q3 and Q4" → Comparative query
```

### Test Case 2: Dimension Changes
```
1. "Sales by product" → Product dimension
2. "Show me by region" → Add region dimension
3. "Just region" → Region only (remove product)
4. "Add month too" → Region + month dimensions
```

### Test Case 3: Progressive Filtering
```
1. "All sales" → No filters
2. "Only electronics" → Add category filter
3. "In North region" → Add region filter
4. "Last 6 months" → Add time filter
5. "Remove region" → Keep category + time
```

### Test Case 4: Pronoun Resolution
```
1. "Top 5 products by revenue" → Base query
2. "Show me that by region" → "that" = top 5 products by revenue
3. "Filter it for electronics" → "it" = top 5 products by revenue by region
```

### Test Case 5: Ambiguous Queries
```
1. "Top products" → Base query
2. "Show me more" → Should trigger clarification
   - More products?
   - More details/columns?
   - More time periods?
```

### Test Case 6: Topic Changes
```
1. "Top products by revenue" → Product analysis
2. "What clients do we have?" → Topic change detected
   - System auto-resets context
   - Treats as new conversation thread
```

---

## Definition of Done

- [ ] All Phase 1 ACs completed and tested
- [ ] Follow-up detection accuracy > 85%
- [ ] Query resolution accuracy > 80%
- [ ] Resolution time < 2s average
- [ ] All 6 test scenarios pass
- [ ] Conversation panel displays correctly
- [ ] Context badge works with clear button
- [ ] Resolution indicator shows and auto-dismisses
- [ ] Logging added for all resolution steps
- [ ] Code reviewed and follows standards
- [ ] No linter errors
- [ ] Manual testing completed
- [ ] Documentation updated (README)

---

## Success Metrics

Track these after deployment:

- **Follow-up detection rate** - % of queries identified as follow-ups (target: 30-40%)
- **Resolution accuracy** - % of follow-ups resolved correctly (target: >85%)
- **Average session length** - Queries per session (target: 5-8 indicates engagement)
- **Clarification frequency** - % of queries needing clarification (target: <10%)
- **Time saved** - Avg characters saved per follow-up vs full query
- **User satisfaction** - Survey: "Did the system understand your follow-up?" (target: >4/5)

---

## Future Enhancements (Post-POC)

- Session persistence (Redis/database)
- View previous query results in panel
- Rerun queries with one click
- Export conversation as report
- Conversation branching (fork from any query)
- Smart autocomplete based on history
- Multi-session comparison
- Saved conversation templates

---

**Story Status:** ✅ Ready for Development

**Assigned To:** Dev Agent (James)

**Started:** TBD

**Completed:** TBD

