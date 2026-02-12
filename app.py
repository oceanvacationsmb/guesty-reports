import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import calendar
import json
import time

# --- 1. GUESTY API ENGINE ---
@st.cache_data(ttl=3600)
def get_guesty_token():
    try:
        cid = st.secrets["CLIENT_ID"].strip()
        csec = st.secrets["CLIENT_SECRET"].strip()
    except:
        return "MISSING_KEYS"

    url = "https://open-api.guesty.com/oauth2/token"
    payload = {"grant_type": "client_credentials", "client_id": cid, "client_secret": csec}
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    
    try:
        # Safety delay to prevent the 429 error seen in your screenshot
        time.sleep(1) 
        r = requests.post(url, data=payload, headers=headers, timeout=15)
        if r.status_code == 200:
            return r.json().get("access_token")
        return f"ERROR_{r.status_code}"
    except:
        return "CONNECTION_FAILED"

@st.cache_data(ttl=600)
def fetch_guesty_data(month, year):
    token = get_guesty_token()
    if "ERROR" in str(token) or token == "MISSING_KEYS":
        return None, None
    
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    start = f"{year}-{month:02d}-01"
    end = f"{year}-{month:02d}-{calendar.monthrange(year, month)[1]}"
    
    try:
        # Get REAL Owners and REAL Reservations
        owners = requests.get("https://open-api.guesty.com/v1/owners", headers=headers).json().get('results', [])
        
        res_filter = json.dumps([{"field": "checkInDateLocalized", "operator": "$gte", "value": start}])
        res_url = f"https://open-api.guesty.com/v1/reservations?limit=100&filters={res_filter}"
        reservations = requests.get(res_url, headers=headers).json().get('results', [])
        
        return owners, reservations
    except:
        return None, None

# --- 2. THE DASHBOARD ---
st.set_page_config(page_title="Owner Settlement", layout="wide")
st.title("🛡️ Guesty Automated Settlement Dashboard")

with st.sidebar:
    st.header("Settlement Period")
    m = st.selectbox("Month", range(1, 13), index=datetime.now().month - 1)
    y = st.number_input("Year", value=2026)
    st.divider()
    if st.button("🔄 Refresh Live Data"):
        st.cache_data.clear()
        st.rerun()

# Attempt to pull real data
owners_list, res_list = fetch_guesty_data(m, y)

if owners_list:
    st.success("✅ Connected to Guesty Pro!")
    owner_names = {f"{o.get('firstName', '')} {o.get('lastName', '')}".strip(): o for o in owners_list}
    selected_name = st.selectbox("Select Owner", sorted(owner_names.keys()))
    
    if selected_name:
        owner_obj = owner_names[selected_name]
        listing_ids = owner_obj.get('listingIds', [])
        is_eran = "ERAN" in selected_name.upper()
        
        detailed_data = []
        for res in (res_list or []):
            if res.get('listingId') in listing_ids:
                money = res.get('money', {})
                acc = money.get('fare', 0)
                detailed_data.append({
                    "Property": res.get('listing', {}).get('title', 'Unknown'),
                    "Guest": res.get('guest', {}).get('fullName', 'Guest'),
                    "Accommodation": acc,
                    "Management Fee": money.get('commission', 0),
                    "Cleaning Fee": money.get('cleaningFee', 0),
                    "Expenses": 0.00,
                    "Net Income": acc - money.get('commission', 0)
                })
        
        if detailed_data:
            df = pd.DataFrame(detailed_data)
            st.header(f"Financial Summary: {selected_name}")
            
            # --- METRICS ---
            c1, c2, c3, c4 = st.columns(4)
            gross = df['Accommodation'].sum()
            total_mgmt = df['Management Fee'].sum()
            total_cln = df['Cleaning Fee'].sum()
            
            c1.metric("Gross Revenue", f"${gross:,.2f}")
            c2.metric("Management Fees", f"-${total_mgmt:,.2f}")
            c3.metric("Cleaning Fees", f"-${total_cln:,.2f}")
            
            with c4:
                if is_eran:
                    draft = total_mgmt + total_cln + (gross * 0.01)
                    st.metric("TOTAL TO DRAFT", f"${draft:,.2f}")
                else:
                    st.metric("NET PAYOUT", f"${df['Net Income'].sum() - total_cln:,.2f}")

            st.divider()
            st.subheader("📝 Reservation Breakdown")
            st.dataframe(df, use_container_width=True)
            
            # Export as JPG-related CSV per your preference
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Settlement CSV", data=csv, file_name=f"{selected_name}_Settlement.csv")
        else:
            st.warning("No reservations found for this owner in the selected month.")
else:
    st.error("❌ Still unable to connect. Check your new Client ID and Secret in Streamlit Secrets.")
    st.info("If you just saved the keys in Guesty, wait 2 minutes for them to activate.")
