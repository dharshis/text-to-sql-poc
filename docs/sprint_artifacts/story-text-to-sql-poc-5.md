# Story 1.5: Integration Testing and Demo Preparation

**Status:** Draft

---

## User Story

As a **product team member preparing for client demo**,
I want **end-to-end tested demo queries with polished UI and error handling**,
So that **we can confidently present the POC to stakeholders**.

---

## Acceptance Criteria

**Given** all previous stories are complete
**When** I test each of 5-8 prepared demo queries
**Then** each query completes successfully within 5 seconds

**And** multi-client switching works without data leakage
**And** validation correctly shows PASS for valid queries
**And** error handling displays user-friendly messages for failures
**And** UI is polished (loading states, proper spacing, professional colors)
**And** I have a demo script documenting:
- Which client to select for each query
- Expected results for each query
- Key talking points about validation and security
**And** backup plan exists (screen recording + screenshots)

---

## Implementation Details

### Tasks / Subtasks

1. **Prepare demo queries**
   - [ ] Create `docs/DEMO_QUERIES.md` document
   - [ ] Define 5-8 realistic market research queries:
     1. "Show me top 10 products by revenue in Q3 2024"
     2. "Compare electronics sales vs apparel across all regions"
     3. "What are the average transaction values by customer segment?"
     4. "Which clients had the highest year-over-year growth?"
     5. "Show me products with the highest profit margins"
     6. "What is the sales trend for electronics category over time?"
     7. "Which regions have the best performance for apparel products?"
     8. "Show me the top 5 brands by total revenue"
   - [ ] Test each query manually against the database
   - [ ] Document expected results for each query

2. **End-to-end integration testing**
   - [ ] Start backend server (Flask)
   - [ ] Start frontend server (Vite)
   - [ ] Test full flow for each demo query:
     - Select client
     - Enter query
     - Submit
     - Verify results appear
     - Verify chart renders
     - Verify table displays data
     - Verify SQL is shown
     - Verify validation shows PASS
   - [ ] Measure response times (all should be < 5 seconds)

3. **Multi-client switching tests**
   - [ ] Select Client 1, run query 1, note results
   - [ ] Switch to Client 2, run same query, verify DIFFERENT results
   - [ ] Verify no data leakage between clients
   - [ ] Test validation shows correct client_id in each case
   - [ ] Test 3-4 different clients to ensure isolation works

4. **Error scenario testing**
   - [ ] Test empty query submission → Error message displayed
   - [ ] Test no client selected → Submit button disabled
   - [ ] Test intentionally bad query → SQL error handled gracefully
   - [ ] Test validation failure (manually modify validator) → Red FAIL chips displayed
   - [ ] Test API timeout (simulate slow response) → Timeout error message
   - [ ] Test backend offline → Connection error displayed
   - [ ] Verify all errors show user-friendly messages (no stack traces)

5. **UI polish and refinement**
   - [ ] Review spacing and alignment across all components
   - [ ] Ensure color scheme is consistent (blue primary, green success, red error)
   - [ ] Verify loading spinner is centered and visible
   - [ ] Check that validation chips are properly color-coded
   - [ ] Ensure SQL display is collapsible and copy button works
   - [ ] Verify table pagination works smoothly
   - [ ] Test responsive behavior (minimum 1024px width)
   - [ ] Add client context display: "Viewing as: Client Name (Industry)"

6. **Performance validation**
   - [ ] Test each demo query 3 times, record average response time
   - [ ] Verify all queries complete in < 5 seconds
   - [ ] Check Claude API latency (typically 1-2 seconds)
   - [ ] Check SQL execution time (should be < 500ms for POC dataset)
   - [ ] If any query is slow, investigate and optimize

7. **Create demo script**
   - [ ] Create `docs/DEMO_SCRIPT.md`
   - [ ] Document setup steps:
     - Start backend server
     - Start frontend server
     - Open browser to localhost:5173
   - [ ] For each demo query, document:
     - Client to select
     - Query to enter
     - Expected chart type
     - Expected number of results
     - Key talking points
   - [ ] Add troubleshooting section
   - [ ] Add backup plan (show recording if live demo fails)

