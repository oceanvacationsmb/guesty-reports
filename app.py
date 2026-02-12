import streamlit as st
import pandas as pd
import httpx # A more robust library for OAuth2
import time

# --- 1. SESSION STATE ---
if "token" not in st.session_state:
    st.session_state.token = None

# --- 2. THE REBUILT AUTH FUNCTION ---
def get_guesty_token_strict(cid, csec):
    url = "https://open-api.guesty.com/oauth2/token"
    
    # Guesty expects x-www-form-urlencoded
    # We use a dictionary and the 'data' parameter to force this
    payload = {
        "grant_type": "client_credentials",
        "scope": "open-api",
        "client_id": cid.strip(), # Remove any hidden spaces
        "client_secret": csec.strip()
    }
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }

    try:
        with httpx.Client() as client:
            response = client.post(url, data=payload, headers=headers)
            
            if response.status_code == 200:
                return response.json().get("access_token")
            else:
                # This will print the exact JSON error from Guesty for us to see
                st.error(f"Auth Failed ({response.status_code})")
                st.json(response.json()) 
                return None
    except Exception as e:
        st.error(f"Connection error: {str(e)}")
        return None

# --- 3. UI SETUP ---
st.set_page_config(page_title="Guesty Live Sync", layout="wide")
st.title("🔌 Guesty Live Data Integration")

with st.sidebar:
    st.header("🔑 API Credentials")
    # I've locked in the ID from your screenshot to ensure it's correct
    c_id = st.text_input("Client ID", value="0oaszuo22iOg2lk1P5d7")
    c_secret = st.text_input("Client Secret", type="password")
    
    if st.button("Verify & Connect"):
        # Reset 429 error by waiting 1 second before attempt
        time.sleep(1) 
        token = get_guesty_token_strict(c_id, c_secret)
        if token:
            st.session_state.token = token
            st.success("✅ Token acquired!")

# --- 4. DATA FETCHING ---
if st.session_state.token:
    if st.button("🔄 Sync 50 Reservations"):
        res_url = "https://open-api.guesty.com/v1/reservations"
        res_headers = {"Authorization": f"Bearer {st.session_state.token}"}
        res_params = {"limit": 50, "fields": "confirmationCode checkIn money listing.nickname"}
        
        with httpx.Client() as client:
            res_response = client.get(res_url, headers=res_headers, params=res_params)
            
            if res_response.status_code == 200:
                data = res_response.json().get("results", [])
                
                # Re-applying your table formatting
                rows = []
                for r in data:
                    m = r.get("money", {})
                    rows.append({
                        "Reservation ID": r.get("confirmationCode"),
                        "Property": r.get("listing", {}).get("nickname"),
                        "Check-In": r.get("checkIn")[:10] if r.get("checkIn") else "",
                        "Accommodation": float(m.get("fare", 0)),
                        "Cleaning": float(m.get("cleaningFee", 0))
                    })
                
                df = pd.DataFrame(rows)
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
                st.error("Session expired. Please click 'Verify & Connect' again.")
                st.session_state.token = None
