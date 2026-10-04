"""
pages/tab_trips.py — Trip management tab with event simulator for TravelPro.
"""
from __future__ import annotations
import streamlit as st
from datetime import date

from core.notifications import fire_event
from core.models import Trip


_STATUS_STYLE = {
    "upcoming":  ("#8B5CF6", "#F5F3FF", "🔵 Upcoming"),
    "active":    ("#10B981", "#F0FDF4", "🟢 Active"),
    "completed": ("#64748B", "#F8FAFC", "⚫ Completed"),
    "cancelled": ("#EF4444", "#FEF2F2", "🔴 Cancelled"),
}


def render_trips(switch_to_ai_tab):
    st.markdown("### ✈️ Trip Management")

    # Tabs: Upcoming/Active | Completed | Event Simulator
    tab_active, tab_history, tab_simulator = st.tabs(["📍 Active & Upcoming", "📁 History", "⚡ Event Simulator"])

    trips = st.session_state.trips

    with tab_active:
        active_trips = [t for t in trips if t.status in ("upcoming", "active")]
        _render_trip_cards(active_trips, switch_to_ai_tab)

    with tab_history:
        past_trips = [t for t in trips if t.status in ("completed", "cancelled")]
        _render_trip_cards(past_trips, switch_to_ai_tab)

    with tab_simulator:
        _render_event_simulator(switch_to_ai_tab)


def _render_trip_cards(trips_list, switch_to_ai_tab):
    if not trips_list:
        st.info("No trips in this category.")
        return

    for trip in trips_list:
        color, bg, status_label = _STATUS_STYLE.get(trip.status, ("#64748B", "#F8FAFC", trip.status.title()))
        booked_cost = trip.total_booking_cost
        variance    = booked_cost - trip.budget_allocated

        with st.container():
            st.markdown(
                f"""<div style="background:#fff;border:1px solid #E2E8F0;border-radius:14px;
                padding:1.2rem 1.5rem;margin-bottom:1rem;border-left:4px solid {color};">
                <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:0.5rem;">
                  <div>
                    <span style="font-size:1.8rem;">{trip.icon}</span>
                    <strong style="font-size:1.1rem;color:#0F2340;margin-left:0.5rem;">{trip.name}</strong>
                    <span style="color:{color};background:{bg};padding:0.15rem 0.6rem;
                    border-radius:20px;font-size:0.75rem;font-weight:600;margin-left:0.5rem;">{status_label}</span>
                  </div>
                  <div style="text-align:right;">
                    <span style="font-size:0.85rem;color:#64748B;">{trip.destination}</span>
                  </div>
                </div>
                <div style="margin-top:0.7rem;display:flex;gap:2rem;flex-wrap:wrap;">
                  <span style="color:#475569;font-size:0.85rem;">📅 {trip.start_date.strftime('%b %d')} – {trip.end_date.strftime('%b %d, %Y')}</span>
                  <span style="color:#475569;font-size:0.85rem;">🌙 {trip.nights} nights</span>
                  <span style="color:#475569;font-size:0.85rem;">🎯 {trip.purpose}</span>
                  <span style="color:#475569;font-size:0.85rem;">💳 {trip.budget_code}</span>
                </div>
                </div>""",
                unsafe_allow_html=True,
            )

            # Itinerary expander
            with st.expander(f"📋 Itinerary & Bookings — {trip.name}"):
                it1, it2, it3 = st.columns(3)

                with it1:
                    st.markdown("**✈️ Flights**")
                    if trip.flights:
                        for f in trip.flights:
                            s_color = "#EF4444" if f.status == "cancelled" else "#10B981" if f.status == "completed" else "#3B82F6"
                            st.markdown(
                                f'<div style="background:#F8FAFC;border-radius:8px;padding:0.6rem;margin-bottom:0.4rem;">'
                                f'<strong>{f.airline} {f.flight_number}</strong> '
                                f'<span style="color:{s_color};font-size:0.75rem;font-weight:600;">● {f.status.upper()}</span><br>'
                                f'{f.origin} → {f.destination}<br>'
                                f'<span style="color:#64748B;font-size:0.78rem;">'
                                f'{f.departure.strftime("%b %d, %H:%M")} · ${f.cost:.0f} · {f.confirmation}</span>'
                                f'</div>',
                                unsafe_allow_html=True,
                            )
                    else:
                        st.caption("No flights booked.")

                with it2:
                    st.markdown("**🏨 Hotels**")
                    if trip.hotels:
                        for h in trip.hotels:
                            s_color = "#EF4444" if h.status == "cancelled" else "#10B981" if h.status == "completed" else "#3B82F6"
                            policy_tag = " ✅" if h.policy_compliant else " ⚠️"
                            st.markdown(
                                f'<div style="background:#F8FAFC;border-radius:8px;padding:0.6rem;margin-bottom:0.4rem;">'
                                f'<strong>{h.name}{policy_tag}</strong> '
                                f'<span style="color:{s_color};font-size:0.75rem;font-weight:600;">● {h.status.upper()}</span><br>'
                                f'{h.city}<br>'
                                f'<span style="color:#64748B;font-size:0.78rem;">'
                                f'{h.check_in.strftime("%b %d")} – {h.check_out.strftime("%b %d")} '
                                f'· ${h.nightly_rate:.0f}/night · ${h.total_cost:.0f} total</span>'
                                f'</div>',
                                unsafe_allow_html=True,
                            )
                    else:
                        st.caption("No hotels booked.")

                with it3:
                    st.markdown("**🚗 Rental Cars**")
                    if trip.rental_cars:
                        for rc in trip.rental_cars:
                            s_color = "#10B981" if rc.status == "confirmed" else "#EF4444"
                            st.markdown(
                                f'<div style="background:#F8FAFC;border-radius:8px;padding:0.6rem;margin-bottom:0.4rem;">'
                                f'<strong>{rc.vendor}</strong> '
                                f'<span style="color:{s_color};font-size:0.75rem;font-weight:600;">● {rc.status.upper()}</span><br>'
                                f'{rc.vehicle_class} · {rc.pickup_location}<br>'
                                f'<span style="color:#64748B;font-size:0.78rem;">'
                                f'{rc.pickup_date.strftime("%b %d")} – {rc.return_date.strftime("%b %d")} '
                                f'· ${rc.daily_rate:.0f}/day · ${rc.total_cost:.0f} total</span>'
                                f'</div>',
                                unsafe_allow_html=True,
                            )
                    else:
                        st.caption("No rental cars booked.")

                # Budget vs actual bar
                st.divider()
                b1, b2, b3 = st.columns(3)
                b1.metric("Budget Allocated", f"${trip.budget_allocated:,.0f}")
                b2.metric("Bookings Total",   f"${booked_cost:,.0f}")
                b3.metric("Variance",         f"${abs(variance):,.0f}", delta=f"{'Over' if variance > 0 else 'Under'} budget",
                          delta_color="inverse" if variance > 0 else "normal")

            st.markdown("")  # spacing


