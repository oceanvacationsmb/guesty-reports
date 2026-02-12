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
    
    # --- ENHANCED DATE SELECTOR ---
    st.divider()
    st.header("📅 Select Period")
    report_type = st.selectbox("Quick Select", ["By Month", "Full Year", "YTD", "Date Range"])
    
    today = date.today()
    
    # Logic to switch between Month/Year UI
    if report_type == "By Month":
        c1, c2 = st.columns(2)
        sel_year = c1.selectbox("Year", [2026, 2025, 2024], index=0)
        month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        sel_month = c2.selectbox("Month", month_names, index=today.month-1)
        start_date = date(sel_year, month_names.index(sel_month)+1, 1)
        end_date = date(sel_year, month_names.index(sel_month)+1, 28) # Dynamic placeholder

    elif report_type == "Full Year":
        sel_year = st.selectbox("Select Year Context", [2026, 2025, 2024], index=0)
        start_date, end_date = date(sel_year, 1, 1), date(sel_year, 12, 31)

    elif report_type == "YTD":
        start_date, end_date = date(today.year, 1, 1), today
        st.info(f"Showing {today.year} Year to Date")

    else: # Date Range
        start_date = st.date_input("Start", date(today.year, today.month, 1))
        end_date = st.date_input("End", today)

    st.divider()
    # --- SETTINGS SECTIONS (OWNER & API) ---
    with st.expander("👤 Manage Owners"):
        target = st.selectbox("Edit/Delete", ["+ Add New"] + list(st.session_state.owner_db.keys()))
        curr = st.session_state.owner_db.get(target, {"pct": 12.0, "type": "Draft"})
        n_name = st.text_input("Name", value="" if target == "+ Add New" else target).upper().strip()
        n_pct = st.number_input("Comm %", 0.0, 100.0, float(curr["pct"]))
        n_style = st.selectbox("Style", ["Draft", "Payout"], index=0 if curr["type"] == "Draft" else 1)
        
        b1, b2 = st.columns(2)
        if b1.button("💾 Save"):
            st.session_state.owner_db[n_name] = {"pct": n_pct, "type": n_style}
            if target != "+ Add New" and target != n_name: del st.session_state.owner_db[target]
            st.rerun()
        if target != "+ Add New" and b2.button("🗑️ Delete", type="primary"):
            del st.session_state.owner_db[target]; st.rerun()

    with st.expander("🔌 API Connection"):
        st.text_input("Client ID", value="0oaszuo22iOg...")
        st.text_input("Client Secret", type="password")
        if st.button("🔄 Save & Fetch Data", type="primary"):
            st.cache_data.clear()
            st.rerun()

# --- 3. MAIN CONTENT (GRAND TOTAL + PROPERTY TABLES) ---
# (Calculation logic remains identical to the previous Master Version)
if mode == "Dashboard":
    st.markdown(f"<div style='text-align: center;'><h1 style='margin-bottom:0;'>PMC Master Statement</h1><h2 style='color:#FFD700;'>{active_owner}</h2></div>", unsafe_allow_html=True)
    
    # Grand Total Section
    # Property Table 1...
    # Property Table 2...
    st.success(f"Report Generated for: {start_date} to {end_date}")
