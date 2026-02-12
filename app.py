import streamlit as st
import pandas as pd
import requests

# --- 1. DIRECT AUTH FUNCTION ---
@st.cache_data(ttl=86400) # Only runs ONCE every 24 hours to avoid 429 errors
def get_guesty_token(cid, csec):
    url = "https://open-api.guesty.com/oauth2/token"
    
    # Direct payload formatting
    data = {
        "grant_type": "client_credentials",
        "scope": "open-api",
        "client_id": cid,
        "client_secret": csec
    }
    
    # Guesty is very strict about this Header
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    response = requests.post(url, data=data, headers=headers)
    
    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        st.error(f"⚠️ Connection Error {response.status_code}")
        st.json(response.json()) # Shows the full error details for debugging
        return None

# --- 2. UI SETUP ---
st.set_page_config(page_title="Guesty Live Connection", layout="wide")
st.title("🔌 Guesty Live Data Integration")

# Sidebar for immediate testing
with st.sidebar:
    st.header("🔑 Credentials")
    # I've pre-filled your ID from the screenshot to save you time
    input_id = st.text_input("Client ID", value="0oaszuo22iOg2lk1P5d7")
    input_secret = st.text_input("Client Secret", type="password")
    
    # Use a specific "Force Connect" button
    connect_btn = st.button("Connect & Fetch Data")

# --- 3. DATA FETCHING ---
if connect_btn:
    if not input_secret:
        st.warning("Please enter your Client Secret.")
    else:
        # 1. Get Token
        token = get_guesty_token(input_id, input_secret)
        
        if token:
            st.success("✅ Success! Connected to Guesty.")
            
            # 2. Fetch Reservations immediately
            res_url = "https://open-api.guesty.com/v1/reservations"
            res_headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
            res_params = {"limit": 10, "fields": "confirmationCode checkIn money listing.nickname"}
            
            with st.spinner("Syncing your latest 10 reservations..."):
                res_data = requests.get(res_url, headers=res_headers, params=res_params)
                
                if res_data.status_code == 200:
                    raw_results = res_data.json().get("results", [])
                    
                    # 3. Format Table
                    clean_data = []
                    for r in raw_results:
                        m = r.get("money", {})
                        clean_data.append({
                            "Reservation ID": r.get("confirmationCode"),
                            "Property": r.get("listing", {}).get("nickname"),
                            "Check-In": r.get("checkIn")[:10] if r.get("checkIn") else "N/A",
                            "Accommodation": float(m.get("fare", 0)),
                            "Cleaning": float(m.get("cleaningFee", 0))
                        })
                    
                    df = pd.DataFrame(clean_data)
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
                    st.error(f"Failed to fetch data: {res_data.text}")
