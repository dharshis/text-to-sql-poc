"""
API routes for text-to-sql-poc backend.

Provides endpoints for:
- POST /query - Main query endpoint for natural language to SQL
- GET /clients - List available clients
- GET /health - Health check endpoint
"""

import logging
import time
import uuid
from flask import Blueprint, request, jsonify
from services.claude_service import ClaudeService
from services.query_executor import QueryExecutor
from services.sql_validator import validate_sql_for_client_isolation, get_validation_summary
from services.agentic_text2sql_service import AgenticText2SQLService

logger = logging.getLogger(__name__)

# Create Blueprint
query_bp = Blueprint('query', __name__)

# Initialize services
claude_service = ClaudeService()
query_executor = QueryExecutor()
agentic_service = AgenticText2SQLService()


def _update_active_dataset_in_config(dataset_id: str) -> bool:
    """
    Update the active_dataset field in config.json.
    
    Args:
        dataset_id: New dataset ID to set as active
        
    Returns:
        bool: True if successful, False otherwise
    """
    import json
    from pathlib import Path
    from config import Config, CONFIG_FILE
    
    try:
        # Validate dataset exists
        if not Config.validate_dataset_id(dataset_id):
            logger.error(f"Invalid dataset ID: {dataset_id}")
            return False
        
        # Read current config
        with open(CONFIG_FILE, 'r') as f:
            config_data = json.load(f)
        
        # Update active_dataset
        config_data['active_dataset'] = dataset_id
        
        # Write back
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config_data, f, indent=2)
        
        # Reload config
        Config.reload()
        
        logger.info(f"✓ Active dataset changed to: {dataset_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error updating active dataset: {e}")
        return False


@query_bp.route('/query', methods=['POST'])
def execute_query():
    """
    Main query endpoint - accepts natural language query and returns SQL + results.

    Request Body:
        {
            "query": "Show me top 10 products by revenue",
            "client_id": 1
        }

    Response:
        {
            "sql": "SELECT ...",
            "results": [...],
            "columns": [...],
            "row_count": 10,
            "metrics": {
                "sql_generation_time": 1.234,
                "query_execution_time": 0.056,
                "total_time": 1.290
            }
        }

    Error Response:
        {
            "error": "Error message",
            "details": "Additional details"
        }
    """
    start_time = time.time()

    try:
        # Validate request body
        data = request.get_json()

        if not data:
            return jsonify({'error': 'Request body is required'}), 400

        query = data.get('query')
        client_id = data.get('client_id')

        if not query:
            return jsonify({'error': 'Query is required'}), 400

        if client_id is None:
            return jsonify({'error': 'Client ID is required'}), 400

        # Validate client_id is a positive integer
        try:
            client_id = int(client_id)
            if client_id <= 0:
                return jsonify({'error': 'Client ID must be a positive integer'}), 400
        except (TypeError, ValueError):
            return jsonify({'error': 'Client ID must be a valid integer'}), 400

        logger.info(f"Received query request: client_id={client_id}, query='{query[:100]}'")

        # Step 1: Generate SQL using Claude
        sql_generation_start = time.time()
        try:
            sql_query = claude_service.generate_sql(query, client_id)
        except ValueError as e:
            return jsonify({'error': 'SQL generation failed', 'details': str(e)}), 500
        sql_generation_time = time.time() - sql_generation_start

        # Step 2: Validate SQL for client isolation and security
        validation_start = time.time()
        validation_result = validate_sql_for_client_isolation(sql_query, client_id)
        validation_time = time.time() - validation_start

        # If validation fails, return 400 error with validation details
        if not validation_result.passed:
            logger.warning(f"SQL validation failed for client_id={client_id}")
            return jsonify({
                'error': 'SQL validation failed',
                'message': 'Generated query does not meet security requirements',
                'sql': sql_query,
                'validation': validation_result.to_dict(),
                'validation_summary': get_validation_summary(validation_result)
            }), 400

        # Step 3: Execute SQL query (only if validation passed)
        query_execution_start = time.time()
        try:
            execution_result = query_executor.execute_query(sql_query)
        except ValueError as e:
            return jsonify({
                'error': 'Query execution failed',
                'details': str(e),
                'sql': sql_query,
                'validation': validation_result.to_dict()
            }), 500
        query_execution_time = time.time() - query_execution_start

        # Calculate total time
        total_time = time.time() - start_time

        # Build response
        response = {
            'sql': sql_query,
            'results': execution_result['results'],
            'columns': execution_result['columns'],
            'row_count': execution_result['row_count'],
            'validation': validation_result.to_dict(),
            'validation_summary': get_validation_summary(validation_result),
            'metrics': {
                'sql_generation_time': round(sql_generation_time, 3),
                'validation_time': round(validation_time, 3),
                'query_execution_time': round(query_execution_time, 3),
                'total_time': round(total_time, 3)
            }
        }

        logger.info(f"Query completed successfully: {execution_result['row_count']} rows in {total_time:.3f}s (validation: PASS)")

        return jsonify(response), 200

    except Exception as e:
        logger.error(f"Unexpected error in /query endpoint: {e}", exc_info=True)
        return jsonify({
            'error': 'Internal server error',
            'details': str(e)
        }), 500


