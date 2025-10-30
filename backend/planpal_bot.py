# backend/planpal_bot.py
import os
import streamlit as st
import json
from typing import List, Dict, Any

# Try to import the new genai SDK (we used this successfully)
HAS_GENAI = False
try:
    from google import genai
    HAS_GENAI = True
except Exception:
    HAS_GENAI = False

class PlanPal:
    def __init__(self, model_name: str = "models/gemini-2.5-flash"):
        self.model_name = model_name
        # Prefer server-side environment key
        self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self.client = None
        # If server key exists and SDK is available, try to init client now
        if self.api_key and HAS_GENAI:
            try:
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                print("PlanPal: failed to create genai.Client:", e)
                self.client = None

    def ensure_client(self, api_key: str = None, model_name: str = None) -> bool:
        """(Re)initialize client optionally with key/model_name from UI"""
        if api_key:
            self.api_key = api_key
        if model_name:
            self.model_name = model_name
        if not self.api_key or not HAS_GENAI:
            return False
        try:
            self.client = genai.Client(api_key=self.api_key)
            return True
        except Exception as e:
            print("PlanPal.ensure_client error:", e)
            return False

    def _call_model(self, prompt: str, max_output_tokens: int = 512) -> str:
        """Call the model (google.genai path). Returns text or raises exception."""
        if not self.client:
            raise RuntimeError("PlanPal client not initialized")
        # Use models.generate_content which worked in your environment
        resp = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt
        )
        # Try typical response attributes
        text = getattr(resp, "text", None) or getattr(resp, "output_text", None)
        if not text and hasattr(resp, "output"):
            try:
                text_parts = []
                for part in resp.output:
                    if isinstance(part, dict):
                        text_parts.append(part.get("content",""))
                    else:
                        text_parts.append(str(part))
                text = "".join(text_parts)
            except Exception:
                text = str(resp)
        return text or str(resp)

    def chat_response(self, user_input: str) -> str:
        """Friendly chat response (with fallback)"""
        prompt = f"As PlanPal, a friendly event planning assistant, respond briefly and helpfully to: {user_input}"
        # If client not ready, return a helpful offline message
        if not self.client:
            return "(PlanPal offline) Paste a valid GEMINI_API_KEY in PlanPal settings to enable live AI."
        try:
            return self._call_model(prompt)
        except Exception as e:
            print("PlanPal.chat_response error:", e)
            return f"(PlanPal error calling model: {e})"

    def get_event_suggestions(self, location="your city", group_size=4, mood="Chill") -> List[Dict[str,Any]]:
        """Return a list of suggestion dicts (tries to parse JSON; falls back to mock)"""
        prompt = (
            f"Suggest 3 concise event ideas for a group of {group_size} people in {location} "
            f"with mood '{mood}'. Return the results as JSON array of objects with keys: name, description, estimated_cost, duration."
        )
        # If no client, return mock suggestions
        if not self.client:
            return [
                {"name":"Café Hangout","description":f"Chill café near {location}","estimated_cost":"₹300","duration":"2 hours"},
                {"name":"Park Picnic","description":f"Relaxing picnic in a nearby park","estimated_cost":"₹150","duration":"3 hours"},
                {"name":"Food Crawl","description":f"Try popular local eateries","estimated_cost":"₹800","duration":"4 hours"}
            ]
        try:
            text = self._call_model(prompt)
            # Attempt to extract JSON array from response
            if "[" in text and "]" in text:
                j = text[text.find("["): text.rfind("]")+1]
                try:
                    return json.loads(j)
                except Exception:
                    pass
            # If parsing fails, return single suggestion in list
            return [{"name":"Suggestion","description":text}]
        except Exception as e:
            print("PlanPal.get_event_suggestions error:", e)
            # fallback mock
            return [
                {"name":"Café Hangout","description":f"Chill café near {location}","estimated_cost":"₹300","duration":"2 hours"},
                {"name":"Park Picnic","description":f"Relaxing picnic in a nearby park","estimated_cost":"₹150","duration":"3 hours"},
                {"name":"Food Crawl","description":f"Try popular local eateries","estimated_cost":"₹800","duration":"4 hours"}
            ]

# Streamlit UI helpers ------------------------------------------------
def _ensure_planpal():
    """Create PlanPal instance in session_state and auto-init if server key exists."""
    if "planpal" not in st.session_state:
        st.session_state.planpal = PlanPal()
        # if server-side key present, try to ensure client now
        server_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if server_key and HAS_GENAI:
            try:
                st.session_state.planpal.ensure_client(api_key=server_key)
            except Exception:
                pass
    return st.session_state.planpal

