"""Unit tests for app/assignment_engine.py"""

import pytest
from app.assignment_engine import assign_to_salesperson, _round_robin, _by_capacity, _by_product_expertise
import app.assignment_engine as engine

RULES = {
    "strategy": "round_robin",
    "salespersons": [
        {"name": "sales1@example.com", "product_expertise": ["ERP", "CRM"], "capacity": 10},
        {"name": "sales2@example.com", "product_expertise": ["Manufacturing"], "capacity": 5},
        {"name": "sales3@example.com", "product_expertise": ["Accounting"], "capacity": 8},
    ]
}

LEAD = {
    "name": "Jane Doe",
    "email": "jane@example.com",
    "phone": "+1-800-555-0199",
    "company": "Acme",
    "product_interest": "ERP Solutions",
}


def test_round_robin_cycles_through_all():
    engine._rr_index = 0
    results = [assign_to_salesperson(LEAD, {**RULES, "strategy": "round_robin"}) for _ in range(3)]
    assert results == ["sales1@example.com", "sales2@example.com", "sales3@example.com"]


def test_round_robin_wraps_around():
    engine._rr_index = 0
    results = [assign_to_salesperson(LEAD, {**RULES, "strategy": "round_robin"}) for _ in range(4)]
    assert results[3] == "sales1@example.com"


def test_by_capacity_picks_highest():
    assigned = assign_to_salesperson(LEAD, {**RULES, "strategy": "by_capacity"})
    assert assigned == "sales1@example.com"


def test_by_product_expertise_matches():
    assigned = assign_to_salesperson(LEAD, {**RULES, "strategy": "by_product_expertise"})
    assert assigned == "sales1@example.com"


def test_by_product_expertise_fallback_to_round_robin():
    engine._rr_index = 0
    lead = {**LEAD, "product_interest": "Unknown Product"}
    assigned = assign_to_salesperson(lead, {**RULES, "strategy": "by_product_expertise"})
    assert assigned == "sales1@example.com"


def test_by_product_expertise_no_interest_field():
    engine._rr_index = 0
    lead = {k: v for k, v in LEAD.items() if k != "product_interest"}
    assigned = assign_to_salesperson(lead, {**RULES, "strategy": "by_product_expertise"})
    assert assigned in [s["name"] for s in RULES["salespersons"]]


def test_unknown_strategy_defaults_to_round_robin():
    engine._rr_index = 0
    assigned = assign_to_salesperson(LEAD, {**RULES, "strategy": "unknown_strategy"})
    assert assigned == "sales1@example.com"


def test_no_salespersons_raises_error():
    with pytest.raises(ValueError, match="No salespersons configured"):
        assign_to_salesperson(LEAD, {"strategy": "round_robin", "salespersons": []})


def test_returns_string():
    assigned = assign_to_salesperson(LEAD, RULES)
    assert isinstance(assigned, str)
