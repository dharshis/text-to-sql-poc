# Session Memory Implementation Plan

**Feature:** Context-Aware Conversational Analytics  
**Target Users:** Market Researchers & Data Analysts  
**Timeline:** 1 week (5 days)  
**Date Created:** November 27, 2025  

---

## 🎯 Vision

Transform the Text-to-SQL tool from a single-query interface into an intelligent analytics assistant that understands follow-up questions and maintains conversation context, enabling natural data exploration.

**User Experience:**
```
Analyst: "Top products by revenue"
System: [Shows results]

Analyst: "What about Q4?"
System: 🤖 Understood: "Top products by revenue in Q4"
        [Shows Q4 results with insights]

Analyst: "Show me by region"
System: 🤖 Understood: "Top products by revenue in Q4 by region"
        [Shows regional breakdown]
```

---

## 📦 Story Breakdown (4 Stories)

### **Story 7.1: Follow-up Detection & Query Resolution** ⭐ CORE
**Estimate:** 2 days  
**Priority:** Must Have  
**Focus:** Backend intelligence

**Delivers:**
- Follow-up detection (keyword + context analysis)
- Claude-powered query resolution
- Integration with workflow
- API response includes `is_followup` flag

**Key Methods:**
- `_detect_followup()` - Returns (is_followup, confidence)
- `_resolve_query_with_history()` - Claude resolves to standalone query

**Test Scenarios:**
- Time period changes: "What about Q4?"
- Dimension changes: "Show me by region"
- Filtering: "Only electronics"
- Pronouns: "Show me that by region"

**Status:** Ready for Dev Agent

---

### **Story 7.2: Enhanced History Storage** 🗄️ FOUNDATION
**Estimate:** 1 day  
**Priority:** Must Have  
**Focus:** Backend data structure

**Delivers:**
- Rich history entries with entity tracking
- Entity extraction from SQL queries
- Results summarization
- Better context for resolution

**Key Methods:**
- `_extract_entities()` - Parse SQL for dimensions, metrics, filters, time
- `_summarize_results()` - Create readable result summary
- Enhanced `_add_to_history()` - Store rich context

**Entities Tracked:**
```python
{
    "dimensions": ["product", "region"],
    "metrics": ["revenue", "quantity"],
    "filters": [{"client_id": 1}, {"category": "electronics"}],
    "time_period": "Q4 2024",
    "grouping": ["product_name"],
    "limit": 5
}
```

**Status:** Ready for Dev Agent

---

### **Story 7.3: Conversation History Panel** 🎨 UI
**Estimate:** 2 days  
**Priority:** Must Have  
**Focus:** Frontend visualization

**Delivers:**
- Professional slide-out conversation panel (350px)
- Last 10 queries with metadata display
- Visual follow-up hierarchy (indentation)
- Clear conversation button
- Enhanced ContextBadge with clear functionality

**Components:**
- `ConversationPanel.jsx` - Main history drawer
- Updated `ContextBadge.jsx` - Add clear button

**UI Features:**
- Query icons: 🔍 (new) / ↪️ (follow-up)
- Status chips: ✅ results / ⚠️ error
- Timestamps: "3 min ago"
- Current query highlight
- Keyboard shortcut: Cmd/Ctrl + H

**Status:** Ready for Dev Agent

---

### **Story 7.4: Resolution Indicator & Smart Features** ✨ POLISH
**Estimate:** 2 days  
**Priority:** Should Have  
**Focus:** UX enhancement

**Delivers:**
- Resolution indicator ("I understood: ...")
- Confirm/clarify buttons
- Auto-dismiss after 5s
- Query suggestions (optional)

**Components:**
- `ResolutionIndicator.jsx` - Shows interpretation
- `QuerySuggestions.jsx` - AI-generated follow-ups (optional)

**User Flow:**
```
1. User asks follow-up
2. Indicator appears: "🤖 I understood: [resolved query]"
3. User can:
   - Ignore (auto-dismisses in 5s) ✓
   - Confirm [✓ Correct] ✓
   - Clarify [⚠️ Clarify] → opens dialog
```

**Status:** Ready for Dev Agent

---

## 🗓️ Implementation Timeline

### **Week 1: Core + UI**

**Day 1-2: Story 7.1 (Detection & Resolution)**
- Implement follow-up detection logic
- Implement Claude-based resolution
- Integrate with workflow
- Test 5 core scenarios
- **Deliverable:** Backend detects and resolves follow-ups

