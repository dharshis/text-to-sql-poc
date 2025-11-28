# Metadata Knowledge Packs

This directory contains metadata knowledge packs for each dataset in the Text-to-SQL system. Metadata enhances SQL generation by providing business rules, query patterns, and detailed schema information.

## 📁 Structure

```
metadata/
├── README.md                   # This file
├── em_market/                  # EM Market dataset metadata
│   ├── business_rules.md       # 60+ SQL patterns and business rules
│   ├── query_patterns.md       # 20+ reusable query templates
│   ├── Fact_Market_Size.md    # Primary fact table with 8 query patterns
│   ├── Dim_Markets.md          # Markets dimension with hierarchy
│   ├── Dim_Geography.md        # Geography dimension
│   ├── Dim_Period.md           # Time dimension
│   └── ...                     # Other table metadata
└── sales/                      # Sales dataset metadata (add yours here)
    └── ...
```

## 🎯 Purpose

Metadata knowledge packs serve as **context augmentation** for LLM-based SQL generation:

1. **Business Rules**: Teach the LLM dataset-specific SQL patterns
2. **Query Patterns**: Provide templates for common queries
3. **Table Metadata**: Explain table structure with examples
4. **Sample Queries**: Show actual SQL for reference

## 📋 What's Included

### For EM Market Dataset

#### business_rules.md
- **60+ Business Rules** organized by category:
  - Time-based queries (latest, YoY growth, trends)
  - Geographic queries (countries, regions, emerging markets)
  - Market queries (top markets, hierarchy, NAICS codes)
  - Segmentation queries
  - Forecast queries (CAGR, scenarios)
  - Multi-dimensional queries
  - Performance optimization rules

Example rule:
```markdown
## RULE: Latest Year Data Query Pattern
**When to use**: User asks for "latest", "current", "most recent"
**SQL Implementation**:
```sql
WHERE t.year = (SELECT MAX(year) FROM dim_time WHERE is_forecast = 0)
```
**Example queries**: "Current market size", "Latest data"
```

#### query_patterns.md
- **20+ Query Templates** with placeholders:
  - Time-based patterns (latest, YoY, trends)
  - Geographic patterns (ranking, comparison, regional)
  - Market patterns (top N, hierarchy, search)
  - Segmentation patterns
  - Forecast patterns
  - Multi-dimensional patterns

Example pattern:
```sql
### Country Ranking
SELECT 
    g.country,
    SUM(fms.market_value_usd_m) AS total_market_value,
    RANK() OVER (ORDER BY SUM(fms.market_value_usd_m) DESC) AS country_rank
FROM fact_market_size fms
INNER JOIN dim_geography g ON fms.geo_id = g.geo_id
WHERE fms.client_id = {{client_id}}
    AND t.year = {{year}}
ORDER BY total_market_value DESC
LIMIT {{limit}};
```

#### Table Metadata Files
Each important table has its own `.md` file with:
- **Overview**: Table purpose and characteristics
- **Column Definitions**: Detailed field descriptions
- **Relationships**: Foreign keys and joins
- **Business Rules**: Table-specific patterns
- **8+ Query Patterns**: Common queries with actual SQL
- **Performance Tips**: Indexing and optimization
- **Example Questions**: User queries mapped to SQL

## 🚀 Usage

### Automatic Loading

The metadata system automatically loads all `.md` files from the active dataset directory:

```python
from services.metadata_loader import load_dataset_metadata

# Load metadata for em_market
loader = load_dataset_metadata("em_market")

# Get statistics
stats = loader.get_statistics()
print(f"Loaded {stats['total_documents']} documents")
```

### Using Metadata Tools

```python
from services.agent_tools import create_metadata_tools_for_dataset

# Create tools for current dataset
tools = create_metadata_tools_for_dataset(
    dataset_id="em_market",
    db_path="data/market_size.db"
)

# Search for relevant business rules
result = tools['search_metadata'].execute(
    query="market size by country",
    top_k=5
)

if result['success']:
    context = result['result']['formatted_context']
    # Use context in LLM prompt
```

### Integration with Agentic Service

```python
def generate_sql_with_metadata(state: dict) -> dict:
    """Enhanced SQL generation with metadata context."""
    
    # Load metadata tools
    tools = create_metadata_tools_for_dataset(
        dataset_id=state['dataset_id'],
        db_path=state['db_path']
    )
    
    # Search for relevant context
    metadata_result = tools['search_metadata'].execute(
        query=state['original_query'],
        top_k=5
    )
    
    # Build enhanced prompt
    system_prompt = f"""You are an expert SQL generator.

{metadata_result['result']['formatted_context']}

Database Schema: {state['schema']}

Generate accurate SQL following the business rules above."""

    # Generate SQL with enriched context
    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=state['original_query'])
    ])
    
    return {"generated_sql": extract_sql(response.content)}
```

