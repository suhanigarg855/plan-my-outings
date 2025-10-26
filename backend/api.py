# backend/api.py
import sqlite3
import uuid
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

DB_PATH = "backend.db"

app = FastAPI(title="PlanMyOutings Backend (SQLite)")

# allow calls from localhost Streamlit
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # for hackathon/dev only; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- DB helpers ----------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS groups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    token TEXT UNIQUE,
                    name TEXT
                 )""")
    c.execute("""CREATE TABLE IF NOT EXISTS plans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    group_id INTEGER,
                    title TEXT,
                    place_json TEXT,
                    FOREIGN KEY(group_id) REFERENCES groups(id)
                 )""")
    c.execute("""CREATE TABLE IF NOT EXISTS votes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    plan_id INTEGER,
                    user_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(plan_id) REFERENCES plans(id)
                 )""")
    conn.commit()
    conn.close()

def get_db():
    return sqlite3.connect(DB_PATH)

init_db()


# ---------- Pydantic models ----------
class CreateGroup(BaseModel):
    name: str

class PlanItem(BaseModel):
    title: str
    place: dict  # simple JSON of place info

class CreatePlans(BaseModel):
    plans: List[PlanItem]


# ---------- API endpoints ----------
@app.post("/groups")
def create_group(payload: CreateGroup):
    token = uuid.uuid4().hex[:8]
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO groups (token, name) VALUES (?, ?)", (token, payload.name))
    conn.commit()
    conn.close()
    return {"token": token}

@app.post("/groups/{token}/plans")
def add_plans(token: str, payload: CreatePlans):
    conn = get_db()
    c = conn.cursor()
    # find group
    c.execute("SELECT id FROM groups WHERE token=?", (token,))
    row = c.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Group not found")
    group_id = row[0]
    inserted = []
    for p in payload.plans:
        place_json = json.dumps(p.place)
        c.execute("INSERT INTO plans (group_id, title, place_json) VALUES (?, ?, ?)", (group_id, p.title, place_json))
        inserted.append({"title": p.title})
    conn.commit()
    conn.close()
    return {"status": "ok", "inserted": len(inserted)}

@app.get("/groups/{token}/plans")
def get_plans(token: str):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id FROM groups WHERE token=?", (token,))
    row = c.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Group not found")
    group_id = row[0]
    c.execute("SELECT id, title, place_json FROM plans WHERE group_id=?", (group_id,))
    plans = []
    rows = c.fetchall()
    for r in rows:
        plan_id, title, place_json = r
        # count votes
        c.execute("SELECT COUNT(*) FROM votes WHERE plan_id=?", (plan_id,))
        vc = c.fetchone()[0]
        plans.append({
            "id": plan_id,
            "title": title,
            "place": json.loads(place_json) if place_json else {},
            "votes": vc
        })
    conn.close()
    return {"plans": plans}

@app.post("/groups/{token}/plans/{plan_id}/vote")
def vote_plan(token: str, plan_id: int, payload: dict):
    """
    payload: {"user_id": "<id>"} -> toggles the vote: if user already voted for plan, remove it; else add vote.
    """
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id required")
    conn = get_db()
    c = conn.cursor()
    # check group exists and plan belongs to it
    c.execute("SELECT id FROM groups WHERE token=?", (token,))
    row = c.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Group not found")
    group_id = row[0]
    c.execute("SELECT id FROM plans WHERE id=? AND group_id=?", (plan_id, group_id))
    if not c.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Plan not found in group")
    # check if vote exists
    c.execute("SELECT id FROM votes WHERE plan_id=? AND user_id=?", (plan_id, user_id))
    existing = c.fetchone()
    if existing:
        # toggle off (remove vote)
        c.execute("DELETE FROM votes WHERE id=?", (existing[0],))
        action = "unvoted"
    else:
        c.execute("INSERT INTO votes (plan_id, user_id) VALUES (?, ?)", (plan_id, user_id))
        action = "voted"
    conn.commit()
    # return updated counts
    c.execute("SELECT COUNT(*) FROM votes WHERE plan_id=?", (plan_id,))
    vc = c.fetchone()[0]
    conn.close()
    return {"status": action, "votes": vc}
