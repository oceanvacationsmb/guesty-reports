import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import calendar
import json

# --- 1. GUESTY API WITH CACHING (PREVENTS RATE LIMITS) ---
@st.cache_data(ttl=3600)  # Caches the token for 1 hour
def get_guesty_token(cid, csec):
    url = "https://open-api.guesty.com/oauth2/token"
    payload = {
        "grant_type": "client_credentials",
        "client_id": cid.strip(),
        "client_secret": csec.strip()
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'accept': 'application/json'
    }
    try:
        r = requests.post(url, data=payload, headers=headers)
        return r.json().get("access_token")
    except Exception as e:
        st.error(f"Authentication Error: {e}")
        return None

@st.cache_data(ttl=600)  # Caches report data for 10 minutes
def fetch_data(month, year):
    token = get_guesty_token(st.secrets["CLIENT_ID"], st.secrets["CLIENT_SECRET"])
    if not token: return None
    
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    
    # Guesty Date Format: YYYY-MM-DD
    start = f"{year}-{month:02d}-01"
    last_day = calendar.monthrange(year, month)[1]
    end = f"{year}-{month:02d}-{last_day}"
    
    # Precise JSON Filter for confirmed reservations
    filters = json.dumps([
        {"field": "checkInDateLocalized", "operator": "$gte", "value": start},
        {"field": "checkInDateLocalized", "operator": "$lte", "value": end},
        {"field": "status", "operator": "$eq", "value": "confirmed"}
    ])
    
    url = f"https://open-api.guesty.com/v1/reservations?limit=100&filters={filters}"
    r = requests.get(url, headers=headers)
    
    if r.status_code == 429:
        st.error(f"Rate Limit Hit. Guesty says wait {r.headers.get('Retry-After', 'a moment')}.")
        return None
    return r.json().get("results", [])

# --- 2. REPORT INTERFACE ---
st.title("🏡 Guesty Automated Monthly Report")

# Prevent accidental multiple API calls with st.form
with st.form("report_form"):
    col1, col2, col3 = st.columns(3)
    with col1:
        owner = st.selectbox("Select Owner", ["ERAN MARON", "YEN FRENCH"])
    with col2:
        m = st.selectbox("Month", range(1, 13), index=datetime.now().month - 1)
    with col3:
        y = st.number_input("Year", value=2026)
    submit = st.form_submit_button("Generate Monthly Report")

if submit:
    results = fetch_data(m, y)
    if results:
        data_list = []
        for res in results:
            money = res.get('money', {})
            # Scan for manual expenses in extraCharges
            expenses = sum(c.get('amount', 0) for c in money.get('extraCharges', []) 
                          if any(x in c.get('description', '').lower() for x in ["expense", "maintenance"]))
            
            data_list.append({
                "Property": res.get('listing', {}).get('title', 'Unknown'), #
                "Accommodation": money.get('fare', 0),
                "Cleaning": money.get('cleaningFee', 0),
                "Expenses": expenses,
                "Source": res.get('source', '').lower()
            })
        
        # --- PROPERTY SUMMARY (Grouping Logic) ---
        df = pd.DataFrame(data_list)
        summary = df.groupby("Property").sum().reset_index()
        
        st.subheader(f"Totals for {owner}")
        st.table(summary)
        
        # Financial Totals
        total_acc = summary['Accommodation'].sum()
        total_exp = summary['Expenses'].sum()
        rate = 0.12 if "ERAN" in owner.upper() else 0.15
        
        st.divider()
        st.write(f"**Total Revenue:** ${total_acc:,.2f}")
        st.write(f"**Management Fee:** -${(total_acc * rate):,.2f}")
        st.write(f"**Total Expenses:** -${total_exp:,.2f}")
