# app.py
from datetime import datetime
import os
import sys
import time
import uuid
import requests

import streamlit as st
from geopy.geocoders import Nominatim

# ---------------- page config ----------------
st.set_page_config(
    page_title="Plan My Outings",
    page_icon="🗺️",
    layout="wide"
)

# ---------------- constants / config ----------------
# Use env var BACKEND_URL if present, otherwise a placeholder
BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")

# Add the backend directory to Python path (if your repo has a backend folder)
backend_path = os.path.join(os.path.dirname(__file__), "..", "backend")
if os.path.exists(backend_path) and backend_path not in sys.path:
    sys.path.append(backend_path)

# ---------------- optional imports (safe) ----------------
# If you have these modules in your project, they'll be imported.
# Otherwise we continue with useful fallbacks and friendly warnings.
try:
    from authentication_new import (
        init_user_db,
        login_page,
        register_page,
        verify_user,
        delete_user,
    )
except Exception:
    init_user_db = login_page = register_page = verify_user = delete_user = None
    st.warning("Optional: `authentication_new` module not found. Authentication pages disabled.")

try:
    from event_management import (
        init_events_db,
        create_event_form,
        save_event,
        get_user_events,
        display_event,
        update_participation_status,
    )
except Exception:
    init_events_db = create_event_form = save_event = get_user_events = display_event = update_participation_status = None
    st.warning("Optional: `event_management` module not found. Event management disabled.")

try:
    import frontend  # your frontend module
except Exception:
    frontend = None
    st.info("Optional: `frontend` module not found. 'Main' screen will be placeholder.")

# Optional PlanPal assistant UI (if defined elsewhere)
try:
    from planpal import show_planpal_interface
except Exception:
    show_planpal_interface = None

# ---------------- session state initialization ----------------
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'main'

if 'user_id' not in st.session_state:
    st.session_state.user_id = uuid.uuid4().hex[:8]

if 'group_token' not in st.session_state:
    st.session_state.group_token = None

if 'plans_local' not in st.session_state:
    st.session_state.plans_local = []  # local representation of current plans

# ---------------- geolocator ----------------
geolocator = Nominatim(user_agent="plan_my_outings_app", timeout=10)

def geocode_city(city: str):
    """Return (lat, lon) for a city or (None, None) on failure."""
    try:
        loc = geolocator.geocode(city)
        if loc:
            return float(loc.latitude), float(loc.longitude)
    except Exception:
        return None, None
    return None, None

def compute_centroid(members_csv: str):
    """Given comma-separated city names, compute centroid lat/lon."""
    cities = [c.strip() for c in members_csv.split(",") if c.strip()]
    coords = []
    for c in cities:
        latlon = geocode_city(c)
        if latlon[0] is not None:
            coords.append(latlon)
    if not coords:
        return None, None
    lat = sum(p[0] for p in coords) / len(coords)
    lon = sum(p[1] for p in coords) / len(coords)
    return lat, lon

def places_near_viewbox(lat: float, lon: float, query: str = "restaurant", limit: int = 6, box_km: float = 6):
    """Query Nominatim for places within a square viewbox around centroid."""
    try:
        deg = box_km / 111.0  # approx degrees per km
        min_lat = lat - deg
        max_lat = lat + deg
        min_lon = lon - deg
        max_lon = lon + deg
        viewbox = f"{min_lon},{max_lat},{max_lon},{min_lat}"
        url = "https://nominatim.openstreetmap.org/search"
        params = {"q": query, "format": "json", "limit": limit, "viewbox": viewbox, "bounded": 1}
        r = requests.get(url, params=params, headers={"User-Agent": "plan-my-outings-demo"}, timeout=8)
        arr = r.json() if r.status_code == 200 else []
        results = []
        for a in arr:
            display_name = a.get("display_name", "")
            name = display_name.split(",")[0] if display_name else a.get("type", "place")
            results.append({
                "id": a.get("osm_id") or str(uuid.uuid4().hex),  # ensure some id
                "name": name,
                "address": display_name,
                "lat": float(a.get("lat", 0)),
                "lon": float(a.get("lon", 0))
            })
        return results
    except Exception as e:
        st.error(f"Places lookup failed: {e}")
        return []

