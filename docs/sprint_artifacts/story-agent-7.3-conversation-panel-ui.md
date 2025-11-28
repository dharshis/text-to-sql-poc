# Story 7.3: Conversation History Panel UI

**Story ID:** STORY-AGENT-7.3  
**Epic:** EPIC-AGENTIC-001 (Agentic Text-to-SQL Enhancement)  
**Priority:** Must Have  
**Status:** Ready for Development  
**Estimate:** 2 days  
**Dependencies:** STORY-AGENT-7.1, STORY-AGENT-7.2, STORY-AGENT-8  

---

## User Story

**As a** market researcher  
**I want** to see my conversation history with the system  
**So that** I can track my analysis flow, reference previous queries, and manage my session

---

## Description

Create a professional conversation history panel for data analysts that displays query history without disrupting the main dashboard layout. The panel slides out from the right, shows the last 10 queries with metadata, and allows users to clear the conversation when starting a new analysis thread.

**UI Paradigm:** Dashboard-first with supportive conversation panel (NOT chat-first interface)

---

## Acceptance Criteria

### AC1: Conversation Panel Component

- [ ] Create **`frontend/src/components/ConversationPanel.jsx`**
- [ ] Material-UI **Drawer** component, anchor="right"
- [ ] Panel width: **350px**
- [ ] Slide-in/out animation (smooth)
- [ ] Props:
  ```javascript
  {
    open: bool,
    onClose: () => void,
    history: Array<QueryHistoryEntry>,
    currentQueryIndex: number,
    onClearConversation: () => void,
    onQueryClick: (index) => void  // Optional for now
  }
  ```

**QueryHistoryEntry type:**
```javascript
{
  user_query: string,
  resolved_query: string,
  timestamp: string,
  success: bool,
  results_summary: string,
  is_followup: bool
}
```

---

### AC2: Panel Header

- [ ] Header section at top:
  ```
  ┌────────────────────────────┐
  │ 💬 Conversation         [×]│
  │ Session: 12 queries        │
  │ ────────────────────────── │
  ```
- [ ] Title: "💬 Conversation" (h6 typography)
- [ ] Subtitle: "Session: {count} queries" (caption, text.secondary)
- [ ] Close button (IconButton with CloseIcon)
- [ ] Divider below header

---

### AC3: Query List Display

- [ ] Scrollable list showing last 10 queries (reverse chronological)
- [ ] Each query item shows:
  
  **Visual structure:**
  ```
  ┌─────────────────────────────────┐
  │ 🔍 Top 5 products by revenue    │ ← Not a follow-up
  │    ✅ 5 results | 3 min ago     │
  │ ─────────────────────────────── │
  │   ↪️ What about Q4?             │ ← Follow-up (indented)
  │      ✅ 5 results | 1 min ago   │
  │ ─────────────────────────────── │
  │   ↪️ Show me by region          │ ← Follow-up (indented)
  │      ⚡ Viewing now              │ ← Current query
  └─────────────────────────────────┘
  ```

- [ ] **Query icon:**
  - 🔍 (SearchIcon) for new queries
  - ↪️ (SubdirectoryArrowRightIcon) for follow-ups
- [ ] **Query text:**
  - Typography: body2
  - Truncate to 50 chars with "..." if longer
  - Bold if current query
  - Left padding: 2 (base) or 4 (follow-up) for visual hierarchy
- [ ] **Status chips (small, outlined):**
  - Success: `✅ {results_summary}` (green)
  - Error: `⚠️ Error` (red)
- [ ] **Timestamp chip:**
  - Format: "3 min ago", "Just now", "1 hour ago"
  - Use `date-fns` library: `formatDistanceToNow(date, { addSuffix: true })`
  - Chip variant: outlined, size: small
- [ ] **Current indicator:**
  - Show `⚡ Viewing` chip if it's the current query
  - Color: primary

---

### AC4: Panel Footer

