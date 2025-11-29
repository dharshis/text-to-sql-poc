# Story 4: Refactor SQL Validator for Method-Driven Validation

**Epic:** Multi-Dataset Refactor
**Priority:** HIGH
**Estimated Effort:** 4 hours
**Status:** Ready for Development

---

## User Story

**As a** developer
**I want** SQL validation to use config-driven filtering methods
**So that** validation adapts to different datasets without hardcoded table name checks

---

## Background

Currently, `backend/services/sql_validator.py` has hardcoded checks for `'Dim_Corporation'` table name (lines 95-96) to determine validation strategy. We need to make this config-driven using the `method` field from `client_isolation` config.

---

## Acceptance Criteria

### AC1: Remove Hardcoded Table Name Checks
- [ ] Remove hardcoded `'Dim_Corporation'` check from lines 82-119
- [ ] Replace with `method` field lookup from dataset_config
- [ ] No table names should appear in conditional logic

**Before (lines 95-96):**
```python
if client_table == 'Dim_Corporation':
    filter_method = "brand-hierarchy"
```

**After:**
```python
filter_method = client_iso.get('method', 'row-level')
```

### AC2: Update `validate_sql_for_client_isolation` Function
- [ ] Modify function starting at line 37
- [ ] Use `method` field from config to determine validation approach
- [ ] Use `filter_field` from config instead of hardcoding field names

**Expected logic:**
```python
def validate_sql_for_client_isolation(sql_query, expected_client_id, dataset_config=None):
    """Validate SQL query for client data isolation (dataset-aware)."""
    start_time = time.time()

    checks = []
    warnings = []
    passed = True

    sql_upper = sql_query.upper()
    sql_normalized = ' '.join(sql_query.split())

    # ==========================================
    # Check 1: Client/Corporation ID Filter (Method-Driven)
    # ==========================================

    # Determine isolation method from config
    filter_field = "client_id"  # Default
    filter_method = "row-level"  # Default

    if dataset_config and 'client_isolation' in dataset_config:
        client_iso = dataset_config['client_isolation']
        filter_method = client_iso.get('method', 'row-level')
        filter_field = client_iso.get('filter_field', 'client_id')

    # Validate based on method
    if filter_method == "brand-hierarchy":
        # Check for filter_field (e.g., corp_id) anywhere in query
        filter_patterns = [
            rf'\bWHERE\s+.*?\b{filter_field}\s*=\s*{expected_client_id}\b',
            rf'\bAND\s+.*?\b{filter_field}\s*=\s*{expected_client_id}\b',
            rf'\b{filter_field}\s*=\s*{expected_client_id}\b',
        ]

        filter_found = False
        for pattern in filter_patterns:
            if re.search(pattern, sql_normalized, re.IGNORECASE):
                filter_found = True
                break

        if not filter_found:
            passed = False
            checks.append({
                "name": "Client ID Filter",
                "status": "FAIL",
                "message": f"Missing {filter_field} = {expected_client_id} filter (method: {filter_method})"
            })
        else:
            checks.append({
                "name": "Client ID Filter",
                "status": "PASS",
                "message": f"Found {filter_field} = {expected_client_id} filter"
            })

    elif filter_method == "row-level":
        # Standard row-level filtering validation
        filter_patterns = [
            rf'\bWHERE\s+.*?\b{filter_field}\s*=\s*{expected_client_id}\b',
            rf'\bAND\s+.*?\b{filter_field}\s*=\s*{expected_client_id}\b',
        ]

        filter_found = any(re.search(p, sql_normalized, re.IGNORECASE) for p in filter_patterns)

        if not filter_found:
            passed = False
            checks.append({
                "name": "Client ID Filter",
                "status": "FAIL",
                "message": f"Missing WHERE {filter_field} = {expected_client_id}"
            })
        else:
            checks.append({
                "name": "Client ID Filter",
                "status": "PASS",
                "message": f"Found WHERE {filter_field} = {expected_client_id}"
            })

    # Rest of validation (single client check, read-only check) stays the same...

    execution_time = time.time() - start_time
    return ValidationResult(passed, checks, warnings, execution_time)
```

### AC3: Preserve Existing Validation Checks
- [ ] Check 2 (Single Client) remains unchanged
- [ ] Check 3 (Read-Only Operations) remains unchanged
- [ ] Only Check 1 (Client ID Filter) is refactored
- [ ] ValidationResult structure stays the same
- [ ] Execution time tracking preserved

### AC4: Update Error Messages
- [ ] Error messages use config-driven field names
- [ ] Example: "Missing corp_id = 123 filter (method: brand-hierarchy)"
- [ ] Not: "Missing client_id filter" (hardcoded)
- [ ] Error messages are informative about which method failed

### AC5: Handle Missing Config Gracefully
- [ ] If `dataset_config` is None, use default values
- [ ] Default: `filter_field="client_id"`, `filter_method="row-level"`
- [ ] Log warning if config is missing
- [ ] Don't crash on missing config

---

## Technical Notes

### Files to Modify
1. `backend/services/sql_validator.py` (lines 37-119)

### Key Changes
- **Lines 82-119:** Remove hardcoded `'Dim_Corporation'` check
- **Lines 86-92:** Add config-driven method/field extraction
- **Lines 99-140:** Update validation logic to use config values
- **Error messages:** Use dynamic filter_field instead of hardcoded "client_id"

### Validation Methods
1. **`row-level`**: Standard WHERE clause validation
   - Pattern: `WHERE filter_field = expected_client_id`
   - Stricter: Must be in WHERE or AND clause

2. **`brand-hierarchy`**: Relaxed validation (can be anywhere)
   - Pattern: `filter_field = expected_client_id` (anywhere in query)
   - More flexible: Allows complex join patterns

