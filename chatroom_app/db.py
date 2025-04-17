import os
import sqlite3
import time
import uuid
import json
from uuid import uuid4

DB_FILE = "sessions.db"
if os.path.dirname(DB_FILE):
    os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS queue (
            user_id TEXT PRIMARY KEY,
            last_seen INTEGER
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            user1 TEXT,
            user2 TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS game_state (
            session_id TEXT PRIMARY KEY,
            state_json TEXT
        )
    ''')
    conn.commit()
    conn.close()

def enqueue_user(user_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    now = int(time.time())
    c.execute("INSERT OR REPLACE INTO queue (user_id, last_seen) VALUES (?, ?)", (user_id, now))
    conn.commit()
    conn.close()

def cleanup_stale_queue(timeout_seconds=120):
    cutoff = int(time.time()) - timeout_seconds
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM queue WHERE last_seen < ?", (cutoff,))
    conn.commit()
    conn.close()

def dequeue_pair():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT user_id FROM queue ORDER BY last_seen ASC")
    all_users = [row[0] for row in c.fetchall()]

    available_users = []
    for user_id in all_users:
        c.execute("SELECT session_id FROM sessions WHERE user1 = ? OR user2 = ?", (user_id, user_id))
        if not c.fetchone():
            available_users.append(user_id)

    for i in range(len(available_users)):
        for j in range(i + 1, len(available_users)):
            u1 = available_users[i]
            u2 = available_users[j]
            if u1 != u2:
                session_id = str(uuid.uuid4())
                c.execute("DELETE FROM queue WHERE user_id IN (?, ?)", (u1, u2))
                c.execute("INSERT INTO sessions (session_id, user1, user2) VALUES (?, ?, ?)",
                          (session_id, u1, u2))
                conn.commit()
                conn.close()
                return session_id, [u1, u2]
    conn.close()
    return None, None

def get_session_for_user(user_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT session_id FROM sessions WHERE user1 = ? OR user2 = ?", (user_id, user_id))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

def clear_session_for_user(user_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM sessions WHERE user1 = ? OR user2 = ?", (user_id, user_id))
    conn.commit()
    conn.close()

def init_game_state(session_id, state):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO game_state (session_id, state_json) VALUES (?, ?)", (session_id, json.dumps(state)))
    conn.commit()
    conn.close()

def get_game_state(session_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT state_json FROM game_state WHERE session_id = ?", (session_id,))
    row = c.fetchone()
    conn.close()
    return json.loads(row[0]) if row else None

def update_game_state(session_id, state):
    init_game_state(session_id, state)
