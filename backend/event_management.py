import streamlit as st
from datetime import datetime, time
import sqlite3
import os
from geopy.geocoders import Nominatim
import requests

# ---------- DATABASE CONFIG ----------
DB_PATH = os.path.join(os.path.dirname(__file__), "backend.db")

def init_events_db():
    """Initialize the events and participants tables."""
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                creator_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                event_datetime TIMESTAMP NOT NULL,
                event_type TEXT NOT NULL,
                location TEXT NOT NULL,
                duration REAL NOT NULL,
                description TEXT,
                cost_estimate REAL,
                max_participants INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                group_id INTEGER,
                FOREIGN KEY (creator_id) REFERENCES users (id),
                FOREIGN KEY (group_id) REFERENCES groups (id)
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS event_participants (
                event_id INTEGER,
                user_id INTEGER,
                status TEXT CHECK(status IN ('attending', 'maybe', 'not_attending')),
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (event_id, user_id),
                FOREIGN KEY (event_id) REFERENCES events (id),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        conn.commit()

# Initialize DB tables on import
init_events_db()

# ---------- GROUP MANAGEMENT ----------
def init_groups_db():
    """Create table for outing groups"""
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                token TEXT UNIQUE NOT NULL,
                creator_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (creator_id) REFERENCES users (id)
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS group_members (
                group_id INTEGER,
                user_id INTEGER,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (group_id, user_id),
                FOREIGN KEY (group_id) REFERENCES groups (id),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        conn.commit()

def create_group(name, creator_id):
    """Create a new group and return its token"""
    import secrets
    token = secrets.token_hex(3).upper()  # short 6-char token
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute(
            "INSERT INTO groups (name, token, creator_id) VALUES (?, ?, ?)",
            (name, token, creator_id)
        )
        group_id = c.lastrowid
        # auto-add creator as member
        c.execute(
            "INSERT INTO group_members (group_id, user_id) VALUES (?, ?)",
            (group_id, creator_id)
        )
        conn.commit()
    return True, f"✅ Group created! Share this token with friends: {token}"

def join_group(token, user_id):
    """Join an existing group using its token"""
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT id FROM groups WHERE token = ?", (token,))
        row = c.fetchone()
        if not row:
            return False, "❌ Invalid group token"
        group_id = row[0]
        # check if already joined
        c.execute(
            "SELECT 1 FROM group_members WHERE group_id = ? AND user_id = ?",
            (group_id, user_id)
        )
        if c.fetchone():
            return False, "You’ve already joined this group"
        c.execute(
            "INSERT INTO group_members (group_id, user_id) VALUES (?, ?)",
            (group_id, user_id)
        )
        conn.commit()
    return True, "🎉 Joined the group successfully!"

# ---------- EVENT CREATION FORM ----------
def create_event_form(user_id=None):
    """Streamlit form to create new events."""
    from sqlite3 import connect

    with st.expander("➕ Create New Event"):
        event_title = st.text_input("Event Title", key="new_event_title")

        # --- Pick a group to attach event to ---
        group_id = None
        group_name = None
        with connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute("""
                SELECT g.id, g.name FROM groups g
                JOIN group_members gm ON g.id = gm.group_id
                WHERE gm.user_id = ?
            """, (user_id,))
            groups = c.fetchall()

        if groups:
            group_choices = {f"{name} (ID: {gid})": gid for gid, name in groups}
            group_choice = st.selectbox(
                "Attach this event to a group",
                list(group_choices.keys()),
                index=0
            )
            group_id = group_choices[group_choice]
        else:
            st.info("ℹ️ You’re not in any group. Create or join one first.")
            group_id = None

        # --- Date, Time, and Type ---
        min_date = datetime.now().date()
        col1, col2 = st.columns(2)
        with col1:
            event_date = st.date_input("Event Date", min_value=min_date, value=min_date)
        with col2:
            hour = st.number_input("Hour", min_value=0, max_value=23, value=12)
            minute = st.number_input("Minute", min_value=0, max_value=59, value=0, step=15)
            event_time = time(hour=int(hour), minute=int(minute))

        col3, col4 = st.columns(2)
        with col3:
            event_type = st.selectbox(
                "Event Type",
                ["Restaurant", "Movie", "Sports", "Shopping", "Outdoor Activity", "Indoor Activity", "Other"]
            )
        with col4:
            duration_hours = st.number_input("Duration (hours)", 0.5, 12.0, 2.0, step=0.5)

        event_location = st.text_input("Location", key="new_event_location", placeholder="Enter location")

        event_description = st.text_area("Event Description", placeholder="Optional: add details")

        col5, col6 = st.columns(2)
        with col5:
            cost_estimate = st.number_input("Estimated Cost (₹)", 0, 10000, 0)
        with col6:
            max_participants = st.number_input("Max Participants", 2, 50, 10)

        return {
            "title": event_title,
            "date": event_date,
            "time": event_time,
            "type": event_type,
            "duration": duration_hours,
            "location": event_location,
            "description": event_description,
            "cost_estimate": cost_estimate,
            "max_participants": max_participants,
            "group_id": group_id
        }
 

# ---------- SAVE EVENT ----------
def save_event(event_data, creator_id, group_id=None):
    """Save event to database."""
    try:
        event_datetime = datetime.combine(event_data["date"], event_data["time"])
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute("""
                INSERT INTO events (
                    creator_id, title, event_datetime, event_type,
                    location, duration, description, cost_estimate,
                    max_participants, group_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                creator_id,
                event_data["title"],
                event_datetime,
                event_data["type"],
                event_data["location"],
                event_data["duration"],
                event_data["description"],
                event_data["cost_estimate"],
                event_data["max_participants"],
                group_id
            ))
            event_id = c.lastrowid

            # Add creator as first participant
            c.execute("""
                INSERT INTO event_participants (event_id, user_id, status)
                VALUES (?, ?, 'attending')
            """, (event_id, creator_id))
            conn.commit()
        return True, "✅ Event created successfully!"
    except Exception as e:
        return False, f"❌ Error creating event: {str(e)}"

# ---------- FETCH EVENTS ----------
def get_user_events(user_id, event_type='all'):
    """Get events relevant to a user based on type (created, participating, or group)."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()

            if event_type == 'created':
                # Only events the user created
                query = """
                    SELECT DISTINCT e.* FROM events e
                    WHERE e.creator_id = ?
                    ORDER BY e.event_datetime DESC
                """
                params = (user_id,)

            elif event_type == 'participating':
                # Events the user joined or RSVP'd to
                query = """
                    SELECT DISTINCT e.* FROM events e
                    JOIN event_participants ep ON e.id = ep.event_id
                    WHERE ep.user_id = ?
                    ORDER BY e.event_datetime DESC
                """
                params = (user_id,)

            elif event_type == 'group':
                # Events created in any group the user belongs to
                query = """
                    SELECT DISTINCT e.* FROM events e
                    JOIN groups g ON e.group_id = g.id
                    JOIN group_members gm ON g.id = gm.group_id
                    WHERE gm.user_id = ?
                    ORDER BY e.event_datetime DESC
                """
                params = (user_id,)

            else:  # 'all'
                # All events created by user, joined by user, or in user's groups
                query = """
                    SELECT DISTINCT e.* FROM events e
                    LEFT JOIN event_participants ep ON e.id = ep.event_id
                    LEFT JOIN group_members gm ON e.group_id = gm.group_id
                    WHERE e.creator_id = ? OR ep.user_id = ? OR gm.user_id = ?
                    ORDER BY e.event_datetime DESC
                """
                params = (user_id, user_id, user_id)

            c.execute(query, params)
            columns = [description[0] for description in c.description]
            events = [dict(zip(columns, row)) for row in c.fetchall()]

        return events
    except Exception as e:
        st.error(f"Database error fetching events: {e}")
        return []

# ---------- DISPLAY EVENT CARD ----------
def display_event(event):
    """Display an event card (safe, uses local helper get_event_participants)."""
    import streamlit as st
    from datetime import datetime

    with st.container():
        # Title
        st.subheader(event.get("title", "Untitled Event"))

        # Event datetime and location
        col1, col2 = st.columns(2)
        with col1:
            # event_datetime might be stored as ISO string or as a datetime object
            ev_dt = event.get("event_datetime")
            if isinstance(ev_dt, str):
                try:
                    event_datetime = datetime.fromisoformat(ev_dt)
                except Exception:
                    # fallback: try parsing as numeric timestamp
                    try:
                        event_datetime = datetime.fromtimestamp(float(ev_dt))
                    except Exception:
                        event_datetime = None
            else:
                event_datetime = ev_dt

            if event_datetime:
                st.write(f"📅 {event_datetime.strftime('%B %d, %Y')}")
                st.write(f"🕒 {event_datetime.strftime('%I:%M %p')}")
            else:
                st.write("📅 Date/time: Not available")

        with col2:
            st.write(f"📍 {event.get('location', 'Location not specified')}")
            st.write(f"⏱️ Duration: {event.get('duration', 'N/A')} hours")

        # Event details
        if event.get("description"):
            st.write("📝 **Details:**")
            st.write(event["description"])

        # Cost and participants
        cost = event.get("cost_estimate") or 0
        try:
            cost_val = float(cost)
        except Exception:
            cost_val = 0.0
        if cost_val > 0:
            st.write(f"💰 Estimated Cost: ₹{cost_val} per person")
        st.write(f"👥 Maximum Participants: {event.get('max_participants', 'N/A')}")

        # RSVPs: call local helper get_event_participants(event_id)
        # IMPORTANT: don't import the same module here — call function directly
        try:
            participants = get_event_participants(event.get("id"))
        except NameError:
            participants = None
        except Exception as e:
            participants = None
            # optional: print or log the error for debugging
            # print("Error fetching participants:", e)

        if participants:
            st.write("👥 **RSVPs:**")
            for p in participants:
                emoji = "✅" if p.get("status") == "attending" else "❓" if p.get("status") == "maybe" else "❌"
                # show name if available, else user_id
                name = p.get("name") or p.get("username") or f"User {p.get('user_id')}"
                st.write(f"{emoji} {name} — {p.get('status')}")



# ---------- UPDATE PARTICIPATION ----------
def update_participation_status(event_id, user_id, status):
    """Update participant status."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute("""
                INSERT INTO event_participants (event_id, user_id, status)
                VALUES (?, ?, ?)
                ON CONFLICT (event_id, user_id)
                DO UPDATE SET status = excluded.status
            """, (event_id, user_id, status))
            conn.commit()
        return True, "Status updated successfully!"
    except Exception as e:
        return False, f"Error updating status: {str(e)}"
    
def get_event_participants(event_id):
    """Fetch who RSVP'd for a specific event."""
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("""
            SELECT u.name, ep.status
            FROM event_participants ep
            JOIN users u ON ep.user_id = u.id
            WHERE ep.event_id = ?
        """, (event_id,))
        rows = c.fetchall()
    return [{"name": name, "status": status} for name, status in rows]


# Initialize the events & groups tables
init_events_db()
init_groups_db()

# ---------- MOOD-BASED SMART SUGGESTIONS ----------
from geopy.geocoders import Nominatim
import requests

def geocode_city(city):
    """Convert city name to coordinates"""
    try:
        geolocator = Nominatim(user_agent="plan_my_outings", timeout=10)
        loc = geolocator.geocode(city)
        if loc:
            return float(loc.latitude), float(loc.longitude)
    except Exception:
        return None, None
    return None, None

def compute_centroid(cities):
    """Compute geographic midpoint of all members' cities"""
    coords = []
    for city in cities:
        latlon = geocode_city(city)
        if latlon[0] is not None:
            coords.append(latlon)
    if not coords:
        return None, None
    lat = sum(p[0] for p in coords) / len(coords)
    lon = sum(p[1] for p in coords) / len(coords)
    return lat, lon

def get_places_nearby(lat, lon, mood="Chill", limit=5):
    """Find nearby places based on mood"""
    if not lat or not lon:
        return []

    query_map = {
        "Chill": "cafe",
        "Foodie": "restaurant",
        "Adventurous": "park"
    }
    query = query_map.get(mood, "restaurant")

    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": query,
        "format": "json",
        "limit": limit,
        "viewbox": f"{lon-0.05},{lat+0.05},{lon+0.05},{lat-0.05}",
        "bounded": 1
    }
    r = requests.get(url, params=params, headers={"User-Agent": "plan-my-outings"})
    if r.status_code != 200:
        return []
    data = r.json()
    return [
        {"name": d.get("display_name").split(",")[0], "lat": d["lat"], "lon": d["lon"]}
        for d in data
    ]
