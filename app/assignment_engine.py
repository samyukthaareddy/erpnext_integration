"""
Salesperson assignment engine.

Supports round-robin, by-capacity, and by-product-expertise strategies.
Assignment rules are loaded from config/assignment_rules.json.
"""

import json
import os
from config.logging import get_logger

logger = get_logger(__name__)

_RULES_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "assignment_rules.json")

# Round-robin state (in-memory; resets on restart)
_rr_index = 0


def _load_rules() -> dict:
    with open(_RULES_PATH, "r") as f:
        return json.load(f)


def _round_robin(salespersons: list) -> str:
    global _rr_index
    person = salespersons[_rr_index % len(salespersons)]
    _rr_index += 1
    return person["name"]


def _by_capacity(salespersons: list) -> str:
    return max(salespersons, key=lambda s: s.get("capacity", 0))["name"]


def _by_product_expertise(salespersons: list, lead_data: dict) -> str:
    interest = lead_data.get("product_interest", "").lower()
    for person in salespersons:
        expertise = [e.lower() for e in person.get("product_expertise", [])]
        if any(e in interest for e in expertise):
            logger.info(f"Matched {person['name']} by product expertise for '{interest}'")
            return person["name"]
    # Fallback to round-robin if no match
    logger.info("No expertise match found, falling back to round-robin")
    return _round_robin(salespersons)


def assign_to_salesperson(lead_data: dict, rules: dict = None) -> str:
    """
    Assign a salesperson to a lead based on configured strategy.

    Args:
        lead_data (dict): The incoming lead payload
        rules (dict): Optional rules override (used in tests)

    Returns:
        str: Assigned salesperson name/email

    Raises:
        ValueError: If no salespersons are configured
    """
    if rules is None:
        rules = _load_rules()

    salespersons = rules.get("salespersons", [])
    if not salespersons:
        raise ValueError("No salespersons configured in assignment rules")

    strategy = rules.get("strategy", "round_robin")
    logger.info(f"Assigning lead using strategy: {strategy}")

    if strategy == "by_capacity":
        assigned = _by_capacity(salespersons)
    elif strategy == "by_product_expertise":
        assigned = _by_product_expertise(salespersons, lead_data)
    else:
        assigned = _round_robin(salespersons)

    logger.info(f"Lead assigned to: {assigned}")
    return assigned
