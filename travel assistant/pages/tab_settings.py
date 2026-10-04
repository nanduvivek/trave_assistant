"""
pages/tab_settings.py — Settings & Configuration tab for TravelPro.
"""
from __future__ import annotations
import io
import time
import streamlit as st


def _extract_pdf_text(file_bytes: bytes) -> str:
    try:
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(file_bytes))
        return "\n".join(p.extract_text() or "" for p in reader.pages)
    except Exception as e:
        return f"[PDF parse error: {e}]"


def _extract_docx_text(file_bytes: bytes) -> str:
    try:
        import docx
        doc = docx.Document(io.BytesIO(file_bytes))
        return "\n".join(p.text for p in doc.paragraphs)
    except Exception as e:
        return f"[DOCX parse error: {e}]"


def render_settings():
    st.markdown("### ⚙️ Settings & Configuration")

    # Sub-tabs
    tab_api, tab_profile, tab_policy, tab_notifs = st.tabs([
        "🔑 API Key", "👤 Profile", "📄 Company Policy", "🔔 Notifications"
    ])

    with tab_api:
        _render_api_settings()

    with tab_profile:
        _render_profile_settings()

    with tab_policy:
        _render_policy_settings()

    with tab_notifs:
        _render_notification_settings()


def _render_api_settings():
    st.markdown("#### Gemini API Key")
    st.markdown(
        "Connect your Gemini API key to enable the AI Assistant, receipt OCR, and event notifications. "
        "Get a free key at [aistudio.google.com](https://aistudio.google.com/app/apikey).",
    )

    current_key = st.session_state.get("ai_api_key", "")
    is_valid    = st.session_state.get("ai_key_valid", False)

    col_key, col_btn = st.columns([4, 1])
    with col_key:
        new_key = st.text_input(
            "Gemini API Key",
            value=current_key,
            type="password",
            placeholder="AIza…",
            label_visibility="collapsed",
        )
    with col_btn:
        validate_clicked = st.button("Validate", type="primary", use_container_width=True)

    if validate_clicked and new_key:
        from agent import TravelAgentSystem
        with st.spinner("Validating API key …"):
            ok, err = TravelAgentSystem.validate_api_key(new_key)
        if ok:
            st.session_state.ai_api_key   = new_key
            st.session_state.ai_key_valid = True
            st.session_state.ai_agent     = None  # will be rebuilt on next AI call
            from pages.tab_ai_assistant import _build_agent
            _build_agent()
            st.success("✅ API key validated and saved! AI Assistant is now active.")
        else:
            st.error(f"❌ Validation failed: {err}")
    elif new_key != current_key:
        st.session_state.ai_api_key  = new_key
        st.session_state.ai_key_valid = False
        st.session_state.ai_agent    = None

    if is_valid:
        st.markdown(
            '<div style="background:#F0FDF4;border:1px solid #BBF7D0;border-radius:8px;'
            'padding:0.7rem 1rem;margin-top:0.5rem;">'
            '<span style="color:#15803D;font-weight:600;">✅ Connected to Gemini Flash</span><br>'
            '<span style="color:#166534;font-size:0.82rem;">AI Assistant, OCR, and event notifications are active.</span>'
            '</div>',
            unsafe_allow_html=True,
        )

    st.divider()
    st.markdown("#### 🛡️ API Key Security Tips")
    st.info(
        "• Your API key is stored only in your browser session and never transmitted outside.\n"
        "• Keys are masked in the UI and not persisted to disk.\n"
        "• Rotate your key periodically at Google AI Studio."
    )


def _render_profile_settings():
    st.markdown("#### User Profile")
    user = st.session_state.current_user

    col1, col2 = st.columns(2)
    with col1:
        new_name  = st.text_input("Full Name",   value=user.name)
        new_email = st.text_input("Email",       value=user.email)
        new_dept  = st.text_input("Department",  value=user.department)
    with col2:
        new_company = st.text_input("Company",   value=user.company)
        new_role    = st.selectbox("Role",       ["employee", "manager", "admin"],
                                   index=["employee", "manager", "admin"].index(user.role))
        new_avatar  = st.selectbox("Avatar",
                                   ["👤", "👩‍💻", "👨‍💻", "👩‍💼", "👨‍💼", "🧑‍💼", "👩‍🔬", "👨‍🔬"],
                                   index=["👤", "👩‍💻", "👨‍💻", "👩‍💼", "👨‍💼", "🧑‍💼", "👩‍🔬", "👨‍🔬"].index(user.avatar_emoji)
                                   if user.avatar_emoji in ["👤", "👩‍💻", "👨‍💻", "👩‍💼", "👨‍💼", "🧑‍💼", "👩‍🔬", "👨‍🔬"] else 0)

    if st.button("💾 Save Profile", type="primary"):
        user.name         = new_name
        user.email        = new_email
        user.department   = new_dept
        user.company      = new_company
        user.role         = new_role
        user.avatar_emoji = new_avatar
        st.success("✅ Profile updated!")
        st.rerun()

    # Approver info
    st.divider()
    st.markdown("#### Approval Chain")
    approver = next((u for u in st.session_state.users.values() if u.id == user.approver_id), None)
    if approver:
        st.markdown(
            f'<div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:8px;'
            f'padding:0.8rem 1rem;">'
            f'{approver.avatar_emoji} <strong>{approver.name}</strong> · {approver.role.title()} '
            f'· {approver.email}'
            f'</div>',
            unsafe_allow_html=True,
        )


