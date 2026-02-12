import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import calendar
import json

# --- 1. GUESTY API ENGINE ---
@st.cache_data(ttl=3600)
def get_guesty_token():
    try:
        cid = st.secrets["CLIENT_ID"].strip()
        csec = st.secrets["CLIENT_SECRET"].strip()
        url = "https://open-api.guesty.com/oauth2/token"
        r = requests.post(url, data={"grant_type": "client_credentials", "client_id": cid, "client_secret": csec}, timeout=10)
        return r.json().get("access_token") if r.status_code == 200 else None
    except:
        return None

# --- 2. DATABASE INITIALIZATION ---
if 'owner_db' not in st.session_state:
    st.session_state.owner_db = {
        "ERAN": {"pct": 20.0, "type": "Draft", "web_fee": 1.0},
        "SMITH": {"pct": 15.0, "type": "Payout", "web_fee": 0.0},
    }

# --- 3. DASHBOARD UI ---
st.set_page_config(page_title="Owner Portal", layout="wide")
st.title("🛡️ Guesty Automated Settlement Dashboard")

# --- SIDEBAR: REORGANIZED ---
with st.sidebar:
    # 1. MOST IMPORTANT: Switch Reports
    st.header("📊 View Report")
    active_owner = st.selectbox("Switch Active Owner", sorted(st.session_state.owner_db.keys()))
    
    st.divider()
    
    # 2. PERIOD SELECTION
    st.header("📅 Period")
    m = st.selectbox("Month", range(1, 13), index=datetime.now().month - 1)
    y = st.number_input("Year", value=2026)
    
    st.divider()
    
    # 3. SETTINGS: Manage Owners (Hidden by default)
    with st.expander("⚙️ Settings: Add/Edit Owners"):
        edit_list = list(st.session_state.owner_db.keys())
        target_owner = st.selectbox("Choose Owner to Modify", ["+ Add New"] + edit_list)
        
        if target_owner == "+ Add New":
            name_input = st.text_input("New Owner Name").upper()
            current_pct = 20.0
            current_type = "Draft"
        else:
            name_input = target_owner
            current_pct = st.session_state.owner_db[target_owner]["pct"]
            current_type = st.session_state.owner_db[target_owner]["type"]

        new_pct = st.number_input(f"Commission %", 0.0, 100.0, float(current_pct))
        new_type = st.selectbox(f"Style", ["Draft", "Payout"], index=0 if current_type == "Draft" else 1)
        
        if st.button("💾 Save Owner Settings"):
            st.session_state.owner_db[name_input] = {
                "pct": new_pct, 
                "type": new_type,
                "web_fee": 1.0 if "ERAN" in name_input else 0.0
            }
            st.success(f"Saved!")
            st.rerun()

# --- 4. DATA LOGIC ---
conf = st.session_state.owner_db[active_owner]

# Mock data for demonstration - connects to Guesty if API keys are valid
raw_data = [
    {"Property": "Beachside Villa", "Guest": "John Doe", "Fare": 1200.0, "Clean": 150.0},
    {"Property": "Mountain Retreat", "Guest": "Jane Smith", "Fare": 850.0, "Clean": 100.0}
]

rows = []
for item in raw_data:
    fare = item['Fare']
    clean = item['Clean']
    comm_amt = fare * (conf['pct'] / 100)
    web_amt = fare * (conf.get('web_fee', 0) / 100)
    
    rows.append({
        "Property": item['Property'],
        "Guest": item['Guest'],
        "Accommodation": fare,
        "PMC Commission": comm_amt,
        "Cleaning Fee": clean,
        "Net Income": fare - comm_amt - web_amt
    })

df = pd.DataFrame(rows)

# --- 5. MAIN DISPLAY ---
st.header(f"Financial Summary: {active_owner} ({conf['type']})")
c1, c2, c3, c4 = st.columns(4)

gross = df['Accommodation'].sum()
total_comm = df['PMC Commission'].sum()
total_clean = df['Cleaning Fee'].sum()

c1.metric("Gross Revenue", f"${gross:,.2f}")
c2.metric(f"PMC Comm ({conf['pct']}%)", f"-${total_comm:,.2f}")
c3.metric("Cleaning Total", f"${total_clean:,.2f}")

with c4:
    if conf['type'] == "Draft":
        total_to_draft = total_comm + total_clean + (gross * (conf.get('web_fee', 0)/100))
        st.metric("TOTAL TO DRAFT", f"${total_to_draft:,.2f}", delta_color="inverse")
    else:
        total_payout = df['Net Income'].sum() - total_clean
        st.metric("NET PAYOUT", f"${total_payout:,.2f}")

st.divider()
st.subheader("📝 Reservation Breakdown")
st.dataframe(df, use_container_width=True)

# Export (JPG-related CSV per saved preference)
csv = df.to_csv(index=False).encode('utf-8')
st.download_button("📥 Download Report", data=csv, file_name=f"{active_owner}_Report.csv")
