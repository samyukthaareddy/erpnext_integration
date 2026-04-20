"""Unit tests for app/routes/crm.py"""

import pytest
from unittest.mock import patch, Mock
from app.main import create_app
import app.assignment_engine as engine


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
    "product_interest": "Industrial sensors",
    "message": "Need pricing for bulk order",
    "source": "whatsapp",
}


def test_process_lead_success(client):
    """Test successful lead processing with assignment."""
    engine._rr_index = 0
    with patch("app.routes.crm.ERPNextClient") as mock_client_class:
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.create_lead.return_value = {
            "name": "LEAD-0001",
            "email_id": "john@example.com",
        }
        mock_client.update_lead.return_value = {"name": "LEAD-0001"}

        response = client.post(
            "/api/crm/process-lead",
            json=VALID_PAYLOAD,
            content_type="application/json",
        )

        assert response.status_code == 201
        data = response.get_json()
        assert data["lead_id"] == "LEAD-0001"
        assert data["status"] == "success"
        assert "assigned_to" in data
        mock_client.create_lead.assert_called_once()
        mock_client.update_lead.assert_called_once()


def test_process_lead_empty_payload(client):
    """Test with empty payload."""
    response = client.post(
        "/api/crm/process-lead",
        json={},
        content_type="application/json",
    )

    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data


def test_process_lead_missing_required_field(client):
    """Test with missing required field (email)."""
    invalid_payload = {k: v for k, v in VALID_PAYLOAD.items() if k != "email"}

    response = client.post(
        "/api/crm/process-lead",
        json=invalid_payload,
        content_type="application/json",
    )

    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data
    assert "Validation failed" in data["error"]


def test_process_lead_invalid_email(client):
    """Test with invalid email format."""
    invalid_payload = {**VALID_PAYLOAD, "email": "not-an-email"}

    response = client.post(
        "/api/crm/process-lead",
        json=invalid_payload,
        content_type="application/json",
    )

    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data


def test_process_lead_invalid_phone(client):
    """Test with invalid phone format."""
    invalid_payload = {**VALID_PAYLOAD, "phone": "abc"}

    response = client.post(
        "/api/crm/process-lead",
        json=invalid_payload,
        content_type="application/json",
    )

    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data


def test_process_lead_no_payload(client):
    """Test with no JSON payload."""
    response = client.post(
        "/api/crm/process-lead",
        content_type="application/json",
    )

    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data


def test_process_lead_erpnext_error(client):
    """Test with ERPNext API error."""
    from app.erpnext_client import ERPNextException

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


def test_process_lead_assignment_included_in_response(client):
    """Test that assigned_to is returned in the response."""
    with patch("app.routes.crm.ERPNextClient") as mock_client_class:
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.create_lead.return_value = {"name": "LEAD-0005"}
        mock_client.update_lead.return_value = {"name": "LEAD-0005"}

        response = client.post(
            "/api/crm/process-lead",
            json=VALID_PAYLOAD,
            content_type="application/json",
        )

        assert response.status_code == 201
        data = response.get_json()
        assert "assigned_to" in data
        assert data["assigned_to"] is not None


def test_process_lead_update_lead_called_with_assign(client):
    """Test that update_lead is called with _assign field."""
    with patch("app.routes.crm.ERPNextClient") as mock_client_class:
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.create_lead.return_value = {"name": "LEAD-0006"}
        mock_client.update_lead.return_value = {"name": "LEAD-0006"}

        client.post(
            "/api/crm/process-lead",
            json=VALID_PAYLOAD,
            content_type="application/json",
        )

        call_args = mock_client.update_lead.call_args
        assert call_args[0][0] == "LEAD-0006"
        assert "_assign" in call_args[0][1]


def test_process_lead_client_init_error(client):
    """Test with ERPNext client initialization error."""
    with patch("app.routes.crm.ERPNextClient") as mock_client_class:
        mock_client_class.side_effect = Exception("Config Error")

        response = client.post(
            "/api/crm/process-lead",
            json=VALID_PAYLOAD,
            content_type="application/json",
        )

        assert response.status_code == 500
        data = response.get_json()
        assert "error" in data


def test_process_lead_with_optional_fields(client):
    """Test with optional fields included."""
    with patch("app.routes.crm.ERPNextClient") as mock_client_class:
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.create_lead.return_value = {
            "name": "LEAD-0002",
            "email_id": "jane@example.com",
        }

        payload = {
            **VALID_PAYLOAD,
            "product_interest": "ERP Solutions",
            "message": "Interested in demo",
        }

        response = client.post(
            "/api/crm/process-lead",
            json=payload,
            content_type="application/json",
        )

        assert response.status_code == 201
        data = response.get_json()
        assert data["status"] == "success"


def test_process_lead_name_parsing(client):
    """Test that name is correctly parsed into first_name and last_name."""
    with patch("app.routes.crm.ERPNextClient") as mock_client_class:
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.create_lead.return_value = {"name": "LEAD-0003"}

        response = client.post(
            "/api/crm/process-lead",
            json=VALID_PAYLOAD,
            content_type="application/json",
        )

        # Verify the lead data passed to create_lead
        call_args = mock_client.create_lead.call_args[0][0]
        assert call_args["first_name"] == "John"
        assert call_args["last_name"] == "Doe"
