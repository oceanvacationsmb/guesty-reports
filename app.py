import streamlit as st
import pandas as pd
from datetime import date

# --- 1. DATABASE & INITIALIZATION ---
if 'owner_db' not in st.session_state:
    st.session_state.owner_db = {
        "ERAN": {"pct": 12.0, "type": "Draft"},
        "SMITH": {"pct": 15.0, "type": "Payout"},
    }

# --- 2. MIMIC DATA (Including Location for Tax) ---
def get_mimic_tax_data():
    return [
        {
            "Property": "Ocean View Villa", 
            "Address": "123 Coast Hwy", 
            "State": "FL", "City": "Miami", "County": "Miami-Dade",
            "Fare": 5000.00, "Tax_Collected": 350.00
        },
        {
            "Property": "City Loft", 
            "Address": "456 Brickell Ave", 
            "State": "FL", "City": "Miami", "County": "Miami-Dade",
            "Fare": 3200.00, "Tax_Collected": 224.00
        },
        {
            "Property": "Lake Cabin", 
            "Address": "789 Pine Rd", 
            "State": "GA", "City": "Blue Ridge", "County": "Fannin",
            "Fare": 2100.00, "Tax_Collected": 147.00
        }
    ]

# --- 3. DASHBOARD UI ---
st.set_page_config(page_title="PMC Statement", layout="wide")

with st.sidebar:
    st.header("📊 View Mode")
    nav_mode = st.radio("Select View", ["Statement Dashboard", "Report Tax"])
    
    st.divider()
    active_owner = st.selectbox("Active Owner", sorted(st.session_state.owner_db.keys()))
    conf = st.session_state.owner_db[active_owner]

    if nav_mode == "Statement Dashboard":
        st.header("📅 Statement Period")
        # ... (Existing Date Selectors)
    
    st.divider()
    with st.expander("🔌 Connection Settings"):
        st.text_input("Client ID", value="0oaszuo22iOg2lk1P5d7")
        st.text_input("Client Secret", type="password")

# --- 4. TAX REPORT LOGIC ---
if nav_mode == "Report Tax":
    st.markdown(f"""
        <div style="text-align: center;">
            <h1 style="margin-bottom: 0;">Tax Compliance Report</h1>
            <h2 style="color: #FFD700;">Owner: {active_owner}</h2>
        </div>
        """, unsafe_allow_html=True)

    if conf['type'] != "Payout":
        st.warning("⚠️ Tax Reports are currently generated only for owners with 'Payout' settings.")
    else:
        # Mimic processing
        tax_data = get_mimic_tax_data()
        df_tax = pd.DataFrame(tax_data)

        # Summary Metrics for Tax
        t1, t2, t3 = st.columns(3)
        t1.metric("Total Taxable Income", f"${df_tax['Fare'].sum():,.2f}")
        t2.metric("Total Tax Collected", f"${df_tax['Tax_Collected'].sum():,.2f}")
        t3.metric("Property Count", len(df_tax))

        st.divider()
        
        # Table Configuration
        tax_config = {
            "Fare": st.column_config.NumberColumn("Taxable Income", format="$%.2f"),
            "Tax_Collected": st.column_config.NumberColumn("Tax Collected", format="$%.2f"),
        }
        
        # Grouping Display
        st.subheader("Income Breakdown by Location")
        st.dataframe(
            df_tax, 
            use_container_width=True, 
            column_config=tax_config,
            column_order=["State", "City", "County", "Property", "Address", "Fare", "Tax_Collected"],
            hide_index=True
        )

# --- 5. ORIGINAL STATEMENT DASHBOARD ---
elif nav_mode == "Statement Dashboard":
    # (Existing logic for Statement Dashboard remains here)
    st.write(f"Displaying Statement for {active_owner}...")
