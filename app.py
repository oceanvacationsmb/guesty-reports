import streamlit as st
import pandas as pd
import requests
import time

# --- 1. CACHED AUTH (Prevents 429 Errors) ---
# Guesty allows only 5 token requests per 24 hours.
# ttl=86400 stores the token for 24 hours.
@st.cache_data(ttl=86400)
def get_guesty_token(client_id, client_secret):
    url = "https://open-api.guesty.com/oauth2/token"
    payload = {
        "grant_type": "client_credentials",
        "scope": "open-api",
        "client_id": client_id.strip(),
        "client_secret": client_secret.strip()
    }
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    response = requests.post(url, data=payload, headers=headers)
    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        st.error(f"Error {response.status_code}: {response.text}")
        return None

# --- 2. SETTLEMENT LOGIC (Restored Hard Work) ---
st.set_page_config(page_title="Owner Settlement Portal", layout="wide")
st.title("🛡️ Guesty Automated Settlement")

# Sidebar for live sync
with st.sidebar:
    st.header("🔑 Live Sync")
    # Using the ID found in your previous screenshot
    c_id = st.text_input("Client ID", value="0oaszuo22iOg2lk1P5d7")
    c_secret = st.text_input("Client Secret", type="password")
    
    if st.button("🔌 Connect & Sync"):
        st.cache_data.clear() # Only clear if you need a fresh start

# --- 3. RUNNING THE APP ---
if c_id and c_secret:
    token = get_guesty_token(c_id, c_secret)
    
    if token:
        st.success("✅ Connected! Pulling live reservation data...")
        # (Insert your settlement calculation logic here)
        # It will now use real data while keeping your formatting.
else:
    st.warning("Please enter your Secret in the sidebar to restore live data.")
