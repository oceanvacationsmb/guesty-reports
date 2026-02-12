import streamlit as st
import requests
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io
from datetime import datetime
import calendar

# --- 1. GUESTY API CONNECTION ---
def get_guesty_token():
    url = "https://open-api.guesty.com/oauth2/token"
    # Using secrets stored in Streamlit dashboard
    payload = {
        "grant_type": "client_credentials",
        "client_id": st.secrets["CLIENT_ID"],
        "client_secret": st.secrets["CLIENT_SECRET"]
    }
    response = requests.post(url, data=payload)
    return response.json().get("access_token")

def fetch_monthly_data(month, year):
    token = get_guesty_token()
    headers = {"Authorization": f"Bearer {token}", "accept": "application/json"}
    
    # Calculate start and end of the month
    last_day = calendar.monthrange(year, month)[1]
    start_date = f"{year}-{month:02d}-01T00:00:00Z"
    end_date = f"{year}-{month:02d}-{last_day}T23:59:59Z"
    
    # API Filter for confirmed bookings checking in this month
    filters = f'[{"field":"checkIn","operator":"$between","from":"{start_date}","to":"{end_date}"},{"field":"status","operator":"$eq","value":"confirmed"}]'
    url = f"https://open-api.guesty.com/v1/reservations?limit=100&filters={filters}&fields=money listing source"
    
    res = requests.get(url, headers=headers)
    return res.json().get("results", [])

# --- 2. DATA PROCESSING & SUMMARY ---
def create_summary(raw_reservations, owner_name):
    rows = []
    for res in raw_reservations:
        acc = res.get('money', {}).get('fare', 0)
        clean = res.get('money', {}).get('cleaningFee', 0)
        payout = res.get('money', {}).get('netPayout', 0)
        source = res.get('source', '').lower()
        prop_title = res.get('listing', {}).get('title', 'Unknown Property')
        
        # FIXED: 1% Website Fee only for Eran on "booking engine" source
        web_fee = (acc * 0.01) if ("ERAN" in owner_name.upper() and "booking engine" in source) else 0
        
        rows.append({
            "Property": prop_title,
            "Accommodation": acc,
            "Cleaning": clean,
            "Net Payout": payout,
            "Web Fee": web_fee
        })
    
    df = pd.DataFrame(rows)
    # Group by Property to show Total per Property
    summary = df.groupby("Property").sum().reset_index()
    return summary

# --- 3. THE WEBSITE UI ---
st.title("🏡 Guesty Automated Monthly Report")

col1, col2, col3 = st.columns(3)
with col1:
    owner = st.selectbox("Select Owner", ["ERAN MARON", "YEN FRENCH"])
with col2:
    m = st.selectbox("Month", range(1, 13), index=datetime.now().month - 1)
with col3:
    y = st.number_input("Year", value=2026)

if st.button("Generate Monthly Report"):
    with st.spinner("Fetching data from Guesty..."):
        data = fetch_monthly_data(m, y)
        if not data:
            st.error("No reservations found for this month.")
        else:
            summary_df = create_summary(data, owner)
            st.write(f"### Report for {owner} - {calendar.month_name[m]} {y}")
            st.table(summary_df)
            
            # Show the Big Totals
            total_acc = summary_df['Accommodation'].sum()
            total_web = summary_df['Web Fee'].sum()
            st.metric("Total Combined Accommodation", f"${total_acc:,.2f}")
            if owner == "ERAN MARON":
                st.metric("Total Website Fees (1%)", f"-${total_web:,.2f}")
