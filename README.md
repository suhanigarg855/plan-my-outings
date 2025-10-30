# 🗺️ Plan My Outings  
### Smart Group Event Planner with AI-Powered Assistant 🤖  

---

## 📖 Overview  

**Plan My Outings** is a smart event-planning web app that helps friends and groups easily decide **when, where, and what to do** together — whether it's a movie night, a trip, or a casual hangout.  
No more endless WhatsApp messages! The app brings together **group creation**, **polls**, **RSVPs**, and an **AI assistant (PlanPal)** that suggests personalized plans, venues, and itineraries based on user preferences and location.  

Built with **Streamlit**, **SQLite**, and **Google Gemini (Generative AI)**.  

---

## 🚀 Key Features  

### 🧑‍🤝‍🧑 Group Management  
- Create and share group invite tokens.  
- Join groups using unique tokens.  
- View and manage all your joined groups.  

### 📅 Event Management  
- Create, edit, and view events in your dashboard.  
- Event details include title, description, duration, cost, and location.  
- RSVP system: participants can mark **Attending / Maybe / Not Attending**.  
- Group creator can view RSVPs from all participants.  

### 🤖 PlanPal – AI Event Assistant  
- Integrated with **Google Gemini 2.5 Flash / Pro API** via the latest `google.genai` SDK.  
- Chat-based assistant that suggests outings, restaurants, and itineraries.  
- Smart recommendations based on **location**, **group size**, and **mood** (Chill, Foodie, Adventurous).  
- Two modes:
  - 💬 **Chat** — talk naturally with the AI assistant.  
  - 🎯 **Planner** — get structured event suggestions instantly.  
- Automatically uses a **server-side API key** if available (no need for every user to add one).

### 📍 Smart Suggestions  
- Get “mood-based” and “midpoint” outing ideas for multiple cities.  
- Integrates **Geopy** for computing geographic centroids between members.  

---

## 🛠️ Tech Stack  

| Component | Technology |
|------------|-------------|
| **Frontend** | Streamlit |
| **Backend** | Python (modular backend functions) |
| **Database** | SQLite |
| **AI Integration** | Google Gemini (via `google-genai`) |
| **Location Services** | Geopy |
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
|   ├── planpal_bot.py
│   └── backend.db # SQLite database
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

>_Note: If you set the API key as an environment variable, the app automatically detects it — no need to paste it in the UI._

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
5. PlanPal AI Assistant: Chat or get AI-generated outing ideas and itineraries.
6. Dashboard: View all created or joined events with status.


## 🤖 PlanPal Assistant (AI Feature)

PlanPal is an AI-based event planning assistant integrated into the app using the **Google Gemini API**.  
It enhances planning by suggesting creative outing ideas, optimized itineraries, and venue options based on the user’s input (city, mood, group size, etc.).

### ✨ What PlanPal Can Do

#### 💬 Chat Mode — Natural, conversational interaction
Ask questions like:
> “Suggest a fun evening plan for four friends in Delhi under ₹1000.”     
“It’s raining — what indoor plans can we do in Noida?                         
“We’re in a foodie mood. Any ideas near Connaught Place?”

#### 🎯 Planner Mode — Structured AI suggestions
Get ready-to-use event recommendations with details like:
- Event name
- Description
- Estimated cost
- Duration

### 🧠 Under the Hood
PlanPal is powered by **Google Gemini 2.5 Flash / Pro**, integrated through the `google.genai` Python SDK.
It can work in two modes:
- ✅ Live Mode — Uses a valid Gemini API key (auto-detected from environment).
- 🔁 Mock Mode — Works offline with locally simulated responses.

PlanPal intelligently adapts responses based on:
- Group size
- User mood (Chill, Foodie, Adventurous)
- Location or midpoint between group members

Internally, it uses modular backend logic from `planpal_bot.py` and returns structured responses that can later be used to auto-create events in the app.


## 🧾 License

This project is created as part of Hackarena 2025 (IIT Mandi).
For educational and demo purposes only.


## ⭐ Acknowledgements  

- [**Streamlit**](https://streamlit.io/) — for rapid UI development  
- [**Google Gemini API**](https://ai.google.dev/) — for AI capabilities  
- [**Geopy**](https://geopy.readthedocs.io/) — for location services  
- 💡 *Inspiration:* the chaos of planning outings with friends 😄  

> _"Don’t just plan your outings — let PlanPal make them smarter!"_
