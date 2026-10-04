# Travel & Expense Hyperautomation Chatbot — Implementation Plan

## Overview

A full-featured, single-page HTML/CSS/JS application (no build tools required) that simulates an intelligent travel & expense chatbot with five use cases, proactive notifications, policy-aware guidance, budget tracking, justification-letter generation, human-in-the-loop approval routing, and a complete audit log.

All backend data (hotels, flights, budgets, policies, vendors, etc.) is **simulated in-memory** via a JavaScript data layer, making the prototype fully self-contained and runnable without any server.

---

## Architecture

```
index.html          ← Shell, navigation sidebar, notification tray
css/
  main.css          ← Design system tokens, layout, responsive grid
  components.css    ← Cards, buttons, badges, chat bubbles, modals
js/
  data/
    simData.js      ← All simulated data (hotels, flights, vendors, budgets, policies, users)
  engine/
    policyEngine.js ← Policy evaluation, compliance checks
    budgetEngine.js ← Budget retrieval, allocation, expiration logic
    aiEngine.js     ← Four-step hyperautomation logic (Detect → Evaluate → Mode → Execute)
    auditLog.js     ← Immutable append-only audit record
  ui/
    chatUI.js       ← Chat panel renderer, message factory, typing indicator
    notificationUI.js ← Proactive alert banners with urgency levels
    dashboardUI.js  ← Use-case panels, option comparison tables
    letterUI.js     ← Justification / approval letter generator and renderer
    prefsUI.js      ← Notification preference controls
  usecases/
    uc1_hotel.js    ← Hotel Cancellation & Late Rebooking
    uc2_flight.js   ← Lower-Cost Flight Selection
    uc3_rental.js   ← Rental Car Pickup Delays & Partner Vendors
    uc4_budget.js   ← Budget Allocation & Funding Deadlines
    uc5_checkin.js  ← Hotel Check-In Delays
  app.js            ← Bootstrap, router, use-case orchestrator
```

---

## Key Design Decisions

> [!IMPORTANT]
> **Single HTML file vs multi-file**: We will use **multiple linked files** (HTML + CSS modules + JS modules) all served from the same directory. This keeps each concern isolated and maintainable. The root `index.html` is the only entry point.

> [!IMPORTANT]
> **No framework, no build step**: Pure HTML5 + Vanilla CSS + ES6 modules (`type="module"`). Works by simply opening `index.html` in a browser (or via VS Code Live Server).

> [!NOTE]
> **Partner vendor data**: Use Case 3 reads partner vendors from `simData.js → vendorMaster` — they are **never hard-coded** in `uc3_rental.js`.

---

## Proposed Changes

### Core Shell

#### [NEW] [index.html](file:///c:/Users/Rakesh/OneDrive/Documents/travel%20assistant/index.html)
- Top navigation bar with user avatar, notification bell, and urgency badge
- Left sidebar: 5 use-case tabs + Audit Log + Preferences
- Main content area: active use-case panel + proactive alert banner slot
- Right panel: persistent chat window (collapsible)
- Footer: confidence meter + mode indicator (Guide / Recommend / Act / Defer)

---

### Styling

#### [NEW] [css/main.css](file:///c:/Users/Rakesh/OneDrive/Documents/travel%20assistant/css/main.css)
- HSL design tokens (colors, spacing, radius, shadow)
- CSS Grid layout for three-column shell
- Responsive breakpoints (mobile collapses chat to bottom sheet)
- Urgency color semantics: critical=red, warning=amber, info=blue, success=green

#### [NEW] [css/components.css](file:///c:/Users/Rakesh/OneDrive/Documents/travel%20assistant/css/components.css)
- Chat bubbles (user vs. system, with avatars)
- Mode badge (Guide 🗺️ / Recommend ⭐ / Act ⚡ / Defer 👤)
- Confidence bar (0–100 %)
- Comparison table (hotels, flights, budget sources)
- Action button strip
- Notification banner (slide-in from top)
- Modal overlay (approval request, letter preview)
- Audit log entry row

---

### Data Layer

