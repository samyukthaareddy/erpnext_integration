"""Unit tests for app/erpnext_client.py (with mocked responses)"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from app.erpnext_client import (
    ERPNextClient,
    ERPNextException,
    ERPNextAuthException,
    ERPNextAPIException,
)


@pytest.fixture
def mock_config():
    """Mock configuration for ERPNext client."""
    with patch("app.erpnext_client.config") as mock:
        mock.ERPNEXT_BASE_URL = "http://mock-erpnext.local"
        mock.ERPNEXT_API_KEY = "test_key"
        mock.ERPNEXT_API_SECRET = "test_secret"
        yield mock


@pytest.fixture
def client(mock_config):
    """Create an ERPNext client for testing."""
    return ERPNextClient()


def test_client_initialization(mock_config):
    """Test ERPNext client initialization with credentials."""
    client = ERPNextClient()
    assert client.base_url == "http://mock-erpnext.local"
    assert client.api_key == "test_key"
    assert client.api_secret == "test_secret"


def test_client_initialization_missing_credentials():
    """Test that missing credentials raise an error."""
    with patch("app.erpnext_client.config") as mock_config:
        mock_config.ERPNEXT_BASE_URL = ""
        mock_config.ERPNEXT_API_KEY = ""
        mock_config.ERPNEXT_API_SECRET = ""
        with pytest.raises(ERPNextAuthException):
            ERPNextClient()


def test_client_initialization_with_explicit_params(mock_config):
    """Test creating client with explicit parameters."""
    client = ERPNextClient(
        base_url="http://custom.local",
        api_key="custom_key",
        api_secret="custom_secret",
    )
    assert client.base_url == "http://custom.local"
    assert client.api_key == "custom_key"


def test_build_url(client):
    """Test URL building."""
    url = client._build_url("Lead")
    assert url == "http://mock-erpnext.local/api/resource/Lead"


def test_build_url_removes_trailing_slash():
    """Test URL building removes trailing slashes."""
    client = ERPNextClient(
        base_url="http://mock-erpnext.local/",
        api_key="key",
        api_secret="secret",
    )
    url = client._build_url("Lead")
    assert url == "http://mock-erpnext.local/api/resource/Lead"


@patch("app.erpnext_client.requests.Session.post")
def test_create_lead_success(mock_post, client):
    """Test successful lead creation."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": {
            "name": "LEAD-0001",
            "email": "john@example.com",
            "company": "ACME",
        }
    }
    mock_post.return_value = mock_response

    lead_data = {"email": "john@example.com", "company": "ACME"}
    result = client.create_lead(lead_data)

    assert result["name"] == "LEAD-0001"
    assert result["email"] == "john@example.com"
    mock_post.assert_called_once()


@patch("app.erpnext_client.requests.Session.post")
def test_create_lead_auth_error(mock_post, client):
    """Test lead creation with authentication error."""
    mock_response = Mock()
    mock_response.status_code = 401
    mock_post.return_value = mock_response

    with pytest.raises(ERPNextAuthException):
        client.create_lead({"email": "john@example.com"})


@patch("app.erpnext_client.requests.Session.post")
def test_create_lead_api_error(mock_post, client):
    """Test lead creation with API error."""
    mock_response = Mock()
    mock_response.status_code = 400
    mock_response.text = "Invalid data"
    mock_response.json.return_value = {"message": "Email already exists"}
    mock_post.return_value = mock_response

    with pytest.raises(ERPNextAPIException):
        client.create_lead({"email": "john@example.com"})


@patch("app.erpnext_client.requests.Session.get")
def test_get_lead_success(mock_get, client):
    """Test successful lead retrieval."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": {
            "name": "LEAD-0001",
            "email": "john@example.com",
        }
    }
    mock_get.return_value = mock_response

    result = client.get_lead("LEAD-0001")

    assert result["name"] == "LEAD-0001"
    assert result["email"] == "john@example.com"
    mock_get.assert_called_once()


@patch("app.erpnext_client.requests.Session.put")
def test_update_lead_success(mock_put, client):
    """Test successful lead update."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": {
            "name": "LEAD-0001",
            "status": "Interested",
        }
    }
    mock_put.return_value = mock_response

    result = client.update_lead("LEAD-0001", {"status": "Interested"})

    assert result["status"] == "Interested"
    mock_put.assert_called_once()


@patch("app.erpnext_client.requests.Session.post")
def test_create_task_success(mock_post, client):
    """Test successful task creation."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": {
            "name": "TASK-0001",
            "title": "Follow up with John",
        }
    }
    mock_post.return_value = mock_response

    task_data = {"title": "Follow up with John", "assigned_to": "salesperson@example.com"}
    result = client.create_task(task_data)

    assert result["name"] == "TASK-0001"
    assert result["title"] == "Follow up with John"
    mock_post.assert_called_once()


@patch("app.erpnext_client.requests.Session.get")
def test_get_user_list_success(mock_get, client):
    """Test successful user list retrieval."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": [
            {"name": "user1@example.com", "full_name": "User One"},
            {"name": "user2@example.com", "full_name": "User Two"},
        ]
    }
    mock_get.return_value = mock_response

    result = client.get_user_list()

    assert len(result) == 2
    assert result[0]["name"] == "user1@example.com"
    mock_get.assert_called_once()


@patch("app.erpnext_client.requests.Session.post")
def test_network_error_handling(mock_post, client):
    """Test handling of network errors."""
    import requests
    mock_post.side_effect = requests.RequestException("Connection failed")

    with pytest.raises(ERPNextAPIException):
        client.create_lead({"email": "john@example.com"})
