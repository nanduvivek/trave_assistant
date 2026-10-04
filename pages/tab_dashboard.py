"""
pages/tab_dashboard.py — Dashboard tab for TravelPro Enterprise.
"""
from __future__ import annotations
import streamlit as st
from datetime import date, timedelta
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

from core.data_store import (
    total_spent_this_month, policy_violations_count,
    pending_approvals_count, unread_count, mark_all_read
)
from core.notifications import get_severity_color, get_severity_bg


def render_dashboard(switch_to_ai_tab):
    """Render the Dashboard tab. `switch_to_ai_tab` is a callable to navigate to Tab 4 (AI)."""
    user = st.session_state.current_user
    notifications = st.session_state.notifications
    trips = st.session_state.trips
    expenses = st.session_state.expenses

    # ── KPI Cards ────────────────────────────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)
    monthly_spend = total_spent_this_month()
    upcoming = [t for t in trips if t.status == "upcoming"]

    with col1:
        st.markdown(_kpi_card("💰", "Spent This Month", f"${monthly_spend:,.0f}", "+12% vs last month", "#3B82F6"), unsafe_allow_html=True)
    with col2:
        pend = pending_approvals_count()
        st.markdown(_kpi_card("✅", "Pending Approvals", str(pend), "requires your action" if pend else "all clear", "#F59E0B" if pend else "#10B981"), unsafe_allow_html=True)
    with col3:
        viol = policy_violations_count()
        st.markdown(_kpi_card("⚠️", "Policy Violations", str(viol), "need review" if viol else "fully compliant", "#EF4444" if viol else "#10B981"), unsafe_allow_html=True)
    with col4:
        st.markdown(_kpi_card("✈️", "Upcoming Trips", str(len(upcoming)), upcoming[0].destination if upcoming else "none scheduled", "#8B5CF6"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Notification Banners ─────────────────────────────────────────────────
    unread = [n for n in notifications if not n.read]
    if unread:
        for notif in unread[:3]:
            col_msg, col_btn = st.columns([5, 1])
            border_color = get_severity_color(notif.severity)
            bg_color = get_severity_bg(notif.severity)
            with col_msg:
                st.markdown(
                    f"""<div style="background:{bg_color};border-left:4px solid {border_color};
                    border-radius:8px;padding:0.75rem 1rem;margin-bottom:0.5rem;">
                    <strong style="color:{border_color};">{notif.title}</strong><br>
                    <span style="font-size:0.85rem;color:#475569;">{notif.body}</span>
                    </div>""",
                    unsafe_allow_html=True,
                )
            with col_btn:
                if notif.ai_query and st.button("🤖 Ask AI", key=f"dash_ai_{notif.id}", help="Open AI Assistant with context"):
                    st.session_state.ai_preload_query = notif.ai_query
                    notif.read = True
                    switch_to_ai_tab()
                    st.rerun()

        if len(unread) > 3:
            st.caption(f"+ {len(unread) - 3} more notifications")
        if st.button("✓ Mark all as read", key="mark_read"):
            mark_all_read()
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Charts Row ───────────────────────────────────────────────────────────
    chart_col1, chart_col2 = st.columns([3, 2])

    with chart_col1:
        st.markdown("#### 📈 Monthly Spend Trend")
        months = ["Apr", "May", "Jun", "Jul", "Aug", "Sep"]
        spend  = [2100, 3400, 1800, 4200, 3750, monthly_spend]
        budget = [4000, 4000, 4000, 4000, 4000, 4000]

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=months, y=spend, mode="lines+markers",
                                 name="Actual Spend", line=dict(color="#3B82F6", width=2.5),
                                 marker=dict(size=7)))
        fig.add_trace(go.Scatter(x=months, y=budget, mode="lines",
                                 name="Monthly Budget", line=dict(color="#E2E8F0", width=1.5, dash="dot")))
        fig.update_layout(height=240, margin=dict(l=0, r=0, t=10, b=0),
                          plot_bgcolor="white", paper_bgcolor="white",
                          legend=dict(orientation="h", yanchor="bottom", y=1.02),
                          xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor="#F1F5F9"))
        st.plotly_chart(fig, use_container_width=True)

    with chart_col2:
        st.markdown("#### 🍩 Spend by Category")
        cat_data = _category_summary(expenses)
        if cat_data:
            fig2 = px.pie(
                values=list(cat_data.values()),
                names=list(cat_data.keys()),
                hole=0.55,
                color_discrete_sequence=["#3B82F6", "#10B981", "#F59E0B", "#8B5CF6", "#EF4444"],
            )
            fig2.update_traces(textposition="inside", textinfo="percent+label")
            fig2.update_layout(height=240, margin=dict(l=0, r=0, t=10, b=0),
                               showlegend=False, paper_bgcolor="white")
            st.plotly_chart(fig2, use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Upcoming Trips ───────────────────────────────────────────────────────
    st.markdown("#### ✈️ Upcoming Trips")
    if upcoming:
        for trip in upcoming[:3]:
            days_away = (trip.start_date - date.today()).days
            st.markdown(
                f"""<div style="background:#fff;border:1px solid #E2E8F0;border-radius:10px;
                padding:1rem 1.2rem;margin-bottom:0.6rem;display:flex;align-items:center;gap:1rem;">
                <span style="font-size:2rem;">{trip.icon}</span>
                <div style="flex:1;">
                  <strong style="color:#0F2340;">{trip.name}</strong>
                  <span style="color:#64748B;font-size:0.82rem;"> — {trip.destination}</span><br>
                  <span style="font-size:0.8rem;color:#94A3B8;">
                    {trip.start_date.strftime('%b %d')} – {trip.end_date.strftime('%b %d, %Y')} 
                    · {trip.nights} nights · ${trip.budget_allocated:,.0f} budget
                  </span>
                </div>
                <span style="background:#EFF6FF;color:#3B82F6;padding:0.2rem 0.7rem;
                border-radius:20px;font-size:0.78rem;font-weight:600;">
                  In {days_away} days
                </span>
                </div>""",
                unsafe_allow_html=True,
            )
    else:
        st.info("No upcoming trips. Head to the Trips tab to plan your next journey!")

    # ── Budget Snapshot ──────────────────────────────────────────────────────
    st.markdown("<br>#### 💼 Budget Snapshot", unsafe_allow_html=True)
    budgets = st.session_state.budgets
    for b in sorted(budgets, key=lambda x: x.days_until_expiry):
        col_name, col_bar, col_expiry = st.columns([2, 4, 1])
        with col_name:
            expire_warning = "🔴 " if b.days_until_expiry <= 10 else ("⚠️ " if b.days_until_expiry <= 30 else "")
            st.markdown(f"**{expire_warning}{b.name}**  \n`{b.code}`", unsafe_allow_html=False)
        with col_bar:
            pct = b.utilization_pct
            bar_color = "#EF4444" if pct > 90 else "#F59E0B" if pct > 70 else "#10B981"
            st.markdown(
                f"""<div style="background:#F1F5F9;border-radius:6px;height:20px;margin-top:4px;">
                <div style="background:{bar_color};width:{min(pct,100):.1f}%;height:100%;border-radius:6px;
                display:flex;align-items:center;padding-left:6px;">
                <span style="color:#fff;font-size:0.72rem;font-weight:600;">${b.spent:,.0f} / ${b.total:,.0f}</span>
                </div></div>""",
                unsafe_allow_html=True,
            )
        with col_expiry:
            color = "#EF4444" if b.days_until_expiry <= 10 else "#F59E0B" if b.days_until_expiry <= 30 else "#94A3B8"
            st.markdown(f'<span style="color:{color};font-size:0.78rem;">Exp. {b.expiry_date.strftime("%b %d")}</span>', unsafe_allow_html=True)


# ─── helpers ─────────────────────────────────────────────────────────────────
def _kpi_card(icon, title, value, sub, color):
    return f"""
<div style="background:#fff;border-radius:12px;padding:1.2rem 1.4rem;
border:1px solid #E2E8F0;box-shadow:0 2px 8px rgba(0,0,0,0.04);">
  <div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.5rem;">
    <span style="font-size:1.3rem;">{icon}</span>
    <span style="font-size:0.78rem;color:#64748B;font-weight:600;text-transform:uppercase;letter-spacing:0.05em;">{title}</span>
  </div>
  <div style="font-size:2rem;font-weight:700;color:{color};">{value}</div>
  <div style="font-size:0.78rem;color:#94A3B8;margin-top:0.2rem;">{sub}</div>
</div>"""


def _category_summary(expenses) -> dict:
    totals: dict[str, float] = {}
    for e in expenses:
        if e.status in ("pending", "approved"):
            totals[e.category] = totals.get(e.category, 0) + e.amount
    return totals
