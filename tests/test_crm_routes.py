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
    "company": "ACME Corp",
    "first_name": "John",
    "last_name": "Doe",
    "email": "john@example.com",
    "phone": "+1-800-555-0199",
    "product_interest": "Industrial sensors",
    "message": "Need pricing for bulk order",
    "lead_source": "whatsapp",
}


def test_process_lead_success(client):
    """Test successful lead processing with assignment."""
    engine._rr_index = 0
    with patch("app.routes.crm.ERPNextClient") as mock_client_class:
        with patch("app.routes.crm.create_followup_task") as mock_task_service:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            mock_client.create_lead.return_value = {
                "name": "LEAD-0001",
                "email_id": "john@example.com",
            }
            mock_client.update_lead.return_value = {"name": "LEAD-0001"}
            mock_task_service.return_value = {"name": "TDO-000001"}

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

        assert response.status_code == 400  # Non-retryable error
        data = response.get_json()
        assert data["retryable"] is False


def test_process_lead_assignment_included_in_response(client):
    """Test that assigned_to is returned in the response."""
    with patch("app.routes.crm.ERPNextClient") as mock_client_class:
        with patch("app.routes.crm.create_followup_task") as mock_task_service:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            mock_client.create_lead.return_value = {"name": "LEAD-0005"}
            mock_client.update_lead.return_value = {"name": "LEAD-0005"}
            mock_task_service.return_value = {"name": "TDO-000001"}

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
        with patch("app.routes.crm.create_followup_task") as mock_task_service:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            mock_client.create_lead.return_value = {
                "name": "LEAD-0002",
                "email_id": "jane@example.com",
            }
            mock_task_service.return_value = {"name": "TDO-000001"}

            payload = {
                **VALID_PAYLOAD,
                "product_interest": "ERP Solutions",
                "message": "Interested in demo",
                "task_priority": "High",
            }

            response = client.post(
                "/api/crm/process-lead",
                json=payload,
                content_type="application/json",
            )

            assert response.status_code == 201
            data = response.get_json()
            assert data["status"] == "success"


def test_process_lead_name_fields_mapped(client):
    """Test that first_name and last_name are passed to lead payload."""
    with patch("app.routes.crm.ERPNextClient") as mock_client_class:
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.create_lead.return_value = {"name": "LEAD-0003"}

        response = client.post(
            "/api/crm/process-lead",
            json=VALID_PAYLOAD,
            content_type="application/json",
        )

        call_args = mock_client.create_lead.call_args[0][0]
        assert call_args["first_name"] == "John"
        assert call_args["last_name"] == "Doe"
        assert call_args["company_name"] == "ACME Corp"


def test_process_lead_with_task_creation(client):
    """Test successful lead processing with task creation."""
    engine._rr_index = 0
    with patch("app.routes.crm.ERPNextClient") as mock_client_class:
        with patch("app.routes.crm.create_followup_task") as mock_task_service:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            mock_client.create_lead.return_value = {"name": "LEAD-0007"}
            mock_client.update_lead.return_value = {"name": "LEAD-0007"}
            mock_task_service.return_value = {"name": "TDO-000001"}

            response = client.post(
                "/api/crm/process-lead",
                json=VALID_PAYLOAD,
                content_type="application/json",
            )

            assert response.status_code == 201
            data = response.get_json()
            assert "task_id" in data
            assert data["task_id"] == "TDO-000001"
            mock_task_service.assert_called_once()


def test_process_lead_task_creation_called_with_correct_args(client):
    """Test that task creation is called with correct arguments."""
    with patch("app.routes.crm.ERPNextClient") as mock_client_class:
        with patch("app.routes.crm.create_followup_task") as mock_task_service:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            mock_client.create_lead.return_value = {"name": "LEAD-0008"}
            mock_task_service.return_value = {"name": "TDO-000001"}

            client.post(
                "/api/crm/process-lead",
                json=VALID_PAYLOAD,
                content_type="application/json",
            )

            # Verify task_service was called with correct arguments
            call_args = mock_task_service.call_args
            assert call_args[1]["lead_id"] == "LEAD-0008"
            assert call_args[1]["lead_data"] == VALID_PAYLOAD
            assert call_args[1]["client"] == mock_client