---

## Testing

### Unit Test
```python
# backend/tests/test_sql_validator_refactor.py
import sys
sys.path.append('..')

from services.sql_validator import validate_sql_for_client_isolation
from config import Config

def test_row_level_validation():
    """Test row-level validation with client_id"""
    dataset_config = {
        'name': 'Test Dataset',
        'client_isolation': {
            'method': 'row-level',
            'filter_field': 'client_id'
        }
    }

    # Valid query
    sql = "SELECT * FROM sales WHERE client_id = 123"
    result = validate_sql_for_client_isolation(sql, 123, dataset_config)
    assert result.passed, "Row-level validation should pass"
    print("✓ Row-level validation passes for valid query")

    # Invalid query (missing filter)
    sql = "SELECT * FROM sales"
    result = validate_sql_for_client_isolation(sql, 123, dataset_config)
    assert not result.passed, "Row-level validation should fail without filter"
    print("✓ Row-level validation fails for invalid query")

def test_brand_hierarchy_validation():
    """Test brand-hierarchy validation with corp_id"""
    dataset_config = {
        'name': 'EM Market',
        'client_isolation': {
            'method': 'brand-hierarchy',
            'filter_field': 'corp_id'
        }
    }

    # Valid query (corp_id in join)
    sql = """
    SELECT b.brand_name, SUM(f.market_size)
    FROM fact_market_size f
    JOIN Dim_Brand b ON f.brand_id = b.brand_id
    WHERE b.corp_id = 123
    GROUP BY b.brand_name
    """
    result = validate_sql_for_client_isolation(sql, 123, dataset_config)
    assert result.passed, "Brand-hierarchy validation should pass"
    print("✓ Brand-hierarchy validation passes for valid query")

    # Invalid query (missing corp_id)
    sql = "SELECT brand_name FROM Dim_Brand"
    result = validate_sql_for_client_isolation(sql, 123, dataset_config)
    assert not result.passed, "Brand-hierarchy validation should fail without filter"
    print("✓ Brand-hierarchy validation fails for invalid query")

def test_em_market_config_integration():
    """Test with actual em_market config"""
    dataset_config = Config.get_dataset('em_market')

    method = dataset_config['client_isolation'].get('method')
    filter_field = dataset_config['client_isolation'].get('filter_field')

    print(f"✓ EM Market config loaded: method={method}, filter_field={filter_field}")

    # Test with em_market-style query
    sql = f"""
    SELECT b.brand_name, SUM(f.market_size_value) as total
    FROM fact_market_size f
    JOIN Dim_Brand b ON f.brand_id = b.brand_id
    WHERE b.{filter_field} = 456
    GROUP BY b.brand_name
    """
    result = validate_sql_for_client_isolation(sql, 456, dataset_config)
    assert result.passed, f"Validation should pass for {filter_field} filter"
    print(f"✓ EM Market validation passes with {filter_field} filter")

def test_fallback_behavior():
    """Test fallback when config is missing"""
    # No config provided
    sql = "SELECT * FROM sales WHERE client_id = 789"
    result = validate_sql_for_client_isolation(sql, 789, None)
    assert result.passed, "Should use default validation"
    print("✓ Fallback validation works without config")

if __name__ == '__main__':
    print("Testing SQL Validator Refactoring")
    print("="*60)

    test_row_level_validation()
    test_brand_hierarchy_validation()
    test_em_market_config_integration()
    test_fallback_behavior()

    print("="*60)
    print("✅ All tests passed!")
```

**Run test:**
```bash
cd backend
python tests/test_sql_validator_refactor.py
```

### Integration Test
1. **Generate SQL with em_market dataset:**
   - Query: "Show me top brands by market size"
   - Expected SQL should have `WHERE b.corp_id = X`

2. **Validate generated SQL:**
   ```python
   from services.sql_validator import validate_sql_for_client_isolation
   from config import Config

   sql = "SELECT b.brand_name FROM Dim_Brand b WHERE b.corp_id = 123"
   config = Config.get_dataset('em_market')
   result = validate_sql_for_client_isolation(sql, 123, config)
   assert result.passed
   ```

3. **Test with invalid SQL:**
   ```python
   sql = "SELECT brand_name FROM Dim_Brand"  # Missing corp_id filter
   result = validate_sql_for_client_isolation(sql, 123, config)
   assert not result.passed
   ```

### Manual Testing
- [ ] Generate SQL for em_market dataset
- [ ] Check validation passes with corp_id filter
- [ ] Check validation fails without corp_id filter
- [ ] Verify error messages mention "corp_id" (not "client_id")
- [ ] Check logs show method-driven validation

---

## Definition of Done
- [ ] All acceptance criteria met
- [ ] Hardcoded `'Dim_Corporation'` check removed
- [ ] Validation uses config `method` and `filter_field`
- [ ] Unit tests pass
- [ ] Integration tests successful
- [ ] Error messages are config-driven
- [ ] Graceful handling of missing config
- [ ] Code committed: "Story 4: Refactor SQL validator for method-driven validation"

---

## Dependencies
- **Depends on:** Story 1 (config enhancement) - needs method/filter_field in config
- **Works with:** Story 3 (ClaudeService refactor) - both consume same config
- **Blocks:** Story 6 (testing suite)

---

## Notes
- This is a **critical security component** - test thoroughly
- Validation must catch queries without proper filtering
- Error messages should be helpful for debugging
- Don't break backward compatibility (fallback to defaults)
- Keep existing validation checks (single client, read-only) unchanged

---

## Reference
See plan document section "Phase 3: Code Refactoring" → "3.2 Refactor sql_validator.py"
