# Story 6: Comprehensive Testing & Validation Suite

**Epic:** Multi-Dataset Refactor
**Priority:** HIGH
**Estimated Effort:** 6 hours
**Status:** Ready for Development

---

## User Story

**As a** developer
**I want** a comprehensive test suite for the multi-dataset refactoring
**So that** I can verify all functionality works correctly and nothing broke

---

## Background

After refactoring for dataset-agnosticism, we need thorough testing to ensure:
1. All em_market functionality works as before (regression testing)
2. Configuration is correctly consumed by all components
3. Metadata loading works properly
4. SQL generation and validation are dataset-aware

---

## Acceptance Criteria

### AC1: Create Comprehensive Test Script
- [ ] Create file: `backend/tests/test_multi_dataset_refactor.py`
- [ ] Include test functions for:
  - Configuration loading
  - Metadata loading
  - ClaudeService initialization
  - SQL validator method-driven validation
  - Service integration
  - End-to-end SQL generation

### AC2: Configuration Tests
- [ ] Test `Config.get_dataset('em_market')` returns expected structure
- [ ] Verify `method` field is present and valid
- [ ] Verify `filter_field` is present and correct
- [ ] Test configuration for all 3 datasets (sales, market_size, em_market)
- [ ] Test graceful handling of invalid dataset_id

**Test code:**
```python
def test_config_structure():
    """Test that config has required fields for em_market"""
    from config import Config

    em_market = Config.get_dataset('em_market')

    # Check required fields
    assert 'client_isolation' in em_market
    assert 'method' in em_market['client_isolation']
    assert 'filter_field' in em_market['client_isolation']

    # Check values
    method = em_market['client_isolation']['method']
    filter_field = em_market['client_isolation']['filter_field']

    assert method in ['row-level', 'brand-hierarchy']
    assert filter_field == 'corp_id'

    print(f"✓ Config structure valid: method={method}, filter_field={filter_field}")
```

### AC3: Metadata Loading Tests
- [ ] Test MetadataLoader loads llm_instructions.md for em_market
- [ ] Test dataset_info.md loads successfully
- [ ] Verify loaded content contains expected keywords (corp_id, Dim_Brand, etc.)
- [ ] Test graceful handling of missing metadata files

**Test code:**
```python
def test_metadata_loading():
    """Test that metadata files load correctly"""
    from services.metadata_loader import MetadataLoader

    loader = MetadataLoader(dataset_id='em_market')

    # Load llm_instructions.md
    inst_docs = loader.search_metadata(file_pattern='llm_instructions.md')
    assert len(inst_docs) > 0, "llm_instructions.md not found"

    # Check content
    content = '\n'.join([doc.content for doc in inst_docs])
    assert 'corp_id' in content, "Missing corp_id references"
    assert 'Dim_Brand' in content, "Missing Dim_Brand references"

    print(f"✓ Metadata loaded: {len(inst_docs)} sections, {len(content)} chars")
```

### AC4: ClaudeService Tests
- [ ] Test ClaudeService initialization with dataset_id
- [ ] Test dataset-specific instructions loaded
- [ ] Test filter instruction generation (config-driven)
- [ ] Test prompt building logic (hybrid approach)
- [ ] Test backward compatibility (works without dataset_id)

**Test code:**
```python
def test_claude_service():
    """Test ClaudeService hybrid instruction loading"""
    from services.claude_service import ClaudeService

    # Initialize with dataset_id
    service = ClaudeService(dataset_id='em_market')

    # Check initialization
    assert service.dataset_id == 'em_market'
    assert hasattr(service, 'dataset_specific_instructions')

    # Check filter instruction
    filter_inst = service._get_filter_instruction(client_id=123, dataset_id='em_market')
    assert 'corp_id' in filter_inst or '123' in filter_inst

    print("✓ ClaudeService hybrid loading works")
```

### AC5: SQL Validator Tests
- [ ] Test row-level validation (with client_id)
- [ ] Test brand-hierarchy validation (with corp_id)
- [ ] Test validation with em_market config
- [ ] Test error messages use correct field names
- [ ] Test graceful handling of missing config

**Test code:**
```python
def test_sql_validator():
    """Test SQL validator method-driven validation"""
    from services.sql_validator import validate_sql_for_client_isolation
    from config import Config

    # Test with em_market config
    config = Config.get_dataset('em_market')

    # Valid query
    sql = """
    SELECT b.brand_name, SUM(f.market_size_value) as total
    FROM fact_market_size f
    JOIN Dim_Brand b ON f.brand_id = b.brand_id
    WHERE b.corp_id = 123
    GROUP BY b.brand_name
    """
    result = validate_sql_for_client_isolation(sql, 123, config)
    assert result.passed, "Valid query should pass validation"

    # Invalid query (missing corp_id)
    sql = "SELECT brand_name FROM Dim_Brand"
    result = validate_sql_for_client_isolation(sql, 123, config)
    assert not result.passed, "Query without filter should fail"

    print("✓ SQL validator method-driven validation works")
```

### AC6: Integration Tests
- [ ] Test full workflow: Config → ClaudeService → SQL Generation → Validation
- [ ] Test with actual em_market database queries
- [ ] Verify SQL generated matches expected patterns
- [ ] Test that validation passes for generated SQL

