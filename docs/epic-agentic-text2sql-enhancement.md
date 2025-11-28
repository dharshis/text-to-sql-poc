# Epic: Agentic Text-to-SQL Enhancement

**Epic ID:** EPIC-AGENTIC-001  
**Status:** Planned  
**Priority:** High  
**Created:** 2025-11-27  
**Owner:** Development Team  

---

## Epic Overview

**Goal:** Transform the current single-shot Text-to-SQL POC into an intelligent agentic system powered by LangGraph that can detect ambiguity, plan workflows, self-correct errors, maintain conversation context, and explain results in natural language.

**Business Value:** 
- Demonstrates technical superiority over Number Station
- Positions in-house solution as "insights engine" not just "query tool"
- Strengthens build vs. buy business case
- Proves AI sophistication and customization potential

**Strategic Impact:**
This enhancement proves the organization can build not just comparable but superior functionality to external vendors, with sophisticated multi-agent intelligence that demonstrates cutting-edge AI capabilities.

---

## Success Criteria

### Epic Complete When:

1. ✅ **Natural Language Explanations Working:** System generates clear insights for all demo queries
2. ✅ **Clarification Flow Working:** System detects ambiguous queries and asks for clarification
3. ✅ **Self-Correction Working:** System recovers from SQL errors through reflection and retry
4. ✅ **Conversation Context Working:** Follow-up queries work seamlessly with context awareness
5. ✅ **Performance Acceptable:** Response times ≤10 seconds including all agent steps
6. ✅ **Demo Ready:** 5-8 prepared scenarios work reliably end-to-end

---

## User Stories

This epic is composed of 8 user stories:

| Story ID | Title | Priority | Estimate | Dependencies |
|----------|-------|----------|----------|--------------|
| STORY-AGENT-1 | LangGraph Foundation & State Machine | Must Have | 3 days | None |
| STORY-AGENT-2 | Planning Agent & Tool Infrastructure | Must Have | 3 days | STORY-AGENT-1 |
| STORY-AGENT-3 | SQL Generation with Tools | Must Have | 2 days | STORY-AGENT-2 |
| STORY-AGENT-4 | Reflection Agent & Retry Logic | Must Have | 2 days | STORY-AGENT-3 |
| STORY-AGENT-5 | Clarification Detection Agent | Must Have | 3 days | STORY-AGENT-2 |
| STORY-AGENT-6 | Natural Language Explanation Generator | Must Have | 2 days | STORY-AGENT-3 |
| STORY-AGENT-7 | Session Management & Conversation Context | Must Have | 2 days | STORY-AGENT-1 |
| STORY-AGENT-8 | Frontend Agentic UI Components | Must Have | 3 days | STORY-AGENT-4, 6, 7 |

**Total Estimated Effort:** 20 days (4 weeks with testing/integration)

---

## Timeline

**Phase 1 (Week 1): Core Infrastructure**
- STORY-AGENT-1: LangGraph Foundation (Days 1-3)
- STORY-AGENT-2: Planning Agent & Tools (Days 4-5)
- STORY-AGENT-3: SQL Generation (Day 5)

**Phase 2 (Week 2): Intelligence Features**
- STORY-AGENT-4: Reflection & Retry (Days 6-7)
- STORY-AGENT-5: Clarification Detection (Days 8-10)
- STORY-AGENT-6: Natural Language Explanations (Days 8-9)

**Phase 3 (Week 3): Context & Frontend**
- STORY-AGENT-7: Session Management (Days 11-12)
- STORY-AGENT-8: Frontend Components (Days 13-15)

**Phase 4 (Week 4): Integration & Demo**
- Integration testing (Days 16-17)
- Demo preparation (Days 18-19)
- Buffer for issues (Day 20)

---

## Technical Approach

**Architecture Pattern:** Multi-agent state machine using LangGraph

**Core Components:**
1. **AgentState (TypedDict):** Central state management
2. **StateGraph Nodes:** Specialized agent functions
3. **Conditional Edges:** Intelligent routing logic
4. **Tool Pattern:** Reusable, modular tools
5. **Session Storage:** In-memory conversation history

