import streamlit as st
import json
import os
import sqlite3
import time
import random
from db import get_session_for_user, get_game_state, update_game_state

st.set_page_config(page_title="LLM Deception Chatroom", page_icon="🎭", initial_sidebar_state="expanded")

if "user_id" not in st.session_state:
    st.error("Enter through the lobby.")
    st.stop()

user_id = st.session_state.user_id
session_id = get_session_for_user(user_id)
if not session_id:
    st.error("No session found.")
    st.stop()

conn = sqlite3.connect("sessions.db")
c = conn.cursor()
c.execute("SELECT user1, user2 FROM sessions WHERE session_id = ?", (session_id,))
row = c.fetchone()
conn.close()

if not row or user_id not in row or row[0] == row[1]:
    st.error("Invalid session.")
    st.stop()

other_id = row[1] if row[0] == user_id else row[0]
game_state = get_game_state(session_id)

topics = game_state["topics"]
chars = game_state["characters"]
user_responses = game_state["responses"]
submitted_flags = game_state["submitted"]
survey_data = game_state["survey"]
round_index = game_state["round"]

base = os.path.dirname(__file__)
with open(os.path.join(base, "../data/crewai_outputs.json")) as f:
    crewai_data = json.load(f)
with open(os.path.join(base, "../data/openai_outputs.json")) as f:
    openai_data = json.load(f)

# --- Persistent Character Label Mapping ---
if "character_label_map" not in game_state:
    true_sources = {
        "Partner": {
            "sheet": chars["user"][other_id],
            "responses": lambda topic: user_responses[other_id][topics.index(topic)]
        },
        "CrewAI + Initial": {
            "sheet": chars["ai"][0],
            "responses": lambda topic: crewai_data[chars["ai"][0]][topic]["initial"]
        },
        "CrewAI + Refined": {
            "sheet": chars["ai"][1],
            "responses": lambda topic: crewai_data[chars["ai"][1]][topic]["refined"]
        },
        "OpenAI + Initial": {
            "sheet": chars["ai"][2],
            "responses": lambda topic: openai_data[chars["ai"][2]][topic]["initial"]
        },
        "OpenAI + Refined": {
            "sheet": chars["ai"][3],
            "responses": lambda topic: openai_data[chars["ai"][3]][topic]["refined"]
        }
    }

    label_map = list(true_sources.items())
    random.shuffle(label_map)
    game_state["character_label_map"] = {f"Character {chr(65+i)}": (label, data["sheet"]) for i, (label, data) in enumerate(label_map)}
    game_state["true_sources"] = {f"Character {chr(65+i)}": label for i, (label, _) in enumerate(label_map)}
    update_game_state(session_id, game_state)

label_map = game_state["character_label_map"]
true_sources = game_state["true_sources"]

# --- Robust character sheet display ---
try:
    user_char_sheet = chars["user"][user_id]
except:
    user_char_sheet = "_[Character sheet not found]_"
try:
    partner_char_sheet = chars["user"][other_id]
except:
    partner_char_sheet = "_[Partner character sheet not found]_"

st.sidebar.title("Your Character's Sheet")
st.sidebar.markdown("**Tell me about yourself**")
st.sidebar.markdown(user_char_sheet)

# --- Begin screen ---
if "instructions_shown" not in st.session_state:
    st.session_state.instructions_shown = False
if "start_clicked" not in st.session_state:
    st.session_state.start_clicked = False

if not st.session_state.instructions_shown:
    st.title("LLM Deception Chatroom")
    st.header("Welcome to the Game")
    st.markdown("""
    You are entering a chatroom with five other characters.

    - Some of them may be humans, and some may be AIs.
    - Each character (including yours) has a unique background.
    - Across three rounds, you’ll be given a topic.
    - Respond in 2–3 sentences, staying in character.
    - After each response, you’ll see the others' responses.
    - After 3 rounds, you’ll complete a survey about the other characters.
    """)
    if st.button("Begin") and not st.session_state.start_clicked:
        st.session_state.start_clicked = True
        st.session_state.instructions_shown = True
        st.rerun()
    st.stop()

# --- Wait after Round 3 before survey ---
if round_index >= 3:
    if "ready_for_survey" not in game_state:
        game_state["ready_for_survey"] = {user_id: True}
        update_game_state(session_id, game_state)
    elif user_id not in game_state["ready_for_survey"]:
        game_state["ready_for_survey"][user_id] = True
        update_game_state(session_id, game_state)

    if len(game_state["ready_for_survey"]) < 2:
        st.info("Waiting for your partner to finish Round 3...")
        time.sleep(2)
        st.rerun()

