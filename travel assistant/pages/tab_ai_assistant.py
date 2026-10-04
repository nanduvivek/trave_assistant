"""
pages/tab_ai_assistant.py — AI Travel Assistant tab for TravelPro.

Embeds the full existing agent.py / tools.py chat system.
Reads st.session_state.ai_preload_query to auto-send context
from events fired in other tabs (e.g., flight cancellation).
"""
from __future__ import annotations
import os
import time
import streamlit as st


# ── Helpers ───────────────────────────────────────────────────────────────────
def _build_agent():
    from agent import TravelAgentSystem
    st.session_state.ai_agent = TravelAgentSystem(
        api_key=st.session_state.ai_api_key,
        policy_text=st.session_state.ai_policy_text,
    )
    st.session_state.ai_suggestions = TravelAgentSystem.STARTER_QUESTIONS


def _process_message(user_text: str):
    user_text = user_text.strip()
    if not user_text:
        return

    st.session_state.ai_messages.append({"role": "user", "content": user_text})
    st.session_state.ai_msg_count = st.session_state.get("ai_msg_count", 0) + 1

    with st.spinner("🔍 Searching the web and checking policy …"):
        try:
            reply, suggestions = st.session_state.ai_agent.send(user_text)
        except Exception as exc:
            reply = f"⚠️ **Error:** {exc}\n\nPlease check your API key or try rephrasing."
            suggestions = []

    st.session_state.ai_messages.append({"role": "assistant", "content": reply})
    st.session_state.ai_suggestions = suggestions or [
        "What other options are available?",
        "Does this require manager approval?",
        "Can you prepare a justification letter?",
        "Show me the total trip cost breakdown.",
    ]


