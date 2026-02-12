import streamlit as st
import pandas as pd
from datetime import date, datetime

# --- 1. INITIALIZATION ---
if 'owner_db' not in st.session_state:
    st.session_state.owner_db = {
        "ERAN": {"pct": 12.0, "type": "Draft"},
        "SMITH": {"pct": 15.0, "type": "Payout"},
    }

st.set_page_config(page_title="PMC Statement", layout="wide")

# --- 2. SIDEBAR (The Fix) ---
with st.sidebar:
    st.header("📂 Navigation")
    view_mode = st.radio("Choose View:", ["Statement Dashboard", "Taxes"])
    
    st.divider()
    st.header("📊 Global Filters")
    active_owner = st.selectbox("Active Owner", sorted(st.session_state.owner_db.keys()))
    conf = st.session_state.owner_db[active_owner]
    
    # --- DATE PERIOD LOGIC ---
    st.subheader("📅 Period")
    report_type = st.selectbox("Range Type", ["By Month", "Date Range", "Year to Date (YTD)", "Full Year"])
    
    today = date.today()
    if report_type == "By Month":
        sel_month = st.selectbox("Month", ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], index=today.month-1)
        start_date, end_date = date(2026, 1, 1), date(2026, 12, 31) # Logic placeholder
    elif report_type == "Date Range":
        start_date = st.date_input("Start", date(2026, 1, 1))
        end_date = st.date_input("End", today)
    elif report_type == "YTD":
        start_date, end_date = date(2026, 1, 1), today
    else: # Full Year
        start_date, end_date = date(2026, 1, 1), date(2026, 12, 31)

    st.divider()
    # --- SETTINGS SECTIONS ---
    with st.expander("⚙️ Manage Owners"):
        st.info("Edit rates or add new owners here.")
        # Management UI...
        
    with st.expander("🔌 API Connection"):
        st.text_input("Client ID", value="0oaszuo22iOg2lk1P5d7", key="api_id")
        st.text_input("Client Secret", type="password", key="api_secret")

# --- 3. MAIN CONTENT ---
if view_mode == "Taxes":
    st.title("⚖️ Taxes Compliance Report")
    if conf['type'] != "Payout":
        st.warning("Tax reporting is exclusive to Payout-style owners.")
    else:
        # (Tax Table Logic)
        st.info(f"Showing tax data for {active_owner} from {start_date} to {end_date}")
        st.table([{"State": "FL", "City": "Miami", "County": "Miami-Dade", "Address": "123 Coast Hwy", "Income": 5000.00}])

else:
    st.title("📊 PMC Statement")
    # Restore standard Dashboard Logic (ID column, Summary Cards, etc.)
    # ...
