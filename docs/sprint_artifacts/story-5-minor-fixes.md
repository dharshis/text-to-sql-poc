# Story 5: Minor Code Fixes and Service Integration

**Epic:** Multi-Dataset Refactor
**Priority:** MEDIUM
**Estimated Effort:** 2 hours
**Status:** Ready for Development

---

## User Story

**As a** developer
**I want** all remaining hardcoded dataset references removed
**So that** the codebase is fully dataset-agnostic

---

## Background

There are a few minor hardcoded references and service integration updates needed:
1. Fix hardcoded table name in agentic_text2sql_service.py comment
2. Update service instantiation to pass dataset_id
3. Ensure all components are wired together correctly

---

## Acceptance Criteria

### AC1: Fix Hardcoded Comment in agentic_text2sql_service.py
- [ ] Open `backend/services/agentic_text2sql_service.py`
- [ ] Find line 1630 (approximate, search for "fact_market_size")
- [ ] Current comment:
  ```python
  metadata.append("--   Example: year >= (SELECT MAX(year) - 1 FROM fact_market_size WHERE is_forecast = 0)")
  ```
- [ ] Change to generic:
  ```python
  metadata.append("--   Example: year >= (SELECT MAX(year) - 1 FROM fact_table WHERE is_forecast = 0)")
  ```
- [ ] Or remove specific table reference entirely

### AC2: Update AgenticText2SQLService to Accept dataset_id
- [ ] Modify `__init__` method signature (around line 88):
  ```python
  def __init__(self, dataset_id=None):
      """Initialize service with dataset awareness."""
      self.dataset_id = dataset_id
      self.claude_service = ClaudeService(dataset_id=dataset_id)
      self.db_engine = get_engine()
      self.tools = self._initialize_tools()
      self.workflow = self._build_workflow()
      self.chat_sessions = {}
      logger.info(f"AgenticText2SQLService initialized for dataset: {dataset_id}")
  ```
- [ ] Add `dataset_id=None` parameter
- [ ] Pass dataset_id to ClaudeService
- [ ] Store dataset_id as instance variable
- [ ] Update docstring

### AC3: Update Service Instantiation in Routes
- [ ] Find where `AgenticText2SQLService()` is instantiated
- [ ] Likely in `backend/routes/query_routes.py` or similar
- [ ] Update to pass dataset_id:
  ```python
  # Example (adjust based on actual code)
  from config import Config
  dataset_id = Config.ACTIVE_DATASET  # or from request/session
  service = AgenticText2SQLService(dataset_id=dataset_id)
  ```
- [ ] Ensure dataset_id is available in route context

### AC4: Verify Dataset ID Flow
- [ ] Trace dataset_id from route → AgenticText2SQLService → ClaudeService
- [ ] Ensure dataset_id is consistently passed through the call stack
- [ ] Check that dataset_id reaches all components that need it:
  - ClaudeService (for metadata loading)
  - SQL validator (for validation config)
  - Query executor (for database path)

### AC5: Update Any Other Instantiation Points
- [ ] Search codebase for `ClaudeService()` instantiations
- [ ] Search codebase for `AgenticText2SQLService()` instantiations
- [ ] Update all to pass dataset_id parameter
- [ ] Document if any instantiation intentionally omits dataset_id

---

## Technical Notes

### Files to Modify
1. `backend/services/agentic_text2sql_service.py` (lines 88-97, 1630)
2. `backend/routes/query_routes.py` (or wherever services are instantiated)
3. Any other files instantiating these services

### Search Commands
```bash
cd backend
grep -r "ClaudeService()" .
grep -r "AgenticText2SQLService()" .
grep -r "fact_market_size" services/
```

### Dataset ID Sources
Dataset ID can come from:
1. **Config.ACTIVE_DATASET** - Global default
2. **Request parameter** - Per-request override
3. **Session storage** - User-selected dataset
4. **Route parameter** - Explicit in URL

Choose appropriate source based on architecture.

---

## Testing

### Unit Test
```python
# backend/tests/test_service_integration.py
import sys
sys.path.append('..')

from services.agentic_text2sql_service import AgenticText2SQLService
from services.claude_service import ClaudeService

def test_agentic_service_accepts_dataset_id():
    """Test AgenticText2SQLService accepts dataset_id parameter"""
    service = AgenticText2SQLService(dataset_id='em_market')
    assert service.dataset_id == 'em_market'
    assert service.claude_service.dataset_id == 'em_market'
    print("✓ AgenticText2SQLService passes dataset_id to ClaudeService")

def test_service_without_dataset_id():
    """Test services work without dataset_id (backward compatibility)"""
    service = AgenticText2SQLService()
    assert service.dataset_id is None
    assert service.claude_service.dataset_id is None
    print("✓ Services work without dataset_id (fallback behavior)")

def test_claude_service_dataset_id():
    """Test ClaudeService stores dataset_id"""
    claude = ClaudeService(dataset_id='em_market')
    assert claude.dataset_id == 'em_market'
    print("✓ ClaudeService stores dataset_id")

if __name__ == '__main__':
    print("Testing Service Integration")
    print("="*60)

    test_agentic_service_accepts_dataset_id()
    test_service_without_dataset_id()
    test_claude_service_dataset_id()

    print("="*60)
    print("✅ All tests passed!")
```

**Run test:**
```bash
cd backend
python tests/test_service_integration.py
```

### Integration Test
1. **Start backend:**
   ```bash
   cd backend
   python app.py
   ```

2. **Check logs for dataset_id:**
   - Should see: "AgenticText2SQLService initialized for dataset: em_market"
   - Should see: "Claude service initialized with model: X, dataset: em_market"

3. **Test API endpoint:**
   - Send query request
   - Verify dataset_id flows through services
   - Check generated SQL uses correct filtering

### Manual Verification
- [ ] Search codebase for "fact_market_size" - should only appear in metadata files
- [ ] Search codebase for "Dim_Corporation" - should only appear in metadata files
- [ ] Verify all service instantiations pass dataset_id
- [ ] Check logs show dataset awareness

---

## Definition of Done
- [ ] All acceptance criteria met
- [ ] Hardcoded table reference in comment fixed
- [ ] AgenticText2SQLService accepts dataset_id parameter
- [ ] Dataset ID passed to ClaudeService
- [ ] All service instantiations updated
- [ ] Unit tests pass
- [ ] Integration test successful
- [ ] No hardcoded dataset references remain in service code
- [ ] Code committed: "Story 5: Minor fixes and service integration for dataset awareness"

---

## Dependencies
- **Depends on:** Story 3 (ClaudeService refactor) - needs ClaudeService to accept dataset_id
- **Works with:** All other stories

---

## Notes
- This is a **cleanup story** - small changes but important for completeness
- Focus on consistency: dataset_id should flow through entire stack
- Don't break existing functionality - maintain backward compatibility
- Be thorough in searching for hardcoded references
- Log messages should show dataset_id for debugging

---

## Reference
See plan document section "Phase 3: Code Refactoring" → "3.3 Fix Hardcoded Comment" and "3.4 Update Service Instantiation"