def _render_policy_settings():
    st.markdown("#### Company Travel Policy Document")
    st.markdown(
        "Upload your company's travel policy (PDF, DOCX, or TXT). "
        "The AI Assistant will use it to give policy-accurate recommendations."
    )

    uploaded = st.file_uploader(
        "Drop your policy document here",
        type=["pdf", "docx", "txt"],
        label_visibility="collapsed",
    )

    if uploaded:
        raw = uploaded.read()
        if uploaded.name.endswith(".pdf"):
            text = _extract_pdf_text(raw)
        elif uploaded.name.endswith(".docx"):
            text = _extract_docx_text(raw)
        else:
            text = raw.decode("utf-8", errors="replace")

        if text != st.session_state.get("ai_policy_text", ""):
            st.session_state.ai_policy_text = text
            st.session_state.policy_loaded  = True
            st.session_state.ai_agent       = None   # force rebuild with new policy
            if st.session_state.get("ai_key_valid"):
                from pages.tab_ai_assistant import _build_agent
                _build_agent()
            st.success(f"✅ Policy loaded: {uploaded.name}")

    if st.session_state.get("policy_loaded"):
        st.markdown(
            '<div style="background:#FFFBEB;border:1px solid #FDE68A;border-radius:8px;'
            'padding:0.7rem 1rem;margin-top:0.5rem;">'
            '<span style="color:#92400E;font-weight:600;">📄 Policy document active</span><br>'
            '<span style="color:#78350F;font-size:0.82rem;">The AI assistant is using your company\'s policy for all recommendations.</span>'
            '</div>',
            unsafe_allow_html=True,
        )

        if st.button("🗑️ Remove Policy Document"):
            st.session_state.ai_policy_text = ""
            st.session_state.policy_loaded  = False
            st.session_state.ai_agent       = None
            if st.session_state.get("ai_key_valid"):
                from pages.tab_ai_assistant import _build_agent
                _build_agent()
            st.success("Policy document removed.")
            st.rerun()

    # Current policy rules preview
    st.divider()
    st.markdown("#### 📋 Active Policy Rules")
    from core.policy_checker import POLICY
    rules = {
        "Hotel nightly limit":          f"${POLICY['hotel_nightly_limit']:.0f}",
        "Meal per-person limit":         f"${POLICY['meal_per_person_limit']:.0f}",
        "Ground transport limit":        f"${POLICY['ground_transport_limit']:.0f}",
        "Preferred hotel chains":        ", ".join(POLICY["preferred_hotel_chains"][:3]) + "…",
        "Tier 1 airlines (no approval)": ", ".join(POLICY["tier1_airlines"]),
        "Receipt required above":        f"${POLICY['require_receipts_above']:.0f}",
    }
    import pandas as pd
    st.dataframe(
        pd.DataFrame({"Policy Rule": list(rules.keys()), "Value": list(rules.values())}),
        use_container_width=True, hide_index=True,
    )


def _render_notification_settings():
    st.markdown("#### Notification Preferences")

    notif_prefs = st.session_state.get("notif_prefs", {
        "flight_cancelled":   True,
        "hotel_cancelled":    True,
        "rental_delay":       True,
        "expense_violation":  True,
        "budget_expiring":    True,
        "approval_updates":   True,
        "min_severity":       "warning",
    })

    with st.form("notif_prefs_form"):
        st.markdown("**Event types to receive:**")
        c1, c2 = st.columns(2)
        with c1:
            notif_prefs["flight_cancelled"]  = st.checkbox("✈️ Flight Cancellations",  value=notif_prefs.get("flight_cancelled", True))
            notif_prefs["hotel_cancelled"]   = st.checkbox("🏨 Hotel Cancellations",   value=notif_prefs.get("hotel_cancelled", True))
            notif_prefs["rental_delay"]      = st.checkbox("🚗 Rental Car Delays",     value=notif_prefs.get("rental_delay", True))
        with c2:
            notif_prefs["expense_violation"] = st.checkbox("⚠️ Policy Violations",    value=notif_prefs.get("expense_violation", True))
            notif_prefs["budget_expiring"]   = st.checkbox("💰 Budget Expiry Alerts", value=notif_prefs.get("budget_expiring", True))
            notif_prefs["approval_updates"]  = st.checkbox("✅ Approval Updates",      value=notif_prefs.get("approval_updates", True))

        st.divider()
        notif_prefs["min_severity"] = st.selectbox(
            "Minimum severity level to show",
            ["info", "warning", "critical"],
            index=["info", "warning", "critical"].index(notif_prefs.get("min_severity", "warning")),
        )

        if st.form_submit_button("💾 Save Preferences", type="primary"):
            st.session_state.notif_prefs = notif_prefs
            st.success("✅ Notification preferences saved!")
