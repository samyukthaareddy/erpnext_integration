"""
Follow-up task service for leads.

Creates and manages follow-up tasks in ERPNext for newly assigned leads.
"""

from datetime import datetime, timedelta
from config.logging import get_logger

logger = get_logger(__name__)


def generate_task_description(lead_data: dict) -> str:
    """
    Generate a task description template based on lead data.

    Args:
        lead_data (dict): The lead payload with name, email, company, etc.

    Returns:
        str: Formatted task description
    """
    name = lead_data.get("name", "Unknown")
    email = lead_data.get("email", "unknown@example.com")
    company = lead_data.get("company", "Unknown")
    phone = lead_data.get("phone", "N/A")
    product_interest = lead_data.get("product_interest", "N/A")
    message = lead_data.get("message", "None")

    description = (
        f"Follow up with {name} from {company}.\n"
        f"Email: {email}\n"
        f"Phone: {phone}\n"
        f"Product Interest: {product_interest}\n"
        f"Message: {message}"
    )
    return description


def calculate_due_date(hours_offset: int = 24) -> str:
    """
    Calculate due date for task (default 24 hours from now).

    Args:
        hours_offset (int): Hours from now for due date (default: 24)

    Returns:
        str: Due date in YYYY-MM-DD format
    """
    due_date = datetime.now() + timedelta(hours=hours_offset)
    return due_date.strftime("%Y-%m-%d")


def create_followup_task(
    lead_id: str,
    assigned_to: str,
    lead_data: dict,
    client,
    hours_offset: int = 24
) -> dict:
    """
    Create a follow-up task for a newly assigned lead.

    Args:
        lead_id (str): ERPNext Lead ID
        assigned_to (str): Assigned salesperson email/name
        lead_data (dict): Original lead payload for description generation
        client: ERPNextClient instance for creating task
        hours_offset (int): Hours from now for due date (default: 24)

    Returns:
        dict: Created task with task_id and other fields

    Raises:
        ERPNextException: On API error during task creation
    """
    try:
        lead_name = lead_data.get("name", f"Lead-{lead_id}")
        description = generate_task_description(lead_data)
        due_date = calculate_due_date(hours_offset)

        task_data = {
            "title": f"Follow up: {lead_name}",
            "description": description,
            "due_date": due_date,
            "assigned_by": assigned_to,
            "reference_type": "Lead",
            "reference_name": lead_id,
            "priority": "Medium",
        }

        logger.info(f"Creating follow-up task for lead {lead_id}, assigned to {assigned_to}")
        task = client.create_task(task_data)
        task_id = task.get("name")
        logger.info(f"Follow-up task created successfully: {task_id}")
        return task

    except Exception as e:
        logger.error(f"Error creating follow-up task for lead {lead_id}: {e}")
        raise
