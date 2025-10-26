import streamlit as st
import sys
import os
import uuid
import time
import requests
from datetime import datetime
from geopy.geocoders import Nominatim

# Backend URL configuration
BACKEND_URL = "http://localhost:8000"

# Add the backend directory to Python path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend'))
print(f"Adding backend path: {backend_path}")  # Debug print
sys.path.append(backend_path)

# Import all components
from authentication_new import (
    init_user_db,
    login_page,
    register_page,
    verify_user,
    delete_user
)
from event_management import (
    init_events_db,
    create_event_form,
    save_event,
    get_user_events,
    display_event,
    update_participation_status
)

# Page configuration
st.set_page_config(
    page_title="Planning My Outings",
    page_icon="🗺️",
    layout="wide"
)

# Initialize geolocation
geolocator = Nominatim(user_agent="plan_my_outings_app", timeout=10)

def show_planpal_interface():
    from backend.planpal_bot import generate_plan, init_gemini_client
    
    st.title("PlanPal - Your Event Planning Assistant")
    
    # Initialize chat history in session state if it doesn't exist
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    # Display chat history
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask PlanPal for event planning suggestions..."):
        # Add user message to chat history
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.write(prompt)
        
        # Get bot response
        client = init_gemini_client()
        with st.chat_message("assistant"):
            with st.spinner("PlanPal is thinking..."):
                response = generate_plan(prompt, client)
                st.write(response)
        
        # Add assistant response to chat history
        st.session_state.chat_history.append({"role": "assistant", "content": response})

# ---------- session state ----------
if 'user_id' not in st.session_state:
    st.session_state.user_id = uuid.uuid4().hex[:8]
if 'group_token' not in st.session_state:
    st.session_state.group_token = None
if 'plans_local' not in st.session_state:
    st.session_state.plans_local = []  # local representation of current plans

# ---------- helper: geocode & places (reuse your working code) ----------
geolocator = Nominatim(user_agent="plan_my_outings_app", timeout=10)

def geocode_city(city):
    try:
        loc = geolocator.geocode(city)
        if loc:
            return float(loc.latitude), float(loc.longitude)
    except Exception:
        return None, None
    return None, None

def compute_centroid(members_csv):
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

def places_near_viewbox(lat, lon, query="restaurant", limit=6, box_km=6):
    import requests, math
    deg = box_km / 111.0
    min_lat = lat - deg
    max_lat = lat + deg
    min_lon = lon - deg
    max_lon = lon + deg
    viewbox = f"{min_lon},{max_lat},{max_lon},{min_lat}"
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": query, "format": "json", "limit": limit, "viewbox": viewbox, "bounded": 1}
    r = requests.get(url, params=params, headers={"User-Agent": "plan-my-outings-demo"})
    arr = r.json() if r.status_code == 200 else []
    results = []
    for a in arr:
        results.append({
            "name": a.get("display_name").split(",")[0],
            "address": a.get("display_name"),
            "lat": float(a.get("lat")),
            "lon": float(a.get("lon"))
        })
    return results

# ---------- UI: inputs ----------
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
            # pick first 3 (or fallback)
            if len(candidates) < 3:
                # fallback demo points near centroid
                candidates = [
                    {"name":"Demo Place A","address":"Demo address A","lat":lat+0.001,"lon":lon+0.001},
                    {"name":"Demo Place B","address":"Demo address B","lat":lat-0.001,"lon":lon+0.001},
                    {"name":"Demo Place C","address":"Demo address C","lat":lat+0.001,"lon":lon-0.001},
                ]
            chosen = candidates[:3]
            # 1) create group on backend
            try:
                resp = requests.post(f"{BACKEND_URL}/groups", json={"name": group_name}, timeout=8)
                token = resp.json().get("token")
                st.session_state.group_token = token
                st.info(f"Group created. Token: `{token}`")
                st.text_input("Group token (copy to share)", value=token)
            except Exception as e:
                st.error("Could not contact backend to create group. Is it running?")
                st.stop()
            # 2) publish plans
            plans_payload = {"plans": []}
            for i,p in enumerate(chosen, start=1):
                title = f"{i}. {p['name']}"
                plans_payload['plans'].append({"title": title, "place": p})
            try:
                r2 = requests.post(f"{BACKEND_URL}/groups/{token}/plans", json=plans_payload, timeout=8)
            except Exception:
                st.error("Failed to publish plans to backend.")
                st.stop()
            st.success("Plans published to backend. Use the voting UI below (and share the group token).")
            # store local copy and fetch full plans (with ids)
            time.sleep(0.3)
            resp = requests.get(f"{BACKEND_URL}/groups/{token}/plans", timeout=8).json()
            st.session_state.plans_local = resp.get("plans", [])
with col2:
    if st.button("Load Demo Data"):
        st.session_state.group_token = None
        st.session_state.plans_local = []
        st.rerun()

# ---------- Voting UI ----------
st.divider()
st.subheader("Vote for a plan")
if not st.session_state.plans_local:
    st.info("No plans published yet. Click 'Find Suggestions & Publish Plans' first.")
else:
    # display plans with votes and vote buttons
    token = st.session_state.group_token
    placeholder = st.empty()
    def fetch_and_render():
        try:
            resp = requests.get(f"{BACKEND_URL}/groups/{token}/plans", timeout=6).json()
            plans = resp.get("plans", [])
        except Exception:
            plans = st.session_state.plans_local  # fallback
        # render
        for p in plans:
            colA, colB = st.columns([4,1])
            with colA:
                st.markdown(f"**{p['title']}**  \n{p.get('place',{}).get('address','')}")
            with colB:
                st.write(f"Votes: {p.get('votes',0)}")
                # vote button
                if st.button("👍 Vote", key=f"vote_{p['id']}"):

                    # toggle vote for this user via backend
                    try:
                        r = requests.post(
                            f"{BACKEND_URL}/groups/{token}/plans/{p['id']}/vote",
                            json={"user_id": st.session_state.user_id},
                            timeout=6
                        )
                        r.raise_for_status()
                    except requests.exceptions.RequestException as exc:
                        st.error(f"Vote failed: {exc}")
                        st.write("Tried URL:", f"{BACKEND_URL}/groups/{token}/plans/{p['id']}/vote")
                        st.stop()
                    else:
                        new = requests.get(f"{BACKEND_URL}/groups/{token}/plans", timeout=6).json()
                        st.session_state.plans_local = new.get("plans", [])
                        st.rerun()

    
    # initial render
    fetch_and_render()
    st.write("")  # spacer
    # manual refresh (improved error reporting)
    if st.button("Refresh votes"):
        if not token:
            st.error("No group token available. Create/publish plans first.")
        else:
            try:
                resp = requests.get(f"{BACKEND_URL}/groups/{token}/plans", timeout=6)
                resp.raise_for_status()
                data = resp.json()
                st.session_state.plans_local = data.get("plans", [])
                st.success("Votes refreshed.")
                st.rerun()
            except requests.exceptions.HTTPError as he:
                st.error(f"HTTP error when refreshing: {he}")
                st.write("Tried URL:", f"{BACKEND_URL}/groups/{token}/plans")
                st.write("HTTP status:", resp.status_code if 'resp' in locals() else "no response")
            except requests.exceptions.RequestException as re:
                st.error(f"Request failed when refreshing: {re}")
                st.write("Tried URL:", f"{BACKEND_URL}/groups/{token}/plans")
            except Exception as e:
                st.error(f"Unexpected error when refreshing: {e}")

