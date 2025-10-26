import os
import streamlit as st
import google.generativeai as genai
import json

# Configure Gemini with environment variable
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    st.warning("⚠️ Gemini API key not found. Set GEMINI_API_KEY in your environment before using PlanPal.")
else:
    genai.configure(api_key=API_KEY)

# --- Core Bot ---
class PlanPalBot:
    def __init__(self):
        self.model = genai.GenerativeModel("gemini-pro")


    def chat_response(self, user_input: str) -> str:
        """Chat-based responses."""
        prompt = f"""You are PlanPal, a friendly AI that helps plan group outings.
        Respond conversationally to:
        {user_input}
        Give practical, fun, and specific suggestions.
        """
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"(PlanPal error: {e})"

    def get_event_suggestions(self, location: str, group_size: int, preferences=None, budget=None):
        """Ask Gemini to generate structured JSON event suggestions."""
        prompt = f"""
        Suggest 3 detailed event ideas in {location} for a group of {group_size} people.
        Preferences: {preferences or "None"} | Budget: {budget or "Flexible"}.

        Format your reply as a JSON list:
        [
          {{
            "name": "Event name",
            "description": "Brief details",
            "estimated_cost": "Approx. cost per person",
            "duration": "How long it takes",
            "best_time": "Best time of day",
            "requirements": "Any prep or items needed"
          }}
        ]
        """
        try:
            response = self.model.generate_content(prompt)
            text = response.text.strip()

            # Try parsing JSON
            if "[" in text and "]" in text:
                json_part = text[text.find("["):text.rfind("]")+1]
                return json.loads(json_part)
            else:
                # Fallback if not valid JSON
                return [{"name": "Suggestion", "description": text}]
        except Exception as e:
            return [{"name": "Error", "description": f"PlanPal failed: {e}"}]

# --- Streamlit Integration ---
def init_planpal():
    if "planpal" not in st.session_state:
        st.session_state.planpal = PlanPalBot()
    return st.session_state.planpal

def show_planpal_chat():
    """Chat UI"""
    st.title("🤖 PlanPal — AI Event Assistant")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if user_input := st.chat_input("Ask me about planning an outing..."):
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        bot = init_planpal()
        with st.spinner("PlanPal is thinking..."):
            reply = bot.chat_response(user_input)

        st.session_state.chat_history.append({"role": "assistant", "content": reply})
        with st.chat_message("assistant"):
            st.markdown(reply)

def show_event_planner():
    """Structured event planner"""
    st.title("🎯 PlanPal Event Planner (AI-powered)")

    bot = init_planpal()
    location = st.text_input("Location", "Delhi")
    group_size = st.number_input("Group Size", min_value=1, value=4)
    mood = st.selectbox("Mood / Preference", ["Chill", "Foodie", "Adventurous", "Cultural"])
    budget = st.selectbox("Budget", ["Low", "Medium", "Luxury"])

    if st.button("✨ Get AI Suggestions"):
        with st.spinner("PlanPal is brainstorming..."):
            ideas = bot.get_event_suggestions(location, group_size, preferences=mood, budget=budget)

        for i, idea in enumerate(ideas, 1):
            with st.expander(f"{i}. 📍 {idea.get('name', 'Suggestion')}"):
                st.write(f"**Description:** {idea.get('description', 'N/A')}")
                st.write(f"**Cost:** {idea.get('estimated_cost', 'N/A')}")
                st.write(f"**Duration:** {idea.get('duration', 'N/A')}")
                st.write(f"**Best Time:** {idea.get('best_time', 'N/A')}")
                st.write(f"**Requirements:** {idea.get('requirements', 'N/A')}")
