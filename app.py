import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import calendar
import json

# --- 1. THE ENGINE (PULLING NATIVE GUESTY FEES) ---
@st.cache_data(ttl=600)
def fetch_financial_data(month, year):
    token = get_guesty_token() # Your existing token function
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    
    start = f"{year}-{month:02d}-01"
    end = f"{year}-{month:02d}-{calendar.monthrange(year, month)[1]}"
    
    # We ask Guesty for Reservations + their Financial break-down
    url = f"https://open-api.guesty.com/v1/reservations?limit=100&filters=[{{'field':'checkInDateLocalized','operator':'$gte','value':'{start}'}},{{'field':'checkInDateLocalized','operator':'$lte','value':'{end}'}},{{'field':'status','operator':'$eq','value':'confirmed'}}]"
    
    response = requests.get(url, headers=headers)
    return response.json().get("results", [])

# --- 2. DYNAMIC OWNER DASHBOARD ---
st.set_page_config(layout="wide")
st.title("📊 Guesty Real-Time Owner Statements")

# We get the data
m = st.sidebar.selectbox("Month", range(1, 13), index=datetime.now().month - 1)
y = st.sidebar.number_input("Year", value=2026)
raw_data = fetch_financial_data(m, y)

if raw_data:
    # 1. Automatically find all Owners in this data
    owners = sorted(list(set([res.get('listing', {}).get('owner', {}).get('firstName', 'Unknown') for res in raw_data])))
    selected_owner = st.selectbox("Select Owner", owners)
    
    processed_rows = []
    for res in raw_data:
        res_owner = res.get('listing', {}).get('owner', {}).get('firstName', 'Unknown')
        
        if res_owner == selected_owner:
            money = res.get('money', {})
            # Guesty's Native Fee Fields
            acc = money.get('fare', 0)
            # This is the 'Management Fee' you set in Guesty
            pmc_fee = money.get('commission', 0) 
            cleaning = money.get('cleaningFee', 0)
            source = res.get('source', '').lower()
            
            # 1% Web Fee logic (Still needed if not a standard Guesty fee)
            web_fee = (acc * 0.01) if (selected_owner.upper() == "ERAN" and "engine" in source) else 0
            
            processed_rows.append({
                "Property": res.get('listing', {}).get('title', 'Unknown'),
                "Gross Accommodation": acc,
                "Cleaning Fee": cleaning,
                "Management Fee": pmc_fee,
                "Web Fee": web_fee,
                "Net to Owner": acc - pmc_fee - web_fee
            })

    if processed_rows:
        df = pd.DataFrame(processed_rows)
        # GROUP BY PROPERTY (As requested)
        summary = df.groupby("Property").sum().reset_index()
        
        st.write(f"### Statement for {selected_owner}")
        st.table(summary)
        
        # --- TOTALS SECTION ---
        total_net = summary['Net to Owner'].sum()
        total_clean = summary['Cleaning Fee'].sum()
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Owner Revenue", f"${total_net:,.2f}")
        with col2:
            st.metric("Total Cleaning to Pay Out", f"${total_clean:,.2f}")

        # Final Decision Logic
        if selected_owner.upper() == "ERAN":
            draft_amt = summary['Management Fee'].sum() + total_clean + summary['Web Fee'].sum()
            st.warning(f"👉 **Action Required:** Draft **${draft_amt:,.2f}** from Eran Maron.")
        else:
            payout = total_net - total_clean
            st.success(f"👉 **Action Required:** Payout **${payout:,.2f}** to Owner.")
    else:
        st.info("No reservations for this owner in the selected period.")
