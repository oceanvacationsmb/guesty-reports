import streamlit as st
import pandas as pd
import requests
import time

# --- 1. SESSION STATE MANAGEMENT ---
# This prevents re-authenticating on every click
if "access_token" not in st.session_state:
    st.session_state.access_token = None
if "expires_at" not in st.session_state:
    st.session_state.expires_at = 0

# --- 2. AUTHENTICATION ---
def get_guesty_token(client_id, client_secret):
    # Check if we already have a valid token in memory
    if st.session_state.access_token and time.time() < st.session_state.expires_at:
        return st.session_state.access_token

    url = "https://open-api.guesty.com/oauth2/token"
    payload = {
        "grant_type": "client_credentials",
        "scope": "open-api",
        "client_id": client_id,
        "client_secret": client_secret
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    
    response = requests.post(url, data=payload, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        st.session_state.access_token = data.get("access_token")
        # Store expiration (usually 24 hours)
        st.session_state.expires_at = time.time() + data.get("expires_in", 86400)
        return st.session_state.access_token
    else:
        st.error(f"Failed to Connect: {response.status_code} - {response.text}")
        return None

# --- 3. UI SETUP ---
st.set_page_config(page_title="Guesty Live Integration", layout="wide")
st.title("🔌 Guesty Live Data Integration")

with st.sidebar:
    st.header("🔑 API Credentials")
    c_id = st.text_input("Client ID", type="default")
    c_secret = st.text_input("Client Secret", type="password")
    
    if st.button("Connect to Guesty"):
        # Clear old token to force a fresh login if requested
        st.session_state.access_token = None 
        token = get_guesty_token(c_id, c_secret)
        if token:
            st.success("Connected & Token Saved!")

# --- 4. DATA FETCHING ---
if st.session_state.access_token:
    if st.button("🔄 Sync Reservations"):
        url = "https://open-api.guesty.com/v1/reservations"
        headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
        # Limit the pull to avoid secondary rate limits
        params = {"limit": 20, "fields": "confirmationCode checkIn money listing.nickname"}
        
        res = requests.get(url, headers=headers, params=params)
        if res.status_code == 200:
            st.dataframe(pd.json_normalize(res.json().get("results", [])))
        elif res.status_code == 429:
            st.warning("⚠️ Still rate limited. Please wait 1-2 minutes before clicking again.")
