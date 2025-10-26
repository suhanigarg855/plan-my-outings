import streamlit as st
from planpal_bot import init_planpal, show_planpal_chat, show_event_planner

st.set_page_config(page_title="PlanPal Assistant", page_icon="🤖", layout="wide")

# Sidebar navigation
tab = st.sidebar.radio("Mode", ["Chat Assistant", "Event Planner"])

if tab == "Chat Assistant":
    show_planpal_chat()
else:
    show_event_planner()