import streamlit as st
import re
import sqlite3
import os
from datetime import datetime

# ---------- DATABASE CONFIG ----------
DB_PATH = os.path.join(os.path.dirname(__file__), "backend.db")

def init_user_db():
    """Initialize users table if not exists."""
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                password TEXT NOT NULL,
                email TEXT UNIQUE,
                mobile TEXT UNIQUE,
                age INTEGER,
                gender TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

# Initialize the database when file runs
init_user_db()

# ---------- HELPER VALIDATORS ----------
def is_valid_email(email):
    if not email:
        return True
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None

def is_valid_mobile(mobile):
    if not mobile:
        return True
    pattern = r'^\+?[0-9]{10,15}$'
    return re.match(pattern, mobile) is not None

def validate_password(password):
    errors = []
    if len(password) < 6:
        errors.append(" Password must be more than 5 characters")
    if not re.search(r'[A-Z]', password):
        errors.append(" Password must contain at least one uppercase letter")
    if not re.search(r'[a-z]', password):
        errors.append(" Password must contain at least one lowercase letter")
    if not re.search(r'[!@#$%^&*()_+\-=\[\]{};:\'",.<>?/\\|`~]', password):
        errors.append(" Password must contain at least one special character")
    if ' ' in password:
        errors.append(" Password must not contain any blank spaces")
    return errors

# ---------- SESSION INITIALIZATION ----------
for key, default in {
    "logged_in": False,
    "current_user": None,
    "registration_error": None,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ---------- DB UTILS ----------
def get_db():
    return sqlite3.connect(DB_PATH)

def create_user(username, name, password, email=None, mobile=None, age=None, gender=None):
    """Create a new user in the DB."""
    try:
        with get_db() as conn:
            c = conn.cursor()

            # Check duplicates manually (for better messages)
            if email:
                c.execute("SELECT id FROM users WHERE email = ?", (email,))
                if c.fetchone():
                    return False, "❌ Email already registered"

            if mobile:
                c.execute("SELECT id FROM users WHERE mobile = ?", (mobile,))
                if c.fetchone():
                    return False, "❌ Mobile number already registered"

            c.execute("""
                INSERT INTO users (username, name, password, email, mobile, age, gender)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (username, name, password, email, mobile, age, gender))
            conn.commit()
            return True, "✅ Account created successfully! You can now login."
    except sqlite3.IntegrityError as e:
        if "users.username" in str(e):
            return False, "❌ Username already exists"
        return False, "❌ Registration failed"
    except Exception as e:
        return False, f"❌ Database error: {str(e)}"

def get_user(username):
    """Fetch user by username."""
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username = ?", (username,))
        columns = [d[0] for d in c.description]
        user = c.fetchone()
    if user:
        return dict(zip(columns, user))
    return None

def verify_user(identifier, password):
    """Verify login using username, email, or mobile."""
    if not identifier or not password:
        return False, None
    try:
        with get_db() as conn:
            c = conn.cursor()
            user = None

            # Username
            c.execute("SELECT * FROM users WHERE username = ?", (identifier,))
            user = c.fetchone()

            # Try email or mobile if not found
            if not user:
                if '@' in identifier:
                    c.execute("SELECT * FROM users WHERE email = ?", (identifier,))
                    user = c.fetchone()
                elif identifier.isdigit():
                    c.execute("SELECT * FROM users WHERE mobile = ?", (identifier,))
                    user = c.fetchone()

            if not user:
                return False, None

            columns = ['id', 'username', 'name', 'password', 'email', 'mobile', 'age', 'gender', 'created_at']
            user_dict = dict(zip(columns, user))

            if user_dict['password'] == password:
                return True, user_dict
            return False, None
    except Exception as e:
        st.error(f"Database error: {str(e)}")
        return False, None

def delete_user(user_id):
    try:
        with get_db() as conn:
            c = conn.cursor()
            c.execute("DELETE FROM users WHERE id = ?", (user_id,))
            conn.commit()
            return True, "Account deleted successfully!"
    except Exception as e:
        return False, f"Error deleting account: {str(e)}"

# ---------- UI FUNCTIONS ----------
def login_page():
    st.subheader("Login to Your Account")

    identifier = st.text_input("Username / Email / Mobile", key="login_identifier")
    password = st.text_input("Password", type="password", key="login_password")

    if st.button("🔓 Login", use_container_width=True, type="primary"):
        if not identifier.strip():
            st.error("Please enter your username, email, or mobile number")
            return
        if not password.strip():
            st.error("Please enter your password")
            return

        success, user = verify_user(identifier.strip(), password)
        if success:
            st.session_state.logged_in = True
            st.session_state.current_user = user
            st.session_state.user_id = user["id"]
            st.session_state.username = user["username"]
            st.success(f"Welcome back, {user['name']}! 🎉")
            st.rerun()

        else:
            st.error("Invalid credentials. Please try again.")

def register_page():
    st.subheader("Create New Account")

    username = st.text_input("Username *", key="signup_username")
    name = st.text_input("Full Name *", key="full_name")
    email = st.text_input("Email (Optional)", key="signup_email")
    mobile = st.text_input("Mobile (Optional)", key="signup_mobile")
    col1, col2 = st.columns(2)
    with col1:
        age = st.number_input("Age *", min_value=13, max_value=120, value=18, key="age")
    with col2:
        gender = st.selectbox("Gender *", ["Male", "Female", "Other"], key="gender")

    password = st.text_input("Password *", type="password", key="signup_password")
    confirm_password = st.text_input("Confirm Password *", type="password", key="confirm_password")

    if st.button("✨ Create Account", use_container_width=True, type="primary"):
        if not username or not name or not password or not confirm_password:
            st.error("Please fill all required fields.")
            return
        if password != confirm_password:
            st.error("Passwords do not match.")
            return
        errors = validate_password(password)
        if errors:
            for e in errors:
                st.error(e)
            return
        success, message = create_user(
            username.strip(), name.strip(), password,
            email.strip() if email else None,
            mobile.strip() if mobile else None,
            age, gender.lower()
        )
        if success:
            st.success(message)
            st.balloons()
        else:
            st.error(message)

def main():
    st.markdown("""
        <h1 style='text-align:center;color:#4F46E5;'>🗺️ Planning My Outings</h1>
        <h4 style='text-align:center;color:#6B7280;'>Your adventure planner companion</h4>
    """, unsafe_allow_html=True)

    if st.session_state.logged_in and st.session_state.current_user:
        user = st.session_state.current_user
        st.sidebar.title(f"Welcome, {user['name']}! 🎉")
        if st.sidebar.button("🚪 Logout"):
            st.session_state.logged_in = False
            st.session_state.current_user = None
            st.rerun()

        st.header("🏠 Dashboard")
        st.info("You’re logged in! Dashboard features appear here.")
    else:
        tab1, tab2 = st.tabs(["🔐 Login", "📝 Sign Up"])
        with tab1:
            login_page()
        with tab2:
            register_page()

if __name__ == "__main__":
    main()
