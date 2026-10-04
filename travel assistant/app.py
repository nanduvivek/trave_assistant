"""
app.py — TravelPro Enterprise: Expensify-like Travel & Expense Management System

A full enterprise T&E platform with AI-powered travel assistant, expense management,
receipt OCR, approval workflows, analytics, and proactive AI notifications.

Run with:
    streamlit run app.py
"""
from __future__ import annotations
import io
import os
import sys
import streamlit as st
from dotenv import load_dotenv

# ── Ensure parent dir is on path so all imports work ─────────────────────────
sys.path.insert(0, os.path.dirname(__file__))
load_dotenv()

# ── Page config — MUST be first Streamlit call ───────────────────────────────
st.set_page_config(
    page_title="TravelPro Enterprise",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Lazy doc extractors ───────────────────────────────────────────────────────
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


# ── CSS ───────────────────────────────────────────────────────────────────────
def _inject_css():
    st.markdown(
        """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* ── App background ── */
.stApp { background: #F0F4F8; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0F2340 0%, #1A3355 100%);
    border-right: 1px solid rgba(200,169,110,0.25);
}
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] small,
[data-testid="stSidebar"] div { color: rgba(255,255,255,0.85) !important; }
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 { color: #C8A96E !important; }

/* ── Tab nav radio group ── */
[data-testid="stSidebar"] .stRadio > div { gap: 2px !important; }
[data-testid="stSidebar"] .stRadio label {
    background: rgba(200,169,110,0.08) !important;
    border: 1px solid rgba(200,169,110,0.2) !important;
    border-radius: 8px !important;
    padding: 0.5rem 0.9rem !important;
    cursor: pointer !important;
    transition: all 0.15s ease !important;
    width: 100% !important;
    font-size: 0.85rem !important;
}
[data-testid="stSidebar"] .stRadio label:hover {
    background: rgba(200,169,110,0.22) !important;
    border-color: #C8A96E !important;
}
[data-testid="stSidebar"] .stRadio label[data-baseweb="radio"] > div:first-child {
    display: none !important;
}

/* ── Top header bar ── */
.tp-header {
    background: linear-gradient(135deg, #0F2340 0%, #1E4080 100%);
    border-radius: 14px;
    padding: 1rem 1.8rem;
    margin-bottom: 1.2rem;
    display: flex;
    align-items: center;
    gap: 1rem;
    box-shadow: 0 6px 24px rgba(15,35,64,0.18);
}
.tp-logo { font-size: 2rem; }
.tp-title { color: #fff !important; font-size: 1.35rem !important; font-weight: 700 !important; margin: 0 !important; }
.tp-sub   { color: rgba(200,169,110,0.9) !important; font-size: 0.78rem !important; margin: 0 !important; }
.tp-right { margin-left: auto; display: flex; align-items: center; gap: 0.75rem; }
.tp-badge {
    padding: 0.18rem 0.6rem; border-radius: 20px;
    font-size: 0.72rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.04em;
}
.tp-badge-live    { background: rgba(16,185,129,0.2); color: #34D399; border: 1px solid rgba(16,185,129,0.4); }
.tp-badge-neutral { background: rgba(99,102,241,0.15); color: #A5B4FC; border: 1px solid rgba(99,102,241,0.3); }

/* ── Notification bell ── */
.notif-bell {
    background: rgba(200,169,110,0.15);
    border: 1px solid rgba(200,169,110,0.4);
    border-radius: 8px;
    padding: 0.3rem 0.7rem;
    cursor: pointer;
    font-size: 1rem;
    color: #C8A96E;
    font-weight: 700;
}

/* ── Cards ── */
.metric-card {
    background: #fff;
    border-radius: 12px;
    padding: 1.2rem 1.4rem;
    border: 1px solid #E2E8F0;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}

/* ── Tables ── */
.stDataFrame { border-radius: 10px !important; overflow: hidden !important; }
.stDataFrame thead th { background: #0F2340 !important; color: #fff !important; }

/* ── Tabs (content sub-tabs) ── */
.stTabs [data-baseweb="tab-list"] { gap: 4px; border-bottom: 2px solid #E2E8F0; }
.stTabs [data-baseweb="tab"] {
    background: transparent;
    border-radius: 8px 8px 0 0;
    padding: 0.5rem 1.2rem;
    font-size: 0.85rem;
    font-weight: 500;
    color: #64748B;
    border: 1px solid transparent;
}
.stTabs [aria-selected="true"] {
    background: #fff !important;
    color: #0F2340 !important;
    font-weight: 600 !important;
    border: 1px solid #E2E8F0 !important;
    border-bottom: 2px solid #fff !important;
}

/* ── Chat messages ── */
[data-testid="stChatMessage"] { background: transparent !important; }
[data-testid="stChatInput"] {
    border-radius: 12px !important;
    border: 2px solid #CBD5E1 !important;
}
[data-testid="stChatInput"]:focus-within {
    border-color: #3B82F6 !important;
    box-shadow: 0 0 0 3px rgba(59,130,246,0.12) !important;
}

/* ── Misc ── */
#MainMenu, footer, .stDeployButton { visibility: hidden !important; }
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-thumb { background: #CBD5E1; border-radius: 3px; }
.stSpinner > div { border-top-color: #1E3A5F !important; }
[data-testid="stFileUploader"] {
    background: rgba(200,169,110,0.06);
    border: 1px dashed rgba(200,169,110,0.45);
    border-radius: 8px;
}
.stAlert { border-radius: 8px !important; font-size: 0.85rem !important; }
.stMarkdown table { border-collapse: collapse; width: 100%; font-size: 0.84rem; }
.stMarkdown table th { background: #0F2340; color: #fff !important; padding: 0.45rem 0.75rem; }
.stMarkdown table td { padding: 0.42rem 0.75rem; border-bottom: 1px solid #E2E8F0; }
</style>
""",
        unsafe_allow_html=True,
    )


# ── Top header bar ────────────────────────────────────────────────────────────
def _render_header():
    from core.data_store import unread_count
    user = st.session_state.get("current_user")
    unread = unread_count()

    ai_badge = (
        '<span class="tp-badge tp-badge-live">● AI Live</span>'
        if st.session_state.get("ai_key_valid")
        else '<span class="tp-badge tp-badge-neutral">○ AI Offline</span>'
    )
    notif_badge = f'🔔 {unread}' if unread else '🔔'
    user_name = user.name if user else "User"
    avatar    = user.avatar_emoji if user else "👤"

    st.markdown(
        f"""<div class="tp-header">
  <span class="tp-logo">✈️</span>
  <div>
    <p class="tp-title">TravelPro Enterprise</p>
    <p class="tp-sub">AI-Powered Travel & Expense Management · Expensify-Class</p>
  </div>
  <div class="tp-right">
    {ai_badge}
    <span class="tp-badge tp-badge-neutral">{notif_badge}</span>
    <span class="tp-badge tp-badge-neutral">{avatar} {user_name}</span>
  </div>
</div>""",
        unsafe_allow_html=True,
    )


# ── Sidebar navigation ────────────────────────────────────────────────────────
_TABS = [
    "🏠  Dashboard",
    "🧾  Expenses",
    "✈️  Trips",
    "✅  Approvals",
    "🤖  AI Assistant",
    "📊  Reports",
    "⚙️  Settings",
]

def _render_sidebar():
    from core.data_store import unread_count, pending_approvals_count, policy_violations_count
    user = st.session_state.get("current_user")

    with st.sidebar:
        st.markdown(
            f'<div style="text-align:center;padding:1rem 0;">'
            f'<div style="font-size:2.5rem;">✈️</div>'
            f'<div style="font-size:1.1rem;font-weight:700;color:#C8A96E;">TravelPro</div>'
            f'<div style="font-size:0.72rem;color:rgba(255,255,255,0.5);">Enterprise Edition</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        st.divider()

        # User info
        if user:
            st.markdown(
                f'<div style="background:rgba(200,169,110,0.1);border-radius:8px;padding:0.7rem;margin-bottom:0.5rem;">'
                f'<span style="font-size:1.5rem;">{user.avatar_emoji}</span> '
                f'<strong style="color:#fff;">{user.name}</strong><br>'
                f'<span style="font-size:0.75rem;color:rgba(255,255,255,0.55);">{user.department} · {user.role.title()}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

        st.divider()

        # Navigation
        st.markdown("### Navigation")
        tab_labels_with_badges = []
        unread = unread_count()
        pend   = pending_approvals_count()
        viol   = policy_violations_count()

        for i, label in enumerate(_TABS):
            badge = ""
            if i == 0 and unread:   badge = f" 🔴{unread}"
            if i == 1 and viol:     badge = f" ⚠️{viol}"
            if i == 3 and pend:     badge = f" 🟡{pend}"
            if i == 4 and unread:   badge = f" 🔔{unread}"
            tab_labels_with_badges.append(label + badge)

        selected = st.radio(
            "Navigation",
            tab_labels_with_badges,
            index=st.session_state.get("active_tab", 0),
            label_visibility="collapsed",
            key="nav_radio",
        )
        active_idx = tab_labels_with_badges.index(selected)
        st.session_state.active_tab = active_idx

        st.divider()

        # Quick stats
        st.markdown("### 📊 Quick Stats")
        from core.data_store import total_spent_this_month
        s1, s2 = st.columns(2)
        s1.metric("Spent", f"${total_spent_this_month():,.0f}", delta=None)
        s2.metric("Alerts", str(unread))

        # Connection status
        st.divider()
        if st.session_state.get("ai_key_valid"):
            st.markdown(
                '<span style="color:#34D399;font-size:0.78rem;">● AI Assistant Connected</span>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<span style="color:#FCA5A5;font-size:0.78rem;">○ AI Offline — add key in Settings</span>',
                unsafe_allow_html=True,
            )

        st.markdown(
            '<p style="font-size:0.65rem;color:rgba(255,255,255,0.25);margin-top:1rem;text-align:center;">'
            'TravelPro v2.0 · Enterprise Edition</p>',
            unsafe_allow_html=True,
        )


# ── Tab switch helper (passed to child renderers) ─────────────────────────────
def _switch_to_ai_tab():
    st.session_state.active_tab = 4  # AI Assistant is index 4


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    _inject_css()

    # Init data store
    from core.data_store import init_data_store
    init_data_store()

    # Render sidebar (sets active_tab)
    _render_sidebar()

    # Render top header
    _render_header()

    # ── Route to active tab ───────────────────────────────────────────────────
    active = st.session_state.get("active_tab", 0)

    if active == 0:   # Dashboard
        from pages.tab_dashboard import render_dashboard
        render_dashboard(_switch_to_ai_tab)

    elif active == 1:  # Expenses
        from pages.tab_expenses import render_expenses
        render_expenses(_switch_to_ai_tab)

    elif active == 2:  # Trips
        from pages.tab_trips import render_trips
        render_trips(_switch_to_ai_tab)

    elif active == 3:  # Approvals
        from pages.tab_approvals import render_approvals
        render_approvals()

    elif active == 4:  # AI Assistant
        from pages.tab_ai_assistant import render_ai_assistant
        render_ai_assistant()

    elif active == 5:  # Reports
        from pages.tab_reports import render_reports
        render_reports()

    elif active == 6:  # Settings
        from pages.tab_settings import render_settings
        render_settings()


if __name__ == "__main__":
    main()