def _render_event_simulator(switch_to_ai_tab):
    """Interactive panel to simulate real travel disruption events."""
    st.markdown("#### ⚡ Travel Event Simulator")
    st.info(
        "💡 Simulate real-world travel disruptions. Each event fires a proactive AI notification "
        "and pre-loads the AI Assistant with the exact context to get instant help."
    )

    trips = [t for t in st.session_state.trips if t.status in ("upcoming", "active")]
    if not trips:
        st.warning("No active or upcoming trips to simulate events for.")
        return

    trip_opts = {t.id: t.name for t in trips}
    selected_trip_id = st.selectbox("Select Trip", options=list(trip_opts.keys()),
                                    format_func=lambda x: trip_opts[x], key="sim_trip")
    selected_trip = next(t for t in trips if t.id == selected_trip_id)

    st.divider()
    st.markdown("**Choose an event to simulate:**")

    ev_col1, ev_col2 = st.columns(2)

    with ev_col1:
        # Flight Cancelled
        st.markdown(
            '<div style="background:#FEF2F2;border-radius:10px;padding:1rem;border:1px solid #FECACA;margin-bottom:0.75rem;">',
            unsafe_allow_html=True,
        )
        st.markdown("🔴 **Flight Cancellation**")
        st.caption("Simulates airline cancelling your outbound flight")
        if selected_trip.flights and st.button("🔴 Simulate Flight Cancelled", key="sim_flight_cancel", use_container_width=True):
            fl = selected_trip.flights[0]
            fl.status = "cancelled"
            notif = fire_event("FLIGHT_CANCELLED", {
                "flight_number": fl.flight_number,
                "airline": fl.airline,
                "route": f"{fl.origin}→{fl.destination}",
                "trip_id": selected_trip.id,
            })
            if notif:
                st.success("✅ Event fired! Notification created.")
                _open_ai_with_query(notif, switch_to_ai_tab)
        elif not selected_trip.flights:
            st.caption("No flights on this trip.")
        st.markdown("</div>", unsafe_allow_html=True)

        # Hotel Cancelled
        st.markdown(
            '<div style="background:#FEF2F2;border-radius:10px;padding:1rem;border:1px solid #FECACA;margin-bottom:0.75rem;">',
            unsafe_allow_html=True,
        )
        st.markdown("🔴 **Hotel Cancellation**")
        st.caption("Simulates hotel cancelling your reservation last-minute")
        if selected_trip.hotels and st.button("🔴 Simulate Hotel Cancelled", key="sim_hotel_cancel", use_container_width=True):
            ho = selected_trip.hotels[0]
            ho.status = "cancelled"
            notif = fire_event("HOTEL_CANCELLED", {
                "hotel": ho.name,
                "city": ho.city,
                "check_in": ho.check_in.strftime("%b %d"),
                "check_out": ho.check_out.strftime("%b %d"),
                "trip_id": selected_trip.id,
            })
            if notif:
                st.success("✅ Event fired! Notification created.")
                _open_ai_with_query(notif, switch_to_ai_tab)
        elif not selected_trip.hotels:
            st.caption("No hotels on this trip.")
        st.markdown("</div>", unsafe_allow_html=True)

    with ev_col2:
        # Rental Car Delay
        st.markdown(
            '<div style="background:#FFFBEB;border-radius:10px;padding:1rem;border:1px solid #FDE68A;margin-bottom:0.75rem;">',
            unsafe_allow_html=True,
        )
        st.markdown("⚠️ **Rental Car Long Queue**")
        st.caption("Simulates long wait at preferred rental counter")
        if selected_trip.rental_cars and st.button("⚠️ Simulate Car Queue", key="sim_car_delay", use_container_width=True):
            rc = selected_trip.rental_cars[0]
            notif = fire_event("RENTAL_CAR_DELAY", {
                "location": rc.pickup_location,
                "wait_time": "45–60 minutes",
                "trip_id": selected_trip.id,
            })
            if notif:
                st.success("✅ Event fired! Notification created.")
                _open_ai_with_query(notif, switch_to_ai_tab)
        elif not selected_trip.rental_cars:
            st.caption("No rental cars on this trip.")
        st.markdown("</div>", unsafe_allow_html=True)

        # Flight Delay
        st.markdown(
            '<div style="background:#FFFBEB;border-radius:10px;padding:1rem;border:1px solid #FDE68A;margin-bottom:0.75rem;">',
            unsafe_allow_html=True,
        )
        st.markdown("⚠️ **Flight Delay**")
        st.caption("Simulates a significant departure delay")
        delay_val = st.selectbox("Delay duration", ["2 hours", "4 hours", "6+ hours"], key="sim_delay_val")
        if selected_trip.flights and st.button("⚠️ Simulate Flight Delayed", key="sim_flight_delay", use_container_width=True):
            fl = selected_trip.flights[0]
            fl.status = "delayed"
            from datetime import timedelta
            hours = int(delay_val.split()[0].replace("+", ""))
            new_dep = fl.departure + timedelta(hours=hours)
            notif = fire_event("FLIGHT_DELAYED", {
                "flight_number": fl.flight_number,
                "airline": fl.airline,
                "delay": delay_val,
                "new_time": new_dep.strftime("%H:%M"),
                "trip_id": selected_trip.id,
            })
            if notif:
                st.success("✅ Event fired! Notification created.")
                _open_ai_with_query(notif, switch_to_ai_tab)
        elif not selected_trip.flights:
            st.caption("No flights on this trip.")
        st.markdown("</div>", unsafe_allow_html=True)

    # Budget Expiry alert
    st.divider()
    st.markdown("**💰 Budget Events**")
    budget_col1, budget_col2 = st.columns(2)
    with budget_col1:
        if st.button("⚠️ Simulate Budget Expiry Warning", key="sim_budget_exp", use_container_width=True):
            b = st.session_state.budgets[2]  # Training fund (expiring soon)
            notif = fire_event("BUDGET_EXPIRING", {
                "budget_name": b.name,
                "budget_code": b.code,
                "amount_remaining": f"${b.available:,.0f}",
                "days": str(b.days_until_expiry),
            })
            if notif:
                st.success("✅ Budget expiry alert fired!")
                _open_ai_with_query(notif, switch_to_ai_tab)


def _open_ai_with_query(notif, switch_to_ai_tab):
    if notif.ai_query:
        st.session_state.ai_preload_query = notif.ai_query
        if st.button("🤖 Open AI Assistant Now →", key=f"open_ai_{notif.id}", type="primary"):
            switch_to_ai_tab()
            st.rerun()
