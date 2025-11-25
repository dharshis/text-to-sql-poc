"""
Configuration management for text-to-sql-poc backend.

Loads environment variables from .env file and provides configuration settings
for Flask, Claude API, and database connections.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Application configuration class."""

    # Claude API Configuration
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
    CLAUDE_MODEL = 'claude-sonnet-4-5-20250929'
    CLAUDE_MAX_TOKENS = 1000
    CLAUDE_TIMEOUT = 10  # seconds

    # Database Configuration
    DATABASE_PATH = os.getenv('DATABASE_PATH', '../data/text_to_sql_poc.db')

    # Flask Configuration
    DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    ENV = os.getenv('FLASK_ENV', 'development')
    PORT = int(os.getenv('FLASK_PORT', 5000))

    # CORS Configuration
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:5173').split(',')

    # Query Execution Limits
    MAX_QUERY_RESULTS = 1000  # Limit results to prevent memory issues
    QUERY_TIMEOUT = 30  # seconds

    @classmethod
    def validate(cls):
        """Validate that required configuration is present."""
        errors = []

        if not cls.ANTHROPIC_API_KEY:
            errors.append("ANTHROPIC_API_KEY is not set. Please add it to your .env file.")

        if not os.path.exists(cls.DATABASE_PATH):
            errors.append(f"Database not found at {cls.DATABASE_PATH}. Run database seed_data.py first.")

        if errors:
            raise ValueError("Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors))

        return True

    @classmethod
    def get_database_url(cls):
        """Get SQLAlchemy database URL."""
        return f'sqlite:///{cls.DATABASE_PATH}'


# Validate configuration on import (optional - comment out if you want to defer validation)
# Config.validate()
