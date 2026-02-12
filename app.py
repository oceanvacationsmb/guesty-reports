import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import calendar
import json

# --- 1. GUESTY API WITH CACHING ---
@st.cache_data(ttl=3600)  # Remembers data for 1 hour to avoid rate limits
def get_guesty_token(cid, csec):
    url = "https://open-api.guesty.com/oauth2/token"
    payload = {"grant_type": "client_credentials", "client_id": cid.strip(), "client_secret": csec.strip()}
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    try:
        r = requests.post(url, data=payload, headers=headers)
        return r.json().get("access_token")
    except:
        return None

@st.cache_data(ttl=600) # Remembers the data for 10 mins
def fetch_data(month, year):
    token = get_guesty_token(st.secrets["CLIENT_ID"], st.secrets["CLIENT_SECRET"])
    if not token: return None
    
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    
    # Guesty uses YYYY-MM-DD
    start = f"{year}-{month:02d}-01"
    last_day = calendar.monthrange(year, month)[1]
    end = f"{year}-{month:02d}-{last_day}"
    
    # Guesty-specific filter structure
    filters = json.dumps([
        {"field": "checkInDate", "operator": "$gte", "value": start},
        {"field": "checkInDate", "operator": "$lte", "value": end}
    ])
    
    url = f"https://open-api.guesty.com/v1/reservations?limit=100&filters={filters}"
    r = requests.get(url, headers=headers)
    return r.json().get("results", [])

# --- 2. THE INTERFACE ---
st.title("🏡 Guesty Automated Monthly Report")

# Use a form to stop the app from refreshing too often
with st.form("my_report"):
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
        st.warning("No data found or API is busy. Wait 2 minutes and try again.")
    else:
        # Process the property summary as requested
        data_list = []
        for res in results:
            money = res.get('money', {})
            # Check if this reservation is from the website for Eran's 1% fee
            is_website = "engine" in res.get('source', '').lower()
            
            data_list.append({
                "Property": res.get('listing', {}).get('title', 'Unknown'),
                "Accommodation": money.get('fare', 0),
                "Cleaning": money.get('cleaningFee', 0),
                "Is Web": is_website
            })
        
        df = pd.DataFrame(data_list)
        # Group by property for a single summary line per house
        summary = df.groupby("Property").sum().reset_index()
        st.table(summary)
        
        # Display Totals
        total_acc = summary['Accommodation'].sum()
        rate = 0.12 if "ERAN" in owner.upper() else 0.15
        st.metric("Total Accommodation", f"${total_acc:,.2f}")
        st.write(f"Management Fee ({int(rate*100)}%): -${(total_acc * rate):,.2f}")
