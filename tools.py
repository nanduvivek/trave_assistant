"""
tools.py — Web search and booking link tools for the T&E Travel Agent.

All search results come from DuckDuckGo (free, no API key required).
Booking links are generated as deep links to real booking platforms.
"""

import json
import urllib.parse
import re

try:
    from duckduckgo_search import DDGS
    DDGS_AVAILABLE = True
except ImportError:
    DDGS_AVAILABLE = False


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _ddg_search(query: str, max_results: int = 6) -> list[dict]:
    """Run a DuckDuckGo text search, return list of result dicts."""
    if not DDGS_AVAILABLE:
        return [{"title": "Search unavailable", "body": "duckduckgo-search not installed.", "href": ""}]
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        return results or []
    except Exception as exc:
        return [{"title": "Search temporarily unavailable", "body": str(exc), "href": ""}]


def _fmt_results(results: list[dict], max_items: int = 4) -> str:
    """Format DDG results into a concise text block."""
    lines = []
    for r in results[:max_items]:
        title = r.get("title", "")
        body  = r.get("body", "")
        href  = r.get("href", "")
        lines.append(f"• {title}: {body[:200]} [source: {href}]")
    return "\n".join(lines) if lines else "No results found."


AIRPORT_CODES = {
    "new york": "JFK", "nyc": "JFK", "manhattan": "JFK", "brooklyn": "JFK",
    "newark": "EWR", "laguardia": "LGA",
    "los angeles": "LAX", "la": "LAX",
    "chicago": "ORD", "o'hare": "ORD", "midway": "MDW",
    "houston": "IAH", "hobby": "HOU",
    "phoenix": "PHX", "philadelphia": "PHL",
    "san antonio": "SAT", "san diego": "SAN",
    "dallas": "DFW", "fort worth": "DFW", "love field": "DAL",
    "san jose": "SJC", "austin": "AUS", "jacksonville": "JAX",
    "san francisco": "SFO", "sf": "SFO", "oakland": "OAK",
    "seattle": "SEA", "tacoma": "SEA", "denver": "DEN",
    "boston": "BOS", "atlanta": "ATL", "miami": "MIA",
    "washington": "DCA", "dc": "DCA", "dulles": "IAD",
    "minneapolis": "MSP", "portland": "PDX", "las vegas": "LAS",
    "detroit": "DTW", "baltimore": "BWI", "charlotte": "CLT",
    "orlando": "MCO", "tampa": "TPA", "pittsburgh": "PIT",
    "raleigh": "RDU", "salt lake city": "SLC", "nashville": "BNA",
    "kansas city": "MCI", "new orleans": "MSY", "cleveland": "CLE",
    "indianapolis": "IND", "columbus": "CMH", "cincinnati": "CVG",
    "memphis": "MEM", "louisville": "SDF", "richmond": "RIC",
    "hartford": "BDL", "albany": "ALB", "buffalo": "BUF",
    "anchorage": "ANC", "honolulu": "HNL", "maui": "OGG",
    "london": "LHR", "paris": "CDG", "frankfurt": "FRA",
    "amsterdam": "AMS", "dubai": "DXB", "tokyo": "NRT",
    "beijing": "PEK", "sydney": "SYD", "toronto": "YYZ",
}


def _airport_code(city: str) -> str:
    c = city.lower().strip()
    for key, code in AIRPORT_CODES.items():
        if key in c:
            return code
    if len(city) == 3 and city.isalpha():
        return city.upper()
    return city[:3].upper()


def _enc(s: str) -> str:
    return urllib.parse.quote(str(s))


# ---------------------------------------------------------------------------
# Public tool functions (called by Gemini via function calling)
# ---------------------------------------------------------------------------

