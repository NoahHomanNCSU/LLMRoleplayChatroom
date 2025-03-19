from datetime import datetime
import json
import re
import subprocess
import pandas as pd

csv_file = "src/class_project/backstories_filtered.csv"
df = pd.read_csv(csv_file)

# Select a random row
random_row = df.sample(n=1).iloc[0]

# Extract and clean the character sheet
if "age_category_4_llm_parsing_prompt" in df.columns:
    raw_text = random_row["age_category_4_llm_parsing_prompt"]

    # Use regex to extract only the text after "Answer: "
    match = re.search(r"Answer:\s*(.+?)\s*(?:\nQuestion:|$)", raw_text, re.DOTALL)
    if match:
        character_sheet = match.group(1).strip()
    else:
        raise ValueError("Could not extract character sheet from the given format.")
else:
    raise ValueError("Column 'age_category_4_llm_parsing_prompt' not found in CSV.")

# Define dynamic inputs
input_data = {
    'character_sheet': character_sheet,
    'current_year': str(datetime.now().year)
}

# Save to a JSON file
with open("input_data.json", "w") as f:
    json.dump(input_data, f)

# Run CrewAI
result = subprocess.run(["crewai", "run"], text=True, capture_output=True)

print(result.stdout)