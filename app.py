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
    url = "https://open-api.guesty.com/oauth2/token"
    if "CLIENT_ID" not in st.secrets or "CLIENT_SECRET" not in st.secrets:
        st.error("Missing API Credentials in Streamlit Secrets!")
        return None
        
    payload = {
        "grant_type": "client_credentials",
        "client_id": st.secrets["CLIENT_ID"].strip(),
        "client_secret": st.secrets["CLIENT_SECRET"].strip()
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    try:
        # Added a tiny sleep to prevent hitting rate limits during refreshes
        time.sleep(1) 
        r = requests.post(url, data=payload, headers=headers, timeout=15)
        
        if r.status_code == 429:
            st.error("Guesty Rate Limit Hit: Please wait 60 seconds and refresh.")
            return None
            
        r.raise_for_status()
        return r.json().get("access_token")
    except Exception as e:
        st.error(f"Token Error: {str(e)}")
        return None

@st.cache_data(ttl=600)
def fetch_master_data(month, year):
    token = get_guesty_token()
    if not token: return None, None, None
    
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    start = f"{year}-{month:02d}-01"
    end = f"{year}-{month:02d}-{calendar.monthrange(year, month)[1]}"
    
    try:
        # Get Owners
        owners_res = requests.get("https://open-api.guesty.com/v1/owners", headers=headers, timeout=15)
        owners = owners_res.json().get('results', [])
        
        # Get Reservations
        res_filter = json.dumps([
            {"field": "checkInDateLocalized", "operator": "$gte", "value": start},
            {"field": "checkInDateLocalized", "operator": "$lte", "value": end},
            {"field": "status", "operator": "$eq", "value": "confirmed"}
        ])
        res_url = f"https://open-api.guesty.com/v1/reservations?limit=100&filters={res_filter}"
        reservations = requests.get(res_url, headers=headers, timeout=15).json().get('results', [])
        
        # Get Listing Expenses
        exp_url = "https://open-api.guesty.com/v1/business-models-api/transactions/expenses-by-listing"
        expenses = requests.get(exp_url, headers=headers, params={"startDate": start, "endDate": end}, timeout=15).json().get("results", [])
        
        return owners, reservations, expenses
    except Exception as e:
        st.error(f"Data Fetch Error: {str(e)}")
        return None, None, None

# --- 2. THE DASHBOARD INTERFACE ---
st.set_page_config(page_title="Owner Portal", layout="wide")
st.title("🛡️ Guesty Automated Settlement Dashboard")

with st.sidebar:
    st.header("Settlement Period")
    m = st.selectbox("Month", range(1, 13), index=datetime.now().month - 1)
    y = st.number_input("Year", value=2026)
    st.info("Data is pulled directly from Guesty.")

owners_list, res_list, exp_list = fetch_master_data(m, y)

if owners_list:
    owner_map = {f"{o.get('firstName', '')} {o.get('lastName', '')}".strip(): o for o in owners_list}
    selected_owner_name = st.selectbox("Select Owner", [""] + sorted(owner_map.keys()))
    
    if selected_owner_name:
        owner_obj = owner_map[selected_owner_name]
        assigned_ids = owner_obj.get('listingIds', [])
        detailed_data = []

        for res in res_list:
            if res.get('listingId') in assigned_ids:
                money = res.get('money', {})
                acc = money.get('fare', 0)
                mgmt = money.get('commission', 0)
                cln = money.get('cleaningFee', 0)
                
                # Check for res-level expenses
                res_exp = sum(c.get('amount', 0) for c in money.get('extraCharges', []) if "expense" in str(c.get('description', '')).lower())
                
                # Fee Logic
                is_eran = "ERAN" in selected_owner_name.upper()
                src = res.get('source', '').lower()
                web_f = (acc * 0.01) if (is_eran and "engine" in src) else 0

                detailed_data.append({
                    "Property": res.get('listing', {}).get('title', 'Unknown'),
                    "Guest": res.get('guest', {}).get('fullName', 'Guest'),
                    "Accommodation": acc,
                    "Management Fee": mgmt,
                    "Cleaning Fee": cln,
                    "Expenses": res_exp,
                    "Net Income": acc - mgmt - web_f - res_exp
                })

        if detailed_data:
            df = pd.DataFrame(detailed_data)
            st.header(f"Financial Summary: {selected_owner_name}")
            c1, c2, c3, c4 = st.columns(4)
            
            listing_exp = sum(e.get('amount', 0) for e in exp_list if e.get('listingId') in assigned_ids)
            total_all_exp = df['Expenses'].sum() + listing_exp

            c1.metric("Gross Revenue", f"${df['Accommodation'].sum():,.2f}")
            c2.metric("Total Management", f"-${df['Management Fee'].sum():,.2f}")
            c3.metric("Total Expenses", f"-${total_all_exp:,.2f}")
            
            with c4:
                if is_eran:
                    total_draft = df['Management Fee'].sum() + df['Cleaning Fee'].sum() + total_all_exp + (df['Accommodation'].sum() * 0.01)
                    st.metric("TOTAL TO DRAFT", f"${total_draft:,.2f}")
                else:
                    final_pay = df['Net Income'].sum() - df['Cleaning Fee'].sum() - listing_exp
                    st.metric("NET PAYOUT", f"${final_pay:,.2f}")

            st.divider()
            st.header("📝 Detailed Reservation Review")
            st.dataframe(df, use_container_width=True)
            
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download CSV", data=csv, file_name=f"{selected_owner_name}.csv", mime='text/csv')
        else:
            st.warning("No confirmed reservations found for this period.")
else:
    st.info("Connecting to Guesty... please wait.")