**Day 3: Story 7.2 (Enhanced History)**
- Implement entity extraction from SQL
- Implement results summarization
- Update history storage structure
- Test extraction accuracy
- **Deliverable:** Rich context stored in history

**Day 4-5: Story 7.3 (Conversation Panel)**
- Build ConversationPanel component
- Integrate with App.jsx
- Add keyboard shortcuts
- Add clear conversation functionality
- Update ContextBadge
- **Deliverable:** Full conversation UI working

### **Week 2: Polish (Optional)**

**Day 6-7: Story 7.4 (Indicators & Suggestions)**
- Build ResolutionIndicator component
- Add confirm/clarify handlers
- Implement query suggestions (optional)
- Polish animations and UX
- **Deliverable:** Enhanced trust and discoverability

---

## 📊 Success Criteria (Epic-Level)

After all stories complete:

### Functional Requirements
- [ ] Users can ask "What about Q4?" and system understands
- [ ] Users can ask "Show me by region" and system adds dimension
- [ ] Users can ask "Only electronics" and system adds filter
- [ ] Conversation panel shows last 10 queries
- [ ] Follow-ups are visually distinguished (indentation)
- [ ] Clear conversation creates new session

### Quality Requirements
- [ ] Follow-up detection accuracy: >85%
- [ ] Query resolution accuracy: >80%
- [ ] Resolution time: <2s average
- [ ] No performance degradation for non-follow-up queries
- [ ] UI responsive and smooth animations

### Business Value
- [ ] Average session length increases (>5 queries)
- [ ] Time saved per follow-up vs full query (target: 50% faster)
- [ ] User satisfaction with follow-up understanding (>4/5)

---

## 🧪 End-to-End Test Scenarios

### **Scenario A: Exploratory Analysis**
```
1. "Top products by revenue"
   ✓ New query, no follow-up
   ✓ Results displayed
   ✓ History: 1 entry

2. "What about Q4?"
   ✓ Detected as follow-up (confidence: 0.9)
   ✓ Resolved to: "Top products by revenue in Q4"
   ✓ Resolution indicator shows
   ✓ Q4 results displayed
   ✓ History: 2 entries, second indented

3. "Compare to Q3"
   ✓ Detected as follow-up (confidence: 0.8)
   ✓ Resolved to: "Top products Q4 vs Q3"
   ✓ Comparative results displayed
   ✓ History: 3 entries
```

### **Scenario B: Progressive Refinement**
```
1. "Show all sales"
   ✓ Base query

2. "Only electronics"
   ✓ Follow-up detected
   ✓ Resolved: "Sales for electronics"
   ✓ Filter applied

3. "In North region"
   ✓ Follow-up detected
   ✓ Resolved: "Sales for electronics in North region"
   ✓ Both filters applied

4. Clear conversation
   ✓ History cleared
   ✓ New session created
   ✓ Context badge removed

5. "What about Q4?"
   ✓ NOT detected as follow-up (no context)
   ✓ Triggers clarification
```

### **Scenario C: UI Interaction Flow**
```
1. Run 5 queries (mix of new and follow-ups)
2. Click history button
   ✓ Panel slides in
   ✓ Shows 5 queries
   ✓ Follow-ups indented
   ✓ Current query highlighted
3. Press Cmd+H
   ✓ Panel closes
4. Press Cmd+H again
   ✓ Panel opens
5. Click "Clear Conversation"
   ✓ Confirmation or immediate clear
   ✓ Panel closes
   ✓ History empty
6. Click history button again
   ✓ Panel shows "No queries yet"
```

---

## 🚀 Getting Started

### For Developer Agent:

**Step 1:** Start with Story 7.1
```
File: docs/sprint_artifacts/story-agent-7.1-followup-detection-resolution.md
Focus: Backend detection and resolution logic
Time: 2 days
```

**Step 2:** Move to Story 7.2
```
File: docs/sprint_artifacts/story-agent-7.2-enhanced-history-storage.md
Focus: Entity extraction and rich history
Time: 1 day
```

**Step 3:** Build Story 7.3
```
File: docs/sprint_artifacts/story-agent-7.3-conversation-panel-ui.md
Focus: Frontend conversation UI
Time: 2 days
```

