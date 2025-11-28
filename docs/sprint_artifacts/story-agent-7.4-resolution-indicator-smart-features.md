# Story 7.4: Resolution Indicator & Smart Query Suggestions

**Story ID:** STORY-AGENT-7.4  
**Epic:** EPIC-AGENTIC-001 (Agentic Text-to-SQL Enhancement)  
**Priority:** Should Have  
**Status:** Ready for Development  
**Estimate:** 2 days  
**Dependencies:** STORY-AGENT-7.1, STORY-AGENT-7.3  

---

## User Story

**As a** market researcher  
**I want** to see how the system interpreted my follow-up question and get suggestions for next queries  
**So that** I can verify understanding and discover related insights efficiently

---

## Description

Add two smart features that enhance the conversational analytics experience:

1. **Resolution Indicator** - Shows how follow-up queries were interpreted, with options to confirm or clarify
2. **Query Suggestions** - AI-generated suggestions for related follow-up queries based on current context

These features build trust (users see what was understood) and accelerate exploration (users discover relevant questions they might not think of).

---

## Acceptance Criteria

### Part A: Resolution Indicator

#### AC1: ResolutionIndicator Component

- [ ] Create **`frontend/src/components/ResolutionIndicator.jsx`**
- [ ] Material-UI **Alert** component (severity="info")
- [ ] Props:
  ```javascript
  {
    resolution: {
      interpreted_as: string,
      confidence: number
    },
    onConfirm: () => void,
    onClarify: () => void
  }
  ```
- [ ] Only renders if `resolution` prop exists
- [ ] Shows when follow-up is resolved

---

#### AC2: Display Content

- [ ] Alert message:
  ```
  🤖 I understood: "Top 5 products by revenue in Q4"
  ```
- [ ] If confidence < 0.9, show confidence score:
  ```
  🤖 I understood: "Sales by region" (Confidence: 75%)
  ```
- [ ] Two action buttons:
  - **[✓ Correct]** - Confirms understanding, dismisses indicator
  - **[⚠️ Clarify]** - Opens clarification dialog

---

#### AC3: Auto-Dismiss Behavior

- [ ] Indicator appears when resolution info is set
- [ ] Automatically fades out after **5 seconds**
- [ ] Use `Collapse` component for smooth animation
- [ ] State management:
  ```javascript
  const [show, setShow] = useState(true);
  
  useEffect(() => {
    if (resolution) {
      setShow(true);
      const timer = setTimeout(() => setShow(false), 5000);
      return () => clearTimeout(timer);
    }
  }, [resolution]);
  ```
- [ ] Clicking [✓ Correct] immediately dismisses
- [ ] Clicking [⚠️ Clarify] dismisses and opens clarification dialog

---

#### AC4: Position & Styling

- [ ] Position: Below ContextBadge, above InsightCard
- [ ] Margin bottom: 2 (16px)
- [ ] Alert styling:
  - Info severity (blue)
  - Icon: info icon (default)
  - Two button actions in alert action slot
- [ ] Buttons:
  - Size: small
  - No variant (default text buttons)

---

#### AC5: Integration with App.jsx

- [ ] Add state:
  ```javascript
  const [resolutionInfo, setResolutionInfo] = useState(null);
  ```

- [ ] Set resolution info after agentic query:
  ```javascript
  if (agenticMode && data.resolution_info) {
    setResolutionInfo(data.resolution_info);
  }
  ```

- [ ] Handle confirm:
  ```javascript
  const handleResolutionConfirm = () => {
    setResolutionInfo(null);
  };
  ```

- [ ] Handle clarify:
  ```javascript
  const handleResolutionClarify = () => {
    setResolutionInfo(null);
    
    // Open clarification dialog
    setClarificationDialog({
      open: true,
      questions: [
        "I want to make sure I understand correctly.",
        "Can you rephrase or provide more details?"
      ],
      originalQuery: lastQuery,
      clientId: currentClientId,
    });
  };
  ```

- [ ] Render in JSX:
  ```jsx
  {/* After ContextBadge, before InsightCard */}
  <ResolutionIndicator
    resolution={resolutionInfo}
    onConfirm={handleResolutionConfirm}
    onClarify={handleResolutionClarify}
  />
  ```

---

### Part B: Query Suggestions (Optional - Nice to Have)

#### AC6: Query Suggestions Component

- [ ] Create **`frontend/src/components/QuerySuggestions.jsx`**
- [ ] Material-UI **Accordion** component (collapsed by default)
- [ ] Props:
  ```javascript
  {
    suggestions: Array<string>,
    onSuggestionClick: (suggestion: string) => void
  }
  ```
- [ ] Position: Below results display (at bottom)

**Visual structure:**
```
┌────────────────────────────────────────┐
│ 💡 You might also want to explore: ▼  │
│ ────────────────────────────────────── │
│ • What about Q3?                       │
│ • Show me by region                    │
│ • Compare to last year                 │
│ • Filter for electronics only          │
└────────────────────────────────────────┘
```

---

#### AC7: Suggestion Display

- [ ] Accordion summary:
  - Icon: 💡 LightbulbIcon
  - Text: "You might also want to explore:"
  - Default: collapsed
- [ ] Accordion details:
  - List of 3-5 clickable suggestions
  - Each suggestion is a Chip or Button
  - Clicking fills search bar with suggestion
  - User can edit before submitting

---

#### AC8: Backend Suggestion Generation

