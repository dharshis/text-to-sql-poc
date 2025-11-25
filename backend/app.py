"""
Text-to-SQL POC - Flask Backend Application

Main application file that initializes Flask, configures CORS, registers routes,
and starts the development server.

Usage:
    python app.py
    OR
    flask run --port 5000
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from flask import Flask, jsonify
from flask_cors import CORS
from config import Config
from routes.query_routes import query_bp

# Configure logging
# Create logs directory if it doesn't exist
os.makedirs('logs', exist_ok=True)

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        # Console handler
        logging.StreamHandler(),
        # File handler with rotation (10MB per file, keep 5 backup files)
        RotatingFileHandler(
            'logs/backend.log',
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
    ]
)
logger = logging.getLogger(__name__)


def create_app():
    """
    Application factory function.

    Returns:
        Flask: Configured Flask application instance
    """
    # Initialize Flask app
    app = Flask(__name__)
    app.config.from_object(Config)

    # Configure CORS
    CORS(app, resources={
        r"/*": {
            "origins": Config.CORS_ORIGINS,
            "methods": ["GET", "POST", "OPTIONS"],
            "allow_headers": ["Content-Type"]
        }
    })

    # Register blueprints
    app.register_blueprint(query_bp)

    # Root endpoint
    @app.route('/', methods=['GET'])
    def root():
        """Root endpoint with API information."""
        return jsonify({
            'name': 'Text-to-SQL POC API',
            'version': '1.0.0',
            'endpoints': {
                'POST /query': 'Execute natural language query',
                'GET /clients': 'Get list of available clients',
                'GET /health': 'Health check',
                'GET /schema': 'Get database schema'
            }
        }), 200

    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 errors."""
        return jsonify({
            'error': 'Endpoint not found',
            'message': 'The requested endpoint does not exist'
        }), 404

    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors."""
        logger.error(f"Internal server error: {error}", exc_info=True)
        return jsonify({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred'
        }), 500

    # Request logging middleware
    @app.before_request
    def log_request():
        """Log incoming requests."""
        from flask import request
        logger.info(f"{request.method} {request.path} - {request.remote_addr}")

    @app.after_request
    def log_response(response):
        """Log outgoing responses."""
        from flask import request
        logger.info(f"{request.method} {request.path} - {response.status_code}")
        return response

    logger.info("Flask application created successfully")
    return app


def validate_environment():
    """Validate that required environment variables and files exist."""
    try:
        Config.validate()
        logger.info("Environment validation successful")
        return True
    except ValueError as e:
        logger.error(f"Environment validation failed: {e}")
        print("\n" + "="*70)
        print("CONFIGURATION ERROR")
        print("="*70)
        print(str(e))
        print("\nPlease fix the configuration issues before starting the server.")
        print("="*70 + "\n")
        return False


if __name__ == '__main__':
    print("="*70)
    print("TEXT-TO-SQL POC - BACKEND SERVER")
    print("="*70)

    # Validate environment before starting
    if not validate_environment():
        exit(1)

    # Create Flask app
    app = create_app()

    # Print startup information
    print(f"\nStarting Flask development server...")
    print(f"Environment: {Config.ENV}")
    print(f"Debug mode: {Config.DEBUG}")
    print(f"Database: {Config.DATABASE_PATH}")
    print(f"CORS origins: {', '.join(Config.CORS_ORIGINS)}")
    print(f"\nServer running at: http://localhost:{Config.PORT}")
    print("\nAvailable endpoints:")
    print(f"  POST http://localhost:{Config.PORT}/query")
    print(f"  GET  http://localhost:{Config.PORT}/clients")
    print(f"  GET  http://localhost:{Config.PORT}/health")
    print(f"  GET  http://localhost:{Config.PORT}/schema")
    print("\nPress CTRL+C to stop the server")
    print("="*70 + "\n")

    # Run Flask development server
    app.run(
        host='0.0.0.0',
        port=Config.PORT,
        debug=Config.DEBUG
    )