# ---------------- sidebar navigation ----------------
def sidebar_nav():
    st.sidebar.title("Navigation")
    options = ["Main", "PlanPal Assistant"]
    choice = st.sidebar.radio("Go to", options)
    return choice

# ---------------- main UI code ----------------
def main():
    nav = sidebar_nav()

    if nav == "Main":
        # If you have a frontend module with .main(), call it. Otherwise show core UI.
        if frontend and hasattr(frontend, "main"):
            frontend.main()
        else:
            run_core_ui()

    elif nav == "PlanPal Assistant":
        if show_planpal_interface and callable(show_planpal_interface):
            show_planpal_interface()
        else:
            st.info("PlanPal Assistant is not installed. Fallback to core UI.")
            run_core_ui()

def run_core_ui():
    # ---------- UI: inputs ----------
    st.header("Plan My Outings — Group Planner")

    st.subheader("Group details")
    group_name = st.text_input("Group name", value="Friends Night")
    members = st.text_area("Member locations (comma-separated)", value="Connaught Place, Saket, Hauz Khas")
    mood = st.selectbox("Mood", ["Chill", "Foodie", "Adventurous"])

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Find Suggestions & Publish Plans"):
            # compute centroid and places
            latlon = compute_centroid(members)
            if not latlon or latlon == (None, None):
                st.error("Could not compute centroid. Try simpler city names or Load Demo Data.")
            else:
                lat, lon = latlon
                qmap = {"Chill":"cafe","Foodie":"restaurant","Adventurous":"park"}
                query = qmap.get(mood, "restaurant")
                candidates = places_near_viewbox(lat, lon, query=query, limit=8, box_km=6)
                # pick first 3 (or fallback demo)
                if len(candidates) < 3:
                    candidates = [
                        {"id": str(uuid.uuid4().hex), "name":"Demo Place A","address":"Demo address A","lat":lat+0.001,"lon":lon+0.001},
                        {"id": str(uuid.uuid4().hex), "name":"Demo Place B","address":"Demo address B","lat":lat-0.001,"lon":lon+0.001},
                        {"id": str(uuid.uuid4().hex), "name":"Demo Place C","address":"Demo address C","lat":lat+0.001,"lon":lon-0.001},
                    ]
                chosen = candidates[:3]

                # 1) create group on backend (if backend available)
                token = None
                try:
                    resp = requests.post(f"{BACKEND_URL}/groups", json={"name": group_name}, timeout=8)
                    resp.raise_for_status()
                    token = resp.json().get("token")
                    if not token:
                        # fallback generate a simple token if backend didn't provide one
                        token = uuid.uuid4().hex[:8]
                    st.session_state.group_token = token
                    st.success(f"Group created. Token: `{token}`")
                    st.text_input("Group token (copy to share)", value=token, key="group_token_input")
                except requests.exceptions.RequestException as e:
                    # backend not reachable -> create a client-only token
                    st.warning(f"Could not contact backend to create group. Working locally. ({e})")
                    token = uuid.uuid4().hex[:8]
                    st.session_state.group_token = token
                    st.text_input("Group token (local)", value=token, key="local_group_token_input")

                # 2) publish plans to backend (if available), otherwise store locally
                plans_payload = {"plans": []}
                for i, p in enumerate(chosen, start=1):
                    title = f"{i}. {p.get('name')}"
                    plans_payload['plans'].append({"title": title, "place": p, "votes": 0, "id": p.get("id", str(uuid.uuid4().hex))})

                try:
                    # attempt to publish; if backend fails we'll fallback
                    r2 = requests.post(f"{BACKEND_URL}/groups/{token}/plans", json=plans_payload, timeout=8)
                    r2.raise_for_status()
                    # fetch full plans (with ids) from backend
                    time.sleep(0.3)
                    resp = requests.get(f"{BACKEND_URL}/groups/{token}/plans", timeout=8)
                    resp.raise_for_status()
                    st.session_state.plans_local = resp.json().get("plans", plans_payload["plans"])
                except requests.exceptions.RequestException:
                    st.warning("Failed to publish plans to backend — using a local copy.")
                    st.session_state.plans_local = plans_payload["plans"]

                st.success("Plans prepared. Use the voting UI below and share the group token with friends.")

    with col2:
        if st.button("Load Demo Data"):
            st.session_state.group_token = None
            # demo plans
            demo_lat, demo_lon = 28.6139, 77.2090  # New Delhi center as example
            st.session_state.plans_local = [
                {"id": "demo_a", "title": "1. Demo Cafe", "place": {"address": "Connaught Place, Delhi"}, "votes": 2},
                {"id": "demo_b", "title": "2. Demo Restaurant", "place": {"address": "Saket, Delhi"}, "votes": 5},
                {"id": "demo_c", "title": "3. Demo Park", "place": {"address": "Hauz Khas, Delhi"}, "votes": 1},
            ]
            st.success("Loaded demo data.")
            st.experimental_rerun()

    # ---------- Voting UI ----------
    st.divider()
    st.subheader("Vote for a plan")
    if not st.session_state.plans_local:
        st.info("No plans published yet. Click 'Find Suggestions & Publish Plans' first or Load Demo Data.")
    else:
        token = st.session_state.group_token
        placeholder = st.empty()

        def fetch_and_render():
            # try to get latest plans from backend, fallback to local
            plans = st.session_state.plans_local
            if token:
                try:
                    resp = requests.get(f"{BACKEND_URL}/groups/{token}/plans", timeout=6)
                    resp.raise_for_status()
                    plans = resp.json().get("plans", plans)
                    # store local copy
                    st.session_state.plans_local = plans
                except Exception:
                    # keep existing local plans
                    plans = st.session_state.plans_local

            # render plans
            for idx, p in enumerate(plans):
                p_id = p.get("id", f"plan_{idx}")
                colA, colB = st.columns([4, 1])
                with colA:
                    address = p.get("place", {}).get("address", "")
                    st.markdown(f"**{p.get('title', 'Untitled')}**  \n{address}")
                with colB:
                    votes = p.get("votes", 0)
                    st.write(f"Votes: {votes}")
                    # voting button per plan
                    if st.button("👍 Vote", key=f"vote_{p_id}"):
                        # optimistic UI: call backend vote endpoint if possible, otherwise update local
                        if token:
                            try:
                                r = requests.post(
                                    f"{BACKEND_URL}/groups/{token}/plans/{p_id}/vote",
                                    json={"user_id": st.session_state.user_id},
                                    timeout=6
                                )
                                r.raise_for_status()
                                # refresh plans
                                new = requests.get(f"{BACKEND_URL}/groups/{token}/plans", timeout=6).json()
                                st.session_state.plans_local = new.get("plans", st.session_state.plans_local)
                                st.experimental_rerun()
                            except requests.exceptions.RequestException as exc:
                                st.error(f"Vote failed: {exc}")
                                st.write("Tried URL:", f"{BACKEND_URL}/groups/{token}/plans/{p_id}/vote")
                        else:
                            # update local copy only
                            for pv in st.session_state.plans_local:
                                if pv.get("id") == p_id:
                                    pv["votes"] = pv.get("votes", 0) + 1
                            st.success("Vote recorded locally.")
                            st.experimental_rerun()

        # initial render
        fetch_and_render()

        st.write("")  # spacer

        # manual refresh
        if st.button("Refresh votes"):
            if not token:
                st.warning("No group token available. Create/publish plans first or use demo data.")
            else:
                try:
                    resp = requests.get(f"{BACKEND_URL}/groups/{token}/plans", timeout=6)
                    resp.raise_for_status()
                    data = resp.json()
                    st.session_state.plans_local = data.get("plans", [])
                    st.success("Votes refreshed.")
                    st.experimental_rerun()
                except requests.exceptions.HTTPError as he:
                    st.error(f"HTTP error when refreshing: {he}")
                    st.write("Tried URL:", f"{BACKEND_URL}/groups/{token}/plans")
                    st.write("HTTP status:", resp.status_code if 'resp' in locals() else "no response")
                except requests.exceptions.RequestException as re:
                    st.error(f"Request failed when refreshing: {re}")
                    st.write("Tried URL:", f"{BACKEND_URL}/groups/{token}/plans")
                except Exception as e:
                    st.error(f"Unexpected error when refreshing: {e}")

# ---------------- run app ----------------
if __name__ == "__main__":
    main()
