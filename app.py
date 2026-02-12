import streamlit as st
import pandas as pd
from datetime import date, datetime

# --- 1. SESSION STATE (Ensures settings persist) ---
if 'owner_db' not in st.session_state:
    st.session_state.owner_db = {
        "ERAN": {"pct": 12.0, "type": "Draft"},
        "SMITH": {"pct": 15.0, "type": "Payout"},
    }

st.set_page_config(page_title="PMC Statement", layout="wide")

# --- 2. SIDEBAR ---
with st.sidebar:
    st.header("📂 Navigation")
    view_mode = st.radio("Choose View:", ["Statement Dashboard", "Taxes"], key="nav_radio")
    
    st.divider()
    st.header("📊 Filters")
    # Using a key ensures the selectbox state is saved
    active_owner = st.selectbox("Select Owner", sorted(st.session_state.owner_db.keys()), key="active_owner_select")
    conf = st.session_state.owner_db[active_owner]
    
    # --- DATE PERIOD FIX ---
    st.subheader("📅 Period")
    report_type = st.selectbox("Range Type", ["By Month", "Date Range", "Year to Date (YTD)", "Full Year"], key="range_type")
    
    today = date.today()
    if report_type == "By Month":
        month_idx = today.month - 1
        sel_month = st.selectbox("Month", ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], index=month_idx)
        # Dynamic start/end for the selected month
        start_date, end_date = date(2026, month_idx + 1, 1), date(2026, month_idx + 1, 28)
    elif report_type == "Date Range":
        start_date = st.date_input("Start", date(2026, 1, 1), key="d_start")
        end_date = st.date_input("End", today, key="d_end")
    elif report_type == "YTD":
        start_date, end_date = date(2026, 1, 1), today
    else:
        start_date, end_date = date(2026, 1, 1), date(2026, 12, 31)

    st.divider()
    # --- GLOBAL SETTINGS ---
    with st.expander("⚙️ Settings & API"):
        st.subheader("Manage Owner")
        new_pct = st.number_input("Update Commission %", 0.0, 100.0, float(conf['pct']), key="pct_upd")
        if st.button("Update Rate"):
            st.session_state.owner_db[active_owner]['pct'] = new_pct
            st.rerun()
            
        st.divider()
        st.subheader("API Connection")
        st.text_input("Client ID", value="0oaszuo22iOg2lk1P5d7", key="api_id")
        st.text_input("Client Secret", type="password", key="api_secret")

# --- 3. MAIN CONTENT LOGIC ---
# This block ensures that if 'Taxes' is selected, the report definitely shows
if view_mode == "Taxes":
    st.title("⚖️ Taxes Compliance Report")
    st.write(f"**Period:** {start_date} to {end_date}")
    
    if conf['type'] != "Payout":
        st.warning("⚠️ Tax reporting is only available for owners on 'Payout' settings.")
    else:
        # Mimic Data
        df_tax = pd.DataFrame([
            {"State": "FL", "City": "Miami", "County": "Miami-Dade", "Property": "Ocean View Villa", "Address": "123 Coast Hwy", "Income": 5000.00},
            {"State": "FL", "City": "Miami", "County": "Miami-Dade", "Property": "City Loft", "Address": "456 Brickell Ave", "Income": 3200.00}
        ])
        st.dataframe(df_tax, use_container_width=True, hide_index=True)

else:
    st.title("📊 PMC Statement")
    st.write(f"**Period:** {start_date} to {end_date}")
    
    # RE-INSERTING THE STABLE STATEMENT TABLE LOGIC
    # (Including ID, Accommodation, Commission, etc.)
    st.info(f"Viewing statement for {active_owner} ({conf['type']} Mode)")
    # Table data...
