"""CRM routes for lead processing."""

from datetime import datetime, timezone
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

            # Enhancement 3: Build enhanced response with URLs and metadata
            erpnext_base = client.base_url
            lead_url = f"{erpnext_base}/app/lead/{lead_id}"
            task_url = f"{erpnext_base}/app/todo/{task_id}"

            response = {
                # Original fields (backward compatible)
                "lead_id": lead_id,
                "task_id": task_id,
                "assigned_to": assigned_to,
                "status": "success",
                # New fields for Spring Boot
                "lead_url": lead_url,
                "task_url": task_url,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "erpnext_name": lead_id,
                "assignment_strategy": "round_robin",
            }

            logger.info(f"Lead process success: {lead_id} → {assigned_to}")
            return jsonify(response), 201

        except ERPNextException as e:
            logger.error(f"ERPNext error: {e}")
            
            # Enhancement 4: Better error responses with retryable flag
            error_msg = str(e).lower()
            retryable = any(keyword in error_msg for keyword in [
                "timeout", "connection", "temporarily", "unavailable", "refused"
            ])
            
            return jsonify({
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__,
                "retryable": retryable,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }), 503 if retryable else 400

    except Exception as e:
        logger.error(f"Unexpected error in process_lead: {e}")
        return jsonify({"error": "Internal server error"}), 500


@bp.route("/health", methods=["GET"])
def health_check():
    """
    Health check endpoint for monitoring and Spring Boot liveness probe.
    
    Returns: {status, erpnext_connected, timestamp, api_version}
    HTTP 200: Healthy
    HTTP 503: Unhealthy (ERPNext down)
    """
    try:
        client = ERPNextClient()
        # Verify ERPNext connectivity by attempting a simple API call
        response = client.session.get(
            client._build_url("Lead?fields=[\"name\"]&limit_page_length=1"),
            timeout=5
        )
        erpnext_connected = response.status_code == 200
    except Exception as e:
        logger.warning(f"Health check: ERPNext unreachable - {e}")
        erpnext_connected = False
    
    status = "healthy" if erpnext_connected else "degraded"
    http_code = 200 if erpnext_connected else 503
    
    return jsonify({
        "status": status,
        "erpnext_connected": erpnext_connected,
        "api_version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }), http_code


@bp.route("/process-leads", methods=["POST"])
def process_leads_batch():
    """
    Process multiple leads in batch.
    
    Input: {leads: [{...lead1}, {...lead2}, {...lead3}]}
    Output: {
        success_count: 2,
        failed_count: 1,
        results: [
            {lead_id: "LEAD-0001", status: "success", ...},
            {lead_id: "LEAD-0002", status: "success", ...},
            {error: "Invalid email", status: "failed", index: 2}
        ]
    }
    
    Notes:
    - Each lead processed independently
    - Failures don't stop other leads
    - Return 207 Multi-Status (some success, some failure)
    """
    try:
        payload = request.get_json(silent=True)
        if not payload or not isinstance(payload.get("leads"), list):
            return jsonify({"error": "Expected {leads: [...]}"}), 400
        
        leads = payload.get("leads", [])
        if not leads:
            return jsonify({"error": "leads array cannot be empty"}), 400
        
        results = []
        success_count = 0
        failed_count = 0
        
        for index, lead_payload in enumerate(leads):
            try:
                # Normalize
                canonical = normalize_incoming_lead(lead_payload)
                
                # Validate
                errors = validate_lead_payload(canonical)
                if errors:
                    results.append({
                        "index": index,
                        "status": "failed",
                        "error": "Validation failed",
                        "details": errors
                    })
                    failed_count += 1
                    continue
                
                # Process (same as /process-lead)
                client = ERPNextClient()
                lead_data = {
                    "company_name": canonical.get("company"),
                    "first_name": canonical.get("first_name"),
                    "last_name": canonical.get("last_name"),
                    "job_title": canonical.get("job_title"),
                    "email_id": canonical.get("email"),
                    "phone": canonical.get("phone"),
                    "fax": canonical.get("fax"),
                    "mobile_no": canonical.get("mobile"),
                    "website": canonical.get("website"),
                    "industry": canonical.get("industry"),
                    "source": canonical.get("lead_source"),
                    "status": canonical.get("lead_status"),
                    "no_of_employees": canonical.get("no_of_employees"),
                    "annual_revenue": canonical.get("annual_revenue"),
                    "address_line1": canonical.get("street"),
                    "city": canonical.get("city"),
                    "state": canonical.get("state"),
                    "pincode": canonical.get("zip_code"),
                    "country": canonical.get("country"),
                    "unsubscribed": canonical.get("email_opt_out"),
                    "owner": canonical.get("lead_owner") or canonical.get("sales_person"),
                    "remarks": canonical.get("description")
                    or (
                        f"Product Interest: {canonical.get('product_interest', 'N/A')}\n"
                        f"Message: {canonical.get('message', 'N/A')}\n"
                        f"Source: {canonical.get('lead_source', 'N/A')}"
                    ),
                }
                lead_data = {k: v for k, v in lead_data.items() if v not in (None, "")}
                
                lead = client.create_lead(lead_data)
                lead_id = lead.get("name")
                
                assigned_to = assign_to_salesperson(canonical)
                client.update_lead(lead_id, {"_assign": assigned_to})
                
                task = create_followup_task(lead_id, assigned_to, canonical, client)
                task_id = task.get("name")
                
                erpnext_base = client.base_url
                lead_url = f"{erpnext_base}/app/lead/{lead_id}"
                task_url = f"{erpnext_base}/app/todo/{task_id}"
                
                results.append({
                    "index": index,
                    "lead_id": lead_id,
                    "task_id": task_id,
                    "assigned_to": assigned_to,
                    "lead_url": lead_url,
                    "task_url": task_url,
                    "status": "success"
                })
                success_count += 1
                
            except Exception as e:
                logger.error(f"Batch processing failed at index {index}: {e}")
                results.append({
                    "index": index,
                    "status": "failed",
                    "error": str(e)
                })
                failed_count += 1
        
        http_code = 200 if failed_count == 0 else 207  # 207 = Multi-Status
        
        return jsonify({
            "success_count": success_count,
            "failed_count": failed_count,
            "results": results
        }), http_code
        
    except Exception as e:
        logger.error(f"Batch processing error: {e}")
        return jsonify({"error": "Batch processing failed", "message": str(e)}), 500
