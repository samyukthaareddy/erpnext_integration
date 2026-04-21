"""Unit tests for app/task_service.py"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from app.task_service import (
    generate_task_description,
    calculate_due_date,
    create_followup_task,
)

LEAD = {
    "name": "Jane Doe",
    "email": "jane@example.com",
    "phone": "+1-800-555-0199",
    "company": "Acme Corp",
    "product_interest": "ERP Solutions",
    "message": "Need pricing and demo",
}


def test_generate_task_description_complete():
    """Test description generation with all fields."""
    description = generate_task_description(LEAD)
    assert "Jane Doe" in description
    assert "jane@example.com" in description
    assert "+1-800-555-0199" in description
    assert "Acme Corp" in description
    assert "ERP Solutions" in description
    assert "Need pricing and demo" in description


def test_generate_task_description_minimal():
    """Test description generation with minimal fields."""
    minimal_lead = {
        "name": "John Smith",
        "email": "john@example.com",
        "company": "Tech Inc",
    }
    description = generate_task_description(minimal_lead)
    assert "John Smith" in description
    assert "john@example.com" in description
    assert "Tech Inc" in description
    assert "N/A" in description  # For missing fields


def test_generate_task_description_empty():
    """Test description generation with empty dict."""
    description = generate_task_description({})
    assert "Unknown" in description
    assert "N/A" in description


def test_calculate_due_date_default_24h():
    """Test due date calculation with default 24 hour offset."""
    due_date = calculate_due_date()
    expected = (datetime.now() + timedelta(hours=24)).strftime("%Y-%m-%d")
    assert due_date == expected


def test_calculate_due_date_custom_offset():
    """Test due date calculation with custom offset."""
    due_date = calculate_due_date(hours_offset=48)
    expected = (datetime.now() + timedelta(hours=48)).strftime("%Y-%m-%d")
    assert due_date == expected


def test_calculate_due_date_zero_offset():
    """Test due date calculation with zero offset (today)."""
    due_date = calculate_due_date(hours_offset=0)
    expected = datetime.now().strftime("%Y-%m-%d")
    assert due_date == expected


def test_calculate_due_date_format():
    """Test that due date is in correct YYYY-MM-DD format."""
    due_date = calculate_due_date()
    # Should parse without error
    datetime.strptime(due_date, "%Y-%m-%d")


def test_create_followup_task_success():
    """Test successful task creation."""
    mock_client = Mock()
    mock_task = {
        "name": "TDO-000001",
        "title": "Follow up: Jane Doe",
        "description": "Test description",
        "due_date": "2026-04-22",
    }
    mock_client.create_task.return_value = mock_task

    result = create_followup_task(
        lead_id="LEAD-0001",
        assigned_to="sales1@example.com",
        lead_data=LEAD,
        client=mock_client,
    )

    assert result["name"] == "TDO-000001"
    assert "Follow up" in result["title"]
    assert "Jane Doe" in result["title"]
    mock_client.create_task.assert_called_once()


def test_create_followup_task_calls_client_with_correct_data():
    """Test that create_task is called with correct task data."""
    mock_client = Mock()
    mock_client.create_task.return_value = {"name": "TDO-000001"}

    create_followup_task(
        lead_id="LEAD-0001",
        assigned_to="sales1@example.com",
        lead_data=LEAD,
        client=mock_client,
    )

    call_args = mock_client.create_task.call_args[0][0]
    assert call_args["title"] == "Follow up: Jane Doe"
    assert call_args["reference_type"] == "Lead"
    assert call_args["reference_name"] == "LEAD-0001"
    assert call_args["priority"] == "Medium"
    assert call_args["assigned_by"] == "sales1@example.com"


def test_create_followup_task_custom_offset():
    """Test task creation with custom hours offset."""
    mock_client = Mock()
    mock_client.create_task.return_value = {"name": "TDO-000001"}

    create_followup_task(
        lead_id="LEAD-0001",
        assigned_to="sales1@example.com",
        lead_data=LEAD,
        client=mock_client,
        hours_offset=48,
    )

    call_args = mock_client.create_task.call_args[0][0]
    expected_date = (datetime.now() + timedelta(hours=48)).strftime("%Y-%m-%d")
    assert call_args["due_date"] == expected_date


def test_create_followup_task_error_propagates():
    """Test that client errors are propagated."""
    mock_client = Mock()
    mock_client.create_task.side_effect = Exception("API Error")

    with pytest.raises(Exception, match="API Error"):
        create_followup_task(
            lead_id="LEAD-0001",
            assigned_to="sales1@example.com",
            lead_data=LEAD,
            client=mock_client,
        )


def test_create_followup_task_returns_task_dict():
    """Test that created task is returned."""
    mock_client = Mock()
    expected_task = {
        "name": "TDO-000001",
        "title": "Follow up: Jane Doe",
        "due_date": "2026-04-22",
    }
    mock_client.create_task.return_value = expected_task

    result = create_followup_task(
        lead_id="LEAD-0001",
        assigned_to="sales1@example.com",
        lead_data=LEAD,
        client=mock_client,
    )

    assert result == expected_task