def test_process_lead_full_response_with_all_fields(client):
    """Test that response includes lead_id, task_id, assigned_to, and status."""
    with patch("app.routes.crm.ERPNextClient") as mock_client_class:
        with patch("app.routes.crm.create_followup_task") as mock_task_service:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            mock_client.create_lead.return_value = {"name": "LEAD-0009"}
            mock_task_service.return_value = {"name": "TDO-000002"}

            response = client.post(
                "/api/crm/process-lead",
                json=VALID_PAYLOAD,
                content_type="application/json",
            )

            assert response.status_code == 201
            data = response.get_json()
            assert "lead_id" in data
            assert "task_id" in data
            assert "assigned_to" in data
            assert "status" in data
            assert data["status"] == "success"


def test_process_lead_task_error_propagates(client):
    """Test that task creation errors are propagated."""
    from app.erpnext_client import ERPNextException

    with patch("app.routes.crm.ERPNextClient") as mock_client_class:
        with patch("app.routes.crm.create_followup_task") as mock_task_service:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            mock_client.create_lead.return_value = {"name": "LEAD-0010"}
            mock_task_service.side_effect = ERPNextException("Task creation failed")

            response = client.post(
                "/api/crm/process-lead",
                json=VALID_PAYLOAD,
                content_type="application/json",
            )

            assert response.status_code == 400  # Non-retryable error
            data = response.get_json()
            assert data["retryable"] is False


def test_process_lead_legacy_payload_is_adapted(client):
    """Test backward compatibility for old payload shape from upstream callers."""
    legacy_payload = {
        "name": "Legacy User",
        "email": "legacy@example.com",
        "phone": "+1-800-555-9999",
        "company": "Legacy Corp",
        "source": "webform",
    }
    with patch("app.routes.crm.ERPNextClient") as mock_client_class:
        with patch("app.routes.crm.create_followup_task") as mock_task_service:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            mock_client.create_lead.return_value = {"name": "LEAD-1010"}
            mock_client.update_lead.return_value = {"name": "LEAD-1010"}
            mock_task_service.return_value = {"name": "TDO-001010"}

            response = client.post(
                "/api/crm/process-lead",
                json=legacy_payload,
                content_type="application/json",
            )

            assert response.status_code == 201
            lead_call = mock_client.create_lead.call_args[0][0]
            assert lead_call["first_name"] == "Legacy"
            assert lead_call["last_name"] == "User"


def test_process_lead_whatsapp_source_adapter(client):
    """Test WhatsApp upstream payload normalization path."""
    whatsapp_payload = {
        "source_type": "whatsapp",
        "full_name": "Asha Rao",
        "email": "asha@example.com",
        "phone_number": "+91-90000-12345",
        "business_name": "Asha Industries",
        "message_text": "Need ERP demo",
    }
    with patch("app.routes.crm.ERPNextClient") as mock_client_class:
        with patch("app.routes.crm.create_followup_task") as mock_task_service:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            mock_client.create_lead.return_value = {"name": "LEAD-1011"}
            mock_client.update_lead.return_value = {"name": "LEAD-1011"}
            mock_task_service.return_value = {"name": "TDO-001011"}

            response = client.post(
                "/api/crm/process-lead",
                json=whatsapp_payload,
                content_type="application/json",
            )

            assert response.status_code == 201
            lead_call = mock_client.create_lead.call_args[0][0]
            assert lead_call["company_name"] == "Asha Industries"
            assert lead_call["first_name"] == "Asha"
            assert lead_call["source"] == "whatsapp"


# ============= Enhancement Tests =============