def planpal_settings_ui(context: str = "global"):
    """
    Small UI to initialize PlanPal from within the app (no keys saved to disk).
    context: string to namespace widget keys (e.g., "chat", "planner") to avoid duplicate keys.
    """
    p = _ensure_planpal()

    st.subheader("PlanPal Settings")
    st.caption("Paste your GEMINI_API_KEY below to enable live AI (not saved).")

    # If a server-side key exists, prefer it and show status
    server_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    uid = st.session_state.get("user_id", "anon")
    # Build unique key suffix with context + uid
    suffix = f"{context}_{uid}"

    if server_key:
        st.success("✅ PlanPal API key provided by server — live AI enabled.")
        st.caption("Using server-provided API key (hidden). If you want to test your own key, unset server env var and restart.")
        # Ensure session_state knows about it (for init flows)
        st.session_state.setdefault("pp_api_key_source", "server")
        st.session_state.setdefault("pp_api_key", server_key)
    else:
        # show input only when no server key -- use a unique key name
        typed_key = st.text_input("GEMINI_API_KEY (local only)", type="password", key=f"pp_key_input_{suffix}")
        if typed_key:
            st.session_state["pp_api_key"] = typed_key
            st.session_state["pp_api_key_source"] = "local"

    # Model input (unique key)
    model_key = f"pp_model_input_{suffix}"
    model_default = st.session_state.get("pp_model", p.model_name)
    model = st.text_input("Model name", value=model_default, key=model_key)
    st.session_state["pp_model"] = model

    # Buttons - give them unique keys too
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("Initialize PlanPal", key=f"pp_init_btn_{suffix}"):
            # choose API key: server if present else session typed key
            use_key = server_key or st.session_state.get("pp_api_key")
            ok = p.ensure_client(api_key=use_key, model_name=st.session_state.get("pp_model"))
            if ok:
                st.success("PlanPal initialized ✅")
            else:
                st.error("Initialization failed. Check key, model name, and network.")
    with col2:
        if st.button("Use Mock (offline)", key=f"pp_mock_btn_{suffix}"):
            # set client to None => use mock suggestions
            st.session_state.planpal.client = None
            st.success("PlanPal set to offline mock mode")

def show_planpal_chat_ui():
    st.title("🤖 PlanPal Assistant")
    # pass a context so settings widgets don't collision with planner
    planpal_settings_ui(context="chat")
    p = _ensure_planpal()
    if "planpal_history" not in st.session_state:
        st.session_state.planpal_history = []
    # render history
    for msg in st.session_state.planpal_history:
        with st.chat_message(msg["role"]):
            st.write(msg["text"])
    # input
    user_msg = st.chat_input("Ask PlanPal anything about planning...")
    if user_msg:
        st.session_state.planpal_history.append({"role":"user","text":user_msg})
        with st.chat_message("user"):
            st.write(user_msg)
        with st.spinner("Thinking..."):
            reply = p.chat_response(user_msg)
            st.session_state.planpal_history.append({"role":"assistant","text":reply})
            with st.chat_message("assistant"):
                st.write(reply)

def show_event_planner_ui():
    st.title("🎯 PlanPal - Event Suggestions")
    # pass a different context so keys are unique
    planpal_settings_ui(context="planner")
    p = _ensure_planpal()
    col1, col2 = st.columns(2)
    with col1:
        location = st.text_input("Location", "Delhi", key=f"pp_planner_loc_{st.session_state.get('user_id','anon')}")
        group_size = st.number_input("Group Size", min_value=1, value=4, key=f"pp_planner_group_{st.session_state.get('user_id','anon')}")
    with col2:
        mood = st.selectbox("Mood", ["Chill","Foodie","Adventurous"], key=f"pp_planner_mood_{st.session_state.get('user_id','anon')}")
    if st.button("Get AI suggestions", key=f"pp_get_suggestions_{st.session_state.get('user_id','anon')}"):
        with st.spinner("Generating suggestions..."):
            suggestions = p.get_event_suggestions(location=location, group_size=group_size, mood=mood)
            for s in suggestions:
                with st.expander(s.get("name","Suggestion")):
                    st.write(s.get("description",""))
                    st.write("Estimated cost:", s.get("estimated_cost","N/A"))
                    st.write("Duration:", s.get("duration","N/A"))
