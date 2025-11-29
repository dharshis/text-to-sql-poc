# Story 2: Create Metadata Knowledge Pack for em_market Dataset

**Epic:** Multi-Dataset Refactor
**Priority:** HIGH
**Estimated Effort:** 6 hours
**Status:** Ready for Development

---

## User Story

**As a** developer setting up a new company dataset
**I want** dataset-specific domain knowledge in metadata files
**So that** LLM instructions are separate from code and easily customizable per dataset

---

## Background

Currently, claude_service.py has hardcoded `DATABASE_SCHEMA` and `SYSTEM_PROMPT` with sales-specific knowledge. We need to extract dataset-specific knowledge (entity hierarchies, query patterns, filtering examples) into metadata files that can be loaded dynamically.

Using a **hybrid approach**: generic SQL rules stay in code, dataset-specific examples and patterns go to metadata.

---

## Acceptance Criteria

### AC1: Create Metadata Directory Structure
- [ ] Create directory: `metadata/em_market/` (if doesn't exist)
- [ ] Verify existing metadata files are preserved (business_rules.md, query_patterns.md, table metadata files)

### AC2: Create dataset_info.md
- [ ] Create file: `metadata/em_market/dataset_info.md`
- [ ] Include sections:
  - Business Domain description
  - Key Concepts (Corporation, Brand, Sub-Brand, Product SKU)
  - Entity Hierarchy diagram (ASCII art showing Dim_Corporation → Dim_Brand → Dim_SubBrand → Dim_Product_SKU)
  - Fact Tables list (fact_market_size, fact_company_share)
  - Time Dimension details (2010-2030, is_forecast flag)
- [ ] Written in clear, human-readable markdown
- [ ] Useful for new developers/demo creators understanding the dataset

**Minimum content:**
```markdown
# Dataset: Euromonitor Market Data (em_market)

## Business Domain
Global market research data for consumer goods, tracking market size and company market share across countries, categories, and brands.

## Key Concepts
- **Corporation**: Parent company that owns multiple brands (e.g., Coca-Cola Company, PepsiCo)
- **Brand**: Product brand owned by a corporation (e.g., Coca-Cola, Sprite)
- **Sub-Brand**: Brand variant or line extension (e.g., Coca-Cola Zero)
- **Product SKU**: Individual sellable product unit

## Entity Hierarchy
[Hierarchy diagram]

## Fact Tables
[Fact table descriptions]

## Time Dimension
[Time dimension details]
```

### AC3: Create llm_instructions.md
- [ ] Create file: `metadata/em_market/llm_instructions.md`
- [ ] Include sections:
  - Domain Context (business domain, entity hierarchy reference)
  - Filtering Examples (how corp_id filtering works with specific table names)
  - Domain-Specific Patterns (time range queries, geography, categories)
  - Common Table Relationships (fact tables and their joins)
  - Example Queries (5-10 realistic queries with natural language + SQL)

**Critical requirements:**
- Use **actual em_market table names** (Dim_Brand, fact_market_size, etc.)
- Show **corp_id filtering** in all examples
- Include **is_forecast** handling patterns
- Include **year-based time range** patterns (using MAX(year) not CURRENT_DATE)
- Show **brand hierarchy join** patterns

**Minimum 5 example queries covering:**
1. Simple brand listing (SELECT from Dim_Brand with corp_id filter)
2. Market size aggregation with brand join
3. Geographic analysis (with Dim_Country join)
4. Time-based query (last N years using MAX(year))
5. Category breakdown (with Dim_Category join)

### AC4: Integrate with Existing Metadata
- [ ] Ensure new files don't conflict with existing metadata files:
  - `business_rules.md` (existing, keep as-is)
  - `query_patterns.md` (existing, keep as-is)
  - Table-specific metadata files (existing, keep as-is)
- [ ] New files complement, not replace existing metadata

### AC5: Metadata Loader Compatibility
- [ ] Test that MetadataLoader can read llm_instructions.md:
  ```python
  from services.metadata_loader import MetadataLoader
  loader = MetadataLoader(dataset_id='em_market')
  docs = loader.search_metadata(file_pattern='llm_instructions.md')
  assert len(docs) > 0, "llm_instructions.md not loaded"
  assert 'corp_id' in docs[0].content, "Missing corp_id filtering examples"
  ```

### AC6: Content Quality
- [ ] All SQL examples are syntactically valid SQLite
- [ ] All table/column names match em_market database schema
- [ ] Filtering examples show corp_id (not client_id)
- [ ] Entity hierarchy accurately reflects database structure
- [ ] Example queries cover common use cases (aggregations, joins, time ranges)

---

## Technical Notes

### Files to Create
1. `metadata/em_market/dataset_info.md` (new)
2. `metadata/em_market/llm_instructions.md` (new)

### Template for llm_instructions.md

```markdown
# Dataset-Specific Instructions: Euromonitor Market Data

## Domain Context

**Business Domain:** Global market research for consumer goods

**Key Entity Hierarchy:**
```
Dim_Corporation (corp_id) ← FILTERING HAPPENS HERE
  └─ Dim_Brand (brand_id, corp_id FK)
      └─ Dim_SubBrand (subbrand_id, brand_id FK)
          └─ Dim_Product_SKU (sku_id, subbrand_id FK)
```

## Filtering Examples

The system will instruct you to filter by corp_id = {client_id}.
Here's how this applies in this dataset:

**Example 1: Brand listing**
```sql
-- User asks: "Show me all my brands"
SELECT brand_name FROM Dim_Brand b
WHERE b.corp_id = {client_id}
```

**Example 2: Market size with joins**
```sql
-- User asks: "Market size by brand"
SELECT b.brand_name, SUM(f.market_size_value) as total
FROM fact_market_size f
JOIN Dim_Brand b ON f.brand_id = b.brand_id
WHERE b.corp_id = {client_id}
  AND f.is_forecast = 0
GROUP BY b.brand_name
ORDER BY total DESC
```

## Domain-Specific Patterns

**Pattern 1: Time Range Queries**
- Use `is_forecast = 0` for historical data only
- For "last N years": `year >= (SELECT MAX(year) - N FROM fact_market_size WHERE is_forecast = 0)`
- NEVER use CURRENT_DATE or NOW() for year calculations

**Pattern 2: Geographic Filters**
- Join through Dim_Country for country-level data
- Join through Dim_Region for regional rollups
- Always filter by corp_id when using geography joins

**Pattern 3: Category Analysis**
- Dim_Category has three-level hierarchy: Category → Subcategory → Segment
- Use appropriate level based on user question

## Common Table Relationships

```
fact_market_size:
  - brand_id → Dim_Brand (always join here for corp_id filtering)
  - country_id → Dim_Country
  - category_id → Dim_Category
  - year (integer, 2010-2030)
  - is_forecast (0 = historical, 1 = forecast)
  - market_size_value (numeric)

fact_company_share:
  - brand_id → Dim_Brand (always join here for corp_id filtering)
  - country_id → Dim_Country
  - category_id → Dim_Category
  - year (integer)
  - market_share_pct (decimal percentage)
```

## Example Queries

[5-10 complete examples with natural language + SQL]
```

### Reference Database Schema
- Consult existing em_market database schema
- Use `sqlite3 data/em_market/em_market.db` and `.schema` to verify table/column names
- Ensure all examples use actual table/column names from the database

---

## Testing

### Metadata Loader Test
```python
# Test script: backend/test_metadata_load.py
from services.metadata_loader import MetadataLoader

def test_em_market_metadata():
    loader = MetadataLoader(dataset_id='em_market')

    # Test dataset_info.md loads
    info_docs = loader.search_metadata(file_pattern='dataset_info.md')
    assert len(info_docs) > 0, "dataset_info.md not found"
    print(f"✓ dataset_info.md loaded ({len(info_docs)} sections)")

    # Test llm_instructions.md loads
    inst_docs = loader.search_metadata(file_pattern='llm_instructions.md')
    assert len(inst_docs) > 0, "llm_instructions.md not found"
    print(f"✓ llm_instructions.md loaded ({len(inst_docs)} sections)")

    # Check for key content
    all_content = '\n'.join([doc.content for doc in inst_docs])
    assert 'corp_id' in all_content, "Missing corp_id references"
    assert 'Dim_Brand' in all_content, "Missing Dim_Brand table references"
    assert 'fact_market_size' in all_content, "Missing fact_market_size references"
    assert 'is_forecast' in all_content, "Missing is_forecast handling"
    print("✓ Key content present")

    print("\n✅ All metadata tests passed!")

if __name__ == '__main__':
    test_em_market_metadata()
```

**Run test:**
```bash
cd backend
python test_metadata_load.py
```

### SQL Syntax Validation
- [ ] Copy each SQL example from llm_instructions.md
- [ ] Run EXPLAIN query in sqlite3 to validate syntax (don't execute, just validate)
- [ ] Ensure no syntax errors

### Manual Review
- [ ] Read dataset_info.md - is it clear and helpful?
- [ ] Read llm_instructions.md - do examples make sense?
- [ ] Check that filtering always uses corp_id (not client_id)
- [ ] Verify table names match actual database schema

---

## Definition of Done
- [ ] All acceptance criteria met
- [ ] Both metadata files created with required content
- [ ] Metadata loader test passes
- [ ] SQL examples validated (no syntax errors)
- [ ] Manual review completed (content is clear and accurate)
- [ ] Code committed: "Story 2: Create em_market metadata knowledge pack"

---

## Dependencies
- **Depends on:** Story 1 (config enhancement) - not blocking, can work in parallel
- **Blocks:** Story 3 (ClaudeService refactor) - needs llm_instructions.md

---

## Notes
- Focus on **quality over quantity** for examples - 5 great examples > 20 mediocre ones
- Use actual database schema - test queries if unsure
- Examples should demonstrate **common patterns** users will ask about
- This is the template for future dataset onboarding, so make it good!

---

## Reference
See plan document section "Phase 2: Metadata Knowledge Pack Creation" for full templates and examples.
