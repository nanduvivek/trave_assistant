"""
core/notifications.py — Event bus for TravelPro proactive notifications.

Usage:
    from core.notifications import fire_event
    fire_event("FLIGHT_CANCELLED", {"flight": "WN 412", "route": "SEA→LAS", "trip_id": "t1"})
"""
from __future__ import annotations
from datetime import datetime
import streamlit as st
from core.models import Notification
from core.data_store import add_notification

# ─── event → (title, severity, ai_query_template) ────────────────────────────
_EVENT_CONFIG: dict[str, dict] = {
    "FLIGHT_CANCELLED": {
        "severity": "critical",
        "title_tpl": "🔴 Flight {flight_number} ({route}) Cancelled",
        "body_tpl":  "Your {airline} flight {flight_number} from {route} has been cancelled. Immediate rebooking required.",
        "query_tpl": "My {airline} flight {flight_number} from {route} was just cancelled and I need to rebook immediately. "
                     "Please search for the next available flights and give me policy-compliant alternatives.",
    },
    "HOTEL_CANCELLED": {
        "severity": "critical",
        "title_tpl": "🔴 Hotel Reservation Cancelled — {hotel}",
        "body_tpl":  "Your reservation at {hotel} in {city} ({check_in} – {check_out}) was cancelled. Find alternatives now.",
        "query_tpl": "My hotel reservation at {hotel} in {city} was just cancelled. "
                     "I arrive on {check_in} and need to check out on {check_out}. "
                     "Please find me policy-compliant hotel alternatives immediately.",
    },
    "RENTAL_CAR_DELAY": {
        "severity": "warning",
        "title_tpl": "⚠️ Rental Car Long Queue at {location}",
        "body_tpl":  "Enterprise at {location} is reporting estimated wait times of {wait_time}. Partner counters may be faster.",
        "query_tpl": "I'm at {location} and the Enterprise rental car counter has a long queue ({wait_time} wait). "
                     "What are my policy-approved alternatives I can use without pre-approval?",
    },
    "EXPENSE_OVER_LIMIT": {
        "severity": "warning",
        "title_tpl": "⚠️ Expense Exceeds Policy Limit",
        "body_tpl":  "Your {category} expense of {amount} at {merchant} exceeds the policy limit. Exception approval required.",
        "query_tpl": "My {category} expense of {amount} at {merchant} exceeds the company policy limit. "
                     "How do I get an exception approved and what justification should I provide?",
    },
    "BUDGET_EXPIRING": {
        "severity": "warning",
        "title_tpl": "⚠️ Budget Expiring Soon — {budget_name}",
        "body_tpl":  "{amount_remaining} in {budget_code} expires in {days} days. Use it before it's forfeited.",
        "query_tpl": "I have {amount_remaining} remaining in my {budget_name} budget ({budget_code}) expiring in {days} days. "
                     "Help me figure out the best way to use this budget before it expires for my upcoming travel.",
    },
    "APPROVAL_NEEDED": {
        "severity": "info",
        "title_tpl": "📋 Expense Submitted for Approval",
        "body_tpl":  "{amount} expense for {description} sent to {approver} for review.",
        "query_tpl": "I submitted an expense of {amount} for {description} that needs manager approval. "
                     "What's the typical approval timeline and what information should I provide?",
    },
    "APPROVAL_GRANTED": {
        "severity": "success",
        "title_tpl": "✅ Expense Approved",
        "body_tpl":  "Your {amount} expense for {description} has been approved by {approver}.",
        "query_tpl": "",  # no AI action needed
    },
    "FLIGHT_DELAYED": {
        "severity": "warning",
        "title_tpl": "⚠️ Flight {flight_number} Delayed {delay}",
        "body_tpl":  "Your {airline} flight {flight_number} is delayed by {delay}. New departure: {new_time}.",
        "query_tpl": "My {airline} flight {flight_number} is delayed by {delay}. "
                     "Will I miss my connection? What are my options for rebooking or compensation?",
    },
}


def fire_event(event_type: str, context: dict) -> Notification | None:
    """
    Fire a travel event, create a notification, and store it in session state.

    Args:
        event_type: One of the keys in _EVENT_CONFIG.
        context: Template variables for title, body, and AI query strings.

    Returns:
        The created Notification, or None if event_type unknown.
    """
    cfg = _EVENT_CONFIG.get(event_type)
    if not cfg:
        return None

    def _fmt(tpl: str) -> str:
        try:
            return tpl.format(**context)
        except KeyError:
            return tpl

    notif = Notification(
        id=f"n{len(st.session_state.get('notifications', [])) + 1}",
        type=event_type,
        title=_fmt(cfg["title_tpl"]),
        body=_fmt(cfg["body_tpl"]),
        severity=cfg["severity"],
        ai_query=_fmt(cfg["query_tpl"]),
        created_at=datetime.now(),
        trip_id=context.get("trip_id", ""),
    )

    add_notification(notif)
    return notif


def get_severity_color(severity: str) -> str:
    return {
        "critical": "#EF4444",
        "warning":  "#F59E0B",
        "info":     "#3B82F6",
        "success":  "#10B981",
    }.get(severity, "#64748B")


def get_severity_bg(severity: str) -> str:
    return {
        "critical": "rgba(239,68,68,0.08)",
        "warning":  "rgba(245,158,11,0.08)",
        "info":     "rgba(59,130,246,0.08)",
        "success":  "rgba(16,185,129,0.08)",
    }.get(severity, "rgba(100,116,139,0.08)")
