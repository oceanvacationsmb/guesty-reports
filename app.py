import streamlit as st
import pandas as pd
from datetime import datetime, date

# --- 1. DATABASE & INITIALIZATION ---
if 'owner_db' not in st.session_state:
    st.session_state.owner_db = {
        "ERAN": {"pct": 12.0, "type": "Draft"},
        "SMITH": {"pct": 15.0, "type": "Payout"},
    }

# --- 2. MIMIC DATA ---
def get_mimic_reservations():
    return [
        {"ID": "RES-55421", "In": date(2026, 2, 1), "Out": date(2026, 2, 5), "Fare": 1200.0, "Clean": 150.0, "Exp": 25.0},
        {"ID": "RES-55429", "In": date(2026, 2, 10), "Out": date(2026, 2, 14), "Fare": 850.50, "Clean": 100.0, "Exp": 0.0},
        {"ID": "RES-55435", "In": date(2026, 2, 18), "Out": date(2026, 2, 22), "Fare": 2100.75, "Clean": 180.0, "Exp": 45.10}
    ]

def get_mimic_tax_data():
    return [
        {"Property": "Ocean View Villa", "Address": "123 Coast Hwy", "State": "FL", "City": "Miami", "County": "Miami-Dade", "Income": 5000.00},
        {"Property": "City Loft", "Address": "456 Brickell Ave", "State": "FL", "City": "Miami", "County": "Miami-Dade", "Income": 3200.00},
        {"Property": "Mountain Retreat", "Address": "789 Peak Rd", "State": "CO", "City": "Aspen", "County": "Pitkin", "Income": 4500.00}
    ]

# --- 3. SIDEBAR ---
st.set_page_config(page_title="PMC Statement", layout="wide")

with st.sidebar:
    st.header("📂 Navigation")
    view_option = st.radio("Go to:", ["Statement Dashboard", "Taxes"])
    
    st.divider()
    st.header("📊 View Report")
    active_owner = st.selectbox("Switch Active Owner", sorted(st.session_state.owner_db.keys()))
    conf = st.session_state.owner_db[active_owner]

    st.divider()
    st.header("⚙️ Settings")
    with st.expander("Manage Owners"):
        # ... (Owner management logic)
        pass
    
    with st.expander("🔌 Connection Settings"):
        st.text_input("Client ID", value="0oaszuo22iOg2lk1P5d7")
        st.text_input("Client Secret", type="password")

# --- 4. TAXES VIEW ---
if view_option == "Taxes":
    st.markdown(f"<div style='text-align: center;'><h1 style='margin-bottom: 0;'>Tax Income Report</h1><h2 style='color: #FFD700;'>Owner: {active_owner}</h2></div><br>", unsafe_allow_html=True)
    
    if conf['type'] != "Payout":
        st.error("The Tax Report is only available for owners set to 'Payout' mode.")
    else:
        tax_df = pd.DataFrame(get_mimic_tax_data())
        
        # Summary for Tax
        t1, t2 = st.columns(2)
        t1.metric("Total Taxable Income", f"${tax_df['Income'].sum():,.2f}")
        t2.metric("Active Tax Jurisdictions", tax_df['County'].nunique())
        
        st.divider()
        
        tax_config = {"Income": st.column_config.NumberColumn(format="$%.2f")}
        st.dataframe(
            tax_df, 
            use_container_width=True, 
            column_config=tax_config,
            column_order=["State", "City", "County", "Property", "Address", "Income"],
            hide_index=True
        )

# --- 5. STATEMENT DASHBOARD VIEW ---
else:
    st.markdown(f"<div style='text-align: center;'><h1 style='margin-bottom: 0;'>PMC Statement</h1><h2 style='color: #FFD700;'>Reservation Report: {active_owner}</h2></div><br>", unsafe_allow_html=True)
    
    # Calculations & Table Display for Statement (Standard logic as before)
    # ...
