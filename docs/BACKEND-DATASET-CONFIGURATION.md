# Backend Dataset Configuration

**Status:** ✅ Complete  
**Date:** November 27, 2025

---

## Overview

The Text-to-SQL system now supports **multiple databases** with **backend-controlled** dataset selection. The frontend doesn't need to know about datasets - the backend manages which database is active.

---

## Architecture

### Backend-Controlled Design

```
┌──────────────┐
│   Frontend   │ ← No dataset_id parameter needed
└──────┬───────┘
       │ POST /query-agentic {"query": "..."}
       ▼
┌──────────────┐
│   Backend    │ ← Reads active dataset from config
└──────┬───────┘
       │
       ├─→ active_dataset.py → Manages current dataset
       ├─→ dataset_config.py → Dataset definitions
       └─→ Queries correct database automatically
```

**Key Benefits:**
- ✅ Simpler frontend (no dataset awareness needed)
- ✅ Centralized dataset management
- ✅ Easy to switch datasets for testing/development
- ✅ Admin can change dataset without frontend redeployment

---

## API Endpoints

### 1. Get Active Dataset
**GET** `/dataset/active`

**Response:**
```json
{
  "active_dataset": "market_size",
  "dataset_info": {
    "id": "market_size",
    "name": "Market Size Analytics",
    "db_path": "data/market_size.db",
    "fact_tables": ["fact_market_size", "fact_forecasts"],
    "sample_queries": [...]
  }
}
```

---

### 2. Switch Active Dataset
**POST** `/dataset/active`

**Request Body:**
```json
{
  "dataset_id": "market_size"
}
```

**Response:**
```json
{
  "success": true,
  "active_dataset": "market_size",
  "dataset_info": {...},
  "message": "Active dataset changed to market_size"
}
```

**Validation:**
- Returns 400 if `dataset_id` is invalid
- Only accepts datasets defined in `dataset_config.py`

---

### 3. List All Datasets
**GET** `/datasets`

**Response:**
```json
{
  "active_dataset": "market_size",
  "datasets": [
    {
      "id": "sales",
      "name": "Sales Transactions",
      "schema_type": "transactional",
      "fact_tables": ["sales"]
    },
    {
      "id": "market_size",
      "name": "Market Size Analytics",
      "schema_type": "dimensional",
      "fact_tables": ["fact_market_size", "fact_forecasts"]
    }
  ]
}
```

---

### 4. Query Endpoint (No Changes Required)
**POST** `/query-agentic`

**Request Body:**
```json
{
  "query": "Show me top electric vehicle markets",
  "session_id": "uuid",
  "client_id": 1
}
```

**Note:** `dataset_id` parameter is **NOT** needed in request. Backend automatically uses the active dataset.

---

## Configuration Files

### 1. `backend/datasets/active_dataset.py`

Manages which dataset is currently active.

**Functions:**

```python
get_active_dataset() -> str
    # Returns: "sales", "market_size", etc.
    # Priority: 1. Environment variable, 2. Config file, 3. Default

set_active_dataset(dataset_id: str) -> bool
    # Changes active dataset
    # Returns: True if successful, False if invalid

get_active_dataset_info() -> dict
    # Returns full config for active dataset
```

**Configuration Sources (Priority Order):**

1. **Environment Variable:** `ACTIVE_DATASET=market_size`
2. **Config File:** `backend/datasets/.active_dataset` (auto-created)
3. **Default:** `"sales"`

---

### 2. `backend/datasets/dataset_config.py`

Defines available datasets.

**Structure:**
```python
DATASETS = {
    "sales": {...},
    "market_size": {...}
}
```

**Dataset Configuration Fields:**
- `id`: Unique identifier
- `name`: Display name
- `description`: Description
- `db_path`: Path to SQLite database
- `schema_type`: "transactional" or "dimensional"
- `fact_tables`: List of fact tables
- `dimension_tables`: List of dimension tables
- `key_dimensions`: Dictionary of dimension columns
- `metrics`: List of metric columns
- `time_field`: Primary time column
- `client_isolation`: Multi-tenancy configuration
- `sample_queries`: Example queries for this dataset

---

## Usage Examples

### Switch to Market Size Dataset
```bash
curl -X POST http://localhost:5001/dataset/active \
  -H "Content-Type: application/json" \
  -d '{"dataset_id": "market_size"}'
```

### Query Active Dataset (Automatic)
```bash
curl -X POST http://localhost:5001/query-agentic \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Show me top electric vehicle markets in 2023",
    "client_id": 1
  }'
```

**Backend automatically:**
1. Reads active dataset → `market_size`
2. Connects to `data/market_size.db`
3. Uses market_size schema for SQL generation
4. Validates client_id on `fact_market_size` and `fact_forecasts` tables

---

### Switch Back to Sales Dataset
```bash
curl -X POST http://localhost:5001/dataset/active \
  -H "Content-Type: application/json" \
  -d '{"dataset_id": "sales"}'
```

---

## Environment Variable Configuration

### Option 1: Set Active Dataset via Environment Variable
```bash
export ACTIVE_DATASET=market_size
python app.py
```

