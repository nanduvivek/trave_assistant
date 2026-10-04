"""
core/models.py — Dataclasses for TravelPro Enterprise.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import List, Optional


# ─────────────────────────────────────────────
#  User
# ─────────────────────────────────────────────
@dataclass
class User:
    id: str
    name: str
    email: str
    department: str
    role: str           # "employee" | "manager" | "admin"
    approver_id: str
    avatar_emoji: str = "👤"
    company: str = "Acme Corp"


# ─────────────────────────────────────────────
#  Budget
# ─────────────────────────────────────────────
@dataclass
class Budget:
    id: str
    name: str
    code: str
    total: float
    spent: float
    expiry_date: date
    category: str       # "Conference" | "Client Visit" | "Training" | "General"
    owner: str

    @property
    def available(self) -> float:
        return max(0.0, self.total - self.spent)

    @property
    def days_until_expiry(self) -> int:
        return (self.expiry_date - date.today()).days

    @property
    def utilization_pct(self) -> float:
        return round(self.spent / self.total * 100, 1) if self.total > 0 else 0.0


# ─────────────────────────────────────────────
#  Flight
# ─────────────────────────────────────────────
@dataclass
class Flight:
    id: str
    airline: str
    flight_number: str
    origin: str
    destination: str
    departure: datetime
    arrival: datetime
    status: str         # "scheduled" | "cancelled" | "delayed" | "completed"
    confirmation: str
    cost: float
    seat: str = "24B"
    cabin: str = "Economy"


# ─────────────────────────────────────────────
#  Hotel
# ─────────────────────────────────────────────
@dataclass
class Hotel:
    id: str
    name: str
    address: str
    city: str
    check_in: date
    check_out: date
    status: str         # "confirmed" | "cancelled" | "completed"
    confirmation: str
    nightly_rate: float
    policy_compliant: bool = True

    @property
    def nights(self) -> int:
        return (self.check_out - self.check_in).days

    @property
    def total_cost(self) -> float:
        return self.nightly_rate * self.nights


# ─────────────────────────────────────────────
#  Rental Car
# ─────────────────────────────────────────────
@dataclass
class RentalCar:
    id: str
    vendor: str
    pickup_location: str
    pickup_date: datetime
    return_date: datetime
    vehicle_class: str
    status: str         # "confirmed" | "cancelled" | "completed"
    confirmation: str
    daily_rate: float

    @property
    def days(self) -> int:
        return max(1, (self.return_date.date() - self.pickup_date.date()).days)

    @property
    def total_cost(self) -> float:
        return self.daily_rate * self.days


# ─────────────────────────────────────────────
#  Trip
# ─────────────────────────────────────────────
@dataclass
class Trip:
    id: str
    user_id: str
    name: str
    destination: str
    purpose: str
    start_date: date
    end_date: date
    status: str         # "upcoming" | "active" | "completed" | "cancelled"
    budget_allocated: float
    flights: List[Flight] = field(default_factory=list)
    hotels: List[Hotel] = field(default_factory=list)
    rental_cars: List[RentalCar] = field(default_factory=list)
    budget_code: str = ""
    icon: str = "✈️"

    @property
    def total_booking_cost(self) -> float:
        f = sum(fl.cost for fl in self.flights)
        h = sum(ho.total_cost for ho in self.hotels)
        r = sum(rc.total_cost for rc in self.rental_cars)
        return f + h + r

    @property
    def nights(self) -> int:
        return (self.end_date - self.start_date).days


# ─────────────────────────────────────────────
#  Expense
# ─────────────────────────────────────────────
@dataclass
class Expense:
    id: str
    user_id: str
    trip_id: str
    expense_date: date
    category: str       # "Accommodation" | "Airfare" | "Meals" | "Ground Transport" | "Other"
    merchant: str
    amount: float
    currency: str
    description: str
    status: str         # "draft" | "pending" | "approved" | "rejected"
    policy_compliant: bool = True
    violations: List[str] = field(default_factory=list)
    receipt_extracted: bool = False
    submitted_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    approved_by: str = ""
    budget_code: str = ""
    notes: str = ""


# ─────────────────────────────────────────────
#  Approval
# ─────────────────────────────────────────────
@dataclass
class Approval:
    id: str
    expense_id: str
    trip_name: str
    requester_name: str
    approver_id: str
    amount: float
    category: str
    description: str
    status: str         # "pending" | "approved" | "rejected" | "info_requested"
    submitted_at: datetime
    decided_at: Optional[datetime] = None
    notes: str = ""
    violations: List[str] = field(default_factory=list)


# ─────────────────────────────────────────────
#  Notification
# ─────────────────────────────────────────────
@dataclass
class Notification:
    id: str
    type: str           # "FLIGHT_CANCELLED" | "HOTEL_CANCELLED" | "EXPENSE_OVER_LIMIT" |
                        # "BUDGET_EXPIRING" | "APPROVAL_NEEDED" | "APPROVAL_GRANTED" | "DELAY"
    title: str
    body: str
    severity: str       # "critical" | "warning" | "info" | "success"
    ai_query: str       # pre-loaded query for AI Assistant tab
    created_at: datetime
    read: bool = False
    trip_id: str = ""
    action_label: str = "View in AI Assistant"