- [ ] Add `_generate_suggestions()` method in `AgenticText2SQLService`
- [ ] Called after successful query execution
- [ ] Uses Claude with prompt:
  ```
  User just asked: "Top products by revenue"
  Results: 5 rows with Le Creuset at top
  
  Generate 3-4 natural follow-up questions a data analyst might ask.
  
  Consider:
  - Time period variations (Q4, last year, this month)
  - Dimension changes (by region, by category)
  - Filtering (only electronics, top 10 instead)
  - Comparisons (compare to Q3, year-over-year)
  
  Respond as JSON array: ["suggestion 1", "suggestion 2", ...]
  ```
- [ ] Include suggestions in API response:
  ```python
  response["suggestions"] = [
      "What about Q4?",
      "Show me by region",
      "Filter for electronics"
  ]
  ```
- [ ] Performance: Run in parallel with other operations (don't block)
- [ ] If suggestion generation fails → return empty array

---

#### AC9: Frontend Integration

- [ ] Add to App.jsx:
  ```javascript
  const [querySuggestions, setQuerySuggestions] = useState([]);
  
  // After successful query
  if (data.suggestions) {
    setQuerySuggestions(data.suggestions);
  }
  
  // Handle suggestion click
  const handleSuggestionClick = (suggestion) => {
    // Fill search bar
    setCurrentQuery(suggestion);
    // Could auto-submit or let user review first
  };
  ```

- [ ] Render below results:
  ```jsx
  {querySuggestions.length > 0 && (
    <QuerySuggestions
      suggestions={querySuggestions}
      onSuggestionClick={handleSuggestionClick}
    />
  )}
  ```

---

## Technical Notes

### Files to Create

```
frontend/src/components/ResolutionIndicator.jsx
frontend/src/components/QuerySuggestions.jsx (optional)
```

### Files to Modify

```
frontend/src/components/ContextBadge.jsx (add clear button)
frontend/src/App.jsx (integrate indicators and suggestions)
backend/services/agentic_text2sql_service.py (add _generate_suggestions)
```

### Dependencies

**NPM Packages:**
- `date-fns` - Already in Story 7.3
- All Material-UI components already installed

---

## Testing

### Manual Test Cases

**Test 1: Resolution Indicator Appears**
```
1. Query: "Top products"
2. Query: "What about Q4?"
   → Resolution indicator appears
   → Shows: "I understood: Top products in Q4"
   → Has [✓ Correct] and [⚠️ Clarify] buttons
   → Auto-dismisses after 5 seconds
```

**Test 2: Confirm Understanding**
```
1. Follow-up query triggers resolution indicator
2. Click [✓ Correct]
   → Indicator dismisses immediately
   → Query proceeds normally
```

**Test 3: Request Clarification**
```
1. Follow-up query triggers resolution indicator
2. Click [⚠️ Clarify]
   → Indicator dismisses
   → Clarification dialog opens
   → User can provide more context
   → Query resubmitted with clarification
```

**Test 4: Low Confidence**
```
1. Ambiguous follow-up: "Show me more"
   → Resolution indicator shows with confidence: 60%
   → User sees they should probably clarify
```

**Test 5: Query Suggestions**
```
1. Query: "Top products by revenue"
   → Results displayed
   → Suggestions accordion appears at bottom
   → Shows 3-4 relevant suggestions
2. Click "What about Q4?"
   → Suggestion fills search bar
   → User can edit or submit
```

**Test 6: Clear Button on ContextBadge**
```
1. Ask follow-up query
2. ContextBadge shows "Following up on: ..."
3. Click [×] on badge
   → Conversation cleared
   → New session started
   → Badge disappears
```

---

## Performance Considerations

### Resolution Indicator
- No performance impact (pure UI component)
- Auto-dismiss timer properly cleaned up

### Query Suggestions
- Generation: ≤2s (Claude API, run async)
- Don't block main query response
- If takes too long, show placeholder or skip
- Cache suggestions briefly (30s) if same query repeated

---

## Definition of Done

### Part A: Resolution Indicator (Must Have)
- [ ] ResolutionIndicator component created
- [ ] Shows interpreted query with confidence
- [ ] [✓ Correct] and [⚠️ Clarify] buttons work
- [ ] Auto-dismisses after 5 seconds
- [ ] Smooth animations (fade in/out)
- [ ] Integrated with App.jsx
- [ ] ContextBadge has clear button
- [ ] Clear button creates new session
- [ ] All 6 manual tests pass
- [ ] No visual bugs

### Part B: Query Suggestions (Nice to Have)
- [ ] QuerySuggestions component created
- [ ] Backend `_generate_suggestions()` implemented
- [ ] Suggestions displayed below results
- [ ] Clicking suggestion fills search bar
- [ ] Accordion UI works correctly
- [ ] Suggestions are contextually relevant
- [ ] Generation doesn't block main response
- [ ] Manual tests pass

---

## Success Metrics

**Resolution Indicator:**
- **Confirmation rate**: % of users who click [✓ Correct] (indicates trust)
- **Clarification rate**: % who click [⚠️ Clarify] (indicates confusion)
- **Ignore rate**: % who let it auto-dismiss (acceptable behavior)

**Query Suggestions:**
- **Click-through rate**: % of suggestions clicked (target: >20%)
- **Most popular suggestions**: Which types get clicked most
- **Session extension**: Do suggestions increase queries per session?

---

**Story Status:** ✅ Ready for Development  
**Assigned To:** Dev Agent  
**Started:** TBD  
**Completed:** TBD


