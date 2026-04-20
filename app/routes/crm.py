"""CRM routes for lead processing."""

from flask import Blueprint, request, jsonify
from utils.validators import validate_lead_payload
from app.erpnext_client import ERPNextClient, ERPNextException
from app.assignment_engine import assign_to_salesperson
from config.logging import get_logger

logger = get_logger(__name__)
bp = Blueprint("crm", __name__, url_prefix="/api/crm")


@bp.route("/process-lead", methods=["POST"])
def process_lead():
    """
    Process incoming lead and create in ERPNext.

    Expected JSON payload:
    {
        "name": "John Doe",
        "email": "john@example.com",
        "phone": "+1-800-555-0199",
        "company": "ACME Corp",
        "product_interest": "Industrial sensors",
        "message": "Need pricing",
        "source": "whatsapp"
    }

    Returns:
    {
        "lead_id": "LEAD-0001",
        "status": "success"
    }
    """
    try:
        # Parse JSON payload
        payload = request.get_json(silent=True)

        if not payload:
            logger.warning("Empty payload received")
            return jsonify({"error": "No payload provided"}), 400

        # Validate payload
        validation_errors = validate_lead_payload(payload)

        if validation_errors:
            logger.warning(f"Validation errors: {validation_errors}")
            return jsonify({"error": "Validation failed", "details": validation_errors}), 400

        # Create ERPNext client
        try:
            client = ERPNextClient()
        except Exception as e:
            logger.error(f"Failed to initialize ERPNext client: {e}")
            return jsonify({"error": "Configuration error"}), 500

        # Create lead in ERPNext
        try:
            lead_data = {
                "first_name": payload.get("name", "").split()[0],
                "last_name": " ".join(payload.get("name", "").split()[1:]) or "Lead",
                "email_id": payload.get("email"),
                "phone": payload.get("phone"),
                "company_name": payload.get("company"),
                "notes": f"Product Interest: {payload.get('product_interest', 'N/A')}\n"
                        f"Message: {payload.get('message', 'N/A')}\n"
                        f"Source: {payload.get('source', 'N/A')}",
            }

            lead = client.create_lead(lead_data)
            lead_id = lead.get("name")
            logger.info(f"Lead created successfully: {lead_id}")

            # Assign lead to salesperson
            assigned_to = assign_to_salesperson(payload)
            client.update_lead(lead_id, {"_assign": assigned_to})
            logger.info(f"Lead {lead_id} assigned to {assigned_to}")

            return jsonify({
                "lead_id": lead_id,
                "assigned_to": assigned_to,
                "status": "success"
            }), 201

        except ERPNextException as e:
            logger.error(f"ERPNext error during lead creation: {e}")
            return jsonify({"error": f"Lead creation failed: {str(e)}"}), 500

    except Exception as e:
        logger.error(f"Unexpected error in process_lead: {e}")
        return jsonify({"error": "Internal server error"}), 500
