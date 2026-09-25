import os
import streamlit as st
import requests
import time
import uuid
import logfire
from dotenv import load_dotenv

env_path = os.path.abspath(os.path.dirname(__file__), "..",".env")
load_dotenv(dotenv_path=env_path)

#init logfire
try:
    token = os.getenv("LOGFIRE_TOKEN")
    if not token:
        print("ERROR: LOGFIRE_TOKEN is empty or None!")
    logfire.configure(token=token)

    LOGFIRE_STATUS = "Connected & Tracing"
except Exception as e:
    print(f"Logfire Init Error in UI: {e}")
    LOGFIRE_STATUS = f"Standby (Error: {e})"


# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Enterprise Agentic RAG",
    page_icon="🤖",
    layout="wide",
)

# --- AVATARS ---
AI_AVATAR = "🤖"
USER_AVATAR = "👤"

#session management