# --- Survey Phase ---
if round_index >= 3:
    if "survey_page" not in st.session_state:
        st.session_state.survey_page = 0
    if "submitted_final" not in st.session_state:
        st.session_state.submitted_final = False
    if user_id not in survey_data:
        survey_data[user_id] = {}

    all_labels = list(label_map.keys())

    if st.session_state.survey_page < len(all_labels):
        label = all_labels[st.session_state.survey_page]
        true_label = true_sources[label]
        sheet = label_map[label][1]

        if true_label == "Partner" and user_id == other_id:
            st.session_state.survey_page += 1
            st.rerun()

        st.title(f"Survey: {label}")
        st.markdown("### Character Sheet")
        st.markdown(sheet)

        for idx, topic in enumerate(topics):
            if "CrewAI" in true_label:
                resp = crewai_data[sheet][topic]["initial"] if "Initial" in true_label else crewai_data[sheet][topic]["refined"]
            elif "OpenAI" in true_label:
                resp = openai_data[sheet][topic]["initial"] if "Initial" in true_label else openai_data[sheet][topic]["refined"]
            else:
                resp = user_responses[other_id][idx]

            st.markdown(f"**Topic {idx+1}: {topic}**")
            st.markdown(f"> {resp}")

        rp_score = st.slider("Roleplay Accuracy (1–5)", 1, 5, key=f"rp_{label}")
        rp_feedback = []
        if rp_score < 5:
            rp_feedback = st.multiselect("Where did it fall short?", [
                "Answers are too generic",
                "Answers contradict the character background",
                "Lacks emotional consistency",
                "Too vague or impersonal",
                "Not believable as a real person"
            ], key=f"rp_fb_{label}")

        hu_score = st.slider("Human-likeness (1–5)", 1, 5, key=f"hu_{label}")
        hu_feedback = []
        if hu_score < 5:
            hu_feedback = st.multiselect("What made it seem artificial?", [
                "Response content",
                "Response structure",
                "Word choice",
                "Tone/voice",
                "Lack of subtlety or nuance",
                "Overly polished or formulaic"
            ], key=f"hu_fb_{label}")

        if st.button("Next", key=f"next_{label}"):
            survey_data[user_id][label] = {
                "true_identity": true_label,
                "character_sheet": sheet,
                "responses": [
                    crewai_data[sheet][topic]["initial"] if true_label == "CrewAI + Initial" else
                    crewai_data[sheet][topic]["refined"] if true_label == "CrewAI + Refined" else
                    openai_data[sheet][topic]["initial"] if true_label == "OpenAI + Initial" else
                    openai_data[sheet][topic]["refined"] if true_label == "OpenAI + Refined" else
                    user_responses[other_id][i]
                    for i, topic in enumerate(topics)
                ],
                "roleplay_score": rp_score,
                "roleplay_feedback": rp_feedback,
                "human_score": hu_score,
                "human_feedback": hu_feedback,
            }
            update_game_state(session_id, game_state)
            st.session_state.survey_page += 1
            st.rerun()
        st.stop()

    if all(label in survey_data[user_id] for label in all_labels):
        if not st.session_state.submitted_final:
            filename = f"results_{session_id}_{user_id}.json"
            with open(filename, "w") as f:
                json.dump(survey_data[user_id], f, indent=2)
            st.session_state.submitted_final = True

        st.success("Survey complete. Thank you!")
        st.stop()
    else:
        st.info("Waiting for your partner to finish the survey...")
        time.sleep(2)
        st.rerun()

# --- Main Game Phase ---
topic = topics[round_index]
st.title(f"Round {round_index + 1}: {topic}")

if not submitted_flags[user_id][round_index]:
    with st.form(key=f"form_{round_index}"):
        response = st.text_area("Your response:", height=100)
        if st.form_submit_button("Submit"):
            user_responses[user_id][round_index] = response
            submitted_flags[user_id][round_index] = True
            update_game_state(session_id, game_state)
            st.rerun()
    st.stop()

if not submitted_flags[other_id][round_index]:
    st.info("Waiting for your partner to respond...")
    time.sleep(2)
    st.rerun()

st.success("Both players submitted. Here are all responses:")

char_map = [("You", user_char_sheet, user_responses[user_id][round_index])]

for label, (true_label, sheet) in label_map.items():
    if "CrewAI" in true_label:
        reply = crewai_data[sheet][topic]["initial"] if "Initial" in true_label else crewai_data[sheet][topic]["refined"]
    elif "OpenAI" in true_label:
        reply = openai_data[sheet][topic]["initial"] if "Initial" in true_label else openai_data[sheet][topic]["refined"]
    else:
        reply = user_responses[other_id][round_index]
    char_map.append((label, sheet, reply))

for name, sheet, reply in char_map:
    st.markdown(f"**{name}**")
    with st.expander("Character Sheet"):
        st.markdown(sheet)
    st.markdown(f"> {reply}")

if st.button("Next Round"):
    if user_id == row[0]:
        game_state["round"] += 1
        update_game_state(session_id, game_state)
    st.rerun()
