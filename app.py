import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import calendar
import json
import time

# --- 1. GUESTY API CONNECTION ---
@st.cache_data(ttl=3600)
def get_guesty_token():
    try:
        cid = st.secrets["CLIENT_ID"].strip()
        csec = st.secrets["CLIENT_SECRET"].strip()
    except:
        return None

    url = "https://open-api.guesty.com/oauth2/token"
    payload = {"grant_type": "client_credentials", "client_id": cid, "client_secret": csec}
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    
    try:
        r = requests.post(url, data=payload, headers=headers, timeout=10)
        if r.status_code == 200:
            return r.json().get("access_token")
        return None
    except:
        return None

@st.cache_data(ttl=600)
def fetch_data(month, year):
    token = get_guesty_token()
    if not token: 
        return None, None
    
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    start = f"{year}-{month:02d}-01"
    end = f"{year}-{month:02d}-{calendar.monthrange(year, month)[1]}"
    
    try:
        owners = requests.get("https://open-api.guesty.com/v1/owners", headers=headers, timeout=10).json().get('results', [])
        res_filter = json.dumps([{"field": "checkInDateLocalized", "operator": "$gte", "value": start}])
        res_url = f"https://open-api.guesty.com/v1/reservations?limit=50&filters={res_filter}"
        reservations = requests.get(res_url, headers=headers, timeout=10).json().get('results', [])
        return owners, reservations
    except:
        return None, None

# --- 2. THE DASHBOARD INTERFACE ---
st.set_page_config(page_title="Owner Portal", layout="wide")
st.title("🛡️ Guesty Automated Settlement Dashboard")

# --- SIDEBAR ---
with st.sidebar:
    st.header("Settlement Period")
    m = st.selectbox("Month", range(1, 13), index=datetime.now().month - 1)
    y = st.number_input("Year", value=2026)
    st.divider()
    use_mock = st.checkbox("Show Mock Data (If API Fails)", value=True)
    if st.button("🔄 Force Update API"):
        st.cache_data.clear()
        st.rerun()

# --- DATA PROCESSING ---
owners, reservations = fetch_data(m, y)

# If API fails and user wants to see the table layout
if not owners and use_mock:
    st.info("💡 Displaying **Mock Data** so you can see the table layout while API keys verify.")
    selected_owner_name = "ERAN - Example Owner"
    detailed_data = [
        {"Property": "Beachside Villa 101", "Guest": "John Doe", "Accommodation": 1200.00, "Management Fee": 240.00, "Cleaning Fee": 150.00, "Expenses": 50.00, "Net Income": 760.00},
        {"Property": "Mountain Retreat", "Guest": "Jane Smith", "Accommodation": 850.00, "Management Fee": 170.00, "Cleaning Fee": 100.00, "Expenses": 0.00, "Net Income": 580.00},
        {"Property": "City Condo", "Guest": "Mike Ross", "Accommodation": 2100.00, "Management Fee": 420.00, "Cleaning Fee": 180.00, "Expenses": 25.00, "Net Income": 1475.00}
    ]
    is_eran = True
else:
    if owners:
        st.success("✅ Connected to Guesty!")
        owner_map = {f"{o.get('firstName', '')} {o.get('lastName', '')}".strip(): o for o in owners}
        selected_owner_name = st.selectbox("Select Owner", sorted(owner_map.keys()))
        owner_obj = owner_map[selected_owner_name]
        assigned_ids = owner_obj.get('listingIds', [])
        is_eran = "ERAN" in selected_owner_name.upper()
        
        detailed_data = []
        for res in (reservations or []):
            if res.get('listingId') in assigned_ids:
                money = res.get('money', {})
                acc = money.get('fare', 0)
                detailed_data.append({
                    "Property": res.get('listing', {}).get('title', 'Property'),
                    "Guest": res.get('guest', {}).get('fullName', 'Guest'),
                    "Accommodation": acc,
                    "Management Fee": money.get('commission', 0),
                    "Cleaning Fee": money.get('cleaningFee', 0),
                    "Expenses": 0.00, # Manual expenses logic goes here
                    "Net Income": acc - money.get('commission', 0)
                })
    else:
        st.error("Waiting for connection... ensure keys are in Streamlit Secrets.")
        selected_owner_name = None

# --- RENDER TABLE ---
if selected_owner_name and (detailed_data or use_mock):
    df = pd.DataFrame(detailed_data)
    
    st.header(f"Financial Summary: {selected_owner_name}")
    c1, c2, c3, c4 = st.columns(4)
    
    gross = df['Accommodation'].sum()
    total_mgmt = df['Management Fee'].sum()
    total_cln = df['Cleaning Fee'].sum()
    total_exp = df['Expenses'].sum()

    c1.metric("Gross Revenue", f"${gross:,.2f}")
    c2.metric("Management Fees", f"-${total_mgmt:,.2f}")
    c3.metric("Total Expenses", f"-${total_exp:,.2f}")
    
    with c4:
        if is_eran:
            # Special logic for ERAN: Totals what needs to be drafted
            draft = total_mgmt + total_cln + total_exp + (gross * 0.01)
            st.metric("TOTAL TO DRAFT", f"${draft:,.2f}")
        else:
            payout = df['Net Income'].sum() - total_cln
            st.metric("NET PAYOUT", f"${payout:,.2f}")

    st.divider()
    st.subheader("📝 Reservation Breakdown")
    st.dataframe(df, use_container_width=True)
    
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download CSV", data=csv, file_name=f"{selected_owner_name}.csv", mime='text/csv')
