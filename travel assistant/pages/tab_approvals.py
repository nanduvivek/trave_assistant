"""
pages/tab_approvals.py — Approval workflow tab for TravelPro Enterprise.
"""
from __future__ import annotations
import streamlit as st
from datetime import datetime

from core.notifications import fire_event


_STATUS_STYLE = {
    "pending":          ("#F59E0B", "#FFFBEB", "⏳ Pending"),
    "approved":         ("#10B981", "#F0FDF4", "✅ Approved"),
    "rejected":         ("#EF4444", "#FEF2F2", "❌ Rejected"),
    "info_requested":   ("#3B82F6", "#EFF6FF", "💬 Info Requested"),
}


def render_approvals():
    st.markdown("### ✅ Approval Workflow")
    user = st.session_state.current_user

    view_tab, history_tab = st.tabs(["📥 Pending Queue", "📜 Decision History"])

    with view_tab:
        _render_pending_queue()

    with history_tab:
        _render_history()


def _render_pending_queue():
    approvals = [a for a in st.session_state.approvals if a.status == "pending"]
    user = st.session_state.current_user

    # Role toggle — simulate manager / employee views
    role_col, _ = st.columns([2, 4])
    with role_col:
        is_manager = st.toggle("👨‍💼 Manager View", value=(user.role == "manager"), key="mgr_view_toggle")

    st.divider()

    if not approvals:
        st.success("🎉 No pending approvals — all caught up!")
        return

    for approval in approvals:
        color, bg, status_label = _STATUS_STYLE["pending"]

        st.markdown(
            f"""<div style="background:#fff;border:1px solid #E2E8F0;border-radius:12px;
            padding:1.2rem 1.5rem;margin-bottom:1rem;border-left:4px solid {color};">
            <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:0.5rem;">
              <div>
                <strong style="font-size:1rem;color:#0F2340;">{approval.description}</strong><br>
                <span style="color:#64748B;font-size:0.83rem;">
                  {approval.category} · {approval.trip_name} · by {approval.requester_name}
                </span><br>
                <span style="color:#94A3B8;font-size:0.78rem;">
                  Submitted {_time_ago(approval.submitted_at)}
                </span>
              </div>
              <div style="text-align:right;">
                <span style="font-size:1.5rem;font-weight:700;color:#0F2340;">${approval.amount:,.2f}</span>
              </div>
            </div>""",
            unsafe_allow_html=True,
        )

        # Violations
        if approval.violations:
            st.warning(f"⚠️ **Policy flags:** {' | '.join(approval.violations)}")

        if is_manager:
            # Manager action buttons
            col_approve, col_reject, col_info, col_notes = st.columns([2, 2, 2, 4])

            with col_notes:
                note_key = f"note_{approval.id}"
                manager_note = st.text_input("Manager note (optional)", key=note_key, label_visibility="collapsed",
                                             placeholder="Add a note…")

            with col_approve:
                if st.button("✅ Approve", key=f"approve_{approval.id}", use_container_width=True, type="primary"):
                    _decide(approval, "approved", manager_note or "Approved by manager.")
                    fire_event("APPROVAL_GRANTED", {
                        "amount": f"${approval.amount:.2f}",
                        "description": approval.description,
                        "approver": user.name,
                    })
                    st.success(f"✅ ${approval.amount:.2f} expense approved!")
                    st.rerun()

            with col_reject:
                if st.button("❌ Reject", key=f"reject_{approval.id}", use_container_width=True):
                    _decide(approval, "rejected", manager_note or "Rejected by manager.")
                    st.error(f"❌ Expense rejected.")
                    st.rerun()

            with col_info:
                if st.button("💬 Need Info", key=f"info_{approval.id}", use_container_width=True):
                    _decide(approval, "info_requested", manager_note or "Please provide more details.")
                    st.info("💬 More information requested.")
                    st.rerun()
        else:
            st.markdown(
                f'<div style="background:#FFFBEB;padding:0.6rem 0.8rem;border-radius:8px;margin-top:0.5rem;">'
                f'<span style="color:#92400E;font-size:0.83rem;">⏳ Awaiting review by your manager</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

        st.markdown("</div><br>", unsafe_allow_html=True)


def _render_history():
    decided = [a for a in st.session_state.approvals if a.status != "pending"]

    if not decided:
        st.info("No decisions recorded yet.")
        return

    for approval in sorted(decided, key=lambda a: a.decided_at or datetime.min, reverse=True):
        color, bg, status_label = _STATUS_STYLE.get(approval.status, ("#64748B", "#F8FAFC", approval.status.title()))

        st.markdown(
            f"""<div style="background:{bg};border:1px solid #E2E8F0;border-radius:10px;
            padding:0.9rem 1.2rem;margin-bottom:0.6rem;display:flex;
            justify-content:space-between;align-items:center;flex-wrap:wrap;gap:0.5rem;">
            <div>
              <strong style="color:{color};">{status_label}</strong>
              <span style="color:#475569;margin-left:0.5rem;">{approval.description}</span><br>
              <span style="color:#94A3B8;font-size:0.78rem;">
                {approval.category} · {approval.trip_name}
                {f" · {_time_ago(approval.decided_at)}" if approval.decided_at else ""}
              </span>
              {f'<br><span style="color:#64748B;font-size:0.78rem;">📝 {approval.notes}</span>' if approval.notes else ""}
            </div>
            <span style="font-size:1.3rem;font-weight:700;color:{color};">${approval.amount:,.2f}</span>
            </div>""",
            unsafe_allow_html=True,
        )


def _decide(approval, status: str, note: str):
    approval.status = status
    approval.decided_at = datetime.now()
    approval.notes = note
    # Update the corresponding expense status
    expense = next((e for e in st.session_state.expenses if e.id == approval.expense_id), None)
    if expense:
        expense.status = status
        expense.approved_at = datetime.now()
        expense.approved_by = st.session_state.current_user.name


def _time_ago(dt: datetime | None) -> str:
    if dt is None:
        return ""
    diff = datetime.now() - dt
    if diff.days > 0:
        return f"{diff.days}d ago"
    hours = int(diff.total_seconds() / 3600)
    if hours > 0:
        return f"{hours}h ago"
    minutes = int(diff.total_seconds() / 60)
    return f"{minutes}m ago"
