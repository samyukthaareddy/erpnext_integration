"""
ERPNext REST API client wrapper.

Provides a reusable interface for all ERPNext API interactions including
lead creation, task creation, and document updates.
"""

import requests
from requests.auth import HTTPBasicAuth
from config.logging import get_logger
from config.settings import get_config

logger = get_logger(__name__)
config = get_config()


class ERPNextException(Exception):
    """Base exception for ERPNext API errors."""
    pass


class ERPNextAuthException(ERPNextException):
    """Authentication error with ERPNext."""
    pass


class ERPNextAPIException(ERPNextException):
    """API response error from ERPNext."""
    pass


class ERPNextClient:
    """Client for interacting with ERPNext REST API."""

    def __init__(self, base_url=None, api_key=None, api_secret=None):
        """
        Initialize ERPNext client with credentials.

        Args:
            base_url (str): ERPNext instance URL
            api_key (str): ERPNext API key
            api_secret (str): ERPNext API secret
        """
        self.base_url = (base_url or config.ERPNEXT_BASE_URL).rstrip("/")
        self.api_key = api_key or config.ERPNEXT_API_KEY
        self.api_secret = api_secret or config.ERPNEXT_API_SECRET

        if not all([self.base_url, self.api_key, self.api_secret]):
            raise ERPNextAuthException(
                "Missing ERPNext credentials. Check config or environment variables."
            )

        self.session = requests.Session()
        self.session.auth = HTTPBasicAuth(self.api_key, self.api_secret)
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json"
        })

    def _build_url(self, endpoint):
        """Build full API URL for an endpoint."""
        return f"{self.base_url}/api/resource/{endpoint}"

    def _handle_response(self, response, operation):
        """
        Handle API response and raise appropriate exceptions.

        Args:
            response: requests.Response object
            operation (str): Description of the operation for logging

        Returns:
            dict: Parsed JSON response

        Raises:
            ERPNextAuthException: Authentication failed
            ERPNextAPIException: API returned error
        """
        if response.status_code == 401:
            logger.error(f"Authentication failed for {operation}")
            raise ERPNextAuthException("Invalid ERPNext credentials")

        if response.status_code == 403:
            logger.error(f"Permission denied for {operation}")
            raise ERPNextAPIException("Permission denied")

        if response.status_code >= 400:
            error_msg = response.text
            try:
                error_data = response.json()
                error_msg = error_data.get("message", error_msg)
            except:
                pass

            logger.error(f"API error for {operation}: {response.status_code} - {error_msg}")
            raise ERPNextAPIException(f"{operation} failed: {error_msg}")

        try:
            return response.json()
        except:
            logger.error(f"Failed to parse response for {operation}")
            raise ERPNextAPIException(f"Invalid response from {operation}")

    def create_lead(self, lead_data):
        """
        Create a new Lead document in ERPNext.

        Args:
            lead_data (dict): Lead document data

        Returns:
            dict: Created Lead with id, name, and other fields

        Raises:
            ERPNextException: On API error
        """
        url = self._build_url("Lead")
        try:
            logger.info(f"Creating lead for {lead_data.get('email', 'unknown')}")
            response = self.session.post(url, json={"data": lead_data})
            result = self._handle_response(response, "create_lead")
            lead_id = result.get("data", {}).get("name")
            logger.info(f"Lead created successfully: {lead_id}")
            return result.get("data", {})
        except requests.RequestException as e:
            logger.error(f"Request failed for create_lead: {e}")
            raise ERPNextAPIException(f"Network error: {e}")

    def get_lead(self, lead_id):
        """
        Retrieve a Lead document from ERPNext.

        Args:
            lead_id (str): Lead document name/ID

        Returns:
            dict: Lead document data

        Raises:
            ERPNextException: On API error
        """
        url = f"{self._build_url('Lead')}/{lead_id}"
        try:
            logger.info(f"Fetching lead: {lead_id}")
            response = self.session.get(url)
            result = self._handle_response(response, f"get_lead({lead_id})")
            return result.get("data", {})
        except requests.RequestException as e:
            logger.error(f"Request failed for get_lead: {e}")
            raise ERPNextAPIException(f"Network error: {e}")

    def update_lead(self, lead_id, update_data):
        """
        Update a Lead document in ERPNext.

        Args:
            lead_id (str): Lead document name/ID
            update_data (dict): Fields to update

        Returns:
            dict: Updated Lead document

        Raises:
            ERPNextException: On API error
        """
        url = f"{self._build_url('Lead')}/{lead_id}"
        try:
            logger.info(f"Updating lead: {lead_id}")
            response = self.session.put(url, json={"data": update_data})
            result = self._handle_response(response, f"update_lead({lead_id})")
            logger.info(f"Lead updated: {lead_id}")
            return result.get("data", {})
        except requests.RequestException as e:
            logger.error(f"Request failed for update_lead: {e}")
            raise ERPNextAPIException(f"Network error: {e}")

    def create_task(self, task_data):
        """
        Create a new Task document in ERPNext.

        Args:
            task_data (dict): Task document data

        Returns:
            dict: Created Task with id, name, and other fields

        Raises:
            ERPNextException: On API error
        """
        url = self._build_url("ToDo")
        try:
            logger.info(f"Creating task for {task_data.get('title', 'unknown')}")
            response = self.session.post(url, json={"data": task_data})
            result = self._handle_response(response, "create_task")
            task_id = result.get("data", {}).get("name")
            logger.info(f"Task created successfully: {task_id}")
            return result.get("data", {})
        except requests.RequestException as e:
            logger.error(f"Request failed for create_task: {e}")
            raise ERPNextAPIException(f"Network error: {e}")

    def get_user_list(self):
        """
        Get list of active users/salespersons from ERPNext.

        Returns:
            list: List of user dictionaries with 'name' field

        Raises:
            ERPNextException: On API error
        """
        url = self._build_url("User")
        try:
            logger.info("Fetching user list")
            response = self.session.get(url, params={"fields": '["name","full_name"]'})
            result = self._handle_response(response, "get_user_list")
            return result.get("data", [])
        except requests.RequestException as e:
            logger.error(f"Request failed for get_user_list: {e}")
            raise ERPNextAPIException(f"Network error: {e}")