8. **Create backup materials**
   - [ ] Record screen capture of successful demo run (5-10 minutes)
   - [ ] Take screenshots of successful results for each query
   - [ ] Save screenshots to `docs/demo_screenshots/`
   - [ ] Document backup plan in demo script

9. **Final pre-demo checklist**
   - [ ] Test on actual demo machine (laptop for presentation)
   - [ ] Verify Claude API key is configured
   - [ ] Verify database exists and has data
   - [ ] Test internet connection stability (for Claude API)
   - [ ] Close unnecessary applications
   - [ ] Bookmark frontend URL in browser
   - [ ] Print or have demo script on second screen
   - [ ] Prepare talking points about:
     - Technical feasibility
     - Client isolation security
     - Local deployment advantage
     - Cost savings potential

10. **Create README documentation**
    - [ ] Create `README.md` in project root
    - [ ] Document project overview
    - [ ] Document setup instructions
    - [ ] Document how to run locally
    - [ ] Document demo queries
    - [ ] Add troubleshooting section

### Technical Summary

**Demo Query Examples:**

1. **Top Products Query**
   - Query: "Show me top 10 products by revenue in Q3 2024"
   - Expected: Bar chart, 10 rows, sorted by revenue descending
   - Validation: PASS (includes WHERE client_id)

2. **Category Comparison Query**
   - Query: "Compare electronics sales vs apparel across all regions"
   - Expected: Grouped bar chart, multiple regions, 2 categories
   - Validation: PASS

3. **Segment Analysis Query**
   - Query: "What are the average transaction values by customer segment?"
   - Expected: Bar chart, 3 segments, average revenue values
   - Validation: PASS

4. **Year-over-Year Growth Query**
   - Query: "Which clients had the highest year-over-year growth?"
   - Expected: Bar chart, client names, growth percentages
   - Validation: PASS

**Performance Targets:**
- Total response time: < 5 seconds
  - Claude API: ~1-2 seconds
  - SQL execution: < 500ms
  - Frontend render: < 100ms
  - Network overhead: < 500ms

**Demo Success Metrics:**
- All 5-8 queries work reliably
- No errors during demo run
- Response times within target
- Validation displays correctly
- Client switching works flawlessly

### Project Structure Notes

- **Files to create:**
  - `docs/DEMO_QUERIES.md`
  - `docs/DEMO_SCRIPT.md`
  - `docs/demo_screenshots/` (directory)
  - `README.md`

- **Files to modify:**
  - None (polish only)

- **Expected test locations:**
  - Manual testing checklist (no automated tests for this story)
  - Integration test results documented in DEMO_QUERIES.md

- **Estimated effort:** 3 story points

- **Prerequisites:** Stories 1.1, 1.2, 1.3, 1.4 (entire system must be functional)

### Key Code References

Refer to tech-spec.md sections:
- "Demo Preparation" (MVP Scope section)
- "Manual Testing Checklist" (page 35)
- "Deployment Strategy" (page 37)
- "Demo Day Checklist" (page 38)

---

## Context References

**Tech-Spec:** [tech-spec.md](../tech-spec.md) - Primary context document containing:
- Complete manual testing checklist
- Demo query preparation guidance
- Performance targets and metrics
- Deployment and demo day checklist
- Backup plan strategies

**Architecture:** [Architecture Diagram](../diagrams/diagram-text-to-sql-poc-architecture.excalidraw)
- Complete system flow for reference during testing

**Prerequisites:** All previous stories (1.1, 1.2, 1.3, 1.4) must be complete and functional

---

## Dev Agent Record

### Agent Model Used

<!-- Will be populated during dev-story execution -->

### Debug Log References

<!-- Will be populated during dev-story execution -->

### Completion Notes

<!-- Will be populated during dev-story execution -->

### Files Modified

<!-- Will be populated during dev-story execution -->

### Test Results

<!-- Will be populated during dev-story execution -->

---

## Review Notes

<!-- Will be populated during code review -->
