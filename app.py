import streamlit as st
import pandas as pd
import requests
import time

# --- 1. THE "GUESTY HANDSHAKE" (Fixes 400 & 429) ---
@st.cache_data(ttl=86400) # Caches for 24h so we don't hit the 429 limit
def get_guesty_token(cid, csec):
    url = "https://open-api.guesty.com/oauth2/token"
    # DATA must be sent as a flat dictionary, not a nested JSON object
    payload = {
        "grant_type": "client_credentials",
        "scope": "open-api",
        "client_id": cid.strip(),
        "client_secret": csec.strip()
    }
    # These headers are the "secret sauce" for Guesty
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }
    
    try:
        # We use 'data=payload' to force x-www-form-urlencoded format
        response = requests.post(url, data=payload, headers=headers)
        if response.status_code == 200:
            return response.json().get("access_token")
        else:
            st.error(f"Guesty says: {response.json().get('error_description', response.text)}")
            return None
    except Exception as e:
        st.error(f"Connection Failed: {e}")
        return None

# --- 2. RESTORED DASHBOARD ---
st.set_page_config(page_title="Owner Portal", layout="wide")
st.title("🛡️ Guesty Automated Settlement")

# RESTORING YOUR OWNER DATABASE (Change these to your real names/rates)
if 'owner_db' not in st.session_state:
    st.session_state.owner_db = {
        "ERAN": {"pct": 20.0, "type": "Draft"},
        "OWNER_B": {"pct": 15.0, "type": "Payout"}
    }

with st.sidebar:
    st.header("🔑 API Connection")
    c_id = st.text_input("Client ID", value="0oaszuo22iOg2lk1P5d7")
    c_secret = st.text_input("Client Secret", type="password")
    
    if st.button("🗑️ Clear Cache & Reconnect"):
        st.cache_data.clear()
        st.success("Cache cleared. Try syncing again.")

    st.divider()
    st.header("👤 Owner Profile")
    active_owner = st.selectbox("Current View", sorted(st.session_state.owner_db.keys()))

# --- 3. THE CALCULATION LOGIC (Restored) ---
token = get_guesty_token(c_id, c_secret)

if token:
    if st.button("🔄 Sync Live Data"):
        res_url = "https://open-api.guesty.com/v1/reservations"
        res_headers = {"Authorization": f"Bearer {token}"}
        # Only pull what we need to stay under data limits
        params = {"limit": 20, "fields": "confirmationCode money checkIn"}
        
        raw = requests.get(res_url, headers=res_headers, params=params).json().get("results", [])
        
        conf = st.session_state.owner_db[active_owner]
        processed = []
        for r in raw:
            m = r.get("money", {})
            fare, clean = float(m.get("fare", 0)), float(m.get("cleaningFee", 0))
            comm = round(fare * (conf['pct'] / 100), 2)
            
            # This is where your "Draft" vs "Payout" logic lives!
            row = {"ID": r.get("confirmationCode"), "Accommodation": fare, "Commission": comm}
            if conf['type'] == "Draft":
                row["Cleaning"] = clean
                row["Total to Owner"] = (fare + clean) - comm
            else:
                row["Total to Owner"] = fare - comm
            processed.append(row)
            
        st.session_state.live_report = pd.DataFrame(processed)

# --- 4. THE FORMATTED TABLE ---
if "live_report" in st.session_state:
    df = st.session_state.live_report
    # Apply your $1,200.00 formatting
    st.dataframe(
        df, 
        use_container_width=True, 
        hide_index=True,
        column_config={col: st.column_config.NumberColumn(format="$%,.2f") for col in df.columns if col != "ID"}
    )
