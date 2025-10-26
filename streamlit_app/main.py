import streamlit as st
import sys
import os
import uuid
import requests
from datetime import datetime
from geopy.geocoders import Nominatim

# Add the backend directory to Python path
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
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

# Configuration
BACKEND_URL = "http://localhost:8000"

# Page configuration
st.set_page_config(
    page_title="Planning My Outings",
    page_icon="🗺️",
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        text-align: center;
        color: #4F46E5;
        font-size: 2.5em;
        font-weight: bold;
        margin-bottom: 10px;
    }
    .sub-header {
        text-align: center;
        color: #6B7280;
        font-size: 1.2em;
        margin-bottom: 30px;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'current_user' not in st.session_state:
    st.session_state.current_user = None
if 'current_page' not in st.session_state:
    st.session_state.current_page = "home"
if 'group_token' not in st.session_state:
    st.session_state.group_token = None
if 'user_id' not in st.session_state:
    st.session_state.user_id = uuid.uuid4().hex[:8]

# Initialize databases
init_user_db()
init_events_db()

# Initialize geolocation
geolocator = Nominatim(user_agent="plan_my_outings_app", timeout=10)

def geocode_city(city):
    """Get coordinates for a city"""
    try:
        loc = geolocator.geocode(city)
        if loc:
            return float(loc.latitude), float(loc.longitude)
    except Exception:
        return None, None
    return None, None

def compute_centroid(members_csv):
    """Compute the center point of multiple cities"""
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
    """Find places near a location"""
    deg = box_km / 111.0
    min_lat = lat - deg
    max_lat = lat + deg
    min_lon = lon - deg
    max_lon = lon + deg
    viewbox = f"{min_lon},{max_lat},{max_lon},{min_lat}"
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": query,
        "format": "json",
        "limit": limit,
        "viewbox": viewbox,
        "bounded": 1
    }
    r = requests.get(url, params=params, headers={"User-Agent": "plan-my-outings-app"})
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