def render_ai_assistant():
    """Main render function for the AI Assistant tab."""

    # ── Handle preload query from other tabs ─────────────────────────────────
    preload = st.session_state.get("ai_preload_query")
    if preload and st.session_state.get("ai_key_valid"):
        st.session_state.ai_preload_query = None
        _process_message(preload)

    # ── Header ────────────────────────────────────────────────────────────────
    live_badge = (
        '<span style="background:rgba(16,185,129,0.15);color:#34D399;padding:0.15rem 0.6rem;'
        'border-radius:20px;font-size:0.75rem;font-weight:600;border:1px solid rgba(16,185,129,0.3);">● Live</span>'
        if st.session_state.get("ai_key_valid")
        else '<span style="background:rgba(239,68,68,0.1);color:#FCA5A5;padding:0.15rem 0.6rem;'
             'border-radius:20px;font-size:0.75rem;font-weight:600;border:1px solid rgba(239,68,68,0.2);">○ Disconnected</span>'
    )
    policy_badge = (
        '<span style="background:rgba(200,169,110,0.15);color:#C8A96E;padding:0.15rem 0.6rem;'
        'border-radius:20px;font-size:0.75rem;font-weight:600;border:1px solid rgba(200,169,110,0.3);">📄 Policy Active</span>'
        if st.session_state.get("policy_loaded")
        else '<span style="background:rgba(99,102,241,0.1);color:#A5B4FC;padding:0.15rem 0.6rem;'
             'border-radius:20px;font-size:0.75rem;font-weight:600;border:1px solid rgba(99,102,241,0.2);">📄 Default Policy</span>'
    )

    st.markdown(
        f"""<div style="background:linear-gradient(135deg,#0F2340 0%,#1E4080 100%);
        border-radius:14px;padding:1.2rem 1.8rem;margin-bottom:1.2rem;
        display:flex;align-items:center;gap:1rem;box-shadow:0 6px 24px rgba(15,35,64,0.18);">
        <span style="font-size:2.2rem;">🤖</span>
        <div>
          <p style="color:#fff;font-size:1.2rem;font-weight:700;margin:0;">T&amp;E AI Travel Assistant</p>
          <p style="color:rgba(200,169,110,0.9);font-size:0.8rem;margin:0;">
            Policy-Aware · Web Search · Direct Booking Links · Event-Driven Alerts
          </p>
        </div>
        <div style="margin-left:auto;display:flex;gap:0.5rem;flex-wrap:wrap;">
          {live_badge} {policy_badge}
        </div>
        </div>""",
        unsafe_allow_html=True,
    )

    # ── API key setup (if not connected) ─────────────────────────────────────
    if not st.session_state.get("ai_key_valid"):
        _render_api_setup()
        return

    # ── Welcome / starter ────────────────────────────────────────────────────
    if not st.session_state.ai_messages:
        _render_welcome()

    # ── Preload banner ───────────────────────────────────────────────────────
    # Show a banner if this tab was opened from an event notification
    if st.session_state.ai_messages and st.session_state.ai_messages[-1]["role"] == "user":
        last_user = st.session_state.ai_messages[-1]["content"]
        if any(kw in last_user.lower() for kw in ["cancelled", "delay", "expiring", "violation"]):
            st.info("🔔 **Event Alert:** The AI has been pre-loaded with your travel situation. See response below.")

    # ── Chat history ─────────────────────────────────────────────────────────
    for msg in st.session_state.ai_messages:
        role = msg["role"]
        with st.chat_message(role, avatar="🤖" if role == "assistant" else "👤"):
            st.markdown(msg["content"], unsafe_allow_html=False)

    # ── Suggestion pills ─────────────────────────────────────────────────────
    suggs = st.session_state.get("ai_suggestions", [])
    if suggs and st.session_state.ai_messages:
        st.markdown(
            '<p style="font-size:0.72rem;font-weight:600;text-transform:uppercase;'
            'letter-spacing:0.06em;color:#64748B;margin-bottom:0.4rem;">💬 Suggested follow-ups</p>',
            unsafe_allow_html=True,
        )
        scols = st.columns(min(len(suggs), 4))
        for i, (col, q) in enumerate(zip(scols, suggs)):
            with col:
                if st.button(q, key=f"ai_sugg_{i}_{st.session_state.get('ai_msg_count', 0)}"):
                    st.session_state.pending_msg = q
                    st.rerun()
    elif not st.session_state.ai_messages:
        _render_starters()

    # ── Pending message handler ───────────────────────────────────────────────
    if st.session_state.get("pending_msg"):
        msg = st.session_state.pending_msg
        st.session_state.pending_msg = None
        _process_message(msg)
        st.rerun()

    # ── Chat input ────────────────────────────────────────────────────────────
    user_input = st.chat_input(
        "Ask about flights, hotels, rental cars, budget … (e.g. 'Find me hotels in Austin Sept 18-22')"
    )
    if user_input:
        _process_message(user_input)
        st.rerun()

    # ── Sidebar controls for this tab ────────────────────────────────────────
    with st.sidebar:
        st.divider()
        st.markdown("#### 🤖 AI Assistant")
        st.markdown(
            f'<span style="font-size:0.8rem;color:#34D399;">● Connected to Gemini Flash</span>',
            unsafe_allow_html=True,
        )
        if st.session_state.ai_messages:
            if st.button("🔄 New Conversation", use_container_width=True, key="ai_new_conv"):
                st.session_state.ai_messages = []
                st.session_state.ai_msg_count = 0
                st.session_state.ai_agent = None
                _build_agent()
                st.rerun()

        # Quick launchers
        st.markdown("#### ⚡ Quick Launch")
        launchers = {
            "🏨 Hotel Cancelled": "My hotel reservation was just canceled and I arrive in 2 days. Help me find alternatives immediately!",
            "✈️ Flight Comparison": "I found a cheaper flight outside our travel system. Can you compare it against preferred options?",
            "🚗 Rental Car Queue": "I'm at the rental car counter and the line is 45+ minutes. What are my policy-approved alternatives?",
            "💰 Budget Expiring": "I have conference travel coming up. Which budget funds should I use first before they expire?",
            "📱 Mobile Check-In": "My hotel might have a long check-in line. How can I do mobile check-in to skip the queue?",
        }
        for label, prompt in launchers.items():
            if st.button(label, use_container_width=True, key=f"ql_{label}"):
                st.session_state.pending_msg = prompt
                st.rerun()


