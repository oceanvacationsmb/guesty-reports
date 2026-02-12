import streamlit as st
import pandas as pd
import requests
import time
from datetime import date

# --- 1. SECURE API CONNECTION (Prevents 429 & 400 Errors) ---
# Guesty allows only 5 token requests per 24 hours.
# We cache it here to "remember" the connection for 24 hours.
@st.cache_data(ttl=86400)
def get_guesty_token(cid, csec):
    url = "https://open-api.guesty.com/oauth2/token"
    # payload must be form-urlencoded, NOT json
    payload = {
        "grant_type": "client_credentials",
        "scope": "open-api",
        "client_id": cid.strip(), # Fixes 400 error by removing hidden spaces
        "client_secret": csec.strip()
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"}
    try:
        res = requests.post(url, data=payload, headers=headers)
        if res.status_code == 200:
            return res.json().get("access_token")
        st.error(f"⚠️ Auth Failed: {res.text}")
        return None
    except: return None

# --- 2. RESTORED SETTINGS & DATABASE ---
st.set_page_config(page_title="Owner Portal", layout="wide")
st.title("🛡️ Guesty Automated Settlement")

if 'owner_db' not in st.session_state:
    st.session_state.owner_db = {"ERAN": {"pct": 20.0, "type": "Draft"}}

with st.sidebar:
    st.header("🔑 Live Sync")
    c_id = st.text_input("Client ID", value="0oaszuo22iOg2lk1P5d7")
    c_secret = st.text_input("Client Secret", type="password")
    
    st.divider()
    st.header("👤 Manage Owners")
    active_owner = st.selectbox("Active Owner", sorted(st.session_state.owner_db.keys()))

# --- 3. LIVE SETTLEMENT CALCULATION ---
token = get_guesty_token(c_id, c_secret)

if token:
    st.success("✅ Live Connection Secure")
    if st.button("🔄 Sync & Calculate Settlements"):
        # Pull live reservation financials
        res_url = "https://open-api.guesty.com/v1/reservations"
        params = {"limit": 20, "fields": "confirmationCode money listing.nickname checkIn"}
        raw_res = requests.get(res_url, headers={"Authorization": f"Bearer {token}"}, params=params).json().get("results", [])
        
        conf = st.session_state.owner_db[active_owner]
        processed = []
        for r in raw_res:
            m = r.get("money", {})
            # Extracting real accommodation and cleaning fees
            fare = float(m.get("fare", 0))
            clean = float(m.get("cleaningFee", 0))
            comm = round(fare * (conf['pct'] / 100), 2)
            
            row = {"ID": r.get("confirmationCode"), "Accommodation": fare, "Commission": comm, "Expenses": 0.0}
            if conf['type'] == "Draft":
                row["Net Payout"] = fare + clean
                row["Cleaning"] = clean
            processed.append(row)
        st.session_state.final_df = pd.DataFrame(processed)

# --- 4. RENDER TABLE WITH $1,200.00 FORMATTING ---
if "final_df" in st.session_state:
    df = st.session_state.final_df
    # Comma formatting $%,.2f ensures professional currency display
    config = {col: st.column_config.NumberColumn(format="$%,.2f") for col in df.columns if col != "ID"}
    st.dataframe(df, use_container_width=True, hide_index=True, column_config=config)
