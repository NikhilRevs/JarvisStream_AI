import os
import json
import threading
import time
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from elevenlabs.conversational_ai.conversation import Conversation
from elevenlabs.conversational_ai.default_audio_interface import DefaultAudioInterface
import streamlit as st

# -------------------------------
# Load environment variables
# -------------------------------
load_dotenv()
AGENT_ID = os.getenv("AGENT_ID")
API_KEY = os.getenv("API_KEY")

# Debug checks
if not AGENT_ID or not API_KEY:
    raise ValueError("❌ Missing AGENT_ID or API_KEY in .env file")

# -------------------------------
# Shared conversation log
# -------------------------------
conversation_log = []
LOG_FILE = "assistant_log.json"

def save_log():
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(conversation_log, f, indent=2, ensure_ascii=False)

# -------------------------------
# Callback functions
# -------------------------------
def print_agent_response(response):
    entry = {"role": "assistant", "text": response}
    conversation_log.append(entry)
    save_log()

def print_interrupted_response(original, corrected):
    entry = {"role": "assistant", "text": corrected + " (interrupted)"}
    conversation_log.append(entry)
    save_log()

def print_user_transcript(transcript):
    entry = {"role": "user", "text": transcript}
    conversation_log.append(entry)
    save_log()

# -------------------------------
# Voice Assistant Setup
# -------------------------------
client = ElevenLabs(api_key=API_KEY)

conversation = Conversation(
    client,
    AGENT_ID,
    requires_auth=True,
    audio_interface=DefaultAudioInterface(),
    callback_agent_response=print_agent_response,
    callback_agent_response_correction=print_interrupted_response,
    callback_user_transcript=print_user_transcript,
)

# -------------------------------
# Function to run assistant in background
# -------------------------------
def run_assistant():
    try:
        conversation.start_session()
    except Exception as e:
        conversation_log.append({"role": "system", "text": f"Error: {e}"})
        save_log()

# -------------------------------
# Streamlit UI
# -------------------------------
st.set_page_config(page_title="Voice Assistant", layout="wide")
st.title("🎤 Real-Time Voice Assistant")

if st.button("▶️ Start Assistant"):
    t = threading.Thread(target=run_assistant, daemon=True)
    t.start()
    st.success("Assistant started. Speak into your microphone!")

if st.button("⏹ Stop Assistant"):
    try:
        conversation.end_session()
        st.warning("Assistant stopped.")
    except Exception:
        st.error("Assistant is not running.")

# Live updating chat
placeholder = st.empty()

while True:
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            messages = json.load(f)

        with placeholder.container():
            for msg in messages:
                if msg["role"] == "user":
                    st.markdown(f"🧑 **You:** {msg['text']}")
                elif msg["role"] == "assistant":
                    st.markdown(f"🤖 **Assistant:** {msg['text']}")
                elif msg["role"] == "system":
                    st.markdown(f"⚠️ {msg['text']}")
    time.sleep(2)

