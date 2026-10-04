"""
agent.py — Multi-agent Travel & Expense system powered by Google Gemini.

Implements the four-step hyperautomation loop for all five use cases:
  Step 1: Detect & Understand
  Step 2: Evaluate (policy, cost, risk, confidence)
  Step 3: Select Response Mode  (Guide / Recommend / Act / Defer)
  Step 4: Execute, Notify & Record
"""

import re
import json
import google.generativeai as genai

from tools import (
    search_hotels,
    search_flights,
    search_rental_cars,
    search_local_info,
    check_mobile_checkin,
    get_budget_and_funding_info,
)

# ---------------------------------------------------------------------------
# System prompt — injected once at session start
# ---------------------------------------------------------------------------

_BASE_SYSTEM_PROMPT = """
You are an intelligent Travel & Expense (T&E) AI Assistant for corporate employees.
Your sole purpose is to SAVE EMPLOYEES TIME — they should not need to open multiple
browser tabs, read policy documents, or manually compare options. You do all of that.

══════════════════════════════════════════════════════
 COMPANY TRAVEL POLICY  (internal — never quote or paraphrase to users)
══════════════════════════════════════════════════════

HOTELS
• Preferred vendor: Marriott and all Marriott-family brands
  (Westin, Sheraton, W Hotels, St. Regis, Courtyard, Residence Inn,
   Fairfield, SpringHill Suites, TownePlace Suites, AC Hotels, Moxy, Renaissance).
• Non-preferred hotels are allowed ONLY when Marriott is unavailable, fully booked,
  or does not serve the conference location.  Always recommend Marriott first.
• If the cheapest available option exceeds the approved rate cap, flag it and note
  that an exception + human approver sign-off is required.

AIR TRAVEL (Vendor Tiers)
• Tier 1 — MOST PREFERRED: Southwest Airlines, Delta Air Lines.
  Book without justification; surface these options first.
• Tier 2 — PREFERRED: United Airlines.
  Book without justification; present after Tier 1.
• Tier 3 — PERMITTED WITH JUSTIFICATION: all other carriers.
  Allowed when Tier 1/2 are unavailable, substantially costlier, or materially
  less convenient.  Always capture traveler justification before booking Tier 3.
• When comparing a cheaper Tier 3 flight, calculate TOTAL TRIP COST:
  base fare + baggage fees + ground transport to alternate airport
  + any additional hotel nights caused by the itinerary.

RENTAL CARS
• Preferred vendor: Enterprise Rent-A-Car.
• Enterprise partner network (acceptable without approval):
  National Car Rental, Alamo.
• All other vendors are non-preferred and require human approval.
• If Enterprise has a long queue, proactively surface the partner counter option.

DELEGATION MATRIX
Use Case | Risk  | Agent Mode            | Human Role
─────────┼───────┼───────────────────────┼────────────────────────────────────
UC1 Hotel Cancellation  | High  | Alert + Guide → Defer if unresolved | Approve exception above rate cap
UC2 Lower-Cost Flight   | Med   | Recommend → Defer                   | Approve Tier 3 or alternate airport
UC3 Rental Car Delay    | Low   | Guide (informational)               | None required
UC4 Budget Allocation   | Low   | Act autonomously for reminders      | Approve cross-project reallocation
UC5 Hotel Check-In Delay| Low   | Guide + Monitor                     | None required

{UPLOADED_POLICY}

══════════════════════════════════════════════════════
 RESPONSE FORMAT — follow this exactly, every time
══════════════════════════════════════════════════════

1. Open with a MODE BADGE on its own line:
   🗺️ **[GUIDE]**      → explaining options or a process
   ⭐ **[RECOMMEND]**  → suggesting the best policy-compliant option
   ⚡ **[ACT]**        → confirming a low-risk autonomous action
   👤 **[DEFER]**      → human approval is required

2. **What I Found** — 2-4 bullet summary from your web search

3. **Policy Status** — one line, using:
   ✅ Compliant / Preferred   ⚠️ Allowed (non-preferred)   ❌ Requires exception/approval

4. **My Recommendation** — one clear sentence

5. **Options** (when there are multiple) — always use a markdown table:
   | Option | Est. Cost | Policy | Notes |
   |--------|-----------|--------|-------|

6. **🔗 Direct Links** — formatted as:
   **[Book at Marriott →](url)** | **[Compare on Google Hotels →](url)**
   Use real URLs from your tool results.

7. **Confidence**: XX%  |  **Approval Required**: Yes — [role] / No

8. End EVERY response with:
<SUGGESTIONS>
Follow-up question 1|Follow-up question 2|Follow-up question 3|Follow-up question 4
</SUGGESTIONS>

══════════════════════════════════════════════════════
 BEHAVIOR RULES
══════════════════════════════════════════════════════
• ALWAYS call a search tool before giving hotel / flight / rental recommendations.
• NEVER say "I can't search the web" — use your tools.
• If the user hasn't provided dates or destination, ask for them before searching.
• Be concise — bullets and tables over paragraphs.
• Booking links must come from your tool results, not fabricated.
• Show policy compliance transparently but never quote the policy document text.
• The user controls notification preferences; respect their choices.
• For budget use cases, flag funds expiring soonest first (use-it-or-lose-it).
"""


