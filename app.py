import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import calendar
import json

# --- 1. GUESTY API ENGINE ---
@st.cache_data(ttl=3600)
def get_guesty_token():
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
    token = get_guesty_token()
    if not token: return None, None, None
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    
    start = f"{year}-{month:02d}-01"
    end = f"{year}-{month:02d}-{calendar.monthrange(year, month)[1]}"
    
    # Fetch Owners
    owners = requests.get("https://open-api.guesty.com/v1/owners", headers=headers).json().get('results', [])
    
    # Fetch Reservations
    res_filter = json.dumps([
        {"field": "checkInDateLocalized", "operator": "$gte", "value": start},
        {"field": "checkInDateLocalized", "operator": "$lte", "value": end},
        {"field": "status", "operator": "$eq", "value": "confirmed"}
    ])
    res_url = f"https://open-api.guesty.com/v1/reservations?limit=100&filters={res_filter}"
    reservations = requests.get(res_url, headers=headers).json().get('results', [])
    
    # Fetch Expenses
    exp_url = "https://open-api.guesty.com/v1/business-models-api/transactions/expenses-by-listing"
    expenses = requests.get(exp_url, headers=headers, params={"startDate": start, "endDate": end}).json().get('results', [])
    
    return owners, reservations, expenses

# --- 2. INTERFACE & OWNER SELECTION ---
st.set_page_config(page_title="PMC Master Portal", layout="wide")
st.title("🛡️ Guesty Automated Settlement Dashboard")

# Month/Year Selection
with st.sidebar:
    st.header("Settlement Period")
    m = st.selectbox("Month", range(1, 13), index=datetime.now().month - 1)
    y = st.number_input("Year", value=2026)

owners_list, res_list, exp_list = fetch_master_data(m, y)

if owners_list:
    owner_map = {f"{o.get('firstName', '')} {o.get('lastName', '')}".strip(): o for o in owners_list}
    selected_owner_name = st.selectbox("Select Owner", [""] + sorted(owner_map.keys()))
    
    if selected_owner_name:
        selected_owner_obj = owner_map[selected_owner_name]
        assigned_ids = selected_owner_obj.get('listingIds', [])

        # --- 3. DATA PROCESSING ---
        detailed_data = []
        for res in res_list:
            if res.get('listingId') in assigned_ids:
                m_data = res.get('money', {})
                acc = m_data.get('fare', 0)
                mgmt = m_data.get('commission', 0)
                cln = m_data.get('cleaningFee', 0)
                
                # Manual expenses from extraCharges
                res_exp = sum(c.get('amount', 0) for c in m_data.get('extraCharges', []) if "expense" in str(c.get('description', '')).lower())
                
                # Eran Web Fee logic
                is_eran = "ERAN" in selected_owner_name.upper()
                src = res.get('source', '').lower()
                web_f = (acc * 0.01) if (is_eran and "engine" in src) else 0

                detailed_data.append({
                    "Property": res.get('listing', {}).get('title', 'Unknown'),
                    "Guest": res.get('guest', {}).get('fullName', 'Guest'),
                    "Accommodation": acc,
                    "Management Fee": mgmt,
                    "Cleaning Fee": cln,
                    "Web Fee": web_f,
                    "Expenses": res_exp,
                    "Net Income": acc - mgmt - web_f - res_exp
                })

        if detailed_data:
            df = pd.DataFrame(detailed_data)
            
            # --- SUMMARY SECTION ---
            st.header(f"Financial Summary: {selected_owner_name}")
            c1, c2, c3, c4 = st.columns(4)
            
            # Global listing-level expenses
            global_exp = sum(e.get('amount', 0) for e in exp_list if e.get('listingId') in assigned_ids)
            total_exp = df['Expenses'].sum() + global_exp

            c1.metric("Gross Accomm.", f"${df['Accommodation'].sum():,.2f}")
            c2.metric("Total Mgmt Fees", f"-${df['Management Fee'].sum():,.2f}")
            c3.metric("Total Expenses", f"-${total_exp:,.2f}")
            
            with c4:
                if is_eran:
                    to_draft = df['Management Fee'].sum() + df['Cleaning Fee'].sum() + total_exp + df['Web Fee'].sum()
                    st.metric("TOTAL TO DRAFT", f"${to_draft:,.2f}")
                else:
                    st.metric("NET PAYOUT", f"${(df['Net Income'].sum() - df['Cleaning Fee'].sum() - global_exp):,.2f}")

            # --- DETAILED TABLE (FOR REVIEW) ---
            st.divider()
            st.header("📝 Detailed Reservation Breakdown")
            st.dataframe(df, use_container_width=True)
            
            if global_exp > 0:
                st.subheader("🛠️ Property Invoices (Non-Reservation)")
                inv_data = [{"Date": e.get('date'), "Property": e.get('listing', {}).get('title'), "Description": e.get('description'), "Amount": e.get('amount')} for e in exp_list if e.get('listingId') in assigned_ids]
                st.table(inv_data)

            # --- CSV EXPORT (FOR PDF) ---
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Statement Data", data=csv, file_name=f"{selected_owner_name}_report.csv", mime='text/csv')
        else:
            st.warning("No data found for this owner in this month.")
else:
    st.error("Connection error. Please check your API keys.")