#### [NEW] [js/data/simData.js](file:///c:/Users/Rakesh/OneDrive/Documents/travel%20assistant/js/data/simData.js)
Exports frozen simulation objects:
- `traveler` — profile, role, preferences, notification level
- `travelRequest` — trip metadata, dates, destination
- `hotels` — 5 hotel options with rate, distance, safety score, availability, policy-compliance flag
- `flights` — system flights + traveler-submitted alternative (with full cost breakdown)
- `vendorMaster` — rental vendor list with `isApprovedPartner`, corporate rate, counter location
- `budgets` — 4 funding sources with balance, expiration, eligible categories, owner
- `policies` — lodging limit, flight policy, rental policy, per-diem rates, approval thresholds
- `hotelReservation` — current booking, check-in status, digital-key availability
- `auditEntries` — starts empty; append-only

---

### Business Logic Engines

#### [NEW] [js/engine/policyEngine.js](file:///c:/Users/Rakesh/OneDrive/Documents/travel%20assistant/js/engine/policyEngine.js)
- `checkLodgingPolicy(hotel)` → `{compliant, overage, requiresException}`
- `checkFlightPolicy(flight)` → `{compliant, altAirportAllowed, requiresApproval}`
- `checkRentalPolicy(vendor)` → `{approved, partnerAllowed, rateCompliant}`
- `checkBudgetEligibility(budgetCode, expenseType)` → `{eligible, restrictions}`

#### [NEW] [js/engine/budgetEngine.js](file:///c:/Users/Rakesh/OneDrive/Documents/travel%20assistant/js/engine/budgetEngine.js)
- `getAvailableFunds(travelerId)` → ranked list of funding sources
- `recommendAllocation(tripCost, funds)` → split proposal
- `getDaysUntilExpiry(fund)` → integer
- `commitFunds(allocationProposal)` → updates simulated balance

#### [NEW] [js/engine/aiEngine.js](file:///c:/Users/Rakesh/OneDrive/Documents/travel%20assistant/js/engine/aiEngine.js)
Implements four-step logic for each use case:
1. **Detect** — collects context from simData + use-case inputs
2. **Evaluate** — calls policyEngine + budgetEngine, scores options, sets confidence
3. **SelectMode** — returns `'guide' | 'recommend' | 'act' | 'defer'`
4. **Execute** — returns structured response object `{mode, message, options, confidence, approverRequired, auditEntry}`

#### [NEW] [js/engine/auditLog.js](file:///c:/Users/Rakesh/OneDrive/Documents/travel%20assistant/js/engine/auditLog.js)
- `append(entry)` — timestamps and stores every recommendation, action, approval, override
- `getAll()` — returns full log
- `exportCSV()` — downloads audit CSV

---

### UI Components

#### [NEW] [js/ui/chatUI.js](file:///c:/Users/Rakesh/OneDrive/Documents/travel%20assistant/js/ui/chatUI.js)
- `addSystemMessage(text, mode, confidence)`
- `addUserMessage(text)`
- `addOptionCard(options[])` — renders comparison table inside chat
- `addActionStrip(buttons[])` — renders action buttons
- `showTypingIndicator()` / `hideTypingIndicator()`

#### [NEW] [js/ui/notificationUI.js](file:///c:/Users/Rakesh/OneDrive/Documents/travel%20assistant/js/ui/notificationUI.js)
- `showAlert({title, body, urgency, buttons})` — slides in from top
- `showPermissionPrompt(useCase)` — for UC5 preference gate
- `dismissAlert(id)`

#### [NEW] [js/ui/dashboardUI.js](file:///c:/Users/Rakesh/OneDrive/Documents/travel%20assistant/js/ui/dashboardUI.js)
- Renders use-case-specific detail panels (hotel list, flight comparison, budget table)
- Policy compliance badges per option
- Budget impact preview

#### [NEW] [js/ui/letterUI.js](file:///c:/Users/Rakesh/OneDrive/Documents/travel%20assistant/js/ui/letterUI.js)
- `generateExceptionLetter(context)` → renders formatted letter in modal
- `generateApprovalRequest(context)` → approval routing form
- `generateJustificationLetter(context)` → flight/budget justification

