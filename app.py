import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import calendar
import json

# --- 1. THE AUTOMATION ENGINE (GUESTY API) ---
@st.cache_data(ttl=3600)
def get_guesty_token():
    """Authenticates with Guesty once per hour."""
    url = "https://open-api.guesty.com/oauth2/token"
    payload = {
        "grant_type": "client_credentials",
        "client_id": st.secrets["CLIENT_ID"].strip(),
        "client_secret": st.secrets["CLIENT_SECRET"].strip()
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    try:
        r = requests.post(url, data=payload, headers=headers)
        return r.json().get("access_token")
    except:
        return None

@st.cache_data(ttl=600)
def fetch_master_data(month, year):
    """Pulls all owners, reservations, and expenses for the month."""
    token = get_guesty_token()
    if not token: return None, None, None
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    
    start = f"{year}-{month:02d}-01"
    end = f"{year}-{month:02d}-{calendar.monthrange(year, month)[1]}"
    
    # A. Fetch Owners
    owners = requests.get("https://open-api.guesty.com/v1/owners", headers=headers).json().get('results', [])
    
    # B. Fetch Reservations (Confirmed only)
    res_filter = json.dumps([
        {"field": "checkInDateLocalized", "operator": "$gte", "value": start},
        {"field": "checkInDateLocalized", "operator": "$lte", "value": end},
        {"field": "status", "operator": "$eq", "value": "confirmed"}
    ])
    res_url = f"https://open-api.guesty.com/v1/reservations?limit=100&filters={res_filter}"
    reservations = requests.get(res_url, headers=headers).json().get('results', [])
    
    # C. Fetch Expenses/Invoices
    exp_url = "https://open-api.guesty.com/v1/business-models-api/transactions/expenses-by-listing"
    expenses = requests.get(exp_url, headers=headers, params={"startDate": start, "endDate": end}).json().get('results', [])
    
    return owners, reservations, expenses

# --- 2. DASHBOARD LAYOUT ---
st.set_page_config(page_title="PMC Master Portal", layout="wide")
st.title("🛡️ Guesty Automated Settlement Dashboard")

# Select Timeframe
with st.sidebar:
    st.header("Settlement Period")
    m = st.selectbox("Month", range(1, 13), index=datetime.now().month - 1)
    y = st.number_input("Year", value=2026)
    st.divider()
    st.caption("All data is pulled directly from Guesty financials and native owner assignments.")

owners_list, res_list, exp_list = fetch_master_data(m, y)

if owners_list:
    # Build a clean owner dropdown
    owner_map = {f"{o.get('firstName', '')} {o.get('lastName', '')}".strip(): o for o in owners_list}
    selected_owner_name = st.selectbox("Select Owner to Generate Statement", sorted(owner_map.keys()))
    
    selected_owner = owner_map[selected_owner_name]
    assigned_listing_ids = selected_owner.get('listingIds', [])

    # --- 3. CALCULATE PROPERTY PERFORMANCE ---
    processed_res = []
    for res in res_list:
        if res.get('listingId') in assigned_listing_ids:
            money = res.get('money', {})
            acc = money.get('fare', 0)
            pmc_fee = money.get('commission', 0) # Native Guesty Management Fee
            cleaning = money.get('cleaningFee', 0)
            
            # 1% Website Fee (Specific logic for Eran)
            source = res.get('source', '').lower()
            web_fee = (acc * 0.01) if ("ERAN" in
