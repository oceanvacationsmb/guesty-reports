import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import calendar
import json

# --- 1. GUESTY API WITH RATE-LIMIT PROTECTION ---
@st.cache_data(ttl=3600)  # Remembers your login token for 1 hour
def get_guesty_token(cid, csec):
    url = "https://open-api.guesty.com/oauth2/token"
    payload = {"grant_type": "client_credentials", "client_id": cid.strip(), "client_secret": csec.strip()}
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    try:
        r = requests.post(url, data=payload, headers=headers)
        return r.json().get("access_token")
    except:
        return None

@st.cache_data(ttl=600) # Remembers reservation data for 10 minutes
def fetch_data(month, year):
    token = get_guesty_token(st.secrets["CLIENT_ID"], st.secrets["CLIENT_SECRET"])
    if not token: return None
    
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    
    # Guesty expects YYYY-MM-DD format
    start = f"{year}-{month:02d}-01"
    last_day = calendar.monthrange(year, month)[1]
    end = f"{year}-{month:02d}-{last_day}"
    
    # Filtering reservations by check-in date within the month
    filters = json.dumps([
        {"field": "checkInDate", "operator": "$gte", "value": start},
        {"field": "checkInDate", "operator": "$lte", "value": end}
    ])
    
    url = f"https://open-api.guesty.com/v1/reservations?limit=100&filters={filters}"
    r = requests.get(url, headers=headers)
    if r.status_code == 429:
        st.error("Guesty Rate Limit Hit. Please wait 2 minutes.")
        return None
    return r.json().get("results", [])

# --- 2. THE WEBSITE INTERFACE ---
st.title("🏡 Guesty Automated Monthly Report")

# Use a form to prevent accidental multiple API calls
with st.form("report_selection"):
    col1, col2, col3 = st.columns(3)
    with col1:
        owner = st.selectbox("Select Owner", ["ERAN MARON", "YEN FRENCH"])
    with col2:
        m = st.selectbox("Month", range(1, 13), index=datetime.now().month - 1)
    with col3:
        y = st.number_input("Year", value=2026)
    submit = st.form_submit_button("Generate Report")

if submit:
    results = fetch_data(m, y)
    if not results:
        st.warning("No data found or API is cooling down. Please wait a moment.")
    else:
        data_list = []
        for res in results:
            money = res.get('money', {})
            # Pulling manual expenses from extraCharges field
            expenses = 0
            for charge in money.get('extraCharges', []):
                desc = charge.get('description', '').lower()
                if any(word in desc for word in ["expense", "maintenance", "repair"]):
                    expenses += charge.get('amount', 0)
            
            # 1% Website Fee logic for Eran
            source = res.get('source', '').lower()
            is_website = "engine" in source or "website" in source
            
            data_list.append({
                "Property": res.get('listing', {}).get('title', 'Unknown'),
                "Accommodation": money.get('fare', 0),
                "Cleaning": money.get('cleaningFee', 0),
                "Expenses": expenses,
                "Is Web": is_website
            })
        
        # --- DATA SUMMARY PER PROPERTY ---
        df = pd.DataFrame(data_list)
        summary = df.groupby("Property").sum().reset_index()
        st.subheader(f"Property Totals for {owner}")
        st.table(summary)
        
        # Final Totals
        total_acc = summary['Accommodation'].sum()
        total_exp = summary['Expenses'].sum()
        rate = 0.12 if "ERAN" in owner.upper() else 0.15
        
        st.divider()
        st.write(f"**Total Accommodation:** ${total_acc:,.2f}")
        st.write(f"**Management Fee ({int(rate*100)}%):** -${(total_acc * rate):,.2f}")
        st.write(f"**Total Expenses:** -${total_exp:,.2f}")