def search_hotels(
    destination: str,
    check_in_date: str,
    check_out_date: str,
    preferences: str = "business travel conference"
) -> str:
    """
    Search the internet for hotels at a destination for the given dates.
    Returns real web search results plus direct booking links.
    ALWAYS call this tool before recommending hotels to a traveler.

    Args:
        destination: City or neighbourhood (e.g. 'Chicago downtown', 'Austin near convention center').
        check_in_date: Human-readable check-in date (e.g. 'September 15 2025').
        check_out_date: Human-readable check-out date (e.g. 'September 18 2025').
        preferences: Any extra preferences such as 'near convention center' or 'airport'.

    Returns:
        JSON string with web search snippets and direct booking links.
    """
    q_general  = f"best hotels {destination} {preferences} {check_in_date}"
    q_marriott = f"Marriott hotel {destination} {check_in_date} availability rates"

    general_results  = _ddg_search(q_general,  max_results=5)
    marriott_results = _ddg_search(q_marriott, max_results=3)

    dest_enc = _enc(destination)

    booking_links = {
        "marriott_preferred": (
            f"https://www.marriott.com/search/default.mi"
            f"?destinationAddress.destination={dest_enc}"
            f"&fromDate={_enc(check_in_date)}&toDate={_enc(check_out_date)}&roomCount=1"
        ),
        "google_hotels": (
            f"https://www.google.com/travel/hotels/{dest_enc}"
            f"?dates={_enc(check_in_date)},{_enc(check_out_date)}&adults=1"
        ),
        "booking_com": (
            f"https://www.booking.com/searchresults.html?ss={dest_enc}"
            f"&checkin={_enc(check_in_date)}&checkout={_enc(check_out_date)}&no_rooms=1&group_adults=1"
        ),
        "expedia": (
            f"https://www.expedia.com/Hotels?destination={dest_enc}"
            f"&startDate={_enc(check_in_date)}&endDate={_enc(check_out_date)}&adults=1"
        ),
        "hotels_com": (
            f"https://www.hotels.com/search?destination={dest_enc}"
            f"&checkin={_enc(check_in_date)}&checkout={_enc(check_out_date)}&adults=1"
        ),
    }

    return json.dumps({
        "destination": destination,
        "check_in": check_in_date,
        "check_out": check_out_date,
        "web_results_general": _fmt_results(general_results),
        "web_results_marriott": _fmt_results(marriott_results),
        "booking_links": booking_links,
        "policy_hint": (
            "Marriott (and Marriott-family brands) is the PREFERRED vendor. "
            "Always surface Marriott first. Other hotels are allowed when Marriott is "
            "unavailable or doesn't serve the location — flag this clearly."
        ),
    })


def search_flights(
    origin: str,
    destination: str,
    departure_date: str,
    return_date: str = "",
    trip_type: str = "round_trip"
) -> str:
    """
    Search the internet for flight options between two cities on given dates.
    Returns real web search results plus direct booking links for all preferred airlines.
    ALWAYS call this before recommending flights.

    Args:
        origin: Departure city or airport code (e.g. 'New York', 'ORD').
        destination: Arrival city or airport code (e.g. 'Austin', 'AUS').
        departure_date: Human-readable departure date (e.g. 'September 14 2025').
        return_date: Human-readable return date for round trips (leave empty for one-way).
        trip_type: 'round_trip' or 'one_way'.

    Returns:
        JSON string with web search snippets and direct booking links.
    """
    q = (
        f"flights from {origin} to {destination} {departure_date} "
        f"Southwest Delta United cheapest nonstop"
    )
    results = _ddg_search(q, max_results=6)

    orig_code = _airport_code(origin)
    dest_code = _airport_code(destination)
    dep_enc   = _enc(departure_date)
    ret_enc   = _enc(return_date) if return_date else ""

    is_rt = bool(return_date)

    booking_links = {
        "southwest_tier1_preferred": (
            f"https://www.southwest.com/air/booking/select.html"
            f"?originationAirportCode={orig_code}&destinationAirportCode={dest_code}"
            f"&departureDate={dep_enc}&returnDate={ret_enc}"
            f"&passengerCount=1&tripType={'roundtrip' if is_rt else 'oneway'}"
        ),
        "delta_tier1_preferred": (
            f"https://www.delta.com/flight-search/book-a-flight"
            f"#/results?type={'round-trip' if is_rt else 'one-way'}"
            f"&origin={orig_code}&destination={dest_code}&departureDate={dep_enc}"
            + (f"&returnDate={ret_enc}" if is_rt else "")
        ),
        "united_tier2": (
            f"https://www.united.com/en/us/fsr/choose-flights"
            f"?f={orig_code}&t={dest_code}&d={dep_enc}"
            + (f"&r={ret_enc}" if is_rt else "")
            + "&sc=7&px=1&taxng=1&clm=7&st=bestmatches&tqp=A"
        ),
        "google_flights_compare_all": (
            f"https://www.google.com/flights?q=flights+from+"
            f"{_enc(origin)}+to+{_enc(destination)}+on+{dep_enc}"
        ),
        "kayak_compare": (
            f"https://www.kayak.com/flights/{orig_code}-{dest_code}/{dep_enc}"
            + (f"/{ret_enc}" if is_rt else "")
            + "/1adults"
        ),
        "expedia_flights": (
            f"https://www.expedia.com/Flights-Search?trip={'roundtrip' if is_rt else 'oneway'}"
            f"&leg1=from%3D{_enc(origin)}%2Cto%3D{_enc(destination)}%2Cdeparture%3D{dep_enc}%2F1%2C0%2CA"
            + (f"&leg2=from%3D{_enc(destination)}%2Cto%3D{_enc(origin)}%2Cdeparture%3D{ret_enc}%2F1%2C0%2CA" if is_rt else "")
        ),
    }

    return json.dumps({
        "origin": origin,
        "destination": destination,
        "departure_date": departure_date,
        "return_date": return_date,
        "origin_code": orig_code,
        "destination_code": dest_code,
        "web_results": _fmt_results(results),
        "booking_links": booking_links,
        "policy_hint": (
            "Airline tiers: Tier 1 MOST PREFERRED = Southwest, Delta (no justification needed). "
            "Tier 2 PREFERRED = United (no justification needed). "
            "Tier 3 ALL OTHERS = permitted but traveler must provide justification. "
            "When a cheaper Tier 3 option exists, compute TOTAL TRIP COST "
            "(base fare + baggage fees + ground transport to alternate airport + any extra hotel nights)."
        ),
    })


