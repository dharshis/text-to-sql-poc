# Story 3: Refactor ClaudeService for Hybrid Instruction Loading

**Epic:** Multi-Dataset Refactor
**Priority:** HIGH
**Estimated Effort:** 6 hours
**Status:** Ready for Development

---

## User Story

**As a** developer
**I want** ClaudeService to load instructions from metadata instead of hardcoded prompts
**So that** SQL generation adapts to different datasets without code changes

---

## Background

Currently, `backend/services/claude_service.py` has hardcoded `DATABASE_SCHEMA` (lines 14-55) and `SYSTEM_PROMPT` (lines 58-85) with sales-specific knowledge. It also has conditional logic checking for `'Dim_Corporation'` table name (lines 133-137).

We need to:
1. Remove hardcoded schema/prompt
2. Create generic base instructions in code (applies to ALL datasets)
3. Load dataset-specific examples from metadata
4. Make filtering instructions config-driven (not table-name-driven)

---

## Acceptance Criteria

### AC1: Remove Hardcoded Schema and Prompt
- [ ] Delete lines 14-86 in `backend/services/claude_service.py`:
  - `DATABASE_SCHEMA = """..."""` (lines 14-55)
  - `SYSTEM_PROMPT = f"""..."""` (lines 58-85)
- [ ] Ensure no references to these constants remain in the file

### AC2: Add Metadata Loader Import
- [ ] Add import after line 9:
  ```python
  from services.metadata_loader import MetadataLoader
  ```

### AC3: Create Base LLM Instructions Constant
- [ ] Add after line 11 (after imports, before class definition):
  ```python
  # Base LLM instructions that apply to ALL datasets (generic SQL rules)
  BASE_LLM_INSTRUCTIONS = """You are an expert SQL query generator for SQLite databases.

  ## SQL Generation Rules

  1. Use ONLY the tables and columns defined in the provided schema
  2. Generate valid SQLite syntax
  3. Return ONLY the SQL query - no explanations, no markdown, no code blocks
  4. Use appropriate JOINs when querying multiple tables
  5. For aggregations, use GROUP BY and appropriate aggregate functions
  6. Limit results to 100 rows unless explicitly requested otherwise
  7. Use proper date formats (YYYY-MM-DD) for date comparisons
  8. Always apply the client/corporation filter as instructed

  ## General Best Practices

  - Use table aliases for clarity (e.g., `FROM sales s JOIN products p`)
  - For "last N years" queries, use fact table's MAX(year), NOT current date
    Example: `year >= (SELECT MAX(year) - N FROM fact_table WHERE is_forecast = 0)`
  - Use proper aggregate functions: SUM(), COUNT(), AVG(), MIN(), MAX()
  - Always order results meaningfully (typically by the metric DESC or by date)

  {DYNAMIC_SCHEMA_PLACEHOLDER}

  {DATASET_SPECIFIC_INSTRUCTIONS}

  {FILTER_INSTRUCTION}
  """
  ```
- [ ] Constant is module-level (before ClaudeService class)
- [ ] Contains placeholders: `{DYNAMIC_SCHEMA_PLACEHOLDER}`, `{DATASET_SPECIFIC_INSTRUCTIONS}`, `{FILTER_INSTRUCTION}`

### AC4: Update `__init__` Method Signature
- [ ] Modify `__init__` method signature (around line 91):
  ```python
  def __init__(self, api_key=None, dataset_id=None):
      """
      Initialize Claude service with hybrid instruction loading.

      Args:
          api_key (str, optional): Anthropic API key
          dataset_id (str, optional): Dataset ID for loading metadata
      """
  ```
- [ ] Add `dataset_id=None` parameter
- [ ] Update docstring

### AC5: Load Dataset-Specific Instructions in `__init__`
- [ ] Add after existing initialization (around line 106):
  ```python
  # Load dataset-specific instructions from metadata
  self.dataset_id = dataset_id
  self.dataset_specific_instructions = self._load_dataset_instructions(dataset_id)

  logger.info(f"Claude service initialized with model: {self.model}, dataset: {dataset_id}")
  ```
