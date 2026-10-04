"""
core/data_store.py — In-memory demo data and session-state helpers for TravelPro.

Call `init_data_store()` at the top of every page to ensure data is seeded.
"""
from __future__ import annotations
import uuid
from datetime import date, datetime, timedelta
import streamlit as st
from core.models import (
    User, Budget, Trip, Flight, Hotel, RentalCar,
    Expense, Approval, Notification
)


# ─────────────────────────────────────────────────────────────────────────────
#  Seed helpers
# ─────────────────────────────────────────────────────────────────────────────
def _uid() -> str:
    return str(uuid.uuid4())[:8]


def _seed_users() -> dict[str, User]:
    return {
        "u1": User("u1", "Sarah Chen",      "sarah@acme.com",   "R&D",       "employee", "u2", "👩‍💻"),
        "u2": User("u2", "James Liu",       "james@acme.com",   "R&D",       "manager",  "u3", "👨‍💼"),
        "u3": User("u3", "Priya Sharma",    "priya@acme.com",   "Finance",   "admin",    "u3", "👩‍💼"),
        "u4": User("u4", "Marcus Webb",     "marcus@acme.com",  "Sales",     "employee", "u2", "👨‍💻"),
    }


def _seed_budgets() -> list[Budget]:
    today = date.today()
    return [
        Budget("b1", "Q4 Conference Fund",    "CONF-Q4",  8000.0,  3420.0, today + timedelta(days=14),  "Conference",    "James Liu"),
        Budget("b2", "Client Visit Budget",   "CLIENT-H2", 5500.0,  1800.0, today + timedelta(days=47),  "Client Visit",  "James Liu"),
        Budget("b3", "Training & Dev Fund",   "TRAIN-24",  3200.0,  2950.0, today + timedelta(days=8),   "Training",      "Priya Sharma"),
        Budget("b4", "General Travel Pool",   "GEN-POOL",  12000.0, 6780.0, today + timedelta(days=90),  "General",       "Priya Sharma"),
    ]


