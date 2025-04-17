# LLM Roleplay Chatroom

This is a multiplayer social deception game built with Streamlit, where human players interact with AI-generated characters to determine who is real and who is an AI.

## Setup Instructions

```bash
# Install dependencies
pip install streamlit
brew install ngrok

# Start ngrok (will fail the first time but gives required URLs)
ngrok https 8501

# Follow the first URL to create an ngrok account
# Then follow the second URL to get and run the authentication command they provide

# Configure Streamlit to allow external access
mkdir -p ~/.streamlit
cat <<EOF > ~/.streamlit/config.toml
[server]
headless = true
enableCORS = false
enableXsrfProtection = false
address = "0.0.0.0"
port = 8501
EOF

# Make sure your .env file exists at the root of the project and includes:
# OPENAI_API_KEY=your-openai-key-here

# Initialize the database
cd chatroom_app
python -c "import db; db.init_db()"

# If sessions break between runs, you can reset:
# rm sessions.db && python -c "import db; db.init_db()"

# In one terminal, start ngrok again and leave it running
ngrok https 8501

# In another terminal, run the Streamlit app
streamlit run main.py

# Access the app at http://0.0.0.0:8501
# Share the "Forwarding" link from the ngrok window with the other player
# Both players must be on the same network

