import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import calendar
import urllib.parse

# --- 1. GUESTY API HELPERS ---
def get_guesty_token():
    url = "https://open-api.guesty.com/oauth2/token"
    # Safety check for Secrets
    if "CLIENT_ID" not in st.secrets:
        st.error("Missing CLIENT_ID in Streamlit Secrets!")
        return None
        
    payload = {
        "grant_type": "client_credentials",
        "scope": "all",
        "client_id": st.secrets["CLIENT_ID"],
        "client_secret": st.secrets["CLIENT_SECRET"]
    }
    response = requests.post(url, data=payload)
    if response.status_code != 200:
        st.error(f"Failed to get Token: {response.text}")
        return None
    return response.json().get("access_token")

def fetch_data(month, year):
    token = get_guesty_token()
    if not token: return []
    
    headers = {"Authorization": f"Bearer {token}", "accept": "application/json"}
    
    # Calculate dates
    start_date = f"{year}-{month:02d}-01"
    last_day = calendar.monthrange(year, month)[1]
    end_date = f"{year}-{month:02d}-{last_day}"
    
    # Correcting the Filter format for Guesty API
    filters = [
        {"field": "checkInDate", "operator": "$gte", "value": start_date},
        {"field": "checkInDate", "operator": "$lte", "value": end_date}
    ]
    
    # Encode the filter for the URL
    filter_json = urllib.parse.quote(str(filters).replace("'", '"'))
    url = f"https://open-api.guesty.com/v1/reservations?limit=100&filters={filter_json}"
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        st.error(f"Guesty API Error: {response.status_code} - {response.text}")
        return []
        
    return response.json().get("results", [])

# --- 2. THE REPORT INTERFACE ---
st.title("🏡 Guesty Automated Monthly Report")

col1, col2, col3 = st.columns(3)
with col1:
    owner = st.selectbox("Select Owner", ["ERAN MARON", "YEN FRENCH"])
with col2:
    m = st.selectbox("Month", range(1, 13), index=datetime.now().month - 1)
with col3:
    y = st.number_input("Year", value=2026)

if st.button("Generate Monthly Report"):
    with st.spinner("Fetching data..."):
        data = fetch_data(m, y)
        
        if not data:
            st.info("No data found for this selection. Double check your API keys and the selected month.")
        else:
            rows = []
            for res in data:
                acc = res.get('money', {}).get('fare', 0)
                clean = res.get('money', {}).get('cleaningFee', 0)
                source = res.get('source', '').lower()
                prop_title = res.get('listing', {}).get('title', 'Unknown Property')
                
                # Logic: 1% Fee for Eran + booking engine
                is_eran = "ERAN" in owner.upper()
                web_fee = (acc * 0.01) if (is_eran and "engine" in source) else 0
                rate = 0.12 if is_eran else 0.15
                
                rows.append({
                    "Property": prop_title,
                    "Accommodation": acc,
                    "Cleaning": clean,
                    "PMC": acc * rate,
                    "Web Fee": web_fee
                })
            
            df = pd.DataFrame(rows)
            summary = df.groupby("Property").sum().reset_index()
            
            st.write(f"### Property Totals for {owner}")
            st.table(summary)
            
            # Show Detailed Calculations
            total_acc = summary['Accommodation'].sum()
            total_pmc = summary['PMC'].sum()
            total_clean = summary['Cleaning'].sum()
            total_web = summary['Web Fee'].sum()
            
            st.write("---")
            st.write(f"**Combined Total Accommodation:** ${total_acc:,.2f}")
            st.write(f"**Combined Management Fee ({int(rate*100)}%):** -${total_pmc:,.2f}")
            
            if is_eran:
                st.write(f"**Combined Cleaning Fee:** -${total_clean:,.2f}")
                st.write(f"**Combined Website Fee (1%):** -${total_web:,.2f}")
                net = (total_acc + total_clean) - (total_pmc + total_clean + total_web)
                st.info(f"**Total to Draft from Eran:** ${net:,.2f}")
            else:
                net = total_acc - (total_pmc + total_clean)
                st.success(f"**Total Net Owner Revenue:** ${net:,.2f}")