def _seed_trips() -> list[Trip]:
    today = date.today()
    return [
        Trip(
            id="t1", user_id="u1",
            name="AWS re:Invent 2026",
            destination="Las Vegas, NV",
            purpose="Conference",
            start_date=today + timedelta(days=18),
            end_date=today + timedelta(days=22),
            status="upcoming",
            budget_allocated=3200.0,
            budget_code="CONF-Q4",
            icon="🎪",
            flights=[
                Flight("f1", "Southwest", "WN 412", "SEA", "LAS",
                       datetime.combine(today + timedelta(days=18), datetime.min.time().replace(hour=8, minute=30)),
                       datetime.combine(today + timedelta(days=18), datetime.min.time().replace(hour=11, minute=15)),
                       "scheduled", "WN-A1B2C3", 287.0),
                Flight("f2", "Southwest", "WN 415", "LAS", "SEA",
                       datetime.combine(today + timedelta(days=22), datetime.min.time().replace(hour=17, minute=0)),
                       datetime.combine(today + timedelta(days=22), datetime.min.time().replace(hour=19, minute=45)),
                       "scheduled", "WN-D4E5F6", 287.0),
            ],
            hotels=[
                Hotel("h1", "MGM Grand (Marriott Autograph)",
                      "3799 Las Vegas Blvd S", "Las Vegas",
                      today + timedelta(days=18), today + timedelta(days=22),
                      "confirmed", "MGM-78901", 189.0, True),
            ],
            rental_cars=[
                RentalCar("rc1", "Enterprise", "LAS Airport",
                          datetime.combine(today + timedelta(days=18), datetime.min.time().replace(hour=12, minute=0)),
                          datetime.combine(today + timedelta(days=22), datetime.min.time().replace(hour=16, minute=0)),
                          "Midsize", "confirmed", "ENT-XY9012", 65.0),
            ],
        ),
        Trip(
            id="t2", user_id="u1",
            name="Chicago Client Meeting",
            destination="Chicago, IL",
            purpose="Client Visit",
            start_date=today - timedelta(days=2),
            end_date=today + timedelta(days=1),
            status="active",
            budget_allocated=1800.0,
            budget_code="CLIENT-H2",
            icon="🏙️",
            flights=[
                Flight("f3", "Delta", "DL 1234", "SEA", "ORD",
                       datetime.combine(today - timedelta(days=2), datetime.min.time().replace(hour=6, minute=0)),
                       datetime.combine(today - timedelta(days=2), datetime.min.time().replace(hour=12, minute=30)),
                       "completed", "DL-C3D4E5", 412.0),
                Flight("f4", "Delta", "DL 4567", "ORD", "SEA",
                       datetime.combine(today + timedelta(days=1), datetime.min.time().replace(hour=15, minute=0)),
                       datetime.combine(today + timedelta(days=1), datetime.min.time().replace(hour=17, minute=45)),
                       "scheduled", "DL-F6G7H8", 412.0),
            ],
            hotels=[
                Hotel("h2", "Marriott Magnificent Mile",
                      "540 N Michigan Ave", "Chicago",
                      today - timedelta(days=2), today + timedelta(days=1),
                      "confirmed", "MAR-56789", 229.0, True),
            ],
        ),
        Trip(
            id="t3", user_id="u1",
            name="San Francisco Q3 Review",
            destination="San Francisco, CA",
            purpose="Internal Meeting",
            start_date=today - timedelta(days=45),
            end_date=today - timedelta(days=42),
            status="completed",
            budget_allocated=1500.0,
            budget_code="GEN-POOL",
            icon="🌉",
            flights=[
                Flight("f5", "Southwest", "WN 789", "SEA", "SFO",
                       datetime.combine(today - timedelta(days=45), datetime.min.time().replace(hour=7, minute=0)),
                       datetime.combine(today - timedelta(days=45), datetime.min.time().replace(hour=9, minute=15)),
                       "completed", "WN-Q1R2S3", 198.0),
            ],
            hotels=[
                Hotel("h3", "Marriott Union Square",
                      "480 Sutter St", "San Francisco",
                      today - timedelta(days=45), today - timedelta(days=42),
                      "confirmed", "MAR-12345", 249.0, True),
            ],
        ),
    ]


def _seed_expenses() -> list[Expense]:
    today = date.today()
    return [
        Expense("e1", "u1", "t3", today - timedelta(days=44), "Airfare",
                "Southwest Airlines", 198.0, "USD", "SEA→SFO round trip",
                "approved", True, [], False, datetime(2026, 8, 2), datetime(2026, 8, 4), "James Liu", "GEN-POOL"),
        Expense("e2", "u1", "t3", today - timedelta(days=44), "Accommodation",
                "Marriott Union Square", 747.0, "USD", "3 nights hotel",
                "approved", True, [], False, datetime(2026, 8, 2), datetime(2026, 8, 4), "James Liu", "GEN-POOL"),
        Expense("e3", "u1", "t3", today - timedelta(days=43), "Meals",
                "The Slanted Door", 124.0, "USD", "Client dinner",
                "approved", True, [], False, datetime(2026, 8, 3), datetime(2026, 8, 5), "James Liu", "GEN-POOL"),
        Expense("e4", "u1", "t2", today - timedelta(days=2), "Airfare",
                "Delta Air Lines", 412.0, "USD", "SEA→ORD outbound",
                "approved", True, [], False, datetime(2026, 9, 13), datetime(2026, 9, 14), "James Liu", "CLIENT-H2"),
        Expense("e5", "u1", "t2", today - timedelta(days=1), "Meals",
                "Alinea Chicago", 285.0, "USD", "Client dinner — 4 people",
                "pending", False,
                ["Meal expense $285 exceeds single-meal limit of $150 per person"],
                False, datetime(2026, 9, 14), None, "", "CLIENT-H2"),
        Expense("e6", "u1", "t2", today, "Ground Transport",
                "Uber", 42.0, "USD", "Airport → hotel",
                "pending", True, [], False, datetime(2026, 9, 15), None, "", "CLIENT-H2"),
        Expense("e7", "u1", "t1", today + timedelta(days=18), "Airfare",
                "Southwest Airlines", 574.0, "USD", "LAS round trip",
                "draft", True, [], False),
        Expense("e8", "u1", "t1", today + timedelta(days=18), "Accommodation",
                "MGM Grand", 756.0, "USD", "4 nights",
                "draft", True, [], False),
    ]


