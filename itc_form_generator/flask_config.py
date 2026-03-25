"""
ITC Form Generator — Configuration

Environment-based configuration for development, testing, and production.
"""

import os


class BaseConfig:
    """Base configuration."""
    APP_NAME = "itc_form_generator"
    APP_VERSION = "2.0.0"
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-change-in-production')

    # File upload
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max upload
    UPLOAD_EXTENSIONS = {'.md', '.txt', '.pdf', '.csv', '.tsv', '.xlsx', '.xls'}

    # AI configuration
    USE_AI = os.environ.get('USE_AI', 'true').lower() == 'true'
    AI_BACKEND = os.environ.get('AI_BACKEND', 'metagen')

    # Output directory
    OUTPUT_DIR = os.environ.get('OUTPUT_DIR', '/tmp/itc_forms')

    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')


class DevelopmentConfig(BaseConfig):
    """Development configuration."""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'


class ProductionConfig(BaseConfig):
    """Production configuration (Nest / hosted)."""
    DEBUG = False
    SECRET_KEY = os.environ.get('SECRET_KEY')  # Must be set in production
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'WARNING')

    # Use Redis for sessions in production if available
    SESSION_TYPE = os.environ.get('SESSION_TYPE', 'filesystem')


class TestingConfig(BaseConfig):
    """Testing configuration."""
    TESTING = True
    USE_AI = False  # Disable AI in tests for speed
    LOG_LEVEL = 'DEBUG'

