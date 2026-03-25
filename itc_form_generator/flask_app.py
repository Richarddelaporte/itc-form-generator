"""
ITC Form Generator — Flask Application Factory

Modular web application for generating ITC inspection/testing forms
from Sequence of Operation documents and BMS points lists.
"""

import os
import logging
from flask import Flask
from datetime import timedelta


def create_app(config_name=None):
    """Application factory pattern."""
    app = Flask(__name__,
                template_folder='templates',
                static_folder='static')

    # Load configuration
    config_name = config_name or os.environ.get('FLASK_ENV', 'development')
    if config_name == 'production':
        app.config.from_object('config.ProductionConfig')
    elif config_name == 'testing':
        app.config.from_object('config.TestingConfig')
    else:
        app.config.from_object('config.DevelopmentConfig')

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, app.config.get('LOG_LEVEL', 'INFO')),
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )

    # Initialize extensions
    _init_extensions(app)

    # Register blueprints
    _register_blueprints(app)

    # Register error handlers
    _register_error_handlers(app)

    # Initialize services
    _init_services(app)

    app.logger.info(f"ITC Form Generator v{app.config['APP_VERSION']} started ({config_name})")
    return app


def _init_extensions(app):
    """Initialize Flask extensions."""
    # Session configuration
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)


def _register_blueprints(app):
    """Register all route blueprints."""
    from routes.main import main_bp
    from routes.api import api_bp
    from routes.export import export_bp
    from routes.feedback import feedback_bp
    from routes.templates_api import templates_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(export_bp, url_prefix='/export')
    app.register_blueprint(feedback_bp, url_prefix='/api/feedback')
    app.register_blueprint(templates_bp, url_prefix='/api/templates')


def _register_error_handlers(app):
    """Register global error handlers."""
    from flask import jsonify, render_template

    @app.errorhandler(400)
    def bad_request(e):
        return jsonify(error=str(e.description)), 400

    @app.errorhandler(404)
    def not_found(e):
        return jsonify(error="Resource not found"), 404

    @app.errorhandler(413)
    def too_large(e):
        return jsonify(error="File too large. Maximum size is 50MB."), 413

    @app.errorhandler(500)
    def server_error(e):
        app.logger.error(f"Internal error: {e}")
        return jsonify(error="Internal server error. Please try again."), 500


def _init_services(app):
    """Initialize application services and store in app context."""
    from itc_form_generator.parser import SOOParser
    from itc_form_generator.form_generator import FormGenerator
    from itc_form_generator.points_parser import PointsListParser
    from itc_form_generator.exporter import FormExporter
    from itc_form_generator.feedback_store import get_feedback_store
    from itc_form_generator.example_form_parser import get_example_store

    # AI configuration
    use_ai = app.config.get('USE_AI', True)

    app.services = {
        'parser': SOOParser(use_ai=use_ai),
        'form_generator': FormGenerator(use_ai=use_ai),
        'points_parser': PointsListParser(),
        'exporter': FormExporter(),
        'feedback_store': get_feedback_store(),
        'example_store': get_example_store(),
    }

    # Session storage (in-memory for now, Redis for production)
    app.sessions = {}

