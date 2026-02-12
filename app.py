import streamlit as st
import requests
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io
from datetime import datetime

# --- 1. GUESTY API CONNECTION ---
def get_guesty_token():
    url = "https://open-api.guesty.com/oauth2/token"
    payload = {
        "grant_type": "client_credentials",
        "scope": "all",
        "client_id": st.secrets["CLIENT_ID"],
        "client_secret": st.secrets["CLIENT_SECRET"]
    }
    response = requests.post(url, data=payload)
    return response.json().get("access_token")

def fetch_guesty_data(month, year):
    token = get_guesty_token()
    headers = {"Authorization": f"Bearer {token}", "accept": "application/json"}
    
    # Filtering for the specific month
    start_date = f"{year}-{month:02d}-01"
    # Simplified query for reservations in that range
    url = f"https://open-api.guesty.com/v1/reservations?limit=100&filters=[{{'field':'checkInDate','operator':'$gte','value':'{start_date}'}}]"
    
    res = requests.get(url, headers=headers)
    return res.json().get("results", [])

# --- 2. THE LOGIC ENGINE ---
def process_report(reservations, owner_name):
    report_data = []
    
    for r in reservations:
        # Check if this reservation belongs to the selected owner (simplified)
        # In real use, we'd filter by Listing ID or Tag
        acc = r.get('money', {}).get('fare', 0)
        cleaning = r.get('money', {}).get('cleaningFee', 0)
        payout = r.get('money', {}).get('netPayout', 0)
        source = r.get('source', '').lower()
        prop_name = r.get('listing', {}).get('title', 'Unknown Property')

        # 1% Website Fee Rule for Eran
        web_fee = (acc * 0.01) if ("ERAN" in owner_name.upper() and "website" in source) else 0
        
        report_data.append({
            "Property": prop_name,
            "Accommodation": acc,
            "Cleaning": cleaning,
            "Payout": payout,
            "WebFee": web_fee
        })
    
    df = pd.DataFrame(report_data)
    # Grouping by Property (Property Summary)
    summary = df.groupby("Property").sum().reset_index()
    return summary

# --- 3. THE WEBSITE UI ---
st.title("🏡 Automatic Owner Statements")

col1, col2, col3 = st.columns(3)
with col1:
    owner = st.selectbox("Select Owner", ["ERAN MARON", "YEN FRENCH"])
with col2:
    report_month = st.selectbox("Month", range(1, 13), index=datetime.now().month - 1)
with col3:
    report_year = st.number_input("Year", value=2026)

if st.button("Pull Data from Guesty"):
    with st.spinner("Fetching data..."):
        raw_data = fetch_guesty_data(report_month, report_year)
        if not raw_data:
            st.error("No reservations found for this period.")
        else:
            summary_df = process_report(raw_data, owner)
            
            st.subheader(f"Property Summary Report - {owner}")
            st.table(summary_df)
            
            # Totals for the Summary Page
            total_acc = summary_df['Accommodation'].sum()
            total_web = summary_df['WebFee'].sum()
            
            st.metric("Combined Accommodation", f"${total_acc:,.2f}")
            if owner == "ERAN MARON":
                st.metric("Total Website Fees (1%)", f"-${total_web:,.2f}")
