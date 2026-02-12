import streamlit as st
import pandas as pd
import requests
from datetime import date

# --- API AUTHENTICATION ---
# Pulls from secrets.toml or Streamlit Cloud Secrets
CLIENT_ID = st.secrets.get("GUESTY_CLIENT_ID")
CLIENT_SECRET = st.secrets.get("GUESTY_CLIENT_SECRET")

@st.cache_data(ttl=86400)
def get_guesty_token():
    """Fetches a 24-hour Bearer token from Guesty."""
    url = "https://open-api.guesty.com/oauth2/token"
    payload = {
        "grant_type": "client_credentials",
        "scope": "open-api",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    try:
        response = requests.post(url, data=payload, headers=headers)
        response.raise_for_status()
        return response.json().get("access_token")
    except Exception as e:
        st.error(f"Authentication Failed: {e}")
        return None

def fetch_live_reservations(token):
    """Pulls the latest 50 reservations from your Guesty account."""
    url = "https://open-api.guesty.com/v1/reservations"
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    params = {
        "limit": 50,
        "sort": "-createdAt",
        "fields": "confirmationCode checkIn checkOut money listing.nickname"
    }
    response = requests.get(url, headers=headers, params=params)
    return response.json().get("results", [])

# --- DASHBOARD UI ---
st.set_page_config(page_title="Guesty Live Settlement", layout="wide")
st.title("🔌 Guesty Live Data Integration")

token = get_guesty_token()

if token:
    st.success("✅ API Connection Active")
    
    if st.button("🔄 Sync Live Guesty Data"):
        raw_data = fetch_live_reservations(token)
        
        processed_rows = []
        for res in raw_data:
            money = res.get("money", {})
            # Cleaning the data and handling potential Nones
            processed_rows.append({
                "Reservation ID": res.get("confirmationCode"),
                "Property": res.get("listing", {}).get("nickname", "Unnamed Listing"),
                "Check-In": res.get("checkIn")[:10],
                "Accommodation": round(float(money.get("fare", 0)), 2),
                "Cleaning": round(float(money.get("cleaningFee", 0)), 2),
                "Total Paid": round(float(money.get("netIncome", 0)), 2)
            })
        
        st.session_state.live_df = pd.DataFrame(processed_rows)

    if "live_df" in st.session_state:
        df = st.session_state.live_df
        
        # Display live metrics
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Revenue", f"${df['Accommodation'].sum():,.2f}")
        c2.metric("Total Cleaning", f"${df['Cleaning'].sum():,.2f}")
        c3.metric("Total Net", f"${df['Total Paid'].sum():,.2f}")

        # Final Table with Comma Formatting Fixed
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Accommodation": st.column_config.NumberColumn(format="$%,.2f"),
                "Cleaning": st.column_config.NumberColumn(format="$%,.2f"),
                "Total Paid": st.column_config.NumberColumn(format="$%,.2f")
            }
        )
else:
    st.error("Missing API Credentials. Please check your secrets.toml file.")