def show_groups():
    """Display groups page"""
    st.header("👥 My Groups")
    
    # Create New Group
    with st.expander("Create New Group"):
        group_name = st.text_input("Group Name", key="new_group_name")
        members = st.text_area(
            "Member locations (comma-separated)", 
            key="group_members",
            help="Enter city names separated by commas"
        )
        mood = st.selectbox(
            "Group Mood",
            ["Chill", "Foodie", "Adventurous"],
            help="This will help suggest appropriate venues"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🎯 Find Suggestions", use_container_width=True):
                with st.spinner("Finding the perfect spots..."):
                    # Compute centroid and find places
                    latlon = compute_centroid(members)
                    if not latlon or latlon == (None, None):
                        st.error("Could not locate cities. Try using simpler city names.")
                    else:
                        lat, lon = latlon
                        qmap = {
                            "Chill": "cafe",
                            "Foodie": "restaurant",
                            "Adventurous": "park"
                        }
                        query = qmap.get(mood, "restaurant")
                        candidates = places_near_viewbox(lat, lon, query=query, limit=8, box_km=6)
                        
                        if candidates:
                            st.success("Found some great spots!")
                            for place in candidates[:3]:
                                with st.container():
                                    st.write(f"**{place['name']}**")
                                    st.write(f"📍 {place['address']}")
                                    if st.button("Create Event Here", key=f"create_event_{place['name']}"):
                                        # Pre-fill event creation form
                                        st.session_state.current_page = "events"
                                        st.session_state.pre_fill_event = {
                                            "title": f"{mood} outing at {place['name']}",
                                            "location": place['address'],
                                            "type": mood
                                        }
                                        st.rerun()
                        else:
                            st.warning("No suitable places found. Try different cities or mood.")

        with col2:
            if st.button("✨ Create Group", use_container_width=True):
                if not group_name.strip():
                    st.error("Please enter a group name")
                elif not members.strip():
                    st.error("Please enter member locations")
                else:
                    # Here you would integrate with your group creation backend
                    token = uuid.uuid4().hex[:8]
                    st.success(f"Group '{group_name}' created!")
                    st.info(f"Share this group code with members: `{token}`")
                    st.session_state.group_token = token

    # Join Existing Group
    with st.expander("Join Existing Group"):
        join_token = st.text_input("Enter Group Code")
        if st.button("🤝 Join Group"):
            if not join_token.strip():
                st.error("Please enter a group code")
            else:
                # Here you would verify the token with your backend
                st.success("Joined group successfully!")
                st.session_state.group_token = join_token

    # List existing groups
    st.subheader("Your Groups")
    if st.session_state.group_token:
        with st.container():
            st.write(f"**Active Group Code:** `{st.session_state.group_token}`")
            st.write("Members: " + members)
            st.write(f"Mood: {mood}")
            
            # Show group actions
            col3, col4 = st.columns(2)
            with col3:
                if st.button("📅 Plan Event", use_container_width=True):
                    st.session_state.current_page = "events"
                    st.rerun()
            with col4:
                if st.button("👋 Leave Group", use_container_width=True):
                    st.session_state.group_token = None
                    st.rerun()
    else:
        st.info("You haven't created or joined any groups yet.")

def main():
    # Header
    st.markdown('<p class="main-header">🗺️ Planning My Outings</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Your adventure planner companion</p>', unsafe_allow_html=True)
    
    if st.session_state.logged_in and st.session_state.current_user:
        # Main navigation
        tab1, tab2, tab3, tab4 = st.tabs(["🏠 Dashboard", "👥 Groups", "📅 Events", "👤 Profile"])
        
        with tab1:
            st.header("🏠 Dashboard")
            # Show upcoming events and group summaries
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("📅 Your Events")
                events = get_user_events(st.session_state.current_user['id'])
                if events:
                    for event in events[:3]:  # Show 3 most recent
                        display_event(event)
                else:
                    st.info("No upcoming events")
            
            with col2:
                st.subheader("👥 Your Groups")
                if st.session_state.group_token:
                    st.write(f"Active Group: `{st.session_state.group_token}`")
                else:
                    st.info("No active groups")
        
        with tab2:
            show_groups()
        
        with tab3:
            st.header("📅 Events")
            event_tab1, event_tab2, event_tab3 = st.tabs(["📝 Create Event", "🎯 My Events", "👥 Participating"])
            
            with event_tab1:
                event_data = create_event_form()
                if st.button("📅 Create Event", type="primary"):
                    success, message = save_event(
                        event_data,
                        creator_id=st.session_state.current_user['id'],
                        group_id=st.session_state.group_token
                    )
                    if success:
                        st.success(message)
                        st.balloons()
                    else:
                        st.error(message)
            
            with event_tab2:
                my_events = get_user_events(st.session_state.current_user['id'], 'created')
                if my_events:
                    for event in my_events:
                        display_event(event)
                else:
                    st.info("You haven't created any events yet")
            
            with event_tab3:
                participating = get_user_events(st.session_state.current_user['id'], 'participating')
                if participating:
                    for event in participating:
                        display_event(event)
                else:
                    st.info("You're not participating in any events yet")
        
        with tab4:
            st.header("👤 Profile")
            user = st.session_state.current_user
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Username:** {user['username']}")
                st.write(f"**Name:** {user['name']}")
                st.write(f"**Email:** {user['email']}")
            with col2:
                st.write(f"**Mobile:** {user['mobile']}")
                st.write(f"**Age:** {user['age']}")
                st.write(f"**Gender:** {user['gender'].capitalize()}")
            
            # Account deletion
            st.write("---")
            with st.expander("❌ Delete Account"):
                st.warning("This action cannot be undone!")
                password = st.text_input("Confirm your password", type="password")
                if st.button("Delete My Account", type="primary"):
                    if password:
                        success, _ = verify_user(user['username'], password)
                        if success:
                            if delete_user(user['id']):
                                st.success("Account deleted successfully")
                                st.session_state.logged_in = False
                                st.session_state.current_user = None
                                st.rerun()
                            else:
                                st.error("Failed to delete account")
                        else:
                            st.error("Incorrect password")
                    else:
                        st.error("Please enter your password")
    else:
        tab1, tab2 = st.tabs(["🔐 Login", "📝 Sign Up"])
        with tab1:
            login_page()
        with tab2:
            register_page()

if __name__ == "__main__":
    main()