# ─── sub-renderers ────────────────────────────────────────────────────────────
def _render_api_setup():
    st.info(
        "👈 **Enter your Gemini API key in the Settings tab to activate the AI assistant.**\n\n"
        "Or enter it here quickly:",
        icon="🔑",
    )
    with st.form("quick_api_key"):
        key_input = st.text_input("Gemini API Key", type="password", placeholder="AIza…")
        submitted = st.form_submit_button("✔ Connect", type="primary")

    if submitted and key_input:
        from agent import TravelAgentSystem
        with st.spinner("Validating …"):
            ok, err = TravelAgentSystem.validate_api_key(key_input)
        if ok:
            st.session_state.ai_api_key  = key_input
            st.session_state.ai_key_valid = True
            _build_agent()
            st.success("✅ Connected!")
            time.sleep(0.5)
            st.rerun()
        else:
            st.error(f"Invalid key: {err}")

    # Feature showcase
    st.markdown("---")
    st.markdown("### What the AI Assistant can do")
    cols = st.columns(3)
    features = [
        ("🏨", "Hotel Rebooking",      "Finds alternatives instantly when your hotel is cancelled."),
        ("✈️", "Flight Comparison",    "Compares total trip cost across all airline tiers."),
        ("🚗", "Rental Car Options",   "Surfaces Enterprise partner counters to avoid long queues."),
        ("💰", "Budget Planning",      "Identifies expiring funds and recommends optimal allocation."),
        ("📱", "Mobile Check-In",      "Guides you through digital check-in to skip front-desk queues."),
        ("📋", "Exception Letters",    "Generates approval letters and justification requests."),
    ]
    for idx, (icon, title, desc) in enumerate(features):
        with cols[idx % 3]:
            st.markdown(
                f'<div style="background:#fff;border-radius:10px;padding:1rem;'
                f'border:1px solid #E2E8F0;margin-bottom:0.75rem;">'
                f'<div style="font-size:1.5rem;margin-bottom:0.3rem;">{icon}</div>'
                f'<strong style="color:#0F2340;">{title}</strong>'
                f'<p style="color:#64748B;font-size:0.82rem;margin-top:0.2rem;margin-bottom:0;">{desc}</p>'
                f'</div>',
                unsafe_allow_html=True,
            )


def _render_welcome():
    st.markdown(
        """<div style="background:linear-gradient(135deg,#EFF6FF 0%,#F0FDF4 100%);
        border:1px solid #BFDBFE;border-radius:12px;padding:1.2rem 1.5rem;margin-bottom:1rem;">
        <h3 style="color:#0F2340;margin-top:0;">👋 Welcome to your T&amp;E AI Assistant</h3>
        <p style="color:#475569;margin-bottom:0.3rem;font-size:0.9rem;">
          I handle all your travel research so you don't have to open multiple tabs or read policy documents.
        </p>
        <p style="color:#475569;margin-bottom:0.3rem;font-size:0.9rem;">
          I can help with <strong>hotel rebooking, flight comparisons, rental car options, budget allocation,
          and mobile check-in</strong> — with real-time web search and direct booking links, all policy-compliant.
        </p>
        <p style="color:#94A3B8;font-size:0.78rem;margin-top:0.5rem;margin-bottom:0;">
          💡 <em>Events from Trips tab automatically pre-load my context — try simulating a flight cancellation!</em>
        </p>
        </div>""",
        unsafe_allow_html=True,
    )


def _render_starters():
    from agent import TravelAgentSystem
    starters = TravelAgentSystem.STARTER_QUESTIONS
    st.markdown(
        '<p style="font-size:0.72rem;font-weight:600;text-transform:uppercase;'
        'letter-spacing:0.06em;color:#64748B;margin-bottom:0.4rem;">🚀 Try one of these scenarios</p>',
        unsafe_allow_html=True,
    )
    scols = st.columns(len(starters))
    for i, (col, q) in enumerate(zip(scols, starters)):
        with col:
            if st.button(q, key=f"start_{i}"):
                st.session_state.pending_msg = q
                st.rerun()
