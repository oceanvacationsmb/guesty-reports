import streamlit as st
import pandas as pd
import requests
from datetime import date

# --- 1. SESSION STATE FOR AUTH ---
if "access_token" not in st.session_state:
    st.session_state.access_token = None

# --- 2. AUTHENTICATION FUNCTION ---
def get_guesty_token(client_id, client_secret):
    url = "https://open-api.guesty.com/oauth2/token"
    # Guesty requires these specific keys in the body
    payload = {
        "grant_type": "client_credentials",
        "scope": "open-api",
        "client_id": client_id,
        "client_secret": client_secret
    }
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    response = requests.post(url, data=payload, headers=headers)
    
    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        st.error(f"Failed to Connect: {response.status_code} - {response.text}")
        return None

# --- 3. UI SETUP ---
st.set_page_config(page_title="Guesty Live Integration", layout="wide")
st.title("🔌 Guesty Live Data Integration")

# Attempt to load from secrets first
s_id = st.secrets.get("GUESTY_CLIENT_ID", "")
s_secret = st.secrets.get("GUESTY_CLIENT_SECRET", "")

# Sidebar for Credentials
with st.sidebar:
    st.header("🔑 API Credentials")
    c_id = st.text_input("Client ID", value=s_id, type="default")
    c_secret = st.text_input("Client Secret", value=s_secret, type="password")
    
    if st.button("Connect to Guesty"):
        with st.spinner("Authenticating..."):
            token = get_guesty_token(c_id, c_secret)
            if token:
                st.session_state.access_token = token
                st.success("Connected!")
            else:
                st.session_state.access_token = None

# --- 4. DATA FETCHING (Only if authenticated) ---
if st.session_state.access_token:
    st.info("✅ Connection Active. You can now pull reservations.")
    
    if st.button("🔄 Sync Reservations"):
        url = "https://open-api.guesty.com/v1/reservations"
        headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
        params = {"limit": 20, "fields": "confirmationCode checkIn checkOut money listing.nickname"}
        
        res = requests.get(url, headers=headers, params=params)
        if res.status_code == 200:
            data = res.json().get("results", [])
            df = pd.json_normalize(data) # Flattens the nested JSON
            st.dataframe(df)
        else:
            st.error("Could not fetch data. Token might have expired.")
else:
    st.warning("Please enter your Client ID and Secret in the sidebar and click 'Connect'.")
