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

# --- 2. OWNER DATABASE (Internal Setup) ---
def get_owner_configs():
    # This acts as your internal "database" for owner rules
    if 'owner_db' not in st.session_state:
        st.session_state.owner_db = {
            "ERAN": {"pct": 20.0, "web_fee": 1.0, "type": "Draft"},
            "SMITH": {"pct": 15.0, "web_fee": 0.0, "type": "Payout"},
            "DOE": {"pct": 25.0, "web_fee": 0.0, "type": "Payout"}
        }
    return st.session_state.owner_db

# --- 3. DASHBOARD UI ---
st.set_page_config(page_title="PMC Manager", layout="wide")
st.title("🛡️ Guesty Automated Settlement Dashboard")

# --- SIDEBAR: SETTINGS & FILTERS ---
with st.sidebar:
    st.header("📅 Period")
    m = st.selectbox("Month", range(1, 13), index=datetime.now().month - 1)
    y = st.number_input("Year", value=2026)
    
    st.divider()
    st.header("👤 Select Owner")
    db = get_owner_configs()
    selected_name = st.selectbox("Switch Active Owner", sorted(db.keys()))
    
    st.divider()
    with st.expander("⚙️ Create/Edit Owners"):
        new_name = st.text_input("Owner Name (Uppercase)").upper()
        new_pct = st.number_input("Comm %", 0.0, 100.0, 20.0)
        new_type = st.selectbox("Settlement Type", ["Draft", "Payout"])
        if st.button("➕ Save Owner"):
            st.session_state.owner_db[new_name] = {"pct": new_pct, "web_fee": 0.0, "type": new_type}
            st.rerun()

# --- DATA PROCESSING ---
conf = db[selected_name]
token = get_guesty_token()

# For now, using Mock Data if API fails, but logic is ready for Live
if token:
    st.success(f"✅ Live Connection Active for {selected_name}")
    # (API Data Fetching would go here)
    # Using sample data for demonstration of the logic
    raw_data = [{"Property": "Villa 101", "Guest": "Guest A", "Fare": 1000, "Clean": 150}]
else:
    st.warning("⚠️ API Pending: Using Internal Rules Engine")
    raw_data = [
        {"Property": "Beachside Villa 101", "Guest": "John Doe", "Fare": 1200.0, "Clean": 150.0},
        {"Property": "Mountain Retreat", "Guest": "Jane Smith", "Fare": 850.0, "Clean": 100.0}
    ]

# --- CALCULATIONS BASED ON YOUR RULES ---
rows = []
for item in raw_data:
    fare = item['Fare']
    clean = item['Clean']
    comm_amt = fare * (conf['pct'] / 100)
    web_amt = fare * (conf['web_fee'] / 100)
    
    rows.append({
        "Property": item['Property'],
        "Guest": item['Guest'],
        "Accommodation": fare,
        "PMC Commission": comm_amt,
        "Cleaning Fee": clean,
        "Web Fee": web_amt,
        "Net Income": fare - comm_amt - web_amt
    })

df = pd.DataFrame(rows)

# --- DISPLAY ---
st.header(f"Financial Summary: {selected_name} ({conf['type']})")
c1, c2, c3, c4 = st.columns(4)

gross = df['Accommodation'].sum()
total_comm = df['PMC Commission'].sum()
total_clean = df['Cleaning Fee'].sum()
total_web = df['Web Fee'].sum()

c1.metric("Gross Revenue", f"${gross:,.2f}")
c2.metric(f"PMC Comm ({conf['pct']}%)", f"-${total_comm:,.2f}")
c3.metric("Cleaning Total", f"${total_clean:,.2f}")

with c4:
    if conf['type'] == "Draft":
        # Logic: What you need to take from the owner
        total_to_collect = total_comm + total_clean + total_web
        st.metric("TOTAL TO DRAFT", f"${total_to_collect:,.2f}", delta_color="inverse")
    else:
        # Logic: What you owe the owner
        total_payout = df['Net Income'].sum() - total_clean
        st.metric("NET PAYOUT", f"${total_payout:,.2f}")

st.divider()
st.subheader("📝 Detailed Breakdown")
st.dataframe(df, use_container_width=True)

# Export per preference
csv = df.to_csv(index=False).encode('utf-8')
st.download_button("📥 Download Report (CSV)", data=csv, file_name=f"{selected_name}_Report.csv")