- [ ] Divider above footer
- [ ] **Clear Conversation** button:
  - Full width
  - Variant: outlined
  - Color: error (red)
  - Disabled if history is empty
  - Text: "Clear Conversation"
- [ ] Clicking clears all history and creates new session ID

---

### AC5: Panel Interactions

- [ ] **Hover effect** on query items:
  - Background: `action.hover`
  - Cursor: pointer
- [ ] **Click query** (future functionality):
  - Call `onQueryClick(index)` callback
  - Console log for now: "Query clicked: {index}"
  - Future: Load that query's results
- [ ] **Close panel:**
  - Click [×] button
  - Click outside panel (drawer backdrop)
  - Keyboard: ESC key

---

### AC6: App.jsx Integration

- [ ] Add state management:
  ```javascript
  const [conversationHistory, setConversationHistory] = useState([]);
  const [conversationPanelOpen, setConversationPanelOpen] = useState(false);
  const [currentQueryIndex, setCurrentQueryIndex] = useState(-1);
  ```

- [ ] Add **History button** in header (top-right):
  ```jsx
  <IconButton 
    onClick={() => setConversationPanelOpen(true)}
    aria-label="conversation history"
  >
    <Badge badgeContent={conversationHistory.length} color="primary">
      <ChatIcon />
    </Badge>
  </IconButton>
  ```

- [ ] Update `handleQuerySubmit()` to add to history:
  ```javascript
  // After successful agentic query
  const historyEntry = {
    user_query: query,
    resolved_query: data.resolution_info?.interpreted_as || query,
    timestamp: new Date().toISOString(),
    success: data.success,
    results_summary: data.results?.row_count 
      ? `${data.results.row_count} rows` 
      : 'No results',
    is_followup: data.is_followup || false
  };
  
  setConversationHistory(prev => [...prev, historyEntry]);
  setCurrentQueryIndex(conversationHistory.length);
  ```