#### [NEW] [js/ui/prefsUI.js](file:///c:/Users/Rakesh/OneDrive/Documents/travel%20assistant/js/ui/prefsUI.js)
- UC5 notification preference selector (4 levels)
- Persists preference to `localStorage`

---

### Use Case Modules

#### [NEW] [js/usecases/uc1_hotel.js](file:///c:/Users/Rakesh/OneDrive/Documents/travel%20assistant/js/usecases/uc1_hotel.js)
Hotel cancellation detection → proactive alert → chat Q&A → compare options → exception letter → approval routing

#### [NEW] [js/usecases/uc2_flight.js](file:///c:/Users/Rakesh/OneDrive/Documents/travel%20assistant/js/usecases/uc2_flight.js)
Traveler flight submission → full cost comparison (baggage, transport, hotel nights) → policy check → justification letter

#### [NEW] [js/usecases/uc3_rental.js](file:///c:/Users/Rakesh/OneDrive/Documents/travel%20assistant/js/usecases/uc3_rental.js)
Arrival monitoring → pickup delay estimate → partner vendor lookup from vendorMaster → comparison → reservation transfer

#### [NEW] [js/usecases/uc4_budget.js](file:///c:/Users/Rakesh/OneDrive/Documents/travel%20assistant/js/usecases/uc4_budget.js)
Funding retrieval → eligibility check → expiry ranking → split allocation → budget owner routing

#### [NEW] [js/usecases/uc5_checkin.js](file:///c:/Users/Rakesh/OneDrive/Documents/travel%20assistant/js/usecases/uc5_checkin.js)
Preference gate → delay prediction → mobile check-in flow → loyalty pre-fill → escalation

---

### App Bootstrap

#### [NEW] [js/app.js](file:///c:/Users/Rakesh/OneDrive/Documents/travel%20assistant/js/app.js)
- Tab router connecting sidebar to use-case modules
- Notification bell driven by simulated event queue
- Global override handler (user can always correct or escalate)

---

## UI/UX Summary

| Element | Detail |
|---|---|
| Layout | 3-column grid: sidebar / main / chat |
| Theme | Deep navy + warm sand accent; HSL tokens |
| Font | Inter (Google Fonts) |
| Urgency colors | Critical=red, Warning=amber, Info=blue, OK=green |
| Chat bubbles | Left=system (with bot avatar), Right=user |
| Mode badge | Color-coded pill on every system message |
| Confidence | Animated progress bar (0–100 %) |
| Comparison table | Sticky header, policy badge per row, highlighted recommendation |
| Letter modal | Print-ready formatted letter with Download button |
| Audit log | Sortable table, CSV export |

---

## Verification Plan

### Manual Verification
1. Open `index.html` in Chrome/Edge — all 5 use-case tabs load
2. UC1: Urgent hotel cancellation banner appears on load; chat Q&A works; exception letter modal opens
3. UC2: Flight entry form accepts input; full cost table renders; justification letter generates
4. UC3: Partner vendor list comes from `vendorMaster`, not hard-coded; recommendation renders
5. UC4: Budget table shows expiry dates; allocation splits across two codes; reminder fires
6. UC5: Notification preference selector gates alerts; mobile check-in flow completes
7. Audit log tab shows all recorded interactions with timestamps
8. Responsive layout works at 375 px (mobile) and 1440 px (desktop)

---

## Open Questions

> [!IMPORTANT]
> **1. Application language**: Requirements say "Python application" in the final section. Should the prototype be a **Python + Flask web app** served locally, or is a **standalone HTML/JS** (open directly in browser, no server needed) acceptable? The plan above uses HTML/JS for maximum portability.

> [!IMPORTANT]
> **2. AI/LLM integration**: Should the chatbot responses use a **real LLM API** (e.g., Gemini API) for natural language, or should they use **rule-based scripted responses** keyed to recognized intents? Rule-based is shown in this plan.

> [!NOTE]
> **3. Data persistence**: Should user preferences, audit logs, and reservations persist across browser sessions (`localStorage`) or reset on each page load?

> [!NOTE]
> **4. Approval workflow**: Should the "Send for Approval" action simulate sending an email/notification, or open an in-app approver view (a second screen or modal)?
