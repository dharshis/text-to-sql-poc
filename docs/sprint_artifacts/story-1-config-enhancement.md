# Story 1: Configuration Enhancement for Dataset-Agnostic Filtering

**Epic:** Multi-Dataset Refactor
**Priority:** HIGH
**Estimated Effort:** 4 hours
**Status:** Ready for Development

---

## User Story

**As a** developer setting up a new company dataset
**I want** dataset-agnostic configuration for client isolation
**So that** I can configure filtering methods without changing code

---

## Background

Currently, the config.json has dataset-specific field names (`client_table: "Dim_Corporation"`) that are checked in code with hardcoded conditionals. We need to make this generic by introducing a `method` field that drives behavior.

---

## Acceptance Criteria

### AC1: Update em_market Configuration
- [ ] Edit `backend/config.json` for em_market dataset
- [ ] Add `"method": "brand-hierarchy"` to `client_isolation` section
- [ ] Rename `client_id_field` → `filter_field` with value `"corp_id"`
- [ ] Add `"filter_table": "Dim_Brand"` (table used for filtering joins)
- [ ] Remove or update `isolation_info` to be description-only (not implementation details)

**Expected config.json structure for em_market:**
```json
"em_market": {
  "id": "em_market",
  "name": "Euromonitor Market Data",
  "db_path": "data/em_market/em_market.db",
  "description": "Global market research data for consumer goods",
  "client_isolation": {
    "enabled": true,
    "method": "brand-hierarchy",
    "filter_field": "corp_id",
    "filter_table": "Dim_Brand",
    "description": "Corporation-based isolation through brand hierarchy (Dim_Corporation → Dim_Brand)"
  }
}
```

### AC2: Update sales Configuration (for consistency, but not implementation yet)
- [ ] Add `"method": "row-level"` to sales dataset `client_isolation`
- [ ] Rename `client_id_field` → `filter_field` with value `"client_id"`
- [ ] Add description field

**Expected config.json structure for sales:**
```json
"sales": {
  "id": "sales",
  "name": "Sales Demo Dataset",
  "db_path": "data/text_to_sql_poc.db",
  "description": "Retail sales demonstration data",
  "client_isolation": {
    "enabled": true,
    "method": "row-level",
    "filter_field": "client_id",
    "description": "Row-level client_id filtering on fact tables"
  }
}
```

### AC3: Update market_size Configuration (for consistency, but not implementation yet)
- [ ] Add `"method": "row-level"` to market_size dataset `client_isolation`
- [ ] Rename `client_id_field` → `filter_field` with value `"client_id"`
- [ ] Add description field

### AC4: Configuration Validation
- [ ] Config.json is valid JSON (no syntax errors)
- [ ] All three datasets (sales, market_size, em_market) have consistent structure
- [ ] `method` field is present with valid values: `"row-level"` or `"brand-hierarchy"`
- [ ] `filter_field` is specified for all datasets

### AC5: Frontend Environment Variable
- [ ] Create `frontend/.env` file if it doesn't exist
- [ ] Add `VITE_API_BASE_URL=http://localhost:5001`
- [ ] Update `frontend/src/services/api.js` line 10:
  ```javascript
  // Before
  const API_BASE_URL = 'http://localhost:5001';

  // After
  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5001';
  ```
- [ ] Test that frontend still connects to backend after change

---

## Technical Notes

### Files to Modify
1. `backend/config.json` (lines 23-55 approximately)
2. `frontend/.env` (create new)
3. `frontend/src/services/api.js` (line 10)

### Configuration Fields Explanation
- **`method`**: Determines how filtering is applied
  - `"row-level"`: Standard WHERE clause with filter_field
  - `"brand-hierarchy"`: Requires join through filter_table

- **`filter_field`**: The field name for filtering (generic, not hardcoded)
  - Examples: `client_id`, `corp_id`, `tenant_id`, `company_id`

- **`filter_table`**: (Only for brand-hierarchy method) The table to join for filtering
  - Example: For em_market, filter through Dim_Brand table

### Backward Compatibility
- Keep old field names temporarily (e.g., `client_id_field`) for reference
- Code will be updated in Story 3 and 4 to use new field names
- This story only updates configuration, not code consumption

---

## Testing

### Manual Testing
1. **Config Validation:**
   ```bash
   cd backend
   python -c "import json; json.load(open('config.json'))"
   # Should not error
   ```

2. **Config Access Test:**
   ```python
   from config import Config
   em_market = Config.get_dataset('em_market')
   assert em_market['client_isolation']['method'] == 'brand-hierarchy'
   assert em_market['client_isolation']['filter_field'] == 'corp_id'
   print("✓ Config updated successfully")
   ```

3. **Frontend API URL Test:**
   - Start backend: `cd backend && python app.py`
   - Start frontend: `cd frontend && npm run dev`
   - Open browser, check Network tab
   - Verify requests go to http://localhost:5001

### Verification Checklist
- [ ] Backend starts without errors
- [ ] Frontend connects to backend
- [ ] Config.get_dataset() returns expected structure for all datasets
- [ ] No breaking changes (code doesn't use new fields yet, so should still work)

---

## Definition of Done
- [ ] All acceptance criteria met
- [ ] Configuration validated (JSON syntax correct)
- [ ] Frontend environment variable working
- [ ] Manual testing completed
- [ ] Code committed with clear message: "Story 1: Add dataset-agnostic config fields"

---

## Dependencies
None - this is the first story

---

## Notes
- This story only updates configuration files
- Code changes to consume these new config fields happen in Story 3 and 4
- The system should continue working with existing code after this change