- [ ] Create `handleClearConversation()`:
  ```javascript
  const handleClearConversation = () => {
    // Generate new session ID
    const newSessionId = `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    setSessionId(newSessionId);
    
    // Clear history
    setConversationHistory([]);
    setCurrentQueryIndex(-1);
    setAgenticData(null);
    
    // Close panel
    setConversationPanelOpen(false);
    
    console.log(`Conversation cleared. New session: ${newSessionId}`);
  };
  ```

- [ ] Render ConversationPanel in JSX:
  ```jsx
  <ConversationPanel
    open={conversationPanelOpen}
    onClose={() => setConversationPanelOpen(false)}
    history={conversationHistory}
    currentQueryIndex={currentQueryIndex}
    onClearConversation={handleClearConversation}
    onQueryClick={(index) => console.log('Query clicked:', index)}
  />
  ```

---

### AC7: Enhanced ContextBadge

- [ ] Update **`frontend/src/components/ContextBadge.jsx`**
- [ ] Add **[×] clear button**:
  ```jsx
  <Chip
    icon={<HistoryIcon />}
    label={`Following up on: ${previousQuery.substring(0, 50)}...`}
    onDelete={onClear}  // NEW: Shows [×] button
    color="info"
    variant="outlined"
    sx={{ mb: 2 }}
  />
  ```
- [ ] Add `onClear` prop:
  ```javascript
  const ContextBadge = ({ previousQuery, isFollowup, onClear }) => {
    if (!isFollowup || !previousQuery) return null;
    
    return (
      <Chip
        icon={<HistoryIcon />}
        label={`Following up on: ${previousQuery.substring(0, 50)}${previousQuery.length > 50 ? '...' : ''}`}
        onDelete={onClear}
        color="info"
        variant="outlined"
        sx={{ mb: 2 }}
      />
    );
  };
  ```
- [ ] Wire up to `handleClearConversation()` in App.jsx

---

### AC8: Keyboard Shortcuts

- [ ] Add keyboard shortcut: **Cmd/Ctrl + H** to open history panel
- [ ] Use React hook:
  ```javascript
  useEffect(() => {
    const handleKeyPress = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'h') {
        e.preventDefault();
        setConversationPanelOpen(prev => !prev);
      }
    };
    
    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, []);
  ```
- [ ] Document shortcut in UI (tooltip on history button)

---

## Visual Design Specs

### Colors & Styling

**Panel:**
- Background: Default paper background
- Padding: 2 (16px)
- Shadow: Material-UI default drawer shadow

**Query Items:**
- Background (normal): transparent
- Background (current): `action.selected` (light blue)
- Background (hover): `action.hover`
- Border radius: 1 (4px)
- Margin bottom: 1 (8px)

**Typography:**
- Header title: h6, fontWeight: 600
- Query text: body2
- Current query: fontWeight: 600
- Timestamp: caption, text.secondary

**Chips:**
- Size: small
- Variant: outlined
- Success chip: color="success"
- Error chip: color="error"
- Timestamp chip: default color
- Current chip: color="primary"

---

## Files to Create

```
frontend/src/components/ConversationPanel.jsx
```

## Files to Modify

```
frontend/src/components/ContextBadge.jsx (add clear button)
frontend/src/App.jsx (integrate panel, manage history state)
frontend/package.json (add date-fns if not present)
```

---

## Testing

### Manual UI Tests

**Test 1: Panel Opens/Closes**
- [ ] Click history button → panel slides in from right
- [ ] Click [×] → panel closes
- [ ] Click outside panel → panel closes
- [ ] Press ESC → panel closes
- [ ] Cmd/Ctrl + H → toggles panel

**Test 2: Query Display**
- [ ] Run 3 queries: base → follow-up → follow-up
- [ ] Open panel → see all 3 queries
- [ ] Follow-ups are indented
- [ ] Current query is highlighted
- [ ] Timestamps are relative ("Just now", "2 min ago")
- [ ] Success chips show result counts

**Test 3: Clear Conversation**
- [ ] Open panel with history
- [ ] Click "Clear Conversation"
- [ ] Panel closes
- [ ] History list is empty
- [ ] Context badge disappears
- [ ] New session ID generated
- [ ] Next query doesn't reference old context

**Test 4: Long Session**
- [ ] Run 15 queries
- [ ] Panel shows only last 10
- [ ] Oldest queries automatically pruned
- [ ] Scrolling works smoothly

**Test 5: Responsive Behavior**
- [ ] Panel doesn't break layout on smaller screens
- [ ] Query text truncates properly
- [ ] Chips wrap if needed

---

## Dependencies

**NPM Packages:**
- `date-fns` - For timestamp formatting
  ```bash
  npm install date-fns
  ```

**Material-UI Components:**
- Already installed: Drawer, List, Chip, IconButton, etc.

---

## Definition of Done

- [ ] ConversationPanel component created
- [ ] Panel displays last 10 queries
- [ ] Follow-ups are visually indented
- [ ] Current query is highlighted
- [ ] Timestamps formatted correctly
- [ ] Clear conversation button works
- [ ] Panel opens/closes smoothly
- [ ] Keyboard shortcut works (Cmd/Ctrl + H)
- [ ] ContextBadge has clear button
- [ ] App.jsx fully integrated
- [ ] All 5 manual UI tests pass
- [ ] No visual bugs or layout issues
- [ ] Responsive on different screen sizes
- [ ] No linter errors
- [ ] Code reviewed and follows standards

---

## Success Metrics

- **Panel usage rate**: % of users who open conversation panel (target: >50%)
- **Clear frequency**: How often users clear conversations (indicates starting new threads)
- **Average queries before clear**: Indicates typical session length

---

**Story Status:** ✅ Ready for Development  
**Assigned To:** Dev Agent  
**Started:** TBD  
**Completed:** TBD

