"""
core/policy_checker.py — Expense policy validation engine for TravelPro.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import List
from core.models import Expense


# ─────────────────────────────────────────────────────────────────────────────
#  Policy limits (can be overridden by uploaded company policy)
# ─────────────────────────────────────────────────────────────────────────────
POLICY = {
    "hotel_nightly_limit":   350.0,   # USD per night
    "meal_per_person_limit": 150.0,   # USD per meal
    "meal_daily_limit":      75.0,    # USD per person per day (for non-client meals)
    "ground_transport_limit": 100.0,  # USD per trip
    "airfare_requires_coach": True,
    "preferred_hotel_chains": ["Marriott", "Westin", "Sheraton", "W Hotels",
                               "Courtyard", "Residence Inn", "Fairfield"],
    "preferred_airlines":     ["Southwest", "Delta", "United"],
    "tier1_airlines":         ["Southwest", "Delta"],
    "preferred_rental":       ["Enterprise", "National", "Alamo"],
    "max_advance_booking_days": 21,   # book at least 21 days out for best rates
    "require_receipts_above": 25.0,   # USD — receipts required above this amount
}


@dataclass
class PolicyResult:
    compliant: bool
    violations: List[str]
    suggestions: List[str]
    requires_approval: bool


def check_expense(expense: Expense) -> PolicyResult:
    """Run all policy checks for a given expense. Returns a PolicyResult."""
    violations: List[str] = []
    suggestions: List[str] = []

    cat = expense.category
    amt = expense.amount

    if cat == "Accommodation":
        # Approximate nightly rate from total (assume description has nights)
        nights = max(1, int(expense.description.lower().split("night")[0].strip().split()[-1])
                     if "night" in expense.description.lower() else 1)
        nightly = amt / nights
        if nightly > POLICY["hotel_nightly_limit"]:
            violations.append(
                f"Nightly rate ~${nightly:.0f} exceeds policy limit of ${POLICY['hotel_nightly_limit']:.0f}/night."
            )
            suggestions.append("Book a Marriott-family property within the rate cap or request a rate exception.")

    elif cat == "Airfare":
        if amt > 600:
            suggestions.append("Flights over $600 — confirm you booked the lowest logical fare class.")
        if not any(airline.lower() in expense.merchant.lower()
                   for airline in POLICY["preferred_airlines"]):
            violations.append(
                f"{expense.merchant} is not a Tier 1/2 preferred airline. Justification required."
            )
            suggestions.append("Preferred airlines: Southwest (Tier 1), Delta (Tier 1), United (Tier 2).")

    elif cat == "Meals":
        if amt > POLICY["meal_per_person_limit"]:
            violations.append(
                f"Meal expense ${amt:.2f} exceeds per-meal policy limit of ${POLICY['meal_per_person_limit']:.2f}."
            )
            suggestions.append(
                "For client dinners above the limit, include attendee count and submit exception request."
            )

    elif cat == "Ground Transport":
        if amt > POLICY["ground_transport_limit"]:
            violations.append(
                f"Ground transport ${amt:.2f} exceeds single-trip limit of ${POLICY['ground_transport_limit']:.2f}."
            )
            suggestions.append("Use hotel shuttle or book shared rides to reduce cost.")

    elif cat == "Other":
        if amt > 500:
            violations.append(f"'Other' category expense of ${amt:.2f} requires detailed description and approval.")
            suggestions.append("Break down into specific sub-categories where possible.")

    # Receipt requirement
    if amt > POLICY["require_receipts_above"] and not expense.receipt_extracted:
        suggestions.append(f"Receipt required for expenses above ${POLICY['require_receipts_above']:.0f}.")

    return PolicyResult(
        compliant=len(violations) == 0,
        violations=violations,
        suggestions=suggestions,
        requires_approval=len(violations) > 0 or amt > 500,
    )


def check_hotel_rate(nightly_rate: float, hotel_name: str) -> PolicyResult:
    violations, suggestions = [], []
    if nightly_rate > POLICY["hotel_nightly_limit"]:
        violations.append(f"Rate ${nightly_rate:.0f}/night exceeds cap of ${POLICY['hotel_nightly_limit']:.0f}.")
        suggestions.append("Search for Marriott-family properties within the rate limit.")
    preferred = any(chain.lower() in hotel_name.lower() for chain in POLICY["preferred_hotel_chains"])
    if not preferred:
        violations.append(f"{hotel_name} is not a Marriott-preferred property.")
        suggestions.append("Marriott-family brands are preferred. Use non-preferred only when Marriott is unavailable.")
    return PolicyResult(not violations, violations, suggestions, bool(violations))


def check_airline(airline_name: str) -> dict:
    """Return tier info for a given airline."""
    name = airline_name.lower()
    if any(a.lower() in name for a in POLICY["tier1_airlines"]):
        return {"tier": 1, "label": "Tier 1 — Most Preferred", "requires_justification": False}
    if "united" in name:
        return {"tier": 2, "label": "Tier 2 — Preferred", "requires_justification": False}
    return {"tier": 3, "label": "Tier 3 — Permitted with Justification", "requires_justification": True}
