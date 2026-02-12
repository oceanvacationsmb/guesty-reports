import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import calendar
import urllib.parse

# --- 1. GUESTY API HELPERS ---
def get_guesty_token():
    url = "https://open-api.guesty.com/oauth2/token"
    # Ensure keys exist in Streamlit Secrets
    if "CLIENT_ID" not in st.secrets or "CLIENT_SECRET" not in st.secrets:
        st.error("Go to Settings > Secrets and add CLIENT_ID and CLIENT_SECRET")
        return None
        
    payload = {
        "grant_type": "client_credentials",
        "client_id": st.secrets["CLIENT_ID"],
        "client_secret": st.secrets["CLIENT_SECRET"]
        # Removed 'scope' as it was causing the 'invalid_scope' error
    }
    
    response = requests.post(url, data=payload)
    if response.status_code != 200:
        st.error(f"Auth Failed: {response.text}")
        return None
    return response.json().get("access_token")

def fetch_data(month, year):
    token = get_guesty_token()
    if not token: return []
    
    headers = {"Authorization": f"Bearer {token}", "accept": "application/json"}
    
    # Standard date strings Guesty expects
    start_date = f"{year}-{month:02d}-01"
    last_day = calendar.monthrange(year, month)[1]
    end_date = f"{year}-{month:02d}-{last_day}"
    
    # Clean filter structure
    filters = [
        {"field": "checkInDate", "operator": "$gte", "value": start_date},
        {"field": "checkInDate", "operator": "$lte", "value": end_date}
    ]
    
    # URL Encoding the filters properly
    encoded_filters = urllib.parse.quote(str(filters).replace("'", '"'))
    url = f"https://open-api.guesty.com/v1/reservations?limit=100&filters={encoded_filters}"
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        st.error(f"Data Fetch Error: {response.status_code}")
        return []
        
    return response.json().get("results", [])

# --- 2. THE WEBSITE ---
st.title("🏡 Guesty Automated Monthly Report")

col1, col2, col3 = st.columns(3)
with col1:
    owner = st.selectbox("Select Owner", ["ERAN MARON", "YEN FRENCH"])
with col2:
    m = st.selectbox("Month", range(1, 13), index=datetime.now().month - 1)
with col3:
    y = st.number_input("Year", value=2026)

if st.button("Generate Monthly Report"):
    with st.spinner("Fetching live data..."):
        data = fetch_data(m, y)
        
        if not data:
            st.warning("No reservations found. Ensure you have confirmed bookings for this month.")
        else:
            rows = []
            for res in data:
                # Basic Money Pulling
                money = res.get('money', {})
                acc = money.get('fare', 0)
                clean = money.get('cleaningFee', 0)
                source = res.get('source', '').lower()
                prop_title = res.get('listing', {}).get('title', 'Unknown Property')
                
                # Logic: Eran 12% + 1% Web Fee | Others 15%
                is_eran = "ERAN" in owner.upper()
                rate = 0.12 if is_eran else 0.15
                
                # FIX: Check if source is 'booking engine' for 1% fee
                web_fee = (acc * 0.01) if (is_eran and "engine" in source) else 0
                
                rows.append({
                    "Property": prop_title,
                    "Accommodation": acc,
                    "Cleaning": clean,
                    "Management Fee": acc * rate,
                    "Website Fee (1%)": web_fee
                })
            
            # Create Property Summary Table
            df = pd.DataFrame(rows)
            summary = df.groupby("Property").sum().reset_index()
            
            st.write(f"### Totals per Property")
            st.table(summary)
            
            # Calculation Footer
            t_acc = summary['Accommodation'].sum()
            t_clean = summary['Cleaning'].sum()
            t_fee = summary['Management Fee'].sum()
            t_web = summary['Website Fee (1%)'].sum()
            
            st.divider()
            st.write(f"**Total Combined Accommodation:** ${t_acc:,.2f}")
            st.write(f"**Total Management Fees:** -${t_fee:,.2f}")
            
            if is_eran:
                st.write(f"**Total Cleaning Fees:** -${t_clean:,.2f}")
                st.write(f"**Total Website Fees (1%):** -${t_web:,.2f}")
                net = (t_acc + t_clean) - (t_fee + t_clean + t_web)
                st.info(f"**Amount to DRAFT from Eran:** ${net:,.2f}")
            else:
                net = t_acc - (t_fee + t_clean)
                st.success(f"**Net Owner Payout:** ${net:,.2f}")
