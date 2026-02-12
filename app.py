import streamlit as st
import pandas as pd
import requests
import time

# --- 1. CACHED AUTHENTICATION ---
# ttl=86400 means the token is saved for 24 hours
@st.cache_data(ttl=86400)
def get_guesty_token(client_id, client_secret):
    url = "https://open-api.guesty.com/oauth2/token"
    payload = {
        "grant_type": "client_credentials",
        "scope": "open-api",
        "client_id": client_id,
        "client_secret": client_secret
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    
    try:
        response = requests.post(url, data=payload, headers=headers)
        if response.status_code == 200:
            return response.json().get("access_token")
        else:
            st.error(f"Auth Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"Connection failed: {e}")
        return None

# --- 2. DATA FETCHING ---
def fetch_reservations(token):
    url = "https://open-api.guesty.com/v1/reservations"
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    # Limit fields to keep the response small and fast
    params = {
        "limit": 50, 
        "fields": "confirmationCode checkIn money listing.nickname"
    }
    
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json().get("results", [])
    return []

# --- 3. UI DASHBOARD ---
st.set_page_config(page_title="Guesty Live Portal", layout="wide")
st.title("🔌 Guesty Live Data Integration")

with st.sidebar:
    st.header("🔑 API Credentials")
    # Using type="password" for the secret for security
    c_id = st.text_input("Client ID", value="0oaszuo22iOg2lk1P5d7")
    c_secret = st.text_input("Client Secret", type="password")
    
    connect_clicked = st.button("Connect to Guesty")

# --- 4. EXECUTION ---
if c_id and c_secret:
    # This only runs the heavy API call if the token isn't already cached
    token = get_guesty_token(c_id, c_secret)
    
    if token:
        st.success("✅ Connected to Guesty (Token Cached)")
        
        if st.button("🔄 Sync Live Reservations"):
            with st.spinner("Fetching latest data..."):
                data = fetch_reservations(token)
                
                if data:
                    # Flatten the 'money' and 'listing' objects for the table
                    processed = []
                    for r in data:
                        m = r.get("money", {})
                        processed.append({
                            "Reservation ID": r.get("confirmationCode"),
                            "Property": r.get("listing", {}).get("nickname"),
                            "Check-In": r.get("checkIn")[:10] if r.get("checkIn") else "",
                            "Accommodation": float(m.get("fare", 0)),
                            "Cleaning": float(m.get("cleaningFee", 0))
                        })
                    
                    df = pd.DataFrame(processed)
                    
                    # Display with the requested comma formatting
                    st.dataframe(
                        df, 
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "Accommodation": st.column_config.NumberColumn(format="$%,.2f"),
                            "Cleaning": st.column_config.NumberColumn(format="$%,.2f")
                        }
                    )
                else:
                    st.warning("No reservations found.")
else:
    st.info("Please enter your Client Secret to begin.")