**Test code:**
```python
def test_end_to_end_integration():
    """Test end-to-end SQL generation and validation"""
    from services.claude_service import ClaudeService
    from services.sql_validator import validate_sql_for_client_isolation
    from services.agentic_text2sql_service import AgenticText2SQLService
    from config import Config

    # Initialize service with em_market
    service = AgenticText2SQLService(dataset_id='em_market')

    # Check integration
    assert service.dataset_id == 'em_market'
    assert service.claude_service.dataset_id == 'em_market'

    print("✓ End-to-end integration successful")
```

### AC7: Regression Tests
- [ ] Compare SQL generation before and after refactoring
- [ ] Ensure em_market queries produce functionally equivalent SQL
- [ ] Test at least 5 common query patterns:
  1. Simple brand listing
  2. Market size aggregation
  3. Geographic analysis
  4. Time-based query
  5. Category breakdown

**Test approach:**
- Save expected SQL outputs for test queries
- Run queries through refactored system
- Compare outputs (allow whitespace differences)

### AC8: Manual Testing Checklist
- [ ] Create manual testing checklist document
- [ ] Include step-by-step instructions for:
  - Starting backend with em_market
  - Testing through UI
  - Verifying SQL generation
  - Checking validation
  - Reviewing logs

**Checklist items:**
1. Start backend: `python app.py`
2. Check startup logs for dataset loading
3. Open frontend: `npm run dev`
4. Select em_market dataset
5. Select a corporation
6. Submit test queries (list provided)
7. Verify SQL includes corp_id filtering
8. Check results return successfully
9. Review backend logs for any errors

---

## Technical Notes

### Files to Create
1. `backend/tests/test_multi_dataset_refactor.py` (comprehensive test suite)
2. `backend/tests/manual_testing_checklist.md` (manual test steps)
3. `backend/tests/test_queries_em_market.json` (test query dataset)

### Test Structure
```python
# backend/tests/test_multi_dataset_refactor.py
"""
Comprehensive test suite for multi-dataset refactoring.
Tests configuration, metadata loading, service integration, and SQL generation.
"""

import sys
sys.path.append('..')

# Test sections:
# 1. Configuration Tests
# 2. Metadata Loading Tests
# 3. ClaudeService Tests
# 4. SQL Validator Tests
# 5. Service Integration Tests
# 6. End-to-End Tests
# 7. Regression Tests

if __name__ == '__main__':
    print("Multi-Dataset Refactoring Test Suite")
    print("="*70)

    # Run all test sections
    test_config_structure()
    test_metadata_loading()
    test_claude_service()
    test_sql_validator()
    test_service_integration()
    test_end_to_end_integration()

    print("="*70)
    print("✅ All tests passed!")
```

### Test Queries for em_market
Create `backend/tests/test_queries_em_market.json`:
```json
{
  "queries": [
    {
      "natural_language": "Show me all my brands",
      "expected_tables": ["Dim_Brand"],
      "expected_filter": "corp_id = "
    },
    {
      "natural_language": "Top 10 brands by market size",
      "expected_tables": ["Dim_Brand", "fact_market_size"],
      "expected_filter": "corp_id = "
    },
    {
      "natural_language": "Market size by country last 3 years",
      "expected_tables": ["Dim_Brand", "fact_market_size", "Dim_Country"],
      "expected_filter": "corp_id = ",
      "expected_patterns": ["MAX(year)"]
    }
  ]
}
```

---

## Testing

### Running the Test Suite
```bash
cd backend

# Run comprehensive test suite
python tests/test_multi_dataset_refactor.py

# Expected output:
# Multi-Dataset Refactoring Test Suite
# ======================================================================
# ✓ Config structure valid: method=brand-hierarchy, filter_field=corp_id
# ✓ Metadata loaded: 5 sections, 2453 chars
# ✓ ClaudeService hybrid loading works
# ✓ SQL validator method-driven validation works
# ✓ Service integration successful
# ✓ End-to-end integration successful
# ======================================================================
# ✅ All tests passed!
```

### Manual Testing
Follow `backend/tests/manual_testing_checklist.md`:
1. Configuration verification
2. Service startup
3. UI testing
4. SQL generation testing
5. Validation testing
6. Log review

### Regression Testing
```bash
# Save current outputs
python tests/save_baseline_outputs.py

# After refactoring
python tests/compare_outputs.py
# Should show: "All outputs match baseline (functional equivalence)"
```

---

## Definition of Done
- [ ] All acceptance criteria met
- [ ] Comprehensive test script created with 15+ test functions
- [ ] Configuration tests pass
- [ ] Metadata loading tests pass
- [ ] ClaudeService tests pass
- [ ] SQL validator tests pass
- [ ] Integration tests pass
- [ ] Regression tests show functional equivalence
- [ ] Manual testing checklist created and executed
- [ ] All tests documented with clear assertions
- [ ] Code committed: "Story 6: Comprehensive testing suite for multi-dataset refactor"

---

## Dependencies
- **Depends on:** All previous stories (1-5)
- **Final story** before documentation

---

## Notes
- This story validates ALL previous work
- **Do not skip** - critical for ensuring refactor success
- If any test fails, fix before proceeding to Story 7
- Tests should be **repeatable and deterministic**
- Document any manual testing observations
- Keep test data separate from production data

---

## Success Metrics
- All automated tests pass
- Manual testing checklist completed with no issues
- Regression tests show <= 5% difference in SQL output (whitespace/formatting only)
- No errors in logs during testing
- Performance is equivalent or better than before refactoring

---

## Reference
See plan document section "Phase 4: Testing & Validation"
