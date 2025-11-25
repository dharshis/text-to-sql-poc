"""
API routes for text-to-sql-poc backend.

Provides endpoints for:
- POST /query - Main query endpoint for natural language to SQL
- GET /clients - List available clients
- GET /health - Health check endpoint
"""

import logging
import time
from flask import Blueprint, request, jsonify
from services.claude_service import ClaudeService
from services.query_executor import QueryExecutor
from services.sql_validator import validate_sql_for_client_isolation, get_validation_summary

logger = logging.getLogger(__name__)

# Create Blueprint
query_bp = Blueprint('query', __name__)

# Initialize services
claude_service = ClaudeService()
query_executor = QueryExecutor()


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


@query_bp.route('/clients', methods=['GET'])
def get_clients():
    """
    Get list of all available clients.

    Response:
        {
            "clients": [
                {"client_id": 1, "client_name": "Webb Inc", "industry": "Retail"},
                ...
            ],
            "count": 10
        }

    Error Response:
        {
            "error": "Error message"
        }
    """
    try:
        clients = query_executor.get_clients()

        return jsonify({
            'clients': clients,
            'count': len(clients)
        }), 200

    except Exception as e:
        logger.error(f"Error in /clients endpoint: {e}", exc_info=True)
        return jsonify({
            'error': 'Failed to fetch clients',
            'details': str(e)
        }), 500


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
