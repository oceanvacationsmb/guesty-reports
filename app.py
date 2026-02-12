import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import calendar
import json

# --- 1. GUESTY API (OPTIMIZED) ---
@st.cache_data(ttl=3600) # This saves data for 1 hour so we don't hit the API too much
def get_guesty_token(client_id, client_secret):
    url = "https://open-api.guesty.com/oauth2/token"
    payload = {
        "grant_type": "client_credentials",
        "client_id": client_id.strip(),
        "client_secret": client_secret.strip()
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    response = requests.post(url, data=payload, headers=headers)
    return response.json().get("access_token") if response.status_code == 200 else None

def fetch_data(month, year):
    token = get_guesty_token(st.secrets["CLIENT_ID"], st.secrets["CLIENT_SECRET"])
    if not token: 
        st.error("Authentication failed. Please check your API keys in Secrets.")
        return []
    
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    start_date = f"{year}-{month:02d}-01"
    last_day = calendar.monthrange(year, month)[1]
    end_date = f"{year}-{month:02d}-{last_day}"
    
    filters = json.dumps([
        {"field": "checkInDate", "operator": "$gte", "value": start_date},
        {"field": "checkInDate", "operator": "$lte", "value": end_date}
    ])
    
    url = f"https://open-api.guesty.com/v1/reservations?limit=100&filters={filters}"
    response = requests.get(url, headers=headers)
    return response.json().get("results", []) if response.status_code == 200 else []

# --- 2. THE INTERFACE ---
st.title("🏡 Guesty Automated Monthly Report")

# Use a form to prevent the app from refreshing every time you click a dropdown
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
    data = fetch_data(m, y)
    if not data:
        st.warning("No data found. Try a different month or check your connection.")
    else:
        rows = []
        for res in data:
            money = res.get('money', {})
            acc = money.get('fare', 0)
            clean = money.get('cleaningFee', 0)
            source = res.get('source', '').lower()
            prop_title = res.get('listing', {}).get('title', 'Unknown Property')
            
            is_eran = "ERAN" in owner.upper()
            rate = 0.12 if is_eran else 0.15
            web_fee = (acc * 0.01) if (is_eran and "engine" in source) else 0
            
            rows.append({
                "Property": prop_title,
                "Accommodation": acc,
                "Cleaning": clean,
                "Fee": acc * rate,
                "Web": web_fee
            })
        
        df = pd.DataFrame(rows)
        summary = df.groupby("Property").sum().reset_index()
        st.table(summary)
        
        # Totals
        net = summary['Accommodation'].sum() - summary['Fee'].sum()
        st.success(f"Final Calculated Net: ${net:,.2f}")
