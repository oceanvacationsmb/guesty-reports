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
    # Ensure these secrets are set in your Streamlit Cloud dashboard
    payload = {
        "grant_type": "client_credentials",
        "client_id": st.secrets["CLIENT_ID"].strip(),
        "client_secret": st.secrets["CLIENT_SECRET"].strip()
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    try:
        r = requests.post(url, data=payload, headers=headers)
        return r.json().get("access_token")
    except Exception as e:
        st.error(f"Auth Error: {e}")
        return None

@st.cache_data(ttl=600)
def fetch_master_data(month, year):
    """Pulls all owners, reservations, and expenses for the month."""
    token = get_guesty_token()
    if not token: return None, None, None
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    
    start = f"{year}-{month:02d}-01"
    end = f"{year}-{month:02d}-{calendar.monthrange(year, month)[1]}"
    
    # A. Fetch Owners to link properties
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
    st.caption("All data is pulled from Guesty financials and native owner assignments.")

owners_list, res_list, exp_list = fetch_master_data(m, y)

if owners_list:
    # Build a clean owner dropdown
    owner_map = {f"{o.get('firstName', '')} {o.get('lastName', '')}".strip(): o for o in owners_list}
    selected_owner_name = st.selectbox("Select Owner to View Statement", sorted(owner_map.keys()))
    
    selected_owner_obj = owner_map[selected_owner_name]
    assigned_listing_ids = selected_owner_obj.get('listingIds', [])

    # --- 3. CALCULATE PROPERTY PERFORMANCE ---
    processed_res = []
    for res in res_list:
        if res.get('listingId') in assigned_listing_ids:
            money = res.get('money', {})
            acc = money.get('fare', 0)
            pmc_fee = money.get('commission', 0) # Pulls the fee you set in Guesty
            cleaning = money.get('cleaningFee', 0)
            
            # 1% Website Fee logic (Fixed syntax error from screenshot)
            source = res.get('source', '').lower()
            web_fee = (acc * 0.01) if ("ERAN" in selected_owner_name.upper() and "engine" in source) else 0
            
            processed_res.append({
                "Property": res.get('listing', {}).get('title', 'Unknown'),
                "Gross Accommodation": acc,
                "Cleaning Fee": cleaning,
                "Management Fee": pmc_fee,
                "Web Fee": web_fee,
                "Net Income": acc - pmc_fee - web_fee
            })

    if processed_res:
        df_res = pd.DataFrame(processed_res)
        summary = df_res.groupby("Property").sum().reset_index()
        
        st.subheader(f"📊 Summary for {selected_owner_name}")
        st.table(summary)

        # --- 4. CALCULATE EXPENSES & INVOICES ---
        st.divider()
        st.subheader("🛠️ Manual Expenses & Invoices")
        
        owner_expenses = [e for e in exp_list if e.get('listingId') in assigned_listing_ids]
        if owner_expenses:
            df_exp = pd.DataFrame([{
                "Date": e.get('date'),
                "Listing": e.get('listing', {}).get('title'),
                "Description": e.get('description', 'Purchase/Invoice'),
                "Amount": e.get('amount', 0)
            } for e in owner_expenses])
            st.table(df_exp)
            total_expenses = df_exp['Amount'].sum()
        else:
            st.info("No manual expenses or invoices found for this period.")
            total_expenses = 0

        # --- 5. FINAL SETTLEMENT LOGIC ---
        st.divider()
        total_income = summary['Net Income'].sum()
        total_cleaning = summary['Cleaning Fee'].sum()
        final_balance = total_income - total_expenses

        c1, c2, c3 = st.columns(3)
        c1.metric("Total Net Income", f"${total_income:,.2f}")
        c2.metric("Total Expenses", f"-${total_expenses:,.2f}")
        
        with c3:
            if "ERAN" in selected_owner_name.upper():
                # Eran's logic: He gets gross, then you draft fees
                total_mgmt = summary['Management Fee'].sum()
                total_web = summary['Web Fee'].sum()
                draft_amount = total_mgmt + total_cleaning + total_expenses + total_web
                st.metric("TOTAL TO DRAFT", f"${draft_amount:,.2f}")
                st.error(f"Action: Draft **${draft_amount:,.2f}** from {selected_owner_name}")
            else:
                # Standard Logic: You pay the net
                st.metric("FINAL PAYOUT", f"${final_balance:,.2f}")
                st.success(f"Action: Payout **${final_balance:,.2f}** to {selected_owner_name}")
    else:
        st.warning(f"No reservations found for {selected_owner_name} in this period.")
else:
    st.error("Could not connect to Guesty. Please verify your CLIENT_ID and CLIENT_SECRET in Streamlit Secrets.")