@query_bp.route('/query-agentic', methods=['POST'])
def execute_agentic_query():
    """
    Agentic text-to-SQL endpoint with enhanced capabilities.
    Architecture Reference: Section 8.1 (API Design)
    
    Request Body:
        {
            "query": "Show me top products",
            "session_id": "uuid",
            "client_id": 1,
            "max_iterations": 10
        }
    
    Response (Success):
        {
            "success": true,
            "sql": "SELECT...",
            "explanation": "Natural language insights...",
            "results": {...},
            "validation": {...},
            "reflection": {...},
            "iterations": 7,
            "method": "agentic"
        }
    
    Response (Clarification):
        {
            "success": false,
            "needs_clarification": true,
            "questions": ["Which time period?", "..."],
            "method": "agentic"
        }
    """
    start_time = time.time()
    
    try:
        from config import Config
        
        data = request.json
        user_query = data.get('query')
        session_id = data.get('session_id', str(uuid.uuid4()))
        client_id = data.get('client_id', 1)
        max_iterations = data.get('max_iterations', 10)
        
        # Get active dataset from backend configuration (not frontend)
        dataset_id = Config.get_active_dataset()
        
        # Input validation (Architecture Section 12.3)
        if not user_query:
            return jsonify({'error': 'Query is required'}), 400
        
        if len(user_query) > 1000:
            return jsonify({'error': 'Query too long (max 1000 chars)'}), 400
        
        if max_iterations < 1 or max_iterations > 15:
            return jsonify({'error': 'max_iterations must be 1-15'}), 400
        
        logger.info(f"Agentic query: session={session_id}, client={client_id}, dataset={dataset_id}, query='{user_query[:100]}'")
        
        # Call agentic service (Architecture Section 3.1 + Backend Dataset Config)
        result = agentic_service.generate_sql_with_agent(
            user_query=user_query,
            session_id=session_id,
            client_id=client_id,
            dataset_id=dataset_id,
            max_iterations=max_iterations
        )
        
        elapsed = time.time() - start_time
        logger.info(f"Agentic query completed in {elapsed:.2f}s, success={result.get('success')}")
        
        # Performance warning (Architecture Section 13.1)
        if elapsed > 10.0:
            logger.warning(f"Query exceeded 10s performance target: {elapsed:.2f}s")
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Agentic query error: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e),
            'method': 'agentic'
        }), 500


# OLD ENDPOINT REMOVED - Now using dataset-aware endpoint below
# @query_bp.route('/clients', methods=['GET'])
# def get_clients():
#     """DEPRECATED: Replaced by dataset-aware list_clients() endpoint"""
#     pass