def search_rental_cars(
    pickup_location: str,
    pickup_date: str,
    return_date: str,
    vehicle_class: str = "midsize"
) -> str:
    """
    Search the internet for rental car options at a location.
    Returns real results and partner-counter information for Enterprise.
    ALWAYS call this before recommending rental cars.

    Args:
        pickup_location: City, airport, or address for pickup (e.g. 'Austin Airport AUS').
        pickup_date: Human-readable pickup date/time (e.g. 'September 14 2025 2pm').
        return_date: Human-readable return date/time.
        vehicle_class: Preferred vehicle class ('economy', 'compact', 'midsize', 'fullsize', 'suv').

    Returns:
        JSON string with web search snippets, partner info, and direct booking links.
    """
    q_enterprise = f"Enterprise car rental {pickup_location} {pickup_date} {vehicle_class} corporate rate"
    q_partners   = f"Enterprise partner counter {pickup_location} National Alamo car rental"
    q_wait       = f"rental car wait time {pickup_location} airport tips avoid long line"

    ent_results  = _ddg_search(q_enterprise, max_results=4)
    part_results = _ddg_search(q_partners,   max_results=3)
    wait_results = _ddg_search(q_wait,       max_results=3)

    loc_enc = _enc(pickup_location)

    booking_links = {
        "enterprise_preferred": (
            f"https://www.enterprise.com/en/car-rental/debit-cards.html"
        ),
        "enterprise_reserve": (
            f"https://www.enterprise.com/en/car-rental.html"
        ),
        "national_partner_network": (
            f"https://www.nationalcar.com/en/car-rental/results.html"
        ),
        "alamo_partner_network": (
            f"https://www.alamo.com/en/car-rental.html"
        ),
        "google_rental_cars": (
            f"https://www.google.com/travel/explore?dest={loc_enc}&car_rental=true"
        ),
        "kayak_cars": (
            f"https://www.kayak.com/cars/{loc_enc}/{_enc(pickup_date)}/{_enc(return_date)}/1"
        ),
    }

    return json.dumps({
        "pickup_location": pickup_location,
        "pickup_date": pickup_date,
        "return_date": return_date,
        "vehicle_class": vehicle_class,
        "enterprise_results": _fmt_results(ent_results),
        "partner_counter_info": _fmt_results(part_results),
        "wait_time_tips": _fmt_results(wait_results),
        "booking_links": booking_links,
        "policy_hint": (
            "Enterprise is the PREFERRED rental vendor. "
            "National and Alamo are part of the Enterprise partner network and are ACCEPTABLE "
            "without approval — surface them proactively if Enterprise has long queues. "
            "All other vendors are non-preferred and require human approval."
        ),
    })


