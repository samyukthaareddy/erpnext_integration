"""CRM routes for lead processing."""

from flask import Blueprint, request, jsonify
from utils.validators import validate_lead_payload
from app.erpnext_client import ERPNextClient, ERPNextException
from app.assignment_engine import assign_to_salesperson
from app.task_service import create_followup_task
from app.exceptions import ValidationError, ERPNextError, AssignmentError, TaskCreationError, ConfigurationError
from config.logging import get_logger

logger = get_logger(__name__)
bp = Blueprint("crm", __name__, url_prefix="/api/crm")


def _build_lead_data(payload: dict) -> dict:
    return {
        "first_name": payload.get("name", "").split()[0],
        "last_name": " ".join(payload.get("name", "").split()[1:]) or "Lead",
        "email_id": payload.get("email"),
        "phone": payload.get("phone"),
        "company_name": payload.get("company"),
        "notes": (
            f"Product Interest: {payload.get('product_interest', 'N/A')}\n"
            f"Message: {payload.get('message', 'N/A')}\n"
            f"Source: {payload.get('source', 'N/A')}"
        ),
    }


@bp.route("/process-lead", methods=["POST"])
def process_lead():
    """
    Process incoming lead: validate → create → assign → create follow-up task.

    Returns:
    {
        "lead_id": "LEAD-0001",
        "task_id": "TDO-000001",
        "assigned_to": "sales1@example.com",
        "status": "success"
    }
    """
    lead_id = None

    try:
        payload = request.get_json(silent=True)
        if not payload:
            raise ValidationError("No payload provided")

        errors = validate_lead_payload(payload)
        if errors:
            raise ValidationError(f"Validation failed: {errors}")

        # Init client
        try:
            client = ERPNextClient()
        except Exception as e:
            raise ConfigurationError(f"ERPNext client init failed: {e}")

        # Create lead
        try:
            lead = client.create_lead(_build_lead_data(payload))
            lead_id = lead.get("name")
            logger.info(f"Lead created: {lead_id}")
        except ERPNextException as e:
            raise ERPNextError(f"Lead creation failed: {e}")

        # Assign lead
        try:
            assigned_to = assign_to_salesperson(payload)
            client.update_lead(lead_id, {"_assign": assigned_to})
            logger.info(f"Lead {lead_id} assigned to {assigned_to}")
        except ValueError as e:
            raise AssignmentError(f"Assignment failed: {e}")
        except ERPNextException as e:
            raise ERPNextError(f"Failed to update lead assignment: {e}")

        # Create follow-up task
        try:
            task = create_followup_task(
                lead_id=lead_id,
                assigned_to=assigned_to,
                lead_data=payload,
                client=client,
            )
            task_id = task.get("name")
            logger.info(f"Follow-up task created: {task_id}")
        except Exception as e:
            # Rollback: delete the lead if task creation fails
            logger.error(f"Task creation failed for lead {lead_id}, attempting rollback: {e}")
            try:
                client.update_lead(lead_id, {"status": "Do Not Contact"})
                logger.warning(f"Rollback: marked lead {lead_id} as 'Do Not Contact'")
            except Exception as rollback_err:
                logger.error(f"Rollback failed for lead {lead_id}: {rollback_err}")
            raise TaskCreationError(f"Follow-up task creation failed: {e}")

        return jsonify({
            "lead_id": lead_id,
            "task_id": task_id,
            "assigned_to": assigned_to,
            "status": "success",
        }), 201

    except ValidationError as e:
        logger.warning(f"Validation error: {e}")
        return jsonify({"error": str(e)}), 400

    except ConfigurationError as e:
        logger.error(f"Configuration error: {e}")
        return jsonify({"error": "Configuration error"}), 500

    except AssignmentError as e:
        logger.error(f"Assignment error: {e}")
        return jsonify({"error": str(e)}), 500

    except TaskCreationError as e:
        logger.error(f"Task creation error (lead {lead_id}): {e}")
        return jsonify({"error": str(e), "lead_id": lead_id}), 500

    except ERPNextError as e:
        logger.error(f"ERPNext error: {e}")
        return jsonify({"error": str(e)}), 500

    except Exception as e:
        logger.error(f"Unexpected error in process_lead: {e}")
        return jsonify({"error": "Internal server error"}), 500
