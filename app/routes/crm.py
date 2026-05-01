"""CRM routes for lead processing."""

from flask import Blueprint, request, jsonify
from utils.validators import validate_lead_payload
from app.erpnext_client import ERPNextClient, ERPNextException
from app.assignment_engine import assign_to_salesperson
from app.task_service import create_followup_task
from app.source_adapters import normalize_incoming_lead
from config.logging import get_logger

logger = get_logger(__name__)
bp = Blueprint("crm", __name__, url_prefix="/api/crm")


@bp.route("/process-lead", methods=["POST"])
def process_lead():
    """
    Process incoming lead and create in ERPNext.

    Expected JSON payload:
    {
        "company": "ACME Corp",
        "first_name": "John",
        "last_name": "Doe",
        "email": "john@example.com",
        "phone": "+1-800-555-0199",
        "lead_source": "whatsapp",
        "product_interest": "Industrial sensors",
        "message": "Need pricing"
    }

    Returns:
    {
        "lead_id": "LEAD-0001",
        "task_id": "TDO-000001",
        "assigned_to": "sales1@example.com",
        "status": "success"
    }
    """
    try:
        # Parse JSON payload
        payload = request.get_json(silent=True)

        if not payload:
            logger.warning("Empty payload received")
            return jsonify({"error": "No payload provided"}), 400

        canonical_payload = normalize_incoming_lead(payload)

        # Validate payload
        validation_errors = validate_lead_payload(canonical_payload)

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
                "company_name": canonical_payload.get("company"),
                "first_name": canonical_payload.get("first_name"),
                "last_name": canonical_payload.get("last_name"),
                "job_title": canonical_payload.get("job_title"),
                "email_id": canonical_payload.get("email"),
                "phone": canonical_payload.get("phone"),
                "fax": canonical_payload.get("fax"),
                "mobile_no": canonical_payload.get("mobile"),
                "website": canonical_payload.get("website"),
                "industry": canonical_payload.get("industry"),
                "source": canonical_payload.get("lead_source"),
                "status": canonical_payload.get("lead_status"),
                "no_of_employees": canonical_payload.get("no_of_employees"),
                "annual_revenue": canonical_payload.get("annual_revenue"),
                "address_line1": canonical_payload.get("street"),
                "city": canonical_payload.get("city"),
                "state": canonical_payload.get("state"),
                "pincode": canonical_payload.get("zip_code"),
                "country": canonical_payload.get("country"),
                "unsubscribed": canonical_payload.get("email_opt_out"),
                "owner": canonical_payload.get("lead_owner") or canonical_payload.get("sales_person"),
                "remarks": canonical_payload.get("description")
                or (
                    f"Product Interest: {canonical_payload.get('product_interest', 'N/A')}\n"
                    f"Message: {canonical_payload.get('message', 'N/A')}\n"
                    f"Source: {canonical_payload.get('lead_source', 'N/A')}"
                ),
            }
            lead_data = {k: v for k, v in lead_data.items() if v not in (None, "")}

            lead = client.create_lead(lead_data)
            lead_id = lead.get("name")
            logger.info(f"Lead created successfully: {lead_id}")

            # Assign lead to salesperson
            assigned_to = assign_to_salesperson(canonical_payload)
            client.update_lead(lead_id, {"_assign": assigned_to})
            logger.info(f"Lead {lead_id} assigned to {assigned_to}")

            # Create follow-up task
            task = create_followup_task(
                lead_id=lead_id,
                assigned_to=assigned_to,
                lead_data=canonical_payload,
                client=client
            )
            task_id = task.get("name")
            logger.info(f"Follow-up task created: {task_id}")

            return jsonify({
                "lead_id": lead_id,
                "task_id": task_id,
                "assigned_to": assigned_to,
                "status": "success"
            }), 201

        except ERPNextException as e:
            logger.error(f"ERPNext error during lead creation: {e}")
            return jsonify({"error": f"Lead creation failed: {str(e)}"}), 500

    except Exception as e:
        logger.error(f"Unexpected error in process_lead: {e}")
        return jsonify({"error": "Internal server error"}), 500
