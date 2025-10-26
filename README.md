# 🗺️ Plan My Outings  
### Smart Group Event Planner with AI-Powered Assistant 🤖  

---

## 📖 Overview  

**Plan My Outings** is a smart event-planning web app that helps friends and groups easily decide **when, where, and what to do** together — whether it's a movie night, a trip, or a casual hangout.  
No more endless WhatsApp messages! The app brings together **group creation**, **polls**, **RSVPs**, and an **AI assistant (PlanPal)** that suggests personalized plans, venues, and itineraries based on user preferences and location.

Built with **Streamlit**, **SQLite**, and **Gemini API (Google Generative AI)**.

---

## 🚀 Key Features  

### 🧑‍🤝‍🧑 Group Management  
- Create and share group invite tokens.  
- Join groups using unique tokens.  
- View all your joined groups.  

### 📅 Event Management  
- Create, edit, and view events in your dashboard.  
- Event details include title, description, type, duration, cost, and location.  
- RSVP system: participants can mark **Attending / Maybe / Not Attending**.  
- Group creator can view RSVPs from all participants.  

### 🤖 PlanPal – AI Event Assistant  
- Integrated with **Google Gemini API** (Generative AI).  
- Chat-based assistant that suggests outings, restaurants, or itineraries.  
- Smart recommendations based on **location**, **budget**, and **preferences** (e.g. foodie, outdoor, chill).  
- Separate tabs for Chat and AI-based Event Planner.

### 📍 Smart Recommendations (future improvements)
- Suggest “Best-rated cafés near all group members.”  
- “Mood-based” recommendations — adventurous, relaxing, foodie, etc.

---

## 🛠️ Tech Stack  

| Component | Technology |
|------------|-------------|
| **Frontend** | Streamlit |
| **Backend** | Python (Flask-style functions within Streamlit) |
| **Database** | SQLite |
| **AI Integration** | Google Generative AI (Gemini 1.5-Pro / 1.0-Pro) |
| **Location Services** | Geopy (for coordinates & address mapping) |
| **Version Control** | Git & GitHub |

---

## 🧩 Project Structure  

```
plan-my-outings/
├── backend/
│   ├── __init__.py
│   ├── api.py
│   ├── api_handler.py
│   ├── authentication_new.py
│   ├── event_management.py
│   └── planpal_bot.py
│
├── streamlit_app/
│   ├── temp_app.py        # main entry (the file you run with `streamlit run ...`)
│   ├── frontend.py
│   ├── main.py
│   └── planpal_interface.py
│
├── requirements.txt
├── README.md
└── .gitignore

```


---

## ⚙️ Setup Instructions  

Follow these simple steps to run the project locally:

### 1️⃣ Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/plan-my-outings.git
cd plan-my-outings
```

### 2️⃣ Create a virtual environment
```bash
python3 -m venv venv
source venv/bin/activate   # On macOS / Linux
venv\Scripts\activate      # On Windows
```
### 3️⃣ Install dependencies
```bash
pip install -r requirements.txt
```

### 4️⃣ Set up your Gemini API Key

Get a Gemini API Key from Google AI Studio.

Then, in your terminal:
```bash
export GEMINI_API_KEY="YOUR_API_KEY_HERE"
```
_(On Windows CMD use `set` instead of `export`.)_

### 5️⃣ Run the app
```bash
cd streamlit_app
streamlit run temp_app.py
```
### 6️⃣ Open in Browser
Streamlit will show a local URL — open it (usually http://localhost:8501)


## 🎬 How It Works

1. Sign Up / Login: Users register and log in with secure validation.
2. Create Groups: A unique token is generated for group sharing.
3. Create Events: Specify event details, type, duration, location, and cost.
4. Invite Members: Share token — members can join and RSVP.
5. PlanPal AI Assistant: Chat or ask for outing ideas, restaurants, itineraries.
6. Dashboard: View all created or joined events with status.

## 🤖 PlanPal Assistant (AI Feature)

PlanPal is an AI-based event planning assistant integrated into the app using the **Google Gemini API**.  
It is designed to generate smart event suggestions, venue recommendations, and itineraries based on user preferences such as mood, group size, and location.

### 🔍 Current Status
Due to limited API access and time constraints, the live AI responses are currently **disabled** in this demo version.  
However, the backend integration with the Gemini API is already implemented in the `planpal_bot.py` file and can be activated once a valid API key is available.

### 🧠 How It Works (Conceptually)
- Users can chat with PlanPal in the app to receive:
  - 🏖️ Mood-based event ideas (e.g., “Chill”, “Foodie”, “Adventurous”)  
  - 📍 Smart location-based suggestions  
  - 🗓️ Itinerary recommendations for group outings  
- Responses are powered by **Google Gemini (Generative AI)** via the `google-generativeai` Python library.

> _Note: The PlanPal AI feature has been built and tested locally using mock data. Live interaction can be enabled by setting a valid Google Gemini API key._



## 🧾 License

This project is created as part of Hackarena 2025 (IIT Mandi).
For educational and demo purposes only.


## ⭐ Acknowledgements  

- [**Streamlit**](https://streamlit.io/) — for rapid UI development  
- [**Google Gemini API**](https://ai.google.dev/) — for AI capabilities  
- [**Geopy**](https://geopy.readthedocs.io/) — for location services  
- 💡 *Inspiration:* the chaos of planning outings with friends 😄  

> _"Don’t just plan your outings — let PlanPal make them smarter!"_
