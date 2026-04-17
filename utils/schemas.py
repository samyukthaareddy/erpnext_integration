"""JSON schema definitions for payload validation."""

LEAD_SCHEMA = {
    "type": "object",
    "required": ["name", "email", "phone", "company"],
    "additionalProperties": False,
    "properties": {
        "name": {"type": "string", "minLength": 1},
        "email": {
            "type": "string",
            "format": "email",
            "pattern": r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
        },
        "phone": {
            "type": "string",
            "pattern": r"^\+?[\d\s\-().]{7,20}$",
        },
        "company": {"type": "string", "minLength": 1},
        "product_interest": {"type": "string"},
        "message": {"type": "string"},
        "source": {"type": "string"},
    },
}