## 📝 Adding Metadata for New Datasets

### Step 1: Create Directory

```bash
mkdir metadata/your_dataset_id
```

### Step 2: Create business_rules.md

Use `metadata/em_market/business_rules.md` as template:

```markdown
# Your Dataset - Business Rules

## RULE: Your Rule Name
**When to use**: Description
**Definition**: Explanation
**SQL Implementation**:
```sql
-- Your SQL pattern
```
**Example queries**: List of questions

---

## RULE: Another Rule
...
```

### Step 3: Create query_patterns.md

Use `metadata/em_market/query_patterns.md` as template:

```markdown
# Your Dataset - Common Query Patterns

### Pattern Name
```sql
-- SQL with {{placeholders}}
SELECT ...
WHERE field = {{variable}}
```
```

### Step 4: Create Table Metadata Files

For each important table, create `TableName.md`:

```markdown
# Table: your_table_name

## Metadata
* **Table Type:** Fact/Dimension
* **Granularity:** One row per ...
* **Primary Key:** field_name

## Description
What this table contains...

## Column Definitions
| Column | Type | Description |
|--------|------|-------------|
| id | INT | Primary key |
| ... | ... | ... |

## Common Query Patterns

### Pattern 1: Description
```sql
SELECT ... FROM your_table ...
```

### Pattern 2: Description
```sql
SELECT ... FROM your_table ...
```
```

### Step 5: Test Loading

```bash
cd backend
python test_metadata_system.py
```

## 🎨 Best Practices

### Writing Business Rules

✅ **DO:**
- Use clear, descriptive rule names
- Include "When to use" guidance
- Provide actual SQL code
- List example user questions
- Keep rules focused (one pattern per rule)

❌ **DON'T:**
- Write vague descriptions
- Skip SQL examples
- Combine multiple patterns in one rule
- Use overly technical jargon

### Creating Query Patterns

✅ **DO:**
- Use `{{variable}}` for placeholders
- Document all variables
- Include comments in SQL
- Show multiple variations
- Cover common use cases

❌ **DON'T:**
- Hard-code values
- Create overly complex patterns
- Skip variable documentation
- Forget edge cases

### Table Metadata

✅ **DO:**
- Include 5-8 query patterns per table
- Show actual SQL examples
- Document JOIN patterns
- Explain indexing strategy
- Map user questions to patterns

❌ **DON'T:**
- Only list column names
- Skip relationship documentation
- Forget NULL handling
- Ignore performance tips

## 🔍 Metadata Types

The system recognizes three types of metadata:

1. **business_rule**: Individual SQL patterns and best practices
2. **query_pattern**: Reusable SQL templates
3. **table_metadata**: Table-specific schema and examples

Each type is parsed and indexed differently for optimal retrieval.

## 📊 Statistics

Current EM Market metadata:
- **60+ Business Rules** covering all major query patterns
- **20+ Query Templates** for common scenarios
- **10+ Table Documentation Files** with detailed examples
- **80+ SQL Examples** showing actual working queries

## 🧪 Testing

Test the metadata system:

```bash
cd backend
python test_metadata_system.py
```

This will:
- Load all metadata files
- Test metadata search
- Test tool execution
- Show statistics
- Display sample results

## 🚧 Maintenance

### When to Update

- ✏️ Schema changes (add/remove columns)
- 🆕 New query patterns discovered
- 🐛 Incorrect rules identified
- 📈 New business requirements
- 🔄 Dataset evolution

### Version Control

All metadata files are version controlled with the code:
- Track changes in git
- Document updates in commit messages
- Review metadata in PRs
- Keep metadata and code in sync

## 💡 Tips

1. **Start Small**: Begin with 10-15 key business rules
2. **Iterate**: Add rules as you see patterns in queries
3. **Be Specific**: Concrete examples beat vague descriptions
4. **Test**: Verify rules with actual queries
5. **Document**: Explain the "why" not just the "what"

## 📚 References

- **Integration Guide**: `backend/services/METADATA_INTEGRATION_GUIDE.md`
- **Loader Code**: `backend/services/metadata_loader.py`
- **Tools Code**: `backend/services/agent_tools.py`
- **Test Script**: `backend/test_metadata_system.py`

## 🤝 Contributing

When adding metadata:
1. Follow existing format conventions
2. Test with `test_metadata_system.py`
3. Include SQL examples for every rule
4. Map rules to actual user questions
5. Keep content concise and actionable

---

**Remember**: Good metadata = Better SQL generation!

The metadata you write here directly improves the quality of SQL queries generated by the LLM. Invest time in creating clear, comprehensive metadata knowledge packs.

