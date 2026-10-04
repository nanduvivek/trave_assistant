"""
pages/tab_expenses.py — Expense management tab for TravelPro Enterprise.
"""
from __future__ import annotations
import uuid
import streamlit as st
from datetime import date, datetime

from core.models import Expense
from core.data_store import add_expense, add_notification
from core.policy_checker import check_expense
from core.notifications import fire_event
from core.ocr_engine import extract_receipt_data, parse_receipt_fallback


_CATEGORIES = ["Airfare", "Accommodation", "Meals", "Ground Transport", "Other"]
_STATUS_COLOR = {
    "draft":    ("#94A3B8", "#F8FAFC"),
    "pending":  ("#F59E0B", "#FFFBEB"),
    "approved": ("#10B981", "#F0FDF4"),
    "rejected": ("#EF4444", "#FEF2F2"),
}
_STATUS_ICON = {"draft": "📝", "pending": "⏳", "approved": "✅", "rejected": "❌"}


def render_expenses(switch_to_ai_tab):
    st.markdown("### 🧾 Expense Management")

    tab_list, tab_new = st.tabs(["📋 All Expenses", "➕ Submit New Expense"])

    # ── Tab: All Expenses ────────────────────────────────────────────────────
    with tab_list:
        _render_expense_list(switch_to_ai_tab)

    # ── Tab: Submit New ───────────────────────────────────────────────────────
    with tab_new:
        _render_expense_form()


def _render_expense_list(switch_to_ai_tab):
    expenses = st.session_state.expenses

    # Filters
    fc1, fc2, fc3 = st.columns(3)
    with fc1:
        status_filter = st.selectbox("Status", ["All", "Draft", "Pending", "Approved", "Rejected"], key="exp_status_filter")
    with fc2:
        cat_filter = st.selectbox("Category", ["All"] + _CATEGORIES, key="exp_cat_filter")
    with fc3:
        trip_names = {t.id: t.name for t in st.session_state.trips}
        trip_opts = ["All"] + [t.name for t in st.session_state.trips]
        trip_filter = st.selectbox("Trip", trip_opts, key="exp_trip_filter")

    filtered = [
        e for e in expenses
        if (status_filter == "All" or e.status == status_filter.lower())
        and (cat_filter == "All" or e.category == cat_filter)
        and (trip_filter == "All" or trip_names.get(e.trip_id, "") == trip_filter)
    ]

    # Summary row
    total = sum(e.amount for e in filtered)
    s1, s2, s3 = st.columns(3)
    s1.metric("Filtered Total", f"${total:,.2f}")
    s2.metric("Count", len(filtered))
    s3.metric("Violations", sum(1 for e in filtered if not e.policy_compliant))

    st.divider()

    if not filtered:
        st.info("No expenses match your filter.")
        return

    for exp in sorted(filtered, key=lambda e: e.expense_date, reverse=True):
        badge_color, badge_bg = _STATUS_COLOR.get(exp.status, ("#64748B", "#F8FAFC"))
        icon = _STATUS_ICON.get(exp.status, "📄")

        with st.container():
            col_main, col_amt, col_status, col_act = st.columns([3, 1.2, 1.2, 1])

            with col_main:
                violation_tag = (
                    ' <span style="background:#FEF2F2;color:#EF4444;padding:0.1rem 0.4rem;'
                    'border-radius:4px;font-size:0.72rem;font-weight:600;">⚠️ Policy Violation</span>'
                    if not exp.policy_compliant else ""
                )
                trip_name = next((t.name for t in st.session_state.trips if t.id == exp.trip_id), "—")
                st.markdown(
                    f"""<div style="padding:0.1rem 0;">
                    <strong>{exp.merchant}</strong>{violation_tag}<br>
                    <span style="color:#64748B;font-size:0.82rem;">
                      {exp.category} · {exp.expense_date.strftime('%b %d, %Y')} · {trip_name}
                    </span><br>
                    <span style="color:#94A3B8;font-size:0.78rem;">{exp.description}</span>
                    </div>""",
                    unsafe_allow_html=True,
                )

            with col_amt:
                st.markdown(
                    f'<div style="font-size:1.1rem;font-weight:700;color:#0F2340;'
                    f'padding-top:0.6rem;">${exp.amount:,.2f}</div>',
                    unsafe_allow_html=True,
                )

            with col_status:
                st.markdown(
                    f'<div style="background:{badge_bg};color:{badge_color};'
                    f'border-radius:20px;padding:0.2rem 0.7rem;font-size:0.78rem;'
                    f'font-weight:600;text-align:center;margin-top:0.6rem;">'
                    f'{icon} {exp.status.title()}</div>',
                    unsafe_allow_html=True,
                )

            with col_act:
                if not exp.policy_compliant and exp.status == "pending":
                    if st.button("🤖 Fix", key=f"fix_{exp.id}", help="Get AI help with this violation"):
                        viol_text = "; ".join(exp.violations)
                        st.session_state.ai_preload_query = (
                            f"My {exp.category} expense of ${exp.amount:.2f} at {exp.merchant} has a policy violation: "
                            f"{viol_text}. How do I resolve this and get it approved?"
                        )
                        switch_to_ai_tab()
                        st.rerun()

            if not exp.policy_compliant and exp.violations:
                with st.expander("🔍 Policy violations — click for details"):
                    for v in exp.violations:
                        st.warning(v)
                    st.info("Click **🤖 Fix** to get AI guidance on how to resolve this.")

            st.markdown('<hr style="border:none;border-top:1px solid #F1F5F9;margin:0.3rem 0;">', unsafe_allow_html=True)


