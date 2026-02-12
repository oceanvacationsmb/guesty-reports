import streamlit as st
import pandas as pd
from datetime import date

# --- 1. PERSISTENT SETTINGS ---
if 'owner_db' not in st.session_state:
    st.session_state.owner_db = {
        "ERAN": {"pct": 12.0, "type": "Draft"},
        "SMITH": {"pct": 15.0, "type": "Payout"},
    }

st.set_page_config(page_title="PMC Statement", layout="wide")

# --- 2. SIDEBAR: NAVIGATION & FILTERS ---
with st.sidebar:
    st.header("📂 Menu")
    view_mode = st.radio("View Selection", ["Statement Dashboard", "Taxes"], key="main_nav")
    
    st.divider()
    st.header("📊 Global Filters")
    active_owner = st.selectbox("Select Owner", sorted(st.session_state.owner_db.keys()), key="owner_sel")
    conf = st.session_state.owner_db[active_owner]

    # Date Period Logic
    st.subheader("📅 Period")
    report_type = st.selectbox("Select Range", ["By Month", "YTD", "Full Year"], key="date_type")
    
    # --- 3. SETTINGS & API (The Missing Section) ---
    st.divider()
    with st.expander("⚙️ Manage Owner Settings", expanded=False):
        st.write(f"Editing: **{active_owner}**")
        new_pct = st.number_input("Commission %", 0.0, 100.0, float(conf['pct']), key="edit_pct")
        new_type = st.selectbox("Type", ["Draft", "Payout"], index=0 if conf['type'] == "Draft" else 1, key="edit_type")
        
        if st.button("Save Owner Changes", key="save_owner"):
            st.session_state.owner_db[active_owner] = {"pct": new_pct, "type": new_type}
            st.success("Saved!")
            st.rerun()

    with st.expander("🔌 API Connection", expanded=False):
        st.text_input("Client ID", value="0oaszuo22iOg...", key="api_id")
        st.text_input("Client Secret", type="password", key="api_secret")

# --- 4. DATA LOGIC (Calculations) ---
# This part MUST run before the report displays
source_data = [
    {"ID": "RES-55421", "In": "02/01", "Out": "02/05", "Fare": 1200.0, "Clean": 150.0, "Exp": 25.0},
    {"ID": "RES-55429", "In": "02/10", "Out": "02/14", "Fare": 850.50, "Clean": 100.0, "Exp": 0.0},
]

# --- 5. REPORT RENDERING ---
if view_mode == "Taxes":
    st.title("⚖️ Taxes Compliance Report")
    if conf['type'] != "Payout":
        st.error("This report is only for 'Payout' accounts.")
    else:
        # Simple Tax Table
        tax_df = pd.DataFrame([{"State": "FL", "City": "Miami", "County": "Miami-Dade", "Property": "Ocean View", "Income": 5000.0}])
        st.dataframe(tax_df, use_container_width=True, hide_index=True)

else:
    st.title("📊 PMC Statement")
    # Show the metrics first
    c1, c2, c3 = st.columns(3)
    c1.metric("Owner", active_owner)
    c2.metric("Commission", f"{conf['pct']}%")
    c3.metric("Mode", conf['type'])
    
    st.divider()
    # Display the actual dataframe
    st.dataframe(pd.DataFrame(source_data), use_container_width=True, hide_index=True)
