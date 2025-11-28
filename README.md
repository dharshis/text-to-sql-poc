# Text-to-SQL POC

A proof-of-concept application that converts natural language queries to SQL using Claude AI, with a React frontend for data visualization.

## Overview

This application allows users to query a multi-tenant database using natural language. It features:
- Natural language to SQL conversion using Claude AI
- SQL security validation for client data isolation
- Interactive data visualization with charts
- Client-specific data access controls

## Architecture

- **Backend:** Flask (Python) with Anthropic Claude API integration
- **Frontend:** React with Material-UI and Recharts
- **Database:** SQLite with multi-tenant data (clients, products, sales, customer segments)

## Prerequisites

### Backend Requirements
- Python 3.8+
- pip (Python package manager)
- Virtual environment (recommended)
- Anthropic API key ([Get one here](https://console.anthropic.com/))

### Frontend Requirements
- Node.js 16+ ([Download](https://nodejs.org/))
- npm (comes with Node.js)

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd text-to-sql-poc
```

### 2. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env and add your Anthropic API key:
# ANTHROPIC_API_KEY=sk-ant-your-key-here
```

### 3. Frontend Setup

```bash
# Navigate to frontend directory
cd ../frontend

# Install dependencies
npm install
```

## Configuration

### Backend Configuration (.env)

Edit `backend/.env` and configure the following:

```env
# Required: Your Anthropic API key
ANTHROPIC_API_KEY=sk-ant-your-actual-key-here

# Server configuration
FLASK_PORT=5001
FLASK_ENV=development
DEBUG=True

# Database
DATABASE_PATH=../data/text_to_sql_poc.db

# CORS (should match frontend URL)
CORS_ORIGINS=http://localhost:5173
```

### Getting an Anthropic API Key

1. Go to https://console.anthropic.com/
2. Sign up or log in
3. Navigate to "API Keys" in the settings
4. Create a new API key
5. Copy the key and add it to your `backend/.env` file

## Starting the Application

### Start Backend Server

```bash
# From backend directory
cd backend

# Activate virtual environment (if not already activated)
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

# Start Flask server
python app.py
```

The backend will start on **http://localhost:5001**

You should see:
```
======================================================================
TEXT-TO-SQL POC - BACKEND SERVER
======================================================================

Server running at: http://localhost:5001

Available endpoints:
  POST http://localhost:5001/query
  GET  http://localhost:5001/clients
  GET  http://localhost:5001/health
  GET  http://localhost:5001/schema
======================================================================
```

### Start Frontend Server

Open a **new terminal window** and run:

```bash
# From frontend directory
cd frontend

# Start Vite dev server
npm run dev
```

The frontend will start on **http://localhost:5173**

You should see:
```
VITE v7.2.4  ready in 266 ms

➜  Local:   http://localhost:5173/
➜  Network: use --host to expose
```

### Access the Application

Open your browser and navigate to:
**http://localhost:5173**

## Usage

1. **Select a Client** - Choose a client from the dropdown menu
2. **Enter Query** - Type your question in natural language, for example:
   - "Show me top 10 products by revenue"
   - "What are the sales trends by month?"
   - "Which customer segments have the highest revenue?"
3. **Click Search** - The application will:
   - Generate SQL using Claude AI
   - Validate the SQL for security
   - Execute the query
   - Display results with visualizations

## API Endpoints

### Backend API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check and database status |
| `/clients` | GET | Get list of available clients |
| `/query` | POST | Submit natural language query |
| `/schema` | GET | Get database schema information |

### Example API Request

```bash
curl -X POST http://localhost:5001/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Show me top 10 products by revenue",
    "client_id": 1
  }'
```

## Log Files

Logs are automatically written to the following locations:

- **Backend logs:** `backend/logs/backend.log`
- **Frontend logs:** `frontend/logs/frontend.log`

### View Logs in Real-Time

```bash
# Backend logs
tail -f backend/logs/backend.log

# Frontend logs
tail -f frontend/logs/frontend.log
```

### Search Logs

```bash
# Find errors in backend logs
grep ERROR backend/logs/backend.log

# Find specific API calls
grep "POST /query" backend/logs/backend.log
```

## Troubleshooting

### Backend Issues

#### "Invalid API Key" Error
- **Problem:** Claude API returns 401 Unauthorized
- **Solution:** Add a valid Anthropic API key to `backend/.env`
- **Check:** Look for `ANTHROPIC_API_KEY=sk-ant-...` in your `.env` file

#### Port 5001 Already in Use
- **Problem:** Another application is using port 5001
- **Solution:** Change `FLASK_PORT` in `backend/.env` to a different port (e.g., 5002)
- **Note:** Also update `frontend/src/services/api.js` to match the new port

#### Database Not Found
- **Problem:** SQLite database file missing
- **Solution:** Ensure `data/text_to_sql_poc.db` exists in the project root
- **Check:** Run Story 1.1 to initialize the database

### Frontend Issues

#### Cannot Connect to Backend
- **Problem:** Frontend shows "Backend connection issue"
- **Solution:**
  1. Ensure backend is running on http://localhost:5001
  2. Check backend logs for errors
  3. Verify CORS configuration in `backend/app.py`

#### Port 5173 Already in Use
- **Problem:** Vite cannot start on port 5173
- **Solution:** Kill the existing process or Vite will automatically try another port
- **Note:** Update `backend/.env` CORS_ORIGINS if port changes

#### Blank Page or React Errors
- **Problem:** Frontend not loading
- **Solution:**
  1. Clear browser cache
  2. Check browser console for errors (F12)
  3. Restart Vite dev server
  4. Run `npm install` again

### Common Errors

#### "No module named 'anthropic'"
```bash
# Solution: Install Python dependencies
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

#### "command not found: npm"
```bash
# Solution: Install Node.js
# Download from https://nodejs.org/
```

## Development

### Project Structure

```
text-to-sql-poc/
├── backend/                    # Flask backend
│   ├── app.py                 # Main application entry point
│   ├── config.py              # Configuration
│   ├── routes/                # API route handlers
│   ├── services/              # Business logic (Claude, SQL validation, query execution)
│   ├── logs/                  # Log files (auto-generated)
│   └── requirements.txt       # Python dependencies
├── frontend/                   # React frontend
│   ├── src/
│   │   ├── App.jsx           # Main React component
│   │   ├── components/        # Reusable UI components
│   │   ├── services/          # API client
│   │   └── styles/            # MUI theme
│   ├── logs/                  # Log files (auto-generated)
│   └── package.json           # Node dependencies
├── data/                       # SQLite database
└── docs/                       # Documentation and stories

```

### Technology Stack

**Backend:**
- Flask 3.0.0
- Anthropic Claude API (claude-3-5-sonnet)
- LangGraph 1.0+ (agentic workflows)
- SQLite
- Python 3.8+

**Frontend:**
- React 18.3.1
- Material-UI 6.3.0
- Recharts 2.15.0
- Axios 1.7.9
- Vite 7.2.4

## Testing

### Test Backend

```bash
# Health check
curl http://localhost:5001/health

# Get clients
curl http://localhost:5001/clients

# Test query
curl -X POST http://localhost:5001/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Show me all products", "client_id": 1}'
```

### Test Frontend

1. Open http://localhost:5173
2. Select a client
3. Enter: "Show me top 10 products by revenue"
4. Click Search
5. Verify results display with chart and table

## Security Features

- **Client Data Isolation:** SQL validation ensures queries only access the selected client's data
- **Read-Only Queries:** Validates that only SELECT statements are allowed
- **Single Client Enforcement:** Prevents queries from accessing multiple clients
- **SQL Injection Prevention:** Parameterized queries and validation checks

## Performance

- **Backend Response Time:** Typically 1-3 seconds per query (depends on Claude API)
- **Database:** SQLite, suitable for POC (not for production)
- **Log Rotation:** Backend logs rotate at 10MB (keeps 5 backup files)

## License

This is a proof-of-concept project for demonstration purposes.

## Support

For issues or questions:
1. Check the Troubleshooting section above
2. Review log files for error details
3. Ensure all prerequisites are installed
4. Verify API key is valid and has credits

---

**Quick Start Summary:**

```bash
# Terminal 1 - Backend
cd backend
source venv/bin/activate
python app.py

# Terminal 2 - Frontend
cd frontend
npm run dev

# Browser
# Open http://localhost:5173
```
