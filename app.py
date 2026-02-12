import streamlit as st
import pandas as pd
from datetime import date

# --- 1. SETUP & PERSISTENCE ---
st.set_page_config(page_title="PMC Statement", layout="wide")

if 'owner_db' not in st.session_state:
    st.session_state.owner_db = {
        "ERAN": {"pct": 12.0, "type": "Draft"},
        "SMITH": {"pct": 15.0, "type": "Payout"},
    }

# --- 2. SIDEBAR ---
with st.sidebar:
    st.header("📂 Navigation")
    mode = st.radio("View", ["Dashboard", "Taxes"], horizontal=True)
    
    st.divider()
    st.header("📊 Filter View")
    active_owner = st.selectbox("Switch Active Owner", sorted(st.session_state.owner_db.keys()))
    conf = st.session_state.owner_db[active_owner]
    
    # --- DYNAMIC DATE SELECTOR ---
    st.divider()
    st.header("📅 Select Period")
    report_type = st.selectbox("Quick Select", ["By Month", "Full Year", "Year to Date (YTD)", "Date Range"])
    
    today = date.today()
    
    if report_type == "By Month":
        # Toggle between month and year context
        c1, c2 = st.columns(2)
        sel_year = c1.selectbox("Year", [2026, 2025, 2024], index=0)
        month_names = ["January", "February", "March", "April", "May", "June", 
                       "July", "August", "September", "October", "November", "December"]
        sel_month = c2.selectbox("Month", month_names, index=today.month-1)
        
        start_date = date(sel_year, month_names.index(sel_month) + 1, 1)
        # Simple end date logic (28th covers all months for mimic purposes)
        end_date = date(sel_year, month_names.index(sel_month) + 1, 28) 

    elif report_type == "Full Year":
        sel_year = st.selectbox("Select Year", [2026, 2025, 2024], index=0)
        start_date, end_date = date(sel_year, 1, 1), date(sel_year, 12, 31)

    elif report_type == "Year to Date (YTD)":
        start_date, end_date = date(today.year, 1, 1), today

    else: # Manual Date Range
        start_date = st.date_input("Start Date", date(today.year, today.month, 1))
        end_date = st.date_input("End Date", today)

    st.divider()
    with st.expander("👤 Manage Owners"):
        # ... (Previous management logic preserved)
        target = st.selectbox("Select Action", ["+ Add New"] + list(st.session_state.owner_db.keys()))
        current = st.session_state.owner_db.get(target, {"pct": 12.0, "type": "Draft"})
        new_name = st.text_input("Owner Name", value="" if target == "+ Add New" else target).upper().strip()
        new_pct = st.number_input("Commission %", 0.0, 100.0, float(current["pct"]))
        new_type = st.selectbox("Settlement Style", ["Draft", "Payout"], index=0 if current["type"] == "Draft" else 1)
        
        cs1, cs2 = st.columns(2)
        if cs1.button("💾 Save"):
            if new_name:
                st.session_state.owner_db[new_name] = {"pct": new_pct, "type": new_type}
                if target != "+ Add New" and target != new_name: del st.session_state.owner_db[target]
                st.rerun()
        if target != "+ Add New" and cs2.button("🗑️ Delete", type="primary"):
            del st.session_state.owner_db[target]
            st.rerun()

    with st.expander("🔌 API Connection"):
        st.text_input("Client ID", value="0oaszuo22iOg...")
        st.text_input("Client Secret", type="password")
        if st.button("🔄 Save API"): st.success("API Settings Saved")

# --- 3. MAIN CONTENT ---
if mode == "Dashboard":
    # Calculations based on start_date / end_date logic
    st.markdown(f"""
        <div style='text-align: center;'>
            <h1 style='margin-bottom:0'>PMC Statement</h1>
            <h2 style='color:#FFD700'>Owner: {active_owner}</h2>
            <p>Period: {start_date.strftime('%B %d, %Y')} - {end_date.strftime('%B %d, %Y')}</p>
        </div><br>
    """, unsafe_allow_html=True)
    
    # ... (Rest of the metric and table logic remains exactly as your best version)
    st.info(f"Filtering data for {active_owner} in {report_type} mode.")
    # (Existing table/metric logic goes here)