**Simplified Approach:**
- ✅ Direct schema retrieval (no hybrid retrieval)
- ✅ Simple metadata search (keyword-based or static file)
- ✅ In-memory sessions (no Redis for POC)
- ✅ Existing Claude service integration

---

## Dependencies & Risks

### External Dependencies
- LangGraph library (`langgraph>=0.0.20`)
- Existing Claude API access (no change)
- Existing database and schema (no change)

### Technical Risks
1. **LangGraph Learning Curve:** Mitigated by studying inspiration code first
2. **Performance with Multiple API Calls:** Mitigated by setting max_iterations=2-3
3. **Clarification Quality:** Mitigated by careful prompt engineering and testing

### Integration Points
- Existing `/query` endpoint maintained for backward compatibility
- New `/query-agentic` endpoint for enhanced flow
- Shared database, validation, and execution services

---

## Out of Scope

**Not Included in This Epic:**
- Hybrid retrieval (Vector + BM25)
- Advanced sample data retrieval with embeddings
- Production-grade session persistence (Redis/database)
- Multi-database support
- Query plan optimization for multi-query decomposition
- Fine-tuned models
- Advanced visualization changes

---

## Acceptance Criteria (Epic Level)

### Functional Requirements
- [ ] System detects and handles ambiguous queries with clarification
- [ ] System self-corrects SQL errors through reflection (max 2-3 iterations)
- [ ] System maintains conversation context for follow-up queries
- [ ] System generates natural language explanations for all successful queries
- [ ] All 5-8 demo scenarios work reliably end-to-end

### Non-Functional Requirements
- [ ] Response time ≤10 seconds per query (including retries and explanations)
- [ ] State machine logic is clear and debuggable
- [ ] Backward compatibility maintained with existing `/query` endpoint
- [ ] Error handling is graceful (no crashes on edge cases)
- [ ] Logging provides visibility into agent decision-making

### Demo Readiness
- [ ] Clarification scenario works (ambiguous query → questions → resolution)
- [ ] Error recovery scenario works (bad SQL → reflection → retry → success)
- [ ] Conversation context scenario works (initial query → 2+ follow-ups)
- [ ] Natural language explanations are clear and insightful
- [ ] UI shows agent workflow transparently

---

## Definition of Done

### Code Quality
- [ ] All code reviewed and approved
- [ ] Unit tests written for agent nodes and tools
- [ ] Integration tests for state machine workflows
- [ ] Code follows existing project conventions
- [ ] No linter errors or warnings

### Documentation
- [ ] Technical documentation updated (architecture diagrams, state machine flow)
- [ ] API documentation for `/query-agentic` endpoint
- [ ] README updated with agentic mode instructions
- [ ] Demo script prepared with 5-8 scenarios

### Testing
- [ ] Unit test coverage ≥70% for new services
- [ ] All demo scenarios tested manually and pass
- [ ] Performance benchmarks meet targets (≤10s response time)
- [ ] Error scenarios tested (API failures, invalid queries, max iterations)

### Demo Preparation
- [ ] Demo environment set up and tested
- [ ] Demo queries prepared and validated
- [ ] Presentation slides created explaining agentic approach
- [ ] Backup plan ready (screen recording of successful demo)

---

## Stakeholder Communication

**Progress Updates:** Weekly standups during 4-week development cycle

**Demo Date:** End of Week 4 (tentative)

**Key Stakeholders:**
- Technical Leadership (architecture review)
- Product Management (demo preparation)
- Business Stakeholders (final demo audience)

---

## Related Documents

- **Product Brief:** `docs/product-brief-agentic-text2sql-enhancement.md`
- **Original POC Brief:** `docs/product-brief-text-to-sql-poc-2025-11-25.md`
- **Technical Spec:** `docs/tech-spec.md`
- **Inspiration Code:** `docs/inspiration/agentic_text2sql.py`

---

**Epic Status:** ✅ Defined - Ready for Sprint Planning

**Next Steps:** 
1. Review story breakdown with team
2. Assign stories to sprint(s)
3. Begin STORY-AGENT-1 (LangGraph Foundation)

