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
        cid = st.secrets["CLIENT_ID"].strip().replace('"', '').replace("'", "")
        csec = st.secrets["CLIENT_SECRET"].strip().replace('"', '').replace("'", "")
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
def fetch_guesty_data(month, year):
    token = get_guesty_token()
    if not token: 
        return None, None
    
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    start = f"{year}-{month:02d}-01"
    
    try:
        # Fetching owners and reservations
        owners = requests.get("https://open-api.guesty.com/v1/owners", headers=headers, timeout=10).json().get('results', [])
        res_filter = json.dumps([{"field": "checkInDateLocalized", "operator": "$gte", "value": start}])
        res_url = f"https://open-api.guesty.com/v1/reservations?limit=100&filters={res_filter}"
        reservations = requests.get(res_url, headers=headers, timeout=10).json().get('results', [])
        return owners, reservations
    except:
        return None, None

# --- 2. DASHBOARD UI ---
st.set_page_config(page_title="PMC Settlement", layout="wide")
st.title("🛡️ Guesty Automated Settlement Dashboard")

# Sidebar
with st.sidebar:
    st.header("Settlement Period")
    m = st.selectbox("Month", range(1, 13), index=datetime.now().month - 1)
    y = st.number_input("Year", value=2026)
    st.divider()
    # Checkbox to toggle between Test and Real mode
    force_mock = st.checkbox("Show Test Data (for layout check)", value=False)
    if st.button("🔄 Refresh Connection"):
        st.cache_data.clear()
        st.rerun()

# Data Logic
owners_list, res_list = fetch_guesty_data(m, y)

# --- THE SWITCHER LOGIC ---
if owners_list and not force_mock:
    # LIVE MODE: Pulling real names from Guesty
    st.success("✅ Connected to Guesty Pro")
    owner_map = {f"{o.get('firstName', '')} {o.get('lastName', '')}".strip(): o for o in owners_list}
    selected_owner = st.selectbox("Select Owner", sorted(owner_map.keys()))
    
    owner_obj = owner_map[selected_owner]
    assigned_ids = owner_obj.get('listingIds', [])
    is_eran = "ERAN" in selected_owner.upper()
    
    final_rows = []
    for res in (res_list or []):
        if res.get('listingId') in assigned_ids:
            money = res.get('money', {})
            acc = money.get('fare', 0)
            final_rows.append({
                "Property": res.get('listing', {}).get('title', 'Property'),
                "Guest": res.get('guest', {}).get('fullName', 'Guest'),
                "Accommodation": acc,
                "Management Fee": money.get('commission', 0),
                "Cleaning Fee": money.get('cleaningFee', 0),
                "Expenses": 0.00,
                "Net Income": acc - money.get('commission', 0)
            })
else:
    # TEST MODE: Showing a fake list so you can see the selector
    st.info("💡 API Pending: Showing Test Switcher")
    selected_owner = st.selectbox("Select Owner (TEST MODE)", ["ERAN - Example", "SMITH - Example", "DOE - Example"])
    is_eran = "ERAN" in selected_owner.upper()
    
    # Fake data changes based on selection
    if "ERAN" in selected_owner:
        final_rows = [{"Property": "Villa 101", "Guest": "John Doe", "Accommodation": 1000.0, "Management Fee": 200.0, "Cleaning Fee": 100.0, "Expenses": 0.0, "Net Income": 700.0}]
    else:
        final_rows = [{"Property": "Beach House", "Guest": "Jane Smith", "Accommodation": 2000.0, "Management Fee": 400.0, "Cleaning Fee": 150.0, "Expenses": 50.0, "Net Income": 1400.0}]

# --- RENDER THE TABLE ---
if final_rows:
    df = pd.DataFrame(final_rows)
    st.header(f"Financial Summary: {selected_owner}")
    
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
            draft_total = total_mgmt + total_cln + total_exp + (gross * 0.01)
            st.metric("TOTAL TO DRAFT", f"${draft_total:,.2f}")
        else:
            payout = df['Net Income'].sum() - total_cln
            st.metric("NET PAYOUT", f"${df['Net Income'].sum() - total_cln:,.2f}")

    st.divider()
    st.subheader("📝 Reservation Breakdown")
    st.dataframe(df, use_container_width=True)
    
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download Report (CSV)", data=csv, file_name=f"{selected_owner}.csv")
