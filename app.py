import streamlit as st
import pandas as pd
import requests
import time

# --- 1. SECURE TOKEN CACHING ---
# ttl=86400 saves the token in memory for 24 hours
@st.cache_data(ttl=86400)
def get_guesty_token(client_id, client_secret):
    url = "https://open-api.guesty.com/oauth2/token"
    
    # Guesty requires x-www-form-urlencoded format
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
    
    try:
        response = requests.post(url, data=payload, headers=headers)
        if response.status_code == 200:
            return response.json().get("access_token")
        else:
            # Displays the exact reason for the 400 error
            st.error(f"Auth Error {response.status_code}: {response.text}")
            return None
    except Exception as e:
        st.error(f"Connection Failed: {e}")
        return None

# --- 2. DATA FETCHING ---
def fetch_reservations(token):
    url = "https://open-api.guesty.com/v1/reservations"
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    # Fields limit the data volume to stay within rate limits
    params = {
        "limit": 50, 
        "fields": "confirmationCode checkIn checkOut money listing.nickname"
    }
    
    response = requests.get(url, headers=headers, params=params)
    return response.json().get("results", []) if response.status_code == 200 else []

# --- 3. UI DASHBOARD ---
st.set_page_config(page_title="Guesty Live Portal", layout="wide")
st.title("🔌 Guesty Live Data Integration")

with st.sidebar:
    st.header("🔑 API Credentials")
    # Using your specific Client ID
    c_id = st.text_input("Client ID", value="0oaszuo22iOg2lk1P5d7")
    c_secret = st.text_input("Client Secret", type="password", help="Found in Integrations > API & Webhooks")
    
    if st.button("Save & Connect"):
        st.cache_data.clear() # Clears old tokens to try a fresh login

# --- 4. EXECUTION ---
if c_id and c_secret:
    token = get_guesty_token(c_id, c_secret)
    
    if token:
        st.success("✅ Connection Secure (Token Cached for 24h)")
        
        if st.button("🔄 Sync Live Data"):
            with st.spinner("Fetching latest reservations..."):
                data = fetch_reservations(token)
                if data:
                    # Flattening the nested JSON for the report
                    processed = []
                    for r in data:
                        m = r.get("money", {})
                        processed.append({
                            "Reservation": r.get("confirmationCode"),
                            "Property": r.get("listing", {}).get("nickname"),
                            "Check-In": r.get("checkIn")[:10] if r.get("checkIn") else "",
                            "Accommodation": float(m.get("fare", 0)),
                            "Cleaning": float(m.get("cleaningFee", 0))
                        })
                    
                    df = pd.DataFrame(processed)
                    st.dataframe(df, use_container_width=True, hide_index=True,
                                 column_config={
                                     "Accommodation": st.column_config.NumberColumn(format="$%,.2f"),
                                     "Cleaning": st.column_config.NumberColumn(format="$%,.2f")
                                 })
                else:
                    st.warning("No data returned. Check if the account has active reservations.")
else:
    st.info("Enter your Client Secret to establish a secure link.")
