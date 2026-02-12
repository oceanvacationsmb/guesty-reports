import streamlit as st
import pandas as pd
import requests
from datetime import date

# --- 1. CONFIG & API AUTH ---
# ⚠️ Store these in your Streamlit Secrets for security!
CLIENT_ID = st.secrets.get("GUESTY_CLIENT_ID", "YOUR_ID")
CLIENT_SECRET = st.secrets.get("GUESTY_CLIENT_SECRET", "YOUR_SECRET")

@st.cache_data(ttl=86400) # Caches token for 24 hours
def get_guesty_token():
    url = "https://open-api.guesty.com/oauth2/token"
    payload = {
        "grant_type": "client_credentials",
        "scope": "open-api",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }
    headers = {"Accept": "application/json", "Content-Type": "application/x-www-form-urlencoded"}
    response = requests.post(url, data=payload, headers=headers)
    return response.json().get("access_token")

# --- 2. DATA PULLING ---
def fetch_reservations(token):
    url = "https://open-api.guesty.com/v1/reservations"
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    
    # Filtering for confirmed reservations
    params = {
        "limit": 50,
        "sort": "-createdAt",
        "fields": "confirmationCode checkIn checkOut money listing.nickname"
    }
    
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json().get("results", [])
    else:
        st.error(f"Error fetching data: {response.text}")
        return []

# --- 3. UI DASHBOARD ---
st.set_page_config(page_title="Guesty Live Portal", layout="wide")
st.title("🔌 Guesty Live Data Integration")

token = get_guesty_token()

if token:
    if st.button("🔄 Sync Live Data"):
        raw_data = fetch_reservations(token)
        
        # Process API response into our table format
        processed_rows = []
        for res in raw_data:
            money = res.get("money", {})
            processed_rows.append({
                "Reservation ID": res.get("confirmationCode"),
                "Property": res.get("listing", {}).get("nickname", "N/A"),
                "Check-In": res.get("checkIn")[:10], # Keep just YYYY-MM-DD
                "Fare": money.get("fare", 0),
                "Cleaning": money.get("cleaningFee", 0),
                "Total Paid": money.get("netIncome", 0)
            })
        
        df = pd.DataFrame(processed_rows)
        st.session_state.live_df = df

    # Display Table
    if "live_df" in st.session_state:
        st.dataframe(
            st.session_state.live_df, 
            column_config={
                "Fare": st.column_config.NumberColumn(format="$%,.2f"),
                "Cleaning": st.column_config.NumberColumn(format="$%,.2f"),
                "Total Paid": st.column_config.NumberColumn(format="$%,.2f")
            },
            hide_index=True
        )
else:
    st.warning("Please enter your API credentials to begin.")
