"""Unit tests for app/exceptions.py and error handling in routes."""

import pytest
from unittest.mock import patch, Mock
from app.main import create_app
from app.exceptions import (
    ValidationError,
    ERPNextError,
    AssignmentError,
    TaskCreationError,
    ConfigurationError,
)
from app.erpnext_client import ERPNextException


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


VALID_PAYLOAD = {
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "+1-800-555-0199",
    "company": "ACME Corp",
}


class TestExceptionClasses:
    """Tests for custom exception classes."""

    def test_validation_error_is_exception(self):
        """Test ValidationError is an Exception."""
        assert issubclass(ValidationError, Exception)

    def test_erpnext_error_is_exception(self):
        """Test ERPNextError is an Exception."""
        assert issubclass(ERPNextError, Exception)

    def test_assignment_error_is_exception(self):
        """Test AssignmentError is an Exception."""
        assert issubclass(AssignmentError, Exception)

    def test_task_creation_error_is_exception(self):
        """Test TaskCreationError is an Exception."""
        assert issubclass(TaskCreationError, Exception)

    def test_configuration_error_is_exception(self):
        """Test ConfigurationError is an Exception."""
        assert issubclass(ConfigurationError, Exception)

    def test_validation_error_can_be_raised(self):
        """Test ValidationError can be raised and caught."""
        with pytest.raises(ValidationError):
            raise ValidationError("Invalid data")

    def test_erpnext_error_can_be_raised(self):
        """Test ERPNextError can be raised and caught."""
        with pytest.raises(ERPNextError):
            raise ERPNextError("API Error")

    def test_assignment_error_can_be_raised(self):
        """Test AssignmentError can be raised and caught."""
        with pytest.raises(AssignmentError):
            raise AssignmentError("Assignment failed")

    def test_task_creation_error_can_be_raised(self):
        """Test TaskCreationError can be raised and caught."""
        with pytest.raises(TaskCreationError):
            raise TaskCreationError("Task creation failed")

    def test_configuration_error_can_be_raised(self):
        """Test ConfigurationError can be raised and caught."""
        with pytest.raises(ConfigurationError):
            raise ConfigurationError("Missing config")


class TestErrorHandlingInRoutes:
    """Tests for error handling in CRM routes."""

    def test_validation_error_response(self, client):
        """Test that validation errors return 400."""
        invalid_payload = {"name": "John"}  # Missing required fields

        response = client.post(
            "/api/crm/process-lead",
            json=invalid_payload,
            content_type="application/json",
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data

    def test_erpnext_client_initialization_error(self, client):
        """Test handling of ERPNext client initialization error."""
        with patch("app.routes.crm.ERPNextClient") as mock_client_class:
            mock_client_class.side_effect = ConfigurationError("Missing credentials")

            response = client.post(
                "/api/crm/process-lead",
                json=VALID_PAYLOAD,
                content_type="application/json",
            )

            assert response.status_code == 500
            data = response.get_json()
            assert "error" in data

    def test_lead_creation_erpnext_error(self, client):
        """Test handling of ERPNext error during lead creation."""
        with patch("app.routes.crm.ERPNextClient") as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            mock_client.create_lead.side_effect = ERPNextException("API Error")

            response = client.post(
                "/api/crm/process-lead",
                json=VALID_PAYLOAD,
                content_type="application/json",
            )

            assert response.status_code == 500
            data = response.get_json()
            assert "error" in data
            assert "Lead creation failed" in data["error"]

    def test_assignment_error_during_process_lead(self, client):
        """Test handling of assignment error."""
        with patch("app.routes.crm.ERPNextClient") as mock_client_class:
            with patch("app.routes.crm.assign_to_salesperson") as mock_assign:
                mock_client = Mock()
                mock_client_class.return_value = mock_client
                mock_client.create_lead.return_value = {"name": "LEAD-0001"}
                mock_assign.side_effect = ValueError("No salespersons configured")

                response = client.post(
                    "/api/crm/process-lead",
                    json=VALID_PAYLOAD,
                    content_type="application/json",
                )

                assert response.status_code == 500
                data = response.get_json()
                assert "error" in data

    def test_task_creation_error_propagates(self, client):
        """Test that task creation errors are caught and return 500."""
        with patch("app.routes.crm.ERPNextClient") as mock_client_class:
            with patch("app.routes.crm.create_followup_task") as mock_task_service:
                mock_client = Mock()
                mock_client_class.return_value = mock_client
                mock_client.create_lead.return_value = {"name": "LEAD-0001"}
                mock_task_service.side_effect = TaskCreationError("Task API failed")

                response = client.post(
                    "/api/crm/process-lead",
                    json=VALID_PAYLOAD,
                    content_type="application/json",
                )

                assert response.status_code == 500
                data = response.get_json()
                assert "error" in data

    def test_unexpected_error_returns_500(self, client):
        """Test that unexpected errors return 500 with generic message."""
        with patch("app.routes.crm.ERPNextClient") as mock_client_class:
            mock_client_class.side_effect = RuntimeError("Unexpected error")

            response = client.post(
                "/api/crm/process-lead",
                json=VALID_PAYLOAD,
                content_type="application/json",
            )

            assert response.status_code == 500
            data = response.get_json()
            assert "error" in data

    def test_successful_response_includes_all_fields(self, client):
        """Test successful response includes all required fields."""
        with patch("app.routes.crm.ERPNextClient") as mock_client_class:
            with patch("app.routes.crm.create_followup_task") as mock_task_service:
                mock_client = Mock()
                mock_client_class.return_value = mock_client
                mock_client.create_lead.return_value = {"name": "LEAD-0001"}
                mock_task_service.return_value = {"name": "TDO-000001"}

                response = client.post(
                    "/api/crm/process-lead",
                    json=VALID_PAYLOAD,
                    content_type="application/json",
                )

                assert response.status_code == 201
                data = response.get_json()
                assert data["status"] == "success"
                assert "lead_id" in data
                assert "task_id" in data
                assert "assigned_to" in data

    def test_response_headers_are_json(self, client):
        """Test that responses have proper JSON content-type."""
        with patch("app.routes.crm.ERPNextClient") as mock_client_class:
            mock_client_class.side_effect = Exception("Error")

            response = client.post(
                "/api/crm/process-lead",
                json=VALID_PAYLOAD,
                content_type="application/json",
            )

            assert "application/json" in response.content_type
