# Text-to-SQL POC - API Testing Guide

## Prerequisites

1. **Anthropic API Key**: Get yours from https://console.anthropic.com/
2. **Update .env file**: Add your actual API key to `backend/.env`
   ```bash
   ANTHROPIC_API_KEY=sk-ant-your-actual-key-here
   ```

## Starting the Server

```bash
cd backend
source venv/bin/activate
python app.py
```

Server will start on: **http://localhost:5001**

---

## API Endpoints

### 1. GET / (Root - API Info)

**Test:**
```bash
curl http://localhost:5001/
```

**Expected Response:**
```json
{
  "name": "Text-to-SQL POC API",
  "version": "1.0.0",
  "endpoints": { ... }
}
```

---

### 2. GET /health (Health Check)

**Test:**
```bash
curl http://localhost:5001/health | python -m json.tool
```

**Expected Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "claude_api": "configured",
  "tables": {
    "clients": 10,
    "products": 200,
    "sales": 2000,
    "customer_segments": 30
  }
}
```

---

### 3. GET /clients (List Clients)

**Test:**
```bash
curl http://localhost:5001/clients | python -m json.tool
```

**Expected Response:**
```json
{
  "clients": [
    {"client_id": 1, "client_name": "Webb Inc", "industry": "Retail"},
    ...
  ],
  "count": 10
}
```

---

### 4. GET /schema (Database Schema)

**Test:**
```bash
curl http://localhost:5001/schema
```

**Expected Response:**
Returns the full database schema with CREATE TABLE statements.

---

### 5. POST /query (Main Query Endpoint) 🚀

**⚠️ IMPORTANT**: This requires a valid ANTHROPIC_API_KEY in your .env file!

#### Example 1: Top Products by Revenue

**Request:**
```bash
curl -X POST http://localhost:5001/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Show me top 10 products by revenue",
    "client_id": 1
  }' | python -m json.tool
```

**Expected Response:**
```json
{
  "sql": "SELECT p.product_name, SUM(s.revenue) as total_revenue FROM sales s JOIN products p ON s.product_id = p.product_id WHERE s.client_id = 1 GROUP BY p.product_name ORDER BY total_revenue DESC LIMIT 10",
  "results": [
    {"product_name": "Samsung Galaxy S24", "total_revenue": 45123.45},
    ...
  ],
  "columns": ["product_name", "total_revenue"],
  "row_count": 10,
  "metrics": {
    "sql_generation_time": 1.234,
    "query_execution_time": 0.056,
    "total_time": 1.290
  }
}
```

---

#### Example 2: Electronics Sales by Region

**Request:**
```bash
curl -X POST http://localhost:5001/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Show me electronics sales by region",
    "client_id": 2
  }' | python -m json.tool
```

---

#### Example 3: Sales Trend Over Time

**Request:**
```bash
curl -X POST http://localhost:5001/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the monthly sales totals for 2024?",
    "client_id": 1
  }' | python -m json.tool
```

---

#### Example 4: Average Transaction Value

**Request:**
```bash
curl -X POST http://localhost:5001/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the average transaction value by customer segment?",
    "client_id": 3
  }' | python -m json.tool
```

---

## Error Scenarios

### Missing API Key
If ANTHROPIC_API_KEY is not set, you'll see:
```json
{
  "error": "SQL generation failed",
  "details": "Anthropic API key is required..."
}
```

### Invalid Client ID
```bash
curl -X POST http://localhost:5001/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "test",
    "client_id": "invalid"
  }'
```

**Response:**
```json
{
  "error": "Client ID must be a valid integer"
}
```

### Missing Query
```bash
curl -X POST http://localhost:5001/query \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": 1
  }'
```

**Response:**
```json
{
  "error": "Query is required"
}
```

---

## Using Postman

1. **Import Collection**: Create a new collection in Postman
2. **Add Requests**: For each endpoint above
3. **Environment Variables**:
   - `base_url`: http://localhost:5001
   - `client_id`: 1 (or any ID from 1-10)

---

## Monitoring Server Logs

Watch the server output for debugging:
- Request logging shows each API call
- SQL queries are logged
- Error messages with stack traces

---

## Stopping the Server

Press **CTRL+C** in the terminal where the server is running.

---

## Next Steps

Once the backend is working:
1. ✅ Backend API (Story 1.2) - **COMPLETE**
2. 🔜 SQL Validator (Story 1.3)
3. 🔜 React Frontend (Story 1.4)
4. 🔜 Integration Testing (Story 1.5)

---

## Troubleshooting

**Port already in use?**
- Change `FLASK_PORT` in `.env` to 5001 or another available port

**Database not found?**
- Run `python -m database.seed_data` from backend directory

**Claude API timeout?**
- Check your internet connection
- Verify API key is correct
- Try a simpler query

---

**Happy Testing! 🚀**
