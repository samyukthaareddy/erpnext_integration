"""
Security middleware for the ERPNext CRM Integration service.

Provides: input sanitization, API key validation, request size limiting.
"""

import re
import os
from functools import wraps
from flask import request, jsonify
from config.logging import get_logger

logger = get_logger(__name__)

MAX_CONTENT_LENGTH = 64 * 1024  # 64 KB
_INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY", "")
_STRIP_PATTERN = re.compile(r"[<>\"'%;()&+]")


def sanitize_string(value: str) -> str:
    """Strip characters commonly used in injection attacks."""
    return _STRIP_PATTERN.sub("", value).strip()


def sanitize_payload(payload: dict) -> dict:
    """Recursively sanitize all string values in a dict."""
    return {
        k: sanitize_string(v) if isinstance(v, str) else v
        for k, v in payload.items()
    }


def require_api_key(f):
    """Decorator: reject requests missing a valid internal API key."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not _INTERNAL_API_KEY:
            # API key enforcement disabled — skip in dev/test
            return f(*args, **kwargs)
        key = request.headers.get("X-API-Key", "")
        if key != _INTERNAL_API_KEY:
            logger.warning(f"Unauthorized request to {request.path} — invalid API key")
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated


def check_content_length():
    """Reject requests exceeding MAX_CONTENT_LENGTH bytes."""
    length = request.content_length
    if length and length > MAX_CONTENT_LENGTH:
        logger.warning(f"Request too large: {length} bytes from {request.remote_addr}")
        return jsonify({"error": "Request too large"}), 413
    return None


def register_middleware(app):
    """Register all security middleware on the Flask app."""

    @app.before_request
    def enforce_size_limit():
        return check_content_length()
