"""Unit tests for app/source_adapters.py."""

from app.source_adapters import normalize_incoming_lead


def test_normalize_legacy_payload():
    payload = {
        "name": "John Doe",
        "email": "john@example.com",
        "phone": "+1-800-555-1111",
        "company": "Acme",
        "source": "webform",
    }
    normalized = normalize_incoming_lead(payload)
    assert normalized["first_name"] == "John"
    assert normalized["last_name"] == "Doe"
    assert normalized["company"] == "Acme"


def test_normalize_whatsapp_payload():
    payload = {
        "source_type": "whatsapp",
        "full_name": "Asha Rao",
        "phone_number": "+91-90000-12345",
        "email": "asha@example.com",
        "business_name": "Asha Industries",
        "message_text": "Need demo",
    }
    normalized = normalize_incoming_lead(payload)
    assert normalized["first_name"] == "Asha"
    assert normalized["last_name"] == "Rao"
    assert normalized["lead_source"] == "whatsapp"


def test_normalize_email_payload():
    payload = {
        "source_type": "email",
        "sender_name": "Mila Khan",
        "sender_email": "mila@example.com",
        "company": "Mila Labs",
        "body": "Share pricing",
    }
    normalized = normalize_incoming_lead(payload)
    assert normalized["first_name"] == "Mila"
    assert normalized["email"] == "mila@example.com"
    assert normalized["lead_source"] == "email"


def test_normalize_webform_payload():
    payload = {
        "source_type": "webform",
        "first_name": "Dev",
        "last_name": "Patel",
        "email": "dev@example.com",
        "phone": "+1-800-555-2222",
        "company_name": "Dev Systems",
    }
    normalized = normalize_incoming_lead(payload)
    assert normalized["company"] == "Dev Systems"
    assert normalized["first_name"] == "Dev"
    assert normalized["last_name"] == "Patel"


def test_passthrough_optional_fields():
    payload = {
        "source_type": "webform",
        "first_name": "Ria",
        "last_name": "Sen",
        "email": "ria@example.com",
        "phone": "+1-800-555-3333",
        "company": "Ria Corp",
        "task_priority": "High",
        "attachments": "file.pdf",
    }
    normalized = normalize_incoming_lead(payload)
    assert normalized["task_priority"] == "High"
    assert normalized["attachments"] == "file.pdf"
