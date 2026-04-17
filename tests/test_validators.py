"""Unit tests for utils/validators.py"""

import pytest
from utils.validators import validate_lead_payload

VALID_PAYLOAD = {
    "name": "Jane Doe",
    "email": "jane@example.com",
    "phone": "+1-800-555-0199",
    "company": "Acme Corp",
}


def test_valid_payload():
    assert validate_lead_payload(VALID_PAYLOAD) == []


def test_valid_payload_with_optional_fields():
    payload = {**VALID_PAYLOAD, "product_interest": "ERP", "message": "Hello", "source": "Web"}
    assert validate_lead_payload(payload) == []


def test_missing_required_field_email():
    payload = {k: v for k, v in VALID_PAYLOAD.items() if k != "email"}
    errors = validate_lead_payload(payload)
    assert any("email" in e for e in errors)


def test_missing_required_field_name():
    payload = {k: v for k, v in VALID_PAYLOAD.items() if k != "name"}
    errors = validate_lead_payload(payload)
    assert any("name" in e for e in errors)


def test_missing_required_field_phone():
    payload = {k: v for k, v in VALID_PAYLOAD.items() if k != "phone"}
    errors = validate_lead_payload(payload)
    assert any("phone" in e for e in errors)


def test_missing_required_field_company():
    payload = {k: v for k, v in VALID_PAYLOAD.items() if k != "company"}
    errors = validate_lead_payload(payload)
    assert any("company" in e for e in errors)


def test_invalid_email_format():
    payload = {**VALID_PAYLOAD, "email": "not-an-email"}
    errors = validate_lead_payload(payload)
    assert errors


def test_invalid_phone_format():
    payload = {**VALID_PAYLOAD, "phone": "abc"}
    errors = validate_lead_payload(payload)
    assert errors


def test_additional_properties_rejected():
    payload = {**VALID_PAYLOAD, "unknown_field": "value"}
    errors = validate_lead_payload(payload)
    assert errors


def test_empty_name_rejected():
    payload = {**VALID_PAYLOAD, "name": ""}
    errors = validate_lead_payload(payload)
    assert errors


def test_empty_payload():
    errors = validate_lead_payload({})
    assert errors
