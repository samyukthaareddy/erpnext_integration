"""Payload validation utilities."""

import jsonschema
from utils.schemas import LEAD_SCHEMA


def validate_lead_payload(payload: dict) -> list[str]:
    """
    Validate a lead payload against LEAD_SCHEMA.

    Returns a list of error messages; empty list means valid.
    """
    validator = jsonschema.Draft7Validator(LEAD_SCHEMA)
    return [e.message for e in sorted(validator.iter_errors(payload), key=str)]
