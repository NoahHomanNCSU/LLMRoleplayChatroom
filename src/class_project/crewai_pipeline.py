from datetime import datetime
import json
import re
import subprocess
import pandas as pd
import os

# === CONFIG ===
topics_file = "topics.txt"
persona_input_file = "persona_outputs.json"  
output_file = "crewai_persona_outputs.json"
output_dir = "crew_outputs"
os.makedirs(output_dir, exist_ok=True)

# === Load topics (first 10 only) ===
with open(topics_file, "r") as f:
    topics = [line.strip() for line in f if line.strip() and not line.lower().startswith("generated cocktail") and not re.match(r"^\d+\.", line)]
topics = topics[:10]

# === Load existing characters from OpenAI persona output JSON ===
with open(persona_input_file, "r") as f:
    character_data = json.load(f)

# === Collect results ===
all_results = {}

for idx, (character_sheet, _) in enumerate(character_data.items()):
    print(f"\n🧠 Character {idx+1}: {character_sheet[:100]}...")

    topic_results = {}

    for topic in topics:
        # Inject all input values into input_data.json
        inputs = {
            "character_sheet": character_sheet,
            "topic": topic,
            "current_year": str(datetime.now().year)
        }
        with open("input_data.json", "w") as f:
            json.dump(inputs, f)

        # Clear previous outputs
        for path in ["outputs/persona_response.txt", "outputs/critique.txt", "outputs/refined_response.txt"]:
            if os.path.exists(path):
                os.remove(path)

        # Run CrewAI pipeline
        subprocess.run(["crewai", "run"], text=True)

        # Read outputs
        try:
            with open("outputs/persona_response.txt") as f1, open("outputs/refined_response.txt") as f2:
                persona_out = f1.read().strip()
                refined_out = f2.read().strip()
                print(f"\n🔸 Topic: {topic}")
                print(f"Initial: {persona_out}")
                print(f"Refined: {refined_out}")
                topic_results[topic] = {
                    "initial": persona_out,
                    "refined": refined_out
                }
        except FileNotFoundError:
            print("⚠️ Missing output file for topic:", topic)
            continue

    all_results[character_sheet] = topic_results

# Save results
with open(output_file, "w") as f:
    json.dump(all_results, f, indent=4)

print(f"\n✅ All results saved to {output_file}")


