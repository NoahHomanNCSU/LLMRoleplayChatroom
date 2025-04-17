import streamlit as st
import uuid
import requests
import sqlite3
import time
import json
import os
import random
from db import (
    init_db,
    enqueue_user,
    dequeue_pair,
    get_session_for_user,
    cleanup_stale_queue,
    clear_session_for_user,
    init_game_state
)

st.set_page_config(page_title="LLM Deception Lobby", page_icon="🕹️", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    [data-testid="stSidebarNav"] { display: none !important; }
    </style>
""", unsafe_allow_html=True)

def get_client_id():
    try:
        response = requests.get("http://localhost:5000/init")
        return response.json().get("client_id", str(uuid.uuid4()))
    except:
        return str(uuid.uuid4())

# DB setup
init_db()
cleanup_stale_queue()

# User identity setup
if "user_id" not in st.session_state:
    st.session_state.user_id = get_client_id()
user_id = st.session_state.user_id

# Only enqueue once
if "queued" not in st.session_state:
    clear_session_for_user(user_id)
    enqueue_user(user_id)
    st.session_state.queued = True

# Attempt to form new session
if "matched" not in st.session_state:
    session_id, users = dequeue_pair()
    if session_id and user_id in users and users[0] != users[1]:
        st.session_state.matched = True

        base = os.path.dirname(__file__)
        with open(os.path.join(base, "data/topics.json")) as f:
            topics = json.load(f)
        with open(os.path.join(base, "data/character_sheets.json")) as f:
            sheets = json.load(f)

        selected_topics = random.sample(topics, 3)
        selected_characters = random.sample(sheets, 6)  # 2 humans + 4 AI

        game_state = {
            "topics": selected_topics,
            "characters": {
                "user": {users[0]: selected_characters[0], users[1]: selected_characters[1]},
                "ai": selected_characters[2:]
            },
            "round": 0,
            "responses": {users[0]: [None]*3, users[1]: [None]*3},
            "submitted": {users[0]: [False]*3, users[1]: [False]*3},
            "survey": {users[0]: {}, users[1]: {}}
        }

        init_game_state(session_id, game_state)
        st.rerun()

# Check existing session
existing_session = get_session_for_user(user_id)
if existing_session:
    conn = sqlite3.connect("sessions.db")
    c = conn.cursor()
    c.execute("SELECT user1, user2 FROM sessions WHERE session_id = ?", (existing_session,))
    row = c.fetchone()
    conn.close()
    if row and row[0] != row[1] and user_id in row:
        st.switch_page("pages/game.py")

# Lobby UI
st.title("LLM Deception Game Lobby")
st.info("Waiting for another player to join...")
st.markdown("Keep this tab open. The game will start automatically once you're matched.")

placeholder = st.empty()
while True:
    session_id = get_session_for_user(user_id)
    if session_id:
        conn = sqlite3.connect("sessions.db")
        c = conn.cursor()
        c.execute("SELECT user1, user2 FROM sessions WHERE session_id = ?", (session_id,))
        row = c.fetchone()
        conn.close()
        if row and row[0] != row[1] and user_id in row:
            st.session_state.matched = True
            st.rerun()
    time.sleep(2)

    conn = sqlite3.connect("sessions.db")
    c = conn.cursor()
    c.execute("SELECT * FROM queue")
    queue = c.fetchall()
    c.execute("SELECT * FROM sessions")
    sessions = c.fetchall()
    conn.close()

    with placeholder.container():
        st.write("Queue:", queue)
        st.write("Sessions:", sessions)

# Manual reset
if st.button("Reset Session"):
    clear_session_for_user(user_id)
    conn = sqlite3.connect("sessions.db")
    c = conn.cursor()
    c.execute("DELETE FROM queue WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()