**Step 4:** Polish with Story 7.4 (Optional)
```
File: docs/sprint_artifacts/story-agent-7.4-resolution-indicator-smart-features.md
Focus: Resolution indicator and suggestions
Time: 2 days
```

---

## 📈 Metrics Dashboard (Post-Implementation)

Track these to measure success:

### Usage Metrics
- Sessions with 3+ queries (indicates deep analysis)
- Average queries per session (target: 5-8)
- % of queries that are follow-ups (target: 30-40%)

### Quality Metrics
- Follow-up detection accuracy (>85%)
- Resolution accuracy (>80%)
- False positive rate (<10%)
- Clarification frequency (<10%)

### Performance Metrics
- Resolution time (p50, p95, p99)
- API calls per query (target: <2 extra for follow-ups)
- Memory usage (history storage)

### User Satisfaction
- "Did system understand your follow-up?" (target: >4/5)
- "Is conversation feature useful?" (target: >80% yes)
- Time saved vs typing full queries (target: >50%)

---

## 🎓 Technical Architecture Summary

### Backend Flow
```
User Query
    ↓
Get History (last 10)
    ↓
Detect Follow-up (keyword + context)
    ↓
If follow-up → Resolve with Claude (last 2-3 for context)
    ↓
Initialize Workflow State (with resolved_query)
    ↓
Run Agentic Workflow
    ↓
Extract Entities from SQL
    ↓
Summarize Results
    ↓
Add Enhanced Entry to History
    ↓
Return Response (with is_followup, resolution_info)
```

### Frontend Flow
```
User Submits Query
    ↓
API Call to /query-agentic
    ↓
Receive Response (with is_followup, resolution_info)
    ↓
If resolution_info → Show ResolutionIndicator (5s)
    ↓
Add to conversationHistory state
    ↓
Update currentQueryIndex
    ↓
If is_followup → ContextBadge shows
    ↓
Display Results
    ↓
User can: Open history panel (Cmd+H), Clear context ([×])
```

---

## 🔄 Dependencies Between Stories

```
7.1 (Detection & Resolution) ← Must be first
    ↓
7.2 (Enhanced History) ← Needs resolution info from 7.1
    ↓
7.3 (Conversation Panel) ← Needs history structure from 7.2
    ↓
7.4 (Indicators & Suggestions) ← Needs panel from 7.3
```

**Sequential implementation required** - each story builds on the previous.

---

## 🚦 Go/No-Go Criteria

**Ready to start when:**
- [ ] All 4 story documents reviewed and approved
- [ ] Developer Agent available for 1 week
- [ ] Backend and frontend servers running
- [ ] Stories 1-8 from agentic epic are complete
- [ ] Current system stable with no blocking bugs

**Abort if:**
- [ ] Current system has critical bugs
- [ ] Claude API quota issues
- [ ] Timeline pressure requires focus elsewhere

---

## 📚 Documentation

All story files created in `docs/sprint_artifacts/`:
- ✅ `story-agent-7.1-followup-detection-resolution.md`
- ✅ `story-agent-7.2-enhanced-history-storage.md`
- ✅ `story-agent-7.3-conversation-panel-ui.md`
- ✅ `story-agent-7.4-resolution-indicator-smart-features.md`

Supporting documents:
- ✅ `story-agent-7-enhanced-session-memory.md` (comprehensive overview)
- ✅ `docs/architecture-agentic-text2sql.md` (Section 7: Session Management)

---

## 🎉 Expected Outcomes

After completing all 4 stories:

**User can:**
- ✅ Ask "What about Q4?" and system understands
- ✅ Ask "Show me by region" and dimension is added
- ✅ Ask "Only electronics" and filter is applied
- ✅ See conversation history (last 10 queries)
- ✅ Clear conversation and start fresh
- ✅ Verify system interpretation
- ✅ Get AI suggestions for next questions

**System provides:**
- ✅ Context-aware intelligence (85%+ accuracy)
- ✅ Fast resolution (<2s overhead)
- ✅ Professional analyst-focused UI
- ✅ Trust through transparency
- ✅ Accelerated exploration

---

**Plan Status:** ✅ Complete and Ready for Implementation  
**Created By:** Business Analyst Agent (Mary)  
**Ready for:** Developer Agent (James)

---

*"The best analytics tools feel like conversations with a knowledgeable colleague."*