- [ ] Store dataset_id as instance variable
- [ ] Store loaded instructions as instance variable

### AC6: Implement `_load_dataset_instructions` Method
- [ ] Add new private method after `__init__`:
  ```python
  def _load_dataset_instructions(self, dataset_id):
      """Load dataset-specific instructions from metadata (hybrid approach)."""
      if not dataset_id:
          logger.warning("No dataset_id provided, no dataset-specific instructions loaded")
          return ""

      try:
          metadata_loader = MetadataLoader(dataset_id=dataset_id)
          # Load llm_instructions.md (dataset-specific examples and patterns)
          docs = metadata_loader.search_metadata(file_pattern='llm_instructions.md')
          if docs:
              # Combine all sections
              instructions = "\n\n".join([doc.content for doc in docs])
              logger.info(f"Loaded dataset-specific instructions from llm_instructions.md ({len(instructions)} chars)")
              return instructions
          else:
              logger.warning(f"No llm_instructions.md found for dataset {dataset_id}, using generic instructions only")
              return ""
      except Exception as e:
          logger.error(f"Error loading dataset instructions for {dataset_id}: {e}")
          return ""
  ```
- [ ] Handles missing dataset_id gracefully (returns empty string)
- [ ] Handles missing metadata file gracefully (logs warning, returns empty string)
- [ ] Handles exceptions gracefully (logs error, returns empty string)

### AC7: Refactor `_get_filter_instruction` Method
- [ ] Update method (lines 108-145) to be config-driven:
  ```python
  def _get_filter_instruction(self, client_id, dataset_id=None):
      """
      Get dataset-specific filtering instruction for SQL generation.

      Args:
          client_id (int): Client/Corporation ID
          dataset_id (str, optional): Dataset identifier

      Returns:
          str: Filtering instruction for the LLM
      """
      if not dataset_id:
          return f'ALWAYS include "WHERE client_id = {client_id}" in your queries'

      try:
          dataset_config = Config.get_dataset(dataset_id)

          if 'client_isolation' in dataset_config:
              client_iso = dataset_config['client_isolation']
              method = client_iso.get('method', 'row-level')
              filter_field = client_iso.get('filter_field', 'client_id')

              if method == 'brand-hierarchy':
                  filter_table = client_iso.get('filter_table', 'Dim_Brand')
                  return (f'MANDATORY: Filter by {filter_field} = {client_id} '
                         f'through {filter_table} join. Refer to dataset-specific examples for hierarchy details.')
              elif method == 'row-level':
                  return f'ALWAYS include "WHERE {filter_field} = {client_id}" in your queries'

          # Default fallback
          return f'ALWAYS include "WHERE client_id = {client_id}" in your queries'

      except Exception as e:
          logger.warning(f"Error loading dataset config for {dataset_id}: {e}")
          return f'ALWAYS include "WHERE client_id = {client_id}" in your queries'
  ```
- [ ] Remove hardcoded `'Dim_Corporation'` check (old lines 133-137)
- [ ] Use `method` field from config
- [ ] Use `filter_field` from config
- [ ] Use `filter_table` from config (for brand-hierarchy method)

### AC8: Update `generate_sql` Method
- [ ] Update method (line 148+) to use hybrid instructions:
  ```python
  def generate_sql(self, natural_language_query, client_id, client_name=None,
                   custom_schema=None, dataset_id=None):
      """
      Generate SQL query from natural language using Claude (hybrid approach).

      Args:
          natural_language_query (str): User's natural language query
          client_id (int): Client/Corporation ID for filtering
          client_name (str, optional): Client name for context
          custom_schema (str, optional): Database schema (dynamically fetched)
          dataset_id (str, optional): Dataset identifier for filtering rules
      """
      try:
          # Start with base instructions (generic SQL rules)
          system_prompt = BASE_LLM_INSTRUCTIONS

          # Add database schema
          if custom_schema:
              system_prompt = system_prompt.replace(
                  "{DYNAMIC_SCHEMA_PLACEHOLDER}",
                  f"\n## Database Schema\n\n{custom_schema}\n"
              )
          else:
              system_prompt = system_prompt.replace("{DYNAMIC_SCHEMA_PLACEHOLDER}", "")

          # Add dataset-specific instructions (examples, patterns)
          if self.dataset_specific_instructions:
              system_prompt = system_prompt.replace(
                  "{DATASET_SPECIFIC_INSTRUCTIONS}",
                  f"\n## Dataset-Specific Patterns\n\n{self.dataset_specific_instructions}\n"
              )
          else:
              system_prompt = system_prompt.replace("{DATASET_SPECIFIC_INSTRUCTIONS}", "")

          # Add runtime filter instruction
          filter_instruction = self._get_filter_instruction(client_id, dataset_id or self.dataset_id)
          system_prompt = system_prompt.replace(
              "{FILTER_INSTRUCTION}",
              f"\n## Client Filtering Requirement\n\n{filter_instruction}\n"
          )

          # Replace client_id placeholders in examples
          system_prompt = system_prompt.replace("{client_id}", str(client_id))

          # Rest of the method stays the same (API call logic)
          # ... existing code for calling Claude API ...
  ```
