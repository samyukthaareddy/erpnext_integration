"""Adapters that normalize upstream lead payloads into one canonical schema."""

from copy import deepcopy


def _split_name(name: str) -> tuple[str, str]:
    parts = (name or "").strip().split()
    if not parts:
        return "", ""
    if len(parts) == 1:
        return parts[0], "Lead"
    return parts[0], " ".join(parts[1:])


def _legacy_adapter(payload: dict) -> dict:
    first_name, last_name = _split_name(payload.get("name", ""))
    return {
        "company": payload.get("company", ""),
        "first_name": first_name,
        "last_name": last_name,
        "email": payload.get("email", ""),
        "phone": payload.get("phone", ""),
        "mobile": payload.get("mobile", ""),
        "lead_source": payload.get("source", ""),
        "description": (
            f"Product Interest: {payload.get('product_interest', 'N/A')}\n"
            f"Message: {payload.get('message', 'N/A')}\n"
            f"Source: {payload.get('source', 'N/A')}"
        ),
        "product_interest": payload.get("product_interest", ""),
        "message": payload.get("message", ""),
    }


def _whatsapp_adapter(payload: dict) -> dict:
    full_name = payload.get("full_name") or payload.get("name") or ""
    first_name, last_name = _split_name(full_name)
    return {
        "company": payload.get("business_name") or payload.get("company") or "",
        "first_name": first_name,
        "last_name": last_name,
        "email": payload.get("email", ""),
        "phone": payload.get("phone_number") or payload.get("phone") or "",
        "lead_source": "whatsapp",
        "description": payload.get("message_text") or payload.get("message") or "",
        "message": payload.get("message_text") or payload.get("message") or "",
    }


def _email_adapter(payload: dict) -> dict:
    sender = payload.get("sender_name") or payload.get("name") or ""
    first_name, last_name = _split_name(sender)
    return {
        "company": payload.get("company", ""),
        "first_name": first_name,
        "last_name": last_name,
        "email": payload.get("sender_email") or payload.get("email") or "",
        "phone": payload.get("phone", ""),
        "lead_source": "email",
        "description": payload.get("body") or payload.get("message") or "",
        "message": payload.get("body") or payload.get("message") or "",
    }


def _webform_adapter(payload: dict) -> dict:
    first_name = payload.get("first_name") or ""
    last_name = payload.get("last_name") or ""
    if not first_name and not last_name:
        first_name, last_name = _split_name(payload.get("name", ""))
    return {
        "company": payload.get("company") or payload.get("company_name") or "",
        "first_name": first_name,
        "last_name": last_name or "Lead",
        "email": payload.get("email", ""),
        "phone": payload.get("phone", ""),
        "mobile": payload.get("mobile", ""),
        "website": payload.get("website", ""),
        "lead_source": payload.get("lead_source") or "webform",
        "description": payload.get("message", ""),
        "message": payload.get("message", ""),
    }


_SOURCE_ADAPTERS = {
    "legacy": _legacy_adapter,
    "whatsapp": _whatsapp_adapter,
    "email": _email_adapter,
    "webform": _webform_adapter,
}


def normalize_incoming_lead(payload: dict) -> dict:
    """Normalize upstream payload into canonical lead schema used by validators."""
    if not isinstance(payload, dict):
        return {}

    source_type = (payload.get("source_type") or "").strip().lower()

    # Already canonical.
    if all(k in payload for k in ("company", "first_name", "last_name", "email", "phone")):
        normalized = deepcopy(payload)
    else:
        adapter = _SOURCE_ADAPTERS.get(source_type)
        if adapter is None:
            # Keep backward compatibility for existing endpoint callers.
            normalized = _legacy_adapter(payload)
        else:
            normalized = adapter(payload)

    # Carry optional canonical fields through when present.
    passthrough_fields = [
        "job_title",
        "fax",
        "website",
        "industry",
        "lead_status",
        "no_of_employees",
        "annual_revenue",
        "street",
        "city",
        "state",
        "zip_code",
        "country",
        "email_opt_out",
        "created_by",
        "modified_by",
        "last_activity_time",
        "sales_person",
        "created_time",
        "lead_owner",
        "task_owner",
        "task_status",
        "task_priority",
        "task_tag",
        "related_to",
        "notes",
        "attachments",
        "reminder",
        "repeat",
        "closed_time",
        "contact_name",
    ]
    for field in passthrough_fields:
        if field in payload and field not in normalized:
            normalized[field] = payload[field]

    return normalized
