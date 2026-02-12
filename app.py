import streamlit as st
import pandas as pd
import requests
from datetime import date

# --- 1. THE CONNECTION (RESTORED) ---
@st.cache_data(ttl=86400)
def get_guesty_token(cid, csec):
    url = "https://open-api.guesty.com/oauth2/token"
    payload = {"grant_type": "client_credentials", "scope": "open-api", "client_id": cid.strip(), "client_secret": csec.strip()}
    headers = {"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"}
    res = requests.post(url, data=payload, headers=headers)
    return res.json().get("access_token") if res.status_code == 200 else None

# --- 2. DASHBOARD & OWNER DB (RESTORED) ---
st.set_page_config(page_title="Owner Portal", layout="wide")
st.title("🛡️ Guesty Automated Settlement")

if 'owner_db' not in st.session_state:
    st.session_state.owner_db = {"ERAN": {"pct": 20.0, "type": "Draft"}}

with st.sidebar:
    st.header("🔑 API Connection")
    c_id = st.text_input("Client ID", value="0oaszuo22iOg2lk1P5d7")
    c_secret = st.text_input("Client Secret", type="password")
    if st.button("🗑️ Clear Cache"):
        st.cache_data.clear()
    
    st.divider()
    active_owner = st.selectbox("Active Owner", sorted(st.session_state.owner_db.keys()))

# --- 3. THE CALCULATION (FIXED ZEROS) ---
token = get_guesty_token(c_id, c_secret)

if token:
    if st.button("🔄 Sync Live Data"):
        res_url = "https://open-api.guesty.com/v1/reservations"
        # We add 'money' to fields to ensure we get the prices
        params = {"limit": 20, "fields": "confirmationCode money listing.nickname checkIn"}
        response = requests.get(res_url, headers={"Authorization": f"Bearer {token}"}, params=params)
        
        if response.status_code == 200:
            raw_res = response.json().get("results", [])
            conf = st.session_state.owner_db[active_owner]
            processed = []
            
            for r in raw_res:
                m = r.get("money", {})
                # Extracting specifically from the Guesty money object structure
                fare = float(m.get("fare", 0))
                clean = float(m.get("cleaningFee", 0))
                comm = round(fare * (conf['pct'] / 100), 2)
                
                row = {
                    "ID": r.get("confirmationCode"),
                    "Accommodation": fare,
                    "Commission": comm,
                    "Expenses": 0.0
                }
                
                if conf['type'] == "Draft":
                    row["Net Payout"] = fare + clean
                    row["Cleaning"] = clean
                else:
                    row["Net Payout"] = fare - comm - 0.0 # Accommodation minus comm/exp
                
                processed.append(row)
            
            st.session_state.final_df = pd.DataFrame(processed)
        else:
            st.error(f"Error: {response.status_code}. Guesty might be busy.")

# --- 4. THE TABLE (FORMATTED) ---
if "final_df" in st.session_state:
    df = st.session_state.final_df
    # Restoring the $1,200.00 formatting with commas
    config = {col: st.column_config.NumberColumn(format="$%,.2f") for col in df.columns if col != "ID"}
    st.dataframe(df, use_container_width=True, hide_index=True, column_config=config)