- [ ] Uses `BASE_LLM_INSTRUCTIONS` as template
- [ ] Replaces `{DYNAMIC_SCHEMA_PLACEHOLDER}` with custom_schema
- [ ] Replaces `{DATASET_SPECIFIC_INSTRUCTIONS}` with loaded metadata
- [ ] Replaces `{FILTER_INSTRUCTION}` with config-driven instruction
- [ ] Replaces `{client_id}` with actual value
- [ ] Preserves existing API call logic (don't change the Claude API interaction)

### AC9: Update Service Instantiation
- [ ] Find where `ClaudeService()` is instantiated (likely in `agentic_text2sql_service.py`)
- [ ] Pass `dataset_id` parameter:
  ```python
  self.claude_service = ClaudeService(dataset_id=dataset_id)
  ```
- [ ] Ensure dataset_id is available in the calling context

---

## Technical Notes

### Files to Modify
1. `backend/services/claude_service.py` - Main refactoring
2. `backend/services/agentic_text2sql_service.py` - Update instantiation (if needed)
3. Any other files that instantiate `ClaudeService`

### Key Changes Summary
- **Lines 14-86:** DELETE (hardcoded schema/prompt)
- **After line 11:** ADD `BASE_LLM_INSTRUCTIONS` constant
- **Line 91:** UPDATE `__init__` signature (add dataset_id param)
- **After line 106:** ADD metadata loading logic
- **New method:** ADD `_load_dataset_instructions()`
- **Lines 108-145:** REFACTOR `_get_filter_instruction()` (config-driven)
- **Line 148+:** REFACTOR `generate_sql()` (hybrid prompt building)

### Backward Compatibility
- If `dataset_id` is None, system uses fallback behavior
- Generic instructions still work without metadata
- Graceful degradation if metadata loading fails

---

## Testing

### Unit Test
```python
# backend/tests/test_claude_service_refactor.py
import sys
sys.path.append('..')

from services.claude_service import ClaudeService, BASE_LLM_INSTRUCTIONS
from config import Config

def test_base_instructions_exist():
    """Test that BASE_LLM_INSTRUCTIONS constant exists"""
    assert BASE_LLM_INSTRUCTIONS is not None
    assert 'SQL Generation Rules' in BASE_LLM_INSTRUCTIONS
    assert '{DYNAMIC_SCHEMA_PLACEHOLDER}' in BASE_LLM_INSTRUCTIONS
    print("✓ BASE_LLM_INSTRUCTIONS defined")

def test_claude_service_initialization():
    """Test ClaudeService initializes with dataset_id"""
    service = ClaudeService(dataset_id='em_market')
    assert service.dataset_id == 'em_market'
    assert hasattr(service, 'dataset_specific_instructions')
    print("✓ ClaudeService initialized with dataset_id")

def test_dataset_instructions_loaded():
    """Test that em_market metadata loads"""
    service = ClaudeService(dataset_id='em_market')
    instructions = service.dataset_specific_instructions
    assert instructions is not None
    if instructions:  # May be empty if metadata not created yet
        assert 'em_market' in instructions.lower() or 'corp_id' in instructions
        print(f"✓ Dataset instructions loaded ({len(instructions)} chars)")
    else:
        print("⚠ No dataset instructions loaded (metadata file may not exist yet)")

def test_filter_instruction_config_driven():
    """Test that filter instruction uses config method field"""
    service = ClaudeService(dataset_id='em_market')
    filter_inst = service._get_filter_instruction(client_id=123, dataset_id='em_market')

    # Check that it uses config-driven approach
    config = Config.get_dataset('em_market')
    method = config['client_isolation'].get('method', 'row-level')
    filter_field = config['client_isolation'].get('filter_field', 'client_id')

    assert filter_field in filter_inst
    print(f"✓ Filter instruction uses config method: {method}, field: {filter_field}")

def test_generate_sql_prompt_building():
    """Test that generate_sql builds prompt correctly"""
    service = ClaudeService(dataset_id='em_market')

    # Mock the prompt building (don't actually call Claude API)
    # This tests the prompt assembly logic
    system_prompt = BASE_LLM_INSTRUCTIONS

    # Test schema replacement
    test_schema = "CREATE TABLE test (id INT)"
    system_prompt = system_prompt.replace(
        "{DYNAMIC_SCHEMA_PLACEHOLDER}",
        f"\n## Database Schema\n\n{test_schema}\n"
    )
    assert "CREATE TABLE test" in system_prompt

    # Test dataset instructions replacement
    system_prompt = system_prompt.replace(
        "{DATASET_SPECIFIC_INSTRUCTIONS}",
        "\n## Dataset-Specific Patterns\n\nTest pattern\n"
    )
    assert "Test pattern" in system_prompt

    print("✓ Prompt building logic works")

if __name__ == '__main__':
    print("Testing ClaudeService Refactoring")
    print("="*60)

    test_base_instructions_exist()
    test_claude_service_initialization()
    test_dataset_instructions_loaded()
    test_filter_instruction_config_driven()
    test_generate_sql_prompt_building()

    print("="*60)
    print("✅ All tests passed!")
```

**Run test:**
```bash
cd backend
python tests/test_claude_service_refactor.py
```

### Integration Test
- [ ] Start backend with em_market dataset active
- [ ] Generate SQL for test query: "Show me top 10 brands by market size"
- [ ] Verify generated SQL includes `corp_id` filtering (not client_id)
- [ ] Verify generated SQL references em_market tables (Dim_Brand, fact_market_size)
- [ ] Check logs for metadata loading confirmation

### Manual Testing
1. **Without metadata:**
   - Comment out Story 2 metadata files temporarily
   - Initialize ClaudeService with dataset_id='em_market'
   - Should log warning but not crash
   - Should use generic instructions only

2. **With metadata:**
   - Ensure Story 2 metadata files exist
   - Initialize ClaudeService with dataset_id='em_market'
   - Should log success message with instruction length
   - Instructions should include em_market examples

3. **Backward compatibility:**
   - Initialize ClaudeService without dataset_id: `ClaudeService()`
   - Should work with fallback behavior
   - Should log warning about missing dataset_id

---

## Definition of Done
- [ ] All acceptance criteria met
- [ ] Hardcoded schema/prompt removed
- [ ] Hybrid instruction loading implemented
- [ ] Filter instruction is config-driven (no hardcoded table names)
- [ ] Unit tests pass
- [ ] Integration test successful
- [ ] Backward compatibility verified
- [ ] Code committed: "Story 3: Refactor ClaudeService for hybrid instruction loading"

---

## Dependencies
- **Depends on:** Story 2 (metadata creation) - needs llm_instructions.md to test fully
- **Depends on:** Story 1 (config enhancement) - needs method/filter_field in config
- **Blocks:** Story 6 (testing suite)

---

## Notes
- This is the **largest code change** in the epic
- Be careful with `generate_sql` method - preserve existing API call logic
- Test thoroughly - this affects SQL generation quality
- If metadata loading fails, system should degrade gracefully, not crash
- Log messages are important for debugging - be verbose about what's loading

---

## Reference
See plan document section "Phase 3: Code Refactoring" → "3.1 Refactor claude_service.py"
