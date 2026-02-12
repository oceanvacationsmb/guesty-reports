import streamlit as st
import pandas as pd
import requests

# --- 1. SECURE CONNECTION (Fixed 400/429) ---
@st.cache_data(ttl=86400)
def get_guesty_token(cid, csec):
    url = "https://open-api.guesty.com/oauth2/token"
    payload = {"grant_type": "client_credentials", "scope": "open-api", 
               "client_id": cid.strip(), "client_secret": csec.strip()}
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    try:
        res = requests.post(url, data=payload, headers=headers)
        return res.json().get("access_token") if res.status_code == 200 else None
    except: return None

# --- 2. RESTORED OWNER DATABASE ---
st.set_page_config(page_title="Owner Settlement", layout="wide")
st.title("🛡️ Guesty Automated Settlement")

if 'owner_db' not in st.session_state:
    st.session_state.owner_db = {
        "ERAN": {"pct": 20.0, "type": "Draft"},
        "ADAM": {"pct": 15.0, "type": "Payout"}
    }

with st.sidebar:
    st.header("🔑 API Link")
    c_id = st.text_input("Client ID", value="0oaszuo22iOg2lk1P5d7")
    c_secret = st.text_input("Client Secret", type="password")
    if st.button("🗑️ Reset Connection"):
        st.cache_data.clear()
        st.rerun()
    
    st.divider()
    active_owner = st.selectbox("Switch Owner Profile", sorted(st.session_state.owner_db.keys()))

# --- 3. DATA EXTRACTION (Fixes the "Zeros" issue) ---
token = get_guesty_token(c_id, c_secret)

if token:
    if st.button("🔄 Sync Live Data"):
        url = "https://open-api.guesty.com/v1/reservations"
        # We ask Guesty for specific money fields
        params = {"limit": 25, "fields": "confirmationCode money checkIn listing.nickname"}
        res = requests.get(url, headers={"Authorization": f"Bearer {token}"}, params=params)
        
        if res.status_code == 200:
            raw_data = res.json().get("results", [])
            conf = st.session_state.owner_db[active_owner]
            final_rows = []

            for r in raw_data:
                # DEEP EXTRACTION: Guesty often nests data under 'money' -> 'fare'
                money = r.get("money", {})
                
                # We use .get() and float() to handle missing or string data
                fare = float(money.get("fare", 0))
                cleaning = float(money.get("cleaningFee", 0))
                
                # Math Logic (Restored)
                commission = round(fare * (conf['pct'] / 100), 2)
                
                row = {
                    "Reservation": r.get("confirmationCode"),
                    "Check-In": r.get("checkIn")[:10] if r.get("checkIn") else "N/A",
                    "Accommodation": fare,
                    "Commission": commission,
                    "Cleaning": cleaning
                }

                # Apply Draft vs Payout Rules
                if conf['type'] == "Draft":
                    row["Net Payout"] = (fare + cleaning) - commission
                else:
                    row["Net Payout"] = fare - commission
                
                final_rows.append(row)
            
            st.session_state.settlement_df = pd.DataFrame(final_rows)
        else:
            st.error("Rate limit hit or Guesty busy. Wait 30 seconds.")

# --- 4. THE FORMATTED TABLE ($1,200.00 style) ---
if "settlement_df" in st.session_state:
    df = st.session_state.settlement_df
    # Apply the requested comma formatting
    format_config = {col: st.column_config.NumberColumn(format="$%,.2f") 
                    for col in df.columns if col not in ["Reservation", "Check-In"]}
    
    st.dataframe(df, use_container_width=True, hide_index=True, column_config=format_config)