@query_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint.

    Response:
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

    Error Response:
        {
            "status": "unhealthy",
            "error": "Error message"
        }
    """
    try:
        # Test database connection
        query_executor.test_connection()

        # Get table info
        table_info = query_executor.get_table_info()

        # Check Claude API key is configured
        claude_configured = bool(claude_service.api_key)

        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'claude_api': 'configured' if claude_configured else 'not configured',
            'tables': table_info
        }), 200

    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500


@query_bp.route('/schema', methods=['GET'])
def get_schema():
    """
    Get database schema information.

    Response:
        {
            "schema": "CREATE TABLE clients ..."
        }
    """
    try:
        schema = claude_service.get_schema_info()

        return jsonify({
            'schema': schema
        }), 200

    except Exception as e:
        logger.error(f"Error in /schema endpoint: {e}", exc_info=True)
        return jsonify({
            'error': 'Failed to fetch schema',
            'details': str(e)
        }), 500


@query_bp.route('/datasets', methods=['GET'])
def list_datasets():
    """
    List all available datasets.
    
    Response:
        {
            "datasets": [
                {
                    "id": "sales",
                    "name": "Sales Transactions",
                    "db_path": "../data/text_to_sql_poc.db",
                    "client_isolation_enabled": true
                },
                ...
            ],
            "active_dataset": "em_market"
        }
    """
    try:
        from config import Config
        
        datasets = Config.list_datasets()
        active_dataset = Config.get_active_dataset()
        
        return jsonify({
            'datasets': datasets,
            'active_dataset': active_dataset
        }), 200
    
    except Exception as e:
        logger.error(f"Error listing datasets: {e}", exc_info=True)
        return jsonify({
            'error': 'Failed to list datasets',
            'details': str(e)
        }), 500


@query_bp.route('/dataset/active', methods=['GET'])
def get_active_dataset_endpoint():
    """
    Get the currently active dataset.
    
    Response:
        {
            "active_dataset": "sales",
            "dataset_info": {...}
        }
    """
    try:
        from config import Config
        
        dataset_id = Config.get_active_dataset()
        dataset_info = Config.get_active_dataset_info()
        
        return jsonify({
            'active_dataset': dataset_id,
            'dataset_info': dataset_info
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting active dataset: {e}", exc_info=True)
        return jsonify({
            'error': 'Failed to get active dataset',
            'details': str(e)
        }), 500


@query_bp.route('/clients', methods=['GET'])
def list_clients():
    """
    List all clients/corporations from the active dataset.
    
    Adapts to different dataset schemas:
    - sales: uses 'clients' table
    - market_size: uses 'dim_clients' table  
    - em_market: uses 'Dim_Corporation' table
    
    Response:
        {
            "clients": [
                {
                    "client_id": 1,  # or corp_id for em_market
                    "client_name": "Acme Corporation",
                    ...
                },
                ...
            ],
            "dataset": "em_market"
        }
    """
    try:
        from config import Config
        import sqlite3
        
        dataset_id = Config.get_active_dataset()
        dataset_info = Config.get_active_dataset_info()
        db_path = dataset_info['db_path']
        
        # Get client configuration for this dataset
        client_config = Config.get_client_config(dataset_id)
        table_name = client_config['table_name']
        id_field = client_config['id_field']
        name_field = client_config['name_field']
        
        # Connect to database
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({
                'clients': [],
                'dataset': dataset_id,
                'message': f'No {table_name} table in this dataset'
            }), 200
        
        # Get all columns for this table
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Build SELECT query with available columns
        # Always include ID and name fields
        select_cols = [f"{id_field} as client_id", f"{name_field} as client_name"]
        
        # Add optional columns if they exist
        optional_cols = {
            'industry': 'industry',
            'region': 'region',
            'subscription_tier': 'subscription_tier',
            'data_access_level': 'data_access_level',
            'max_users': 'max_users',
            'account_manager': 'account_manager',
            'is_active': 'is_active',
            'price_segment': 'price_segment',  # For em_market brands
            'headquarters_location': 'headquarters_location'  # For em_market corps
        }
        
        for alias, col in optional_cols.items():
            if col in columns:
                select_cols.append(f"{col} as {alias}")
        
        # Build WHERE clause  
        # Handle different is_active representations (INTEGER 1, TEXT 'True', etc.)
        where_clause = ""
        if 'is_active' in columns:
            where_clause = "WHERE (is_active = 1 OR is_active = 'True' OR is_active = 'true')"
        
        # Execute query
        query = f"""
            SELECT {', '.join(select_cols)}
            FROM {table_name}
            {where_clause}
            ORDER BY {name_field}
        """
        
        logger.debug(f"Executing client query: {query}")
        cursor.execute(query)
        
        clients = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        logger.info(f"Retrieved {len(clients)} clients from {dataset_id} ({table_name})")
        
        return jsonify({
            'clients': clients,
            'dataset': dataset_id,
            'client_table': table_name
        }), 200
    
    except Exception as e:
        logger.error(f"Error listing clients: {e}", exc_info=True)
        return jsonify({
            'error': 'Failed to list clients',
            'details': str(e)
        }), 500


@query_bp.route('/dataset/active', methods=['POST'])
def set_active_dataset_endpoint():
    """
    Switch the active dataset (backend configuration).
    
    Request Body:
        {
            "dataset_id": "market_size"
        }
    
    Response:
        {
            "success": true,
            "active_dataset": "market_size",
            "message": "Active dataset changed to market_size"
        }
    """
    try:
        from config import Config
        
        data = request.json
        dataset_id = data.get('dataset_id')
        
        if not dataset_id:
            return jsonify({
                'success': False,
                'error': 'dataset_id is required'
            }), 400
        
        # Set active dataset
        # Update active dataset in config.json
        success = _update_active_dataset_in_config(dataset_id)
        
        if success:
            dataset_info = Config.get_active_dataset_info()
            logger.info(f"✓ Active dataset changed to: {dataset_id}")
            
            return jsonify({
                'success': True,
                'active_dataset': dataset_id,
                'dataset_info': dataset_info,
                'message': f"Active dataset changed to {dataset_id}"
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': f"Invalid dataset_id: {dataset_id}"
            }), 400
    
    except Exception as e:
        logger.error(f"Error setting active dataset: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Failed to set active dataset',
            'details': str(e)
        }), 500


@query_bp.route('/session/<session_id>', methods=['DELETE'])
def delete_session(session_id):
    """
    Delete a session and all its conversation history.
    
    This ensures complete memory cleanup when starting a new session.
    
    Path Parameters:
        session_id: The session ID to delete
        
    Response:
        {
            "success": true,
            "message": "Session deleted",
            "session_id": "session-..."
        }
    """
    try:
        # Check if session exists
        if session_id in agentic_service.chat_sessions:
            query_count = len(agentic_service.chat_sessions[session_id])
            del agentic_service.chat_sessions[session_id]
            logger.info(f"Session {session_id} deleted ({query_count} queries cleared)")
            
            return jsonify({
                'success': True,
                'message': 'Session deleted',
                'session_id': session_id,
                'queries_cleared': query_count
            }), 200
        else:
            logger.info(f"Session {session_id} not found (already cleared or never existed)")
            return jsonify({
                'success': True,
                'message': 'Session not found or already cleared',
                'session_id': session_id
            }), 200
    
    except Exception as e:
        logger.error(f"Error deleting session {session_id}: {e}", exc_info=True)
        return jsonify({
            'error': 'Failed to delete session',
            'details': str(e)
        }), 500