def search_local_info(location: str, info_type: str = "conference") -> str:
    """
    Search for local travel information such as conference venues, transportation options,
    or airport details at a given location.

    Args:
        location: City or specific address to look up.
        info_type: One of 'conference', 'transportation', 'airport', 'general'.

    Returns:
        JSON string with local information snippets.
    """
    queries = {
        "conference": f"convention center conference venues {location} hotels nearby parking transportation",
        "transportation": f"ground transportation options {location} airport taxi rideshare shuttle cost",
        "airport": f"{location} airport terminals car rental pickup shuttle ride options",
        "general": f"travel tips {location} business traveler things to know",
    }
    q = queries.get(info_type, f"{info_type} {location}")
    results = _ddg_search(q, max_results=5)

    return json.dumps({
        "location": location,
        "info_type": info_type,
        "results": _fmt_results(results),
    })


def check_mobile_checkin(hotel_name: str, location: str) -> str:
    """
    Search for mobile check-in and digital key availability for a specific hotel.
    Use this for Use Case 5 — hotel check-in delays.

    Args:
        hotel_name: Name of the hotel (e.g. 'Marriott Downtown Austin').
        location: City where the hotel is located.

    Returns:
        JSON string with mobile check-in details and app links.
    """
    q = f"{hotel_name} {location} mobile check-in digital key app how to skip front desk queue"
    results = _ddg_search(q, max_results=4)

    is_marriott = "marriott" in hotel_name.lower()

    checkin_links = {
        "marriott_bonvoy_app": "https://www.marriott.com/mobile-app.mi" if is_marriott else None,
        "marriott_checkin_guide": (
            "https://www.marriott.com/en-us/loyalty/member-benefits/mobile-key.mi"
            if is_marriott else None
        ),
        "google_play_marriott": (
            "https://play.google.com/store/apps/details?id=com.marriott.mrt"
            if is_marriott else None
        ),
        "apple_store_marriott": (
            "https://apps.apple.com/us/app/marriott-bonvoy/id455004730"
            if is_marriott else None
        ),
    }

    return json.dumps({
        "hotel": hotel_name,
        "location": location,
        "mobile_checkin_search": _fmt_results(results),
        "checkin_links": {k: v for k, v in checkin_links.items() if v},
        "general_tip": (
            "Most major hotel chains offer mobile check-in via their app, typically available "
            "24 hours before your arrival. Download the hotel's app before your trip to enable "
            "digital key access and skip the front-desk queue entirely."
        ),
    })


def get_budget_and_funding_info(
    travel_type: str = "conference",
    destination: str = "",
    duration_nights: int = 3
) -> str:
    """
    Search for typical corporate travel budget guidance, per-diem rates,
    and funding best practices for business travel.

    Args:
        travel_type: Type of travel ('conference', 'client visit', 'training', 'internal meeting').
        destination: Destination city for cost-of-living context.
        duration_nights: Number of nights for the trip.

    Returns:
        JSON string with budget guidance and typical cost ranges.
    """
    q_rates  = f"GSA per diem rates {destination} {travel_type} 2025 lodging meals"
    q_budget = f"corporate travel budget allocation best practices {travel_type} conference"

    rate_results   = _ddg_search(q_rates,  max_results=4)
    budget_results = _ddg_search(q_budget, max_results=3)

    gsa_link = (
        f"https://www.gsa.gov/travel/plan-book/per-diem-rates/per-diem-rates-results"
        f"?action=perdiems_report&fiscal_year=2025&state=0&city={_enc(destination)}&zip="
    )

    return json.dumps({
        "travel_type": travel_type,
        "destination": destination,
        "duration_nights": duration_nights,
        "per_diem_rates_search": _fmt_results(rate_results),
        "budget_guidance": _fmt_results(budget_results),
        "useful_links": {
            "gsa_per_diem_lookup": gsa_link,
            "concur_travel": "https://www.concur.com",
            "irs_travel_rates": "https://www.irs.gov/tax-professionals/standard-mileage-rates",
        },
        "policy_hint": (
            "Allocation priority: use funds with the EARLIEST expiration date first "
            "to avoid losing use-it-or-lose-it budgets. "
            "Any reallocation of funds across projects or fiscal periods requires "
            "approval from the responsible budget owner."
        ),
    })