def _seed_approvals() -> list[Approval]:
    today = datetime.now()
    return [
        Approval("a1", "e5", "Chicago Client Meeting", "Sarah Chen", "u2",
                 285.0, "Meals", "Client dinner — 4 people at Alinea Chicago",
                 "pending", today - timedelta(hours=18),
                 violations=["Meal expense $285 exceeds per-meal limit of $150"]),
        Approval("a2", "e6", "Chicago Client Meeting", "Sarah Chen", "u2",
                 42.0, "Ground Transport", "Uber — Airport to hotel",
                 "pending", today - timedelta(hours=6)),
    ]


def _seed_notifications() -> list[Notification]:
    now = datetime.now()
    return [
        Notification(
            id="n1",
            type="BUDGET_EXPIRING",
            title="⚠️ Training Budget Expiring in 8 Days",
            body="You have $250 remaining in TRAIN-24 (Training & Dev Fund) that expires on "
                 f"{(date.today() + timedelta(days=8)).strftime('%b %d')}. Use it or lose it!",
            severity="warning",
            ai_query="I have $250 remaining in my Training & Dev budget expiring in 8 days. "
                     "Help me figure out the best way to use this before it expires.",
            created_at=now - timedelta(hours=2),
        ),
    ]


# ─────────────────────────────────────────────────────────────────────────────
#  Session-state initializer  (idempotent)
# ─────────────────────────────────────────────────────────────────────────────
def init_data_store():
    """Seed session state with demo data on first run. Safe to call on every page."""
    if st.session_state.get("_ds_initialized"):
        return

    st.session_state._ds_initialized = True
    st.session_state.current_user   = _seed_users()["u1"]
    st.session_state.users          = _seed_users()
    st.session_state.budgets        = _seed_budgets()
    st.session_state.trips          = _seed_trips()
    st.session_state.expenses       = _seed_expenses()
    st.session_state.approvals      = _seed_approvals()
    st.session_state.notifications  = _seed_notifications()

    # AI assistant shared state
    st.session_state.setdefault("ai_agent",           None)
    st.session_state.setdefault("ai_messages",        [])
    st.session_state.setdefault("ai_suggestions",     [])
    st.session_state.setdefault("ai_key_valid",       False)
    st.session_state.setdefault("ai_api_key",         "")
    st.session_state.setdefault("ai_policy_text",     "")
    st.session_state.setdefault("ai_preload_query",   None)
    st.session_state.setdefault("ai_msg_count",       0)
    st.session_state.setdefault("policy_loaded",      False)

    # Navigation
    st.session_state.setdefault("active_tab",         0)
    st.session_state.setdefault("pending_msg",        None)


# ─────────────────────────────────────────────────────────────────────────────
#  Convenience accessors
# ─────────────────────────────────────────────────────────────────────────────
def get_trip(trip_id: str) -> Trip | None:
    return next((t for t in st.session_state.trips if t.id == trip_id), None)

def get_expense(expense_id: str) -> Expense | None:
    return next((e for e in st.session_state.expenses if e.id == expense_id), None)

def add_expense(expense: Expense):
    st.session_state.expenses.append(expense)

def add_notification(notif: Notification):
    st.session_state.notifications.insert(0, notif)

def unread_count() -> int:
    return sum(1 for n in st.session_state.notifications if not n.read)

def mark_all_read():
    for n in st.session_state.notifications:
        n.read = True

def pending_approvals_count() -> int:
    return sum(1 for a in st.session_state.approvals if a.status == "pending")

def total_spent_this_month() -> float:
    today = date.today()
    return sum(
        e.amount for e in st.session_state.expenses
        if e.expense_date.month == today.month
        and e.expense_date.year == today.year
        and e.status in ("pending", "approved")
    )

def policy_violations_count() -> int:
    return sum(1 for e in st.session_state.expenses if not e.policy_compliant and e.status == "pending")