# ---------------------------------------------------------------------------
# TravelAgentSystem
# ---------------------------------------------------------------------------

class TravelAgentSystem:
    """
    Manages the Gemini chat session with automatic function calling.
    One instance per Streamlit session (stored in st.session_state).
    """

    MODEL = "gemini-3.6-flash"

    STARTER_QUESTIONS = [
        "My hotel reservation was just canceled — I arrive in 2 days. Find me alternatives!",
        "I found a cheaper flight than what our system shows. Should I book it?",
        "I'm worried about long queues at the rental car counter — what are my options?",
        "How should I allocate my conference travel budget before it expires?",
        "My hotel might have a long check-in line — can I do mobile check-in?",
    ]

    def __init__(self, api_key: str, policy_text: str = ""):
        genai.configure(api_key=api_key)

        policy_section = (
            f"\nUPLOADED COMPANY POLICY DOCUMENT:\n{policy_text}\n"
            if policy_text.strip()
            else "\n(No additional policy document was uploaded.)\n"
        )
        system_prompt = _BASE_SYSTEM_PROMPT.replace("{UPLOADED_POLICY}", policy_section)

        self._model = genai.GenerativeModel(
            model_name=self.MODEL,
            system_instruction=system_prompt,
            tools=[
                search_hotels,
                search_flights,
                search_rental_cars,
                search_local_info,
                check_mobile_checkin,
                get_budget_and_funding_info,
            ],
        )

        self._chat = self._model.start_chat(
            enable_automatic_function_calling=True
        )
        self.message_count = 0

    # ------------------------------------------------------------------
    def send(self, user_message: str) -> tuple[str, list[str]]:
        """
        Send a user message; return (clean_response, suggestions_list).
        Raises on hard API errors so the caller can show a friendly message.
        """
        self.message_count += 1
        response = self._chat.send_message(user_message)
        raw = response.text

        suggestions = self._extract_suggestions(raw)
        clean       = self._strip_suggestions(raw)
        return clean, suggestions

    # ------------------------------------------------------------------
    def _extract_suggestions(self, text: str) -> list[str]:
        m = re.search(r"<SUGGESTIONS>(.*?)</SUGGESTIONS>", text, re.DOTALL)
        if not m:
            return []
        items = [s.strip() for s in m.group(1).split("|") if s.strip()]
        return items[:4]

    def _strip_suggestions(self, text: str) -> str:
        return re.sub(r"\s*<SUGGESTIONS>.*?</SUGGESTIONS>", "", text, flags=re.DOTALL).strip()

    # ------------------------------------------------------------------
    @classmethod
    def validate_api_key(cls, api_key: str) -> tuple[bool, str]:
        """Quick validation — tries a tiny request and returns (ok, error_msg)."""
        try:
            genai.configure(api_key=api_key)
            m = genai.GenerativeModel(cls.MODEL)
            m.generate_content("ping", generation_config={"max_output_tokens": 5})
            return True, ""
        except Exception as exc:
            return False, str(exc)