def _render_expense_form():
    st.markdown("#### Add a New Expense")

    # ── Receipt Upload (OCR) ──────────────────────────────────────────────────
    with st.expander("📎 Upload Receipt (AI auto-fill)", expanded=True):
        uploaded = st.file_uploader(
            "Drop receipt image or PDF — Gemini Vision will extract the details automatically",
            type=["png", "jpg", "jpeg", "pdf", "txt"],
            key="receipt_upload",
        )
        extracted: dict = {}
        if uploaded:
            file_bytes = uploaded.read()
            mime = "image/jpeg"
            if uploaded.name.endswith(".png"):
                mime = "image/png"
            elif uploaded.name.endswith(".pdf"):
                from core.ocr_engine import parse_receipt_fallback
                try:
                    from pypdf import PdfReader
                    import io
                    reader = PdfReader(io.BytesIO(file_bytes))
                    text = "\n".join(p.extract_text() or "" for p in reader.pages)
                    extracted = parse_receipt_fallback(text)
                except Exception:
                    extracted = {}
                mime = None
            elif uploaded.name.endswith(".txt"):
                extracted = parse_receipt_fallback(file_bytes.decode("utf-8", errors="replace"))
                mime = None

            if mime:
                with st.spinner("🔍 Extracting receipt data with Gemini Vision …"):
                    extracted = extract_receipt_data(file_bytes, mime)

            if extracted:
                st.success("✅ Receipt data extracted! Fields pre-filled below.")
            elif not st.session_state.get("ai_key_valid"):
                st.info("💡 Connect your Gemini API key in the AI Assistant tab to enable auto-fill.")
            else:
                st.warning("Could not extract data automatically — please fill in manually.")

    st.divider()

    # ── Form ──────────────────────────────────────────────────────────────────
    with st.form("new_expense_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            merchant = st.text_input("Merchant / Vendor *", value=extracted.get("merchant", ""))
            category = st.selectbox("Category *", _CATEGORIES,
                                    index=_CATEGORIES.index(extracted["category"])
                                    if extracted.get("category") in _CATEGORIES else 0)
            amount = st.number_input("Amount *", min_value=0.0, step=0.01,
                                     value=float(extracted.get("amount", 0.0) or 0.0))
        with c2:
            currency = st.selectbox("Currency", ["USD", "EUR", "GBP", "CAD", "INR"],
                                    index=0)
            try:
                from datetime import date as dt
                parsed_date = dt.fromisoformat(extracted["date"]) if extracted.get("date") else dt.today()
            except Exception:
                parsed_date = date.today()
            expense_date = st.date_input("Date *", value=parsed_date)
            trip_opts    = {t.id: t.name for t in st.session_state.trips}
            trip_id      = st.selectbox("Trip *", options=list(trip_opts.keys()),
                                        format_func=lambda x: trip_opts[x])

        description = st.text_input("Description *", value=extracted.get("description", ""))
        notes       = st.text_area("Notes (optional)", height=80)
        budget_opts = {b.id: f"{b.name} ({b.code})" for b in st.session_state.budgets}
        budget_id   = st.selectbox("Budget Code", options=list(budget_opts.keys()),
                                   format_func=lambda x: budget_opts[x])

        submitted = st.form_submit_button("💾 Save & Check Policy", use_container_width=True, type="primary")

    if submitted:
        if not merchant or not description or amount <= 0:
            st.error("Please fill in all required fields (marked with *).")
            return

        # Build expense and run policy check
        exp = Expense(
            id=f"e{_uid()}",
            user_id=st.session_state.current_user.id,
            trip_id=trip_id,
            expense_date=expense_date,
            category=category,
            merchant=merchant,
            amount=amount,
            currency=currency,
            description=description,
            status="draft",
            receipt_extracted=bool(extracted),
            notes=notes,
            budget_code=budget_opts[budget_id].split("(")[1].rstrip(")"),
        )

        result = check_expense(exp)
        exp.policy_compliant = result.compliant
        exp.violations = result.violations

        add_expense(exp)

        if result.compliant:
            st.success(f"✅ Expense saved! Fully policy compliant.")
        else:
            st.warning(f"⚠️ Expense saved with **{len(result.violations)} policy violation(s)**:")
            for v in result.violations:
                st.error(f"• {v}")
            for s in result.suggestions:
                st.info(f"💡 {s}")
            # Fire notification
            fire_event("EXPENSE_OVER_LIMIT", {
                "category": category, "amount": f"${amount:.2f}",
                "merchant": merchant,
            })

        st.rerun()


def _uid():
    return str(uuid.uuid4())[:6]