def test_health_check_healthy(client):
    """Test /health endpoint when ERPNext is up."""
    with patch("app.routes.crm.ERPNextClient") as mock_client_class:
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_response = Mock()
        mock_response.status_code = 200
        mock_client.session.get.return_value = mock_response

        response = client.get("/api/crm/health")

        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "healthy"
        assert data["erpnext_connected"] is True
        assert "timestamp" in data
        assert "api_version" in data
        assert data["api_version"] == "1.0.0"


def test_health_check_degraded(client):
    """Test /health endpoint when ERPNext is down."""
    with patch("app.routes.crm.ERPNextClient") as mock_client_class:
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_response = Mock()
        mock_response.status_code = 500
        mock_client.session.get.return_value = mock_response

        response = client.get("/api/crm/health")

        assert response.status_code == 503
        data = response.get_json()
        assert data["status"] == "degraded"
        assert data["erpnext_connected"] is False


def test_health_check_connection_error(client):
    """Test /health endpoint when connection fails."""
    with patch("app.routes.crm.ERPNextClient") as mock_client_class:
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.session.get.side_effect = Exception("Connection refused")

        response = client.get("/api/crm/health")

        assert response.status_code == 503
        data = response.get_json()
        assert data["status"] == "degraded"
        assert data["erpnext_connected"] is False


def test_process_leads_batch_all_valid(client):
    """Test batch processing with all valid leads."""
    engine._rr_index = 0
    batch_payload = {
        "leads": [
            {
                "company": "ABC Inc",
                "first_name": "John",
                "last_name": "Doe",
                "email": "john@abc.com",
                "phone": "+1-555-1234",
            },
            {
                "company": "XYZ Ltd",
                "first_name": "Jane",
                "last_name": "Smith",
                "email": "jane@xyz.com",
                "phone": "+1-555-5678",
            },
        ]
    }

    with patch("app.routes.crm.ERPNextClient") as mock_client_class:
        with patch("app.routes.crm.create_followup_task") as mock_task_service:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            mock_client.base_url = "http://localhost:8080"
            mock_client.create_lead.side_effect = [
                {"name": "LEAD-0001"},
                {"name": "LEAD-0002"},
            ]
            mock_task_service.return_value = {"name": "TDO-000001"}

            response = client.post(
                "/api/crm/process-leads",
                json=batch_payload,
                content_type="application/json",
            )

            assert response.status_code == 200
            data = response.get_json()
            assert data["success_count"] == 2
            assert data["failed_count"] == 0
            assert len(data["results"]) == 2
            assert data["results"][0]["status"] == "success"
            assert data["results"][1]["status"] == "success"


def test_process_leads_batch_mixed(client):
    """Test batch processing with mixed valid/invalid leads."""
    batch_payload = {
        "leads": [
            {
                "company": "ABC Inc",
                "first_name": "John",
                "last_name": "Doe",
                "email": "john@abc.com",
                "phone": "+1-555-1234",
            },
            {
                "company": "XYZ Ltd",
                "first_name": "Jane",
                "last_name": "Smith",
                "email": "invalid-email",
                "phone": "+1-555-5678",
            },
        ]
    }

    with patch("app.routes.crm.ERPNextClient") as mock_client_class:
        with patch("app.routes.crm.create_followup_task") as mock_task_service:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            mock_client.base_url = "http://localhost:8080"
            mock_client.create_lead.return_value = {"name": "LEAD-0001"}
            mock_task_service.return_value = {"name": "TDO-000001"}

            response = client.post(
                "/api/crm/process-leads",
                json=batch_payload,
                content_type="application/json",
            )

            assert response.status_code == 207  # Multi-Status
            data = response.get_json()
            assert data["success_count"] == 1
            assert data["failed_count"] == 1
            assert data["results"][0]["status"] == "success"
            assert data["results"][1]["status"] == "failed"


def test_process_leads_batch_empty(client):
    """Test batch processing with empty leads array."""
    batch_payload = {"leads": []}

    response = client.post(
        "/api/crm/process-leads",
        json=batch_payload,
        content_type="application/json",
    )

    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data


