import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import calendar

# --- 1. GUESTY API HELPERS ---
def get_guesty_token():
    url = "https://open-api.guesty.com/oauth2/token"
    try:
        payload = {
            "grant_type": "client_credentials",
            "client_id": st.secrets["CLIENT_ID"],
            "client_secret": st.secrets["CLIENT_SECRET"]
        }
        response = requests.post(url, data=payload)
        return response.json().get("access_token")
    except:
        st.error("API Keys missing! Go to Settings > Secrets in Streamlit.")
        return None

def fetch_data(month, year):
    token = get_guesty_token()
    if not token: return []
    
    headers = {"Authorization": f"Bearer {token}", "accept": "application/json"}
    
    # Simpler date format to avoid the ValueError
    start_date = f"{year}-{month:02d}-01"
    last_day = calendar.monthrange(year, month)[1]
    end_date = f"{year}-{month:02d}-{last_day}"
    
    # Fetching Reservations
    url = f"https://open-api.guesty.com/v1/reservations?limit=100&filters=[{{'field':'checkInDate','operator':'$gte','value':'{start_date}'}},{{'field':'checkInDate','operator':'$lte','value':'{end_date}'}}]"
    
    res = requests.get(url, headers=headers)
    return res.json().get("results", [])

# --- 2. THE REPORT LOGIC ---
st.title("🏡 Guesty Automated Monthly Report")

col1, col2, col3 = st.columns(3)
with col1:
    owner = st.selectbox("Select Owner", ["ERAN MARON", "YEN FRENCH"])
with col2:
    m = st.selectbox("Month", range(1, 13), index=datetime.now().month - 1)
with col3:
    y = st.number_input("Year", value=2026)

if st.button("Generate Monthly Report"):
    with st.spinner("Talking to Guesty..."):
        data = fetch_data(m, y)
        
        if not data:
            st.warning(f"No reservations found for {calendar.month_name[m]} {y}. Try a different month?")
        else:
            rows = []
            for res in data:
                # Basic Math
                acc = res.get('money', {}).get('fare', 0)
                clean = res.get('money', {}).get('cleaningFee', 0)
                source = res.get('source', '').lower()
                prop_title = res.get('listing', {}).get('title', 'Unknown Property')
                
                # Eran's 1% Website Fee (Checks if source is 'booking engine')
                is_eran = "ERAN" in owner.upper()
                web_fee = (acc * 0.01) if (is_eran and "engine" in source) else 0
                
                # PMC Logic (12% for Eran, 15% for others)
                rate = 0.12 if is_eran else 0.15
                pmc_amt = acc * rate
                
                # FINDING EXPENSES (Looking for Guesty Financial Orders)
                # Note: We look for attachments/links if they exist in the reservation data
                expense_total = 0
                expense_links = []
                
                # This part looks for any extra charges listed as 'manually added'
                for charge in res.get('money', {}).get('extraCharges', []):
                    if "expense" in charge.get('description', '').lower():
                        expense_total += charge.get('amount', 0)
                
                rows.append({
                    "Property": prop_title,
                    "Accommodation": acc,
                    "Cleaning": clean,
                    "PMC": pmc_amt,
                    "Web Fee": web_fee,
                    "Expenses": expense_total
                })
            
            # --- DISPLAY SUMMARY ---
            df = pd.DataFrame(rows)
            summary = df.groupby("Property").sum().reset_index()
            
            st.write(f"### Property Summary for {owner}")
            st.table(summary)
            
            # Final Totals
            total_acc = summary['Accommodation'].sum()
            total_pmc = summary['PMC'].sum()
            total_clean = summary['Cleaning'].sum()
            total_web = summary['Web Fee'].sum()
            total_exp = summary['Expenses'].sum()
            
            st.write("---")
            st.write("### Monthly Totals")
            st.write(f"**Total Accommodation:** ${total_acc:,.2f}")
            st.write(f"**Management Fee ({int(rate*100)}%):** -${total_pmc:,.2f}")
            st.write(f"**Total Cleaning Fees:** -${total_clean:,.2f}")
            
            if is_eran:
                st.write(f"**1% Website Fees:** -${total_web:,.2f}")
                net = (total_acc + total_clean) - (total_pmc + total_clean + total_exp + total_web)
                st.info(f"**Amount to DRAFT from Eran:** ${abs(net):,.2f}")
            else:
                net = total_acc - (total_pmc + total_clean + total_exp)
                st.success(f"**Net Owner Payout:** ${net:,.2f}")
