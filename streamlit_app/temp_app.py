# temp_app.py (complete — replace your existing file with this)
import os
import sys

# Path to this file's directory
THIS_DIR = os.path.dirname(__file__)

# Project root (one level up from this file)
PROJECT_ROOT = os.path.abspath(os.path.join(THIS_DIR, ".."))

# Backend directory (for diagnostics)
BACKEND_PATH = os.path.join(PROJECT_ROOT, "backend")

# Debug prints (visible in terminal running Streamlit)
print("TEMP_APP STARTING: __file__ =", __file__)
print("Computed PROJECT_ROOT =", PROJECT_ROOT)
print("Computed BACKEND_PATH =", BACKEND_PATH)
print("PROJECT_ROOT exists? ->", os.path.exists(PROJECT_ROOT))
print("BACKEND_PATH exists? ->", os.path.exists(BACKEND_PATH))
if os.path.exists(BACKEND_PATH):
    print("Listing BACKEND_PATH files:", os.listdir(BACKEND_PATH))
else:
    print("BACKEND_PATH missing!")

# Ensure project root is in sys.path so Python can import 'backend' package
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# ---------- Now normal imports ----------
import streamlit as st
from datetime import datetime
from geopy.geocoders import Nominatim

# Import backend modules using package-qualified imports
from backend.planpal_bot import show_planpal_chat_ui, show_event_planner_ui
from backend.authentication_new import init_user_db, login_page, register_page, verify_user
from backend.event_management import (
    init_events_db,
    create_event_form,
    save_event,
    get_user_events,
    display_event,
    update_participation_status
)

# ---------- STREAMLIT CONFIG ----------
st.set_page_config(page_title="Plan My Outings", page_icon="🗺️", layout="wide")

# ---------- INITIALIZE DATABASES ----------
init_user_db()
init_events_db()

# ---------- SESSION STATE ----------
defaults = {
    "logged_in": False,
    "username": None,
    "user_id": None
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ---------- PAGE SECTIONS ----------
def show_login_page():
    """Display login/register side by side."""
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🔐 Login")
        login_page()
    with col2:
        st.subheader("📝 Register")
        register_page()

def show_dashboard():
    st.header("🏠 Your Dashboard")
    events = get_user_events(st.session_state.user_id)
    if events:
        for event in events:
            display_event(event)
    else:
        st.info("No upcoming events. Create one from the sidebar!")

def show_create_event():
    st.header("📅 Create a New Event")

    # Safety check
    if not st.session_state.get("user_id"):
        st.error("You must be logged in to create an event.")
        return

    st.caption("Fill the details below to add your new event.")
    event_data = create_event_form(st.session_state.user_id)

    # Add a "Create Event" button
    if st.button("📅 Create Event", type="primary", use_container_width=True):
        if not event_data["title"] or not event_data["location"]:
            st.error("Please provide both title and location.")
        else:
            success, msg = save_event(
                event_data,
                creator_id=st.session_state.user_id,
                group_id=event_data.get("group_id")
            )
            if success:
                st.success(msg)
                st.balloons()
            else:
                st.error(msg)

def show_join_events():
    st.header("👥 Group Events You Can Join")
    events = get_user_events(st.session_state.user_id, event_type='group')

    if events:
        for event in events:
            if event['creator_id'] != st.session_state.user_id:
                display_event(event)
    else:
        st.info("No group events available yet. Ask your friends to create one!")

def show_my_events():
    st.header("🎯 My Events")
    events = get_user_events(st.session_state.user_id, event_type='created')
    if events:
        for event in events:
            display_event(event)
    else:
        st.info("You haven't created any events yet. Go to 'Create Event' to make one!")

def show_groups():
    st.header("👥 My Groups")

    # Create new group
    with st.expander("➕ Create a Group"):
        group_name = st.text_input("Group Name", key="create_group_name")
        if st.button("Create Group", use_container_width=True, key="btn_create_group"):
            if group_name.strip():
                from backend.event_management import create_group
                success, msg = create_group(group_name.strip(), st.session_state.user_id)
                if success:
                    st.success(msg)
                else:
                    st.error(msg)
            else:
                st.error("Please enter a group name")

    # Join existing group
    with st.expander("🔑 Join a Group"):
        token = st.text_input("Enter Group Token", key="join_group_token")
        if st.button("Join Group", use_container_width=True, key="btn_join_group"):
            if token.strip():
                from backend.event_management import join_group
                success, msg = join_group(token.strip().upper(), st.session_state.user_id)
                if success:
                    st.success(msg)
                else:
                    st.error(msg)
            else:
                st.error("Please enter a valid token")

def show_smart_suggestions():
    st.header("🧠 Mood-Based Smart Suggestions")

    st.caption("Get outing ideas based on your group's mood and member locations!")

    # Collect inputs
    group_cities = st.text_area("Enter group members' cities (comma separated)", value="Delhi, Noida, Gurgaon")
    mood = st.selectbox("Choose a mood", ["Chill", "Foodie", "Adventurous"])

    if st.button("✨ Suggest Places"):
        from backend.event_management import compute_centroid, get_places_nearby

        cities = [c.strip() for c in group_cities.split(",") if c.strip()]
        lat, lon = compute_centroid(cities)
        if not lat or not lon:
            st.error("Couldn't compute midpoint — check city names.")
            return

        places = get_places_nearby(lat, lon, mood)
        if not places:
            st.warning("No suggestions found nearby. Try again with simpler names.")
        else:
            st.success(f"Top suggestions for '{mood}' mood:")
            for i, p in enumerate(places, 1):
                st.write(f"{i}. 📍 {p['name']}")

# ---------- MAIN APP ----------
def main():
    if not st.session_state.logged_in:
        # Show login/register page
        show_login_page()
    else:
        # Sidebar navigation
        st.sidebar.title(f"Welcome, {st.session_state.username or 'User'} 👋")
        nav = st.sidebar.radio(
            "Navigation",
            ["Dashboard", "Groups", "Create Event", "Join Events", "My Events", "PlanPal Assistant", "Smart Suggestions"]
        )

        if nav == "Dashboard":
            show_dashboard()
        elif nav == "Groups":
            show_groups()
        elif nav == "Create Event":
            show_create_event()
        elif nav == "Join Events":
            show_join_events()
        elif nav == "My Events":
            show_my_events()
        elif nav == "PlanPal Assistant":
            # ✅ Show both chat & planner tabs
            tab1, tab2 = st.tabs(["Chat", "Planner"])
            with tab1:
                show_planpal_chat_ui()
            with tab2:
                show_event_planner_ui()
        elif nav == "Smart Suggestions":
            show_smart_suggestions()

        # Logout
        st.sidebar.write("---")
        if st.sidebar.button("🚪 Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.username = None
            st.session_state.user_id = None
            st.rerun()

if __name__ == "__main__":
    main()
