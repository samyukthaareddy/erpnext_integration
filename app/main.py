"""
Flask application factory with middleware for the ERPNext CRM Integration service.
"""

import time
from flask import Flask, request, jsonify
from flask_cors import CORS
from config.logging import get_logger

logger = get_logger(__name__)


def create_app():
    app = Flask(__name__)
    CORS(app)

    @app.before_request
    def log_request():
        request._start_time = time.time()
        logger.info(f"→ {request.method} {request.path}")

    @app.after_request
    def log_response(response):
        duration = time.time() - getattr(request, "_start_time", time.time())
        logger.info(f"← {response.status_code} {request.path} ({duration:.3f}s)")
        return response

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({"error": "Method not allowed"}), 405

    @app.errorhandler(500)
    def internal_error(e):
        logger.error(f"Internal server error: {e}")
        return jsonify({"error": "Internal server error"}), 500

    from app.routes import crm
    app.register_blueprint(crm.bp)

    return app