### Option 2: Set in .env File
```bash
# backend/.env
ACTIVE_DATASET=market_size
```

### Option 3: Use API to Switch (Persists to File)
```bash
curl -X POST http://localhost:5001/dataset/active \
  -d '{"dataset_id": "market_size"}'
```

**Persistence:**
- API changes are saved to `backend/datasets/.active_dataset`
- Persists across server restarts
- Environment variable takes precedence if set

---

## Adding New Datasets

### Step 1: Create Database
```bash
# Create new SQLite database
python backend/database/init_new_dataset_db.py
```

### Step 2: Add Configuration
```python
# In backend/datasets/dataset_config.py
DATASETS["new_dataset"] = {
    "id": "new_dataset",
    "name": "New Dataset Name",
    "db_path": "data/new_dataset.db",
    "fact_tables": ["fact_table_name"],
    "dimension_tables": ["dim_table1", "dim_table2"],
    "client_isolation": {
        "enabled": True,
        "field": "client_id",
        "tables_requiring_filter": ["fact_table_name"]
    },
    # ... other fields
}
```

### Step 3: Activate
```bash
curl -X POST http://localhost:5001/dataset/active \
  -d '{"dataset_id": "new_dataset"}'
```

---

## Security & Validation

### Client Isolation
- **Sales dataset:** Validates `client_id` on `sales` table
- **Market_size dataset:** Validates `client_id` on `fact_market_size` and `fact_forecasts` tables
- All queries **must** include `WHERE client_id = X` filter
- Cross-client queries are **blocked**

### Dataset Validation
- Only configured datasets can be activated
- Invalid dataset_id returns 400 error
- All database paths are validated on activation

---

## Implementation Details

### File Structure
```
backend/
├── datasets/
│   ├── __init__.py
│   ├── dataset_config.py          # Dataset definitions
│   ├── active_dataset.py          # Active dataset management
│   └── .active_dataset            # Auto-created config file
├── routes/
│   └── query_routes.py            # API endpoints
└── services/
    ├── agentic_text2sql_service.py # Reads active dataset
    └── sql_validator.py            # Dataset-aware validation
```

### Modified Files
- ✅ `routes/query_routes.py` - Added dataset endpoints, reads active dataset
- ✅ `services/agentic_text2sql_service.py` - Uses active dataset for queries
- ✅ `services/sql_validator.py` - Dataset-aware client validation

### New Files
- ✅ `datasets/active_dataset.py` - Backend configuration management
- ✅ `datasets/dataset_config.py` - Dataset definitions

---

## Testing

### Test Dataset Switching
```bash
# 1. Check current dataset
curl http://localhost:5001/dataset/active

# 2. Switch to market_size
curl -X POST http://localhost:5001/dataset/active \
  -d '{"dataset_id": "market_size"}'

# 3. Run query (uses market_size automatically)
curl -X POST http://localhost:5001/query-agentic \
  -d '{"query": "Show me EV markets", "client_id": 1}'

# 4. Switch back to sales
curl -X POST http://localhost:5001/dataset/active \
  -d '{"dataset_id": "sales"}'

# 5. Run query (uses sales automatically)
curl -X POST http://localhost:5001/query-agentic \
  -d '{"query": "Top 5 products", "client_id": 1}'
```

---

## Benefits Over Frontend-Controlled Datasets

| Aspect | Backend-Controlled | Frontend-Controlled |
|--------|-------------------|---------------------|
| **Frontend Complexity** | ✅ Minimal (no changes) | ❌ Needs dataset selector UI |
| **API Simplicity** | ✅ No extra parameters | ❌ Every call needs dataset_id |
| **Admin Control** | ✅ Centralized switching | ❌ Distributed to clients |
| **Testing** | ✅ Easy to switch for dev/test | ❌ Need to update all test calls |
| **Deployment** | ✅ Backend-only change | ❌ Frontend + backend changes |
| **User Experience** | ✅ Transparent to users | ❌ Users must select dataset |

---

## Status

✅ **Backend Configuration:** Complete  
✅ **Dataset Switching API:** Complete  
✅ **Active Dataset Detection:** Complete  
✅ **Client Validation:** Complete  
✅ **Multi-Database Support:** Complete  
✅ **Frontend on Port 5173:** Complete  

**Active Dataset:** `market_size`  
**Available Datasets:** `sales`, `market_size`  

---

## Quick Reference

### Current Setup
- Frontend: http://localhost:5173 (no changes needed)
- Backend: http://localhost:5001
- Active Dataset: Managed by backend (`market_size`)
- Configuration File: `backend/datasets/.active_dataset`

### Admin Commands
```bash
# Check active dataset
curl http://localhost:5001/dataset/active

# Switch to market_size
curl -X POST http://localhost:5001/dataset/active -d '{"dataset_id": "market_size"}'

# Switch to sales
curl -X POST http://localhost:5001/dataset/active -d '{"dataset_id": "sales"}'

# List all datasets
curl http://localhost:5001/datasets
```

---

**System is ready for production use!** 🚀

