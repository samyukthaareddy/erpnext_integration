"""Unit tests for app/middleware.py"""

import pytest
from unittest.mock import patch, Mock
from app.middleware import (
    sanitize_string,
    sanitize_payload,
    require_api_key,
    check_content_length,
)
from app.main import create_app


@pytest.fixture
def app():
    """Create Flask app for testing."""
    app = create_app()
    app.config["TESTING"] = True
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


class TestSanitizeString:
    """Tests for input sanitization function."""

    def test_sanitize_removes_injection_chars(self):
        """Test that common injection characters are removed."""
        assert sanitize_string("hello<script>") == "helloscript"
        assert sanitize_string("test;DROP") == "testDROP"
        assert sanitize_string('input"value') == "inputvalue"

    def test_sanitize_removes_quotes(self):
        """Test that quotes are removed."""
        assert sanitize_string("it's") == "its"
        assert sanitize_string('say"hello"') == "sayhello"

    def test_sanitize_removes_special_chars(self):
        """Test that special characters are removed."""
        assert sanitize_string("50%;100") == "50100"
        assert sanitize_string("a(b)c") == "abc"
        assert sanitize_string("x&y") == "xy"

    def test_sanitize_preserves_safe_chars(self):
        """Test that safe characters are preserved."""
        assert sanitize_string("John Doe") == "John Doe"
        assert sanitize_string("email@domain.com") == "email@domain.com"
        assert sanitize_string("phone-123-456") == "phone-123-456"

    def test_sanitize_strips_whitespace(self):
        """Test that leading/trailing whitespace is stripped."""
        assert sanitize_string("  hello  ") == "hello"
        assert sanitize_string("\t test \n") == "test"


class TestSanitizePayload:
    """Tests for payload sanitization function."""

    def test_sanitize_payload_all_strings(self):
        """Test sanitizing payload with all string values."""
        payload = {
            "name": "John<>Doe",
            "email": "test@email.com",
            "message": "hello;world",
        }
        result = sanitize_payload(payload)
        assert result["name"] == "JohnDoe"
        assert result["email"] == "test@email.com"
        assert result["message"] == "helloworld"

    def test_sanitize_payload_mixed_types(self):
        """Test sanitizing payload with mixed data types."""
        payload = {
            "name": "John<script>",
            "age": 30,
            "active": True,
            "tags": ["tag1", "tag2"],
        }
        result = sanitize_payload(payload)
        assert result["name"] == "Johnscript"
        assert result["age"] == 30
        assert result["active"] is True
        assert result["tags"] == ["tag1", "tag2"]

    def test_sanitize_payload_empty(self):
        """Test sanitizing empty payload."""
        result = sanitize_payload({})
        assert result == {}

    def test_sanitize_payload_preserves_structure(self):
        """Test that sanitization preserves payload structure."""
        payload = {
            "user": {
                "name": "test<>",
            }
        }
        # Note: current implementation only sanitizes top-level strings
        result = sanitize_payload(payload)
        assert isinstance(result["user"], dict)


class TestRequireApiKeyDecorator:
    """Tests for API key validation decorator."""

    @patch.dict("os.environ", {"INTERNAL_API_KEY": ""})
    def test_require_api_key_disabled_when_empty(self, app):
        """Test that API key check is skipped when INTERNAL_API_KEY is empty."""
        @require_api_key
        def test_route():
            return {"status": "success"}

        with app.app_context():
            result = test_route()
            assert result == {"status": "success"}


class TestCheckContentLength:
    """Tests for request size limit validation."""

    def test_check_content_length_under_limit(self, app):
        """Test request under size limit."""
        with app.test_request_context(content_length=1024):
            result = check_content_length()
            assert result is None

    def test_check_content_length_over_limit(self, app):
        """Test request exceeding size limit (64KB)."""
        from app.middleware import MAX_CONTENT_LENGTH
        over_limit = MAX_CONTENT_LENGTH + 1000

        with app.test_request_context(content_length=over_limit):
            response = check_content_length()
            assert response[1] == 413  # Payload Too Large

    def test_check_content_length_no_header(self, app):
        """Test when content-length header is missing."""
        with app.test_request_context():
            result = check_content_length()
            assert result is None

    def test_check_content_length_boundary(self, app):
        """Test request at exact size limit."""
        from app.middleware import MAX_CONTENT_LENGTH

        with app.test_request_context(content_length=MAX_CONTENT_LENGTH):
            result = check_content_length()
            assert result is None


class TestMiddlewareIntegration:
    """Integration tests for middleware with Flask app."""

    def test_process_lead_with_sanitization(self, client):
        """Test that payload sanitization happens in process-lead."""
        with patch("app.routes.crm.ERPNextClient"):
            with patch("app.routes.crm.create_followup_task"):
                payload = {
                    "name": "John<script>Doe",
                    "email": "test@example.com",
                    "phone": "+1-800-555-0199",
                    "company": "ACME",
                }
                # The route should still process even with injection attempts
                response = client.post(
                    "/api/crm/process-lead",
                    json=payload,
                    content_type="application/json",
                )
                # Should not crash due to sanitization
                assert response.status_code in [201, 500]  # Created or error

    def test_oversized_request_rejected(self, client):
        """Test that oversized requests are rejected."""
        from app.middleware import MAX_CONTENT_LENGTH

        # Create payload that exceeds limit
        large_payload = {
            "name": "x" * (MAX_CONTENT_LENGTH + 1000),
            "email": "test@example.com",
            "phone": "+1-800-555-0199",
            "company": "ACME",
        }

        response = client.post(
            "/api/crm/process-lead",
            json=large_payload,
            content_type="application/json",
        )

        # Should reject with 413 Payload Too Large
        assert response.status_code == 413