def test_process_leads_batch_no_leads_field(client):
    """Test batch processing without leads field."""
    batch_payload = {"data": "something"}

    response = client.post(
        "/api/crm/process-leads",
        json=batch_payload,
        content_type="application/json",
    )

    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data


def test_process_lead_enhanced_response_fields(client):
    """Test that /process-lead returns enhanced response fields."""
    engine._rr_index = 0
    with patch("app.routes.crm.ERPNextClient") as mock_client_class:
        with patch("app.routes.crm.create_followup_task") as mock_task_service:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            mock_client.base_url = "http://localhost:8080"
            mock_client.create_lead.return_value = {"name": "LEAD-0001"}
            mock_task_service.return_value = {"name": "TDO-000001"}

            response = client.post(
                "/api/crm/process-lead",
                json=VALID_PAYLOAD,
                content_type="application/json",
            )

            assert response.status_code == 201
            data = response.get_json()
            # Original fields
            assert "lead_id" in data
            assert "task_id" in data
            assert "assigned_to" in data
            assert "status" in data
            # Enhanced fields
            assert "lead_url" in data
            assert "task_url" in data
            assert "created_at" in data
            assert "erpnext_name" in data
            assert "assignment_strategy" in data
            # Verify URL format
            assert "http://localhost:8080/app/lead/LEAD-0001" == data["lead_url"]
            assert "http://localhost:8080/app/todo/TDO-000001" == data["task_url"]


def test_process_lead_error_retryable_timeout(client):
    """Test error response with retryable=true for timeout."""
    from app.erpnext_client import ERPNextException

    with patch("app.routes.crm.ERPNextClient") as mock_client_class:
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.create_lead.side_effect = ERPNextException("Connection timeout")

        response = client.post(
            "/api/crm/process-lead",
            json=VALID_PAYLOAD,
            content_type="application/json",
        )

        assert response.status_code == 503  # Retryable errors return 503
        data = response.get_json()
        assert data["status"] == "error"
        assert data["retryable"] is True
        assert "timestamp" in data
        assert data["error_type"] == "ERPNextException"


def test_process_lead_error_not_retryable_validation(client):
    """Test error response with retryable=false for validation error."""
    from app.erpnext_client import ERPNextException

    with patch("app.routes.crm.ERPNextClient") as mock_client_class:
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.create_lead.side_effect = ERPNextException("Validation failed")

        response = client.post(
            "/api/crm/process-lead",
            json=VALID_PAYLOAD,
            content_type="application/json",
        )

        assert response.status_code == 400  # Non-retryable errors return 400
        data = response.get_json()
        assert data["status"] == "error"
        assert data["retryable"] is False
        assert "timestamp" in data


def test_process_leads_batch_returns_urls(client):
    """Test that batch processing returns URLs for each lead."""
    batch_payload = {
        "leads": [
            {
                "company": "ABC Inc",
                "first_name": "John",
                "last_name": "Doe",
                "email": "john@abc.com",
                "phone": "+1-555-1234",
            }
        ]
    }

    with patch("app.routes.crm.ERPNextClient") as mock_client_class:
        with patch("app.routes.crm.create_followup_task") as mock_task_service:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            mock_client.base_url = "http://localhost:8080"
            mock_client.create_lead.return_value = {"name": "LEAD-0001"}
            mock_task_service.return_value = {"name": "TDO-000001"}

            response = client.post(
                "/api/crm/process-leads",
                json=batch_payload,
                content_type="application/json",
            )

            assert response.status_code == 200
            data = response.get_json()
            assert "lead_url" in data["results"][0]
            assert "task_url" in data["results"][0]
            assert "http://localhost:8080/app/lead/LEAD-0001" == data["results"][0]["lead_url"]
            assert "http://localhost:8080/app/todo/TDO-000001" == data["results"][0]["task_url"]
