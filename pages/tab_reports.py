"""
pages/tab_reports.py — Analytics & Reports tab for TravelPro Enterprise.
"""
from __future__ import annotations
import io
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import date


def render_reports():
    st.markdown("### 📊 Spend Reports & Analytics")

    expenses  = st.session_state.expenses
    trips     = st.session_state.trips
    budgets   = st.session_state.budgets

    # ── Summary Metrics ──────────────────────────────────────────────────────
    total_all   = sum(e.amount for e in expenses if e.status in ("approved", "pending"))
    approved    = sum(e.amount for e in expenses if e.status == "approved")
    violations  = sum(1 for e in expenses if not e.policy_compliant)
    compliance  = round((1 - violations / max(len(expenses), 1)) * 100, 1)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Spend",       f"${total_all:,.2f}")
    m2.metric("Approved Amount",   f"${approved:,.2f}")
    m3.metric("Policy Violations", str(violations))
    m4.metric("Compliance Rate",   f"{compliance}%",
              delta=f"+{compliance - 80:.1f}pp vs target",
              delta_color="normal" if compliance >= 80 else "inverse")

    st.divider()

    # ── Chart row ────────────────────────────────────────────────────────────
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Spend by Category")
        cat_totals: dict[str, float] = {}
        for e in expenses:
            if e.status in ("approved", "pending"):
                cat_totals[e.category] = cat_totals.get(e.category, 0) + e.amount
        if cat_totals:
            fig = px.bar(
                x=list(cat_totals.keys()), y=list(cat_totals.values()),
                color=list(cat_totals.keys()),
                color_discrete_sequence=["#3B82F6", "#10B981", "#F59E0B", "#8B5CF6", "#EF4444"],
                labels={"x": "Category", "y": "Amount (USD)"},
            )
            fig.update_layout(height=280, showlegend=False, margin=dict(l=0, r=0, t=10, b=0),
                              plot_bgcolor="white", paper_bgcolor="white",
                              xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor="#F1F5F9"))
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("#### Budget Utilization")
        budget_names  = [b.name.split()[0] for b in budgets]
        budget_spent  = [b.spent for b in budgets]
        budget_avail  = [b.available for b in budgets]

        fig2 = go.Figure()
        fig2.add_trace(go.Bar(name="Spent", x=budget_names, y=budget_spent,
                              marker_color="#3B82F6"))
        fig2.add_trace(go.Bar(name="Available", x=budget_names, y=budget_avail,
                              marker_color="#E2E8F0"))
        fig2.update_layout(barmode="stack", height=280, margin=dict(l=0, r=0, t=10, b=0),
                           plot_bgcolor="white", paper_bgcolor="white",
                           legend=dict(orientation="h", y=1.05),
                           xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor="#F1F5F9"))
        st.plotly_chart(fig2, use_container_width=True)

    # ── Spend by Trip ─────────────────────────────────────────────────────────
    st.markdown("#### Spend by Trip")
    trip_map = {t.id: t.name for t in trips}
    trip_spend: dict[str, float] = {}
    for e in expenses:
        if e.status in ("approved", "pending"):
            name = trip_map.get(e.trip_id, "Other")
            trip_spend[name] = trip_spend.get(name, 0) + e.amount

    if trip_spend:
        fig3 = px.pie(values=list(trip_spend.values()), names=list(trip_spend.keys()),
                      hole=0.4,
                      color_discrete_sequence=px.colors.qualitative.Set2)
        fig3.update_layout(height=260, margin=dict(l=0, r=0, t=10, b=0), paper_bgcolor="white")
        col_pie, col_tbl = st.columns([2, 3])
        with col_pie:
            st.plotly_chart(fig3, use_container_width=True)
        with col_tbl:
            tbl_data = [{"Trip": n, "Amount": f"${v:,.2f}", "Share": f"{v/total_all*100:.1f}%"}
                        for n, v in sorted(trip_spend.items(), key=lambda x: -x[1])]
            st.dataframe(pd.DataFrame(tbl_data), use_container_width=True, hide_index=True)

    st.divider()

    # ── Full Expense Table ────────────────────────────────────────────────────
    st.markdown("#### 📋 Full Expense Register")

    df = pd.DataFrame([
        {
            "Date":        e.expense_date.strftime("%Y-%m-%d"),
            "Merchant":    e.merchant,
            "Category":    e.category,
            "Amount":      e.amount,
            "Currency":    e.currency,
            "Trip":        trip_map.get(e.trip_id, "—"),
            "Status":      e.status.title(),
            "Compliant":   "✅" if e.policy_compliant else "⚠️",
        }
        for e in expenses
    ])

    st.dataframe(
        df.style.format({"Amount": "${:.2f}"}),
        use_container_width=True,
        hide_index=True,
    )

    # ── Export ────────────────────────────────────────────────────────────────
    csv_buf = io.StringIO()
    df.to_csv(csv_buf, index=False)

    st.download_button(
        label="⬇️ Export to CSV",
        data=csv_buf.getvalue(),
        file_name=f"travelPro_expenses_{date.today().isoformat()}.csv",
        mime="text/csv",
        type="primary",
    )
