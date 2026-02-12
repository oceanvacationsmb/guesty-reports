import streamlit as st
import pandas as pd
from datetime import date

# --- 1. SETUP & PERSISTENCE ---
st.set_page_config(page_title="PMC Master Statement", layout="wide")

if 'owner_db' not in st.session_state:
    st.session_state.owner_db = {
        "ERAN": {"pct": 12.0, "type": "Draft"},
        "SMITH": {"pct": 15.0, "type": "Payout"},
    }

# Mimic data with multiple properties and simulated tax rates
def get_mimic_data(owner):
    if owner == "ERAN":
        return [
            {"ID": "RES-101", "Prop": "Sunset Villa", "Addr": "742 Evergreen Terrace", "City": "Miami", "In": date(2026, 2, 1), "Out": date(2026, 2, 5), "Fare": 1200.0, "Cln": 150.0, "Exp": 25.0},
            {"ID": "RES-201", "Prop": "Beach House", "Addr": "123 Ocean Drive", "City": "Miami", "In": date(2026, 2, 5), "Out": date(2026, 2, 8), "Fare": 2500.0, "Cln": 200.0, "Exp": 150.0}
        ]
    # Smith is a Payout account
    return [
        {"ID": "RES-301", "Prop": "Mountain Lodge", "Addr": "55 Peak Road", "City": "Aspen", "In": date(2026, 2, 1), "Out": date(2026, 2, 5), "Fare": 1500.0, "Cln": 100.0, "Exp": 10.0},
        {"ID": "RES-302", "Prop": "Mountain Lodge", "Addr": "55 Peak Road", "City": "Aspen", "In": date(2026, 2, 10), "Out": date(2026, 2, 14), "Fare": 1800.0, "Cln": 100.0, "Exp": 0.0}
    ]

# --- 2. SIDEBAR (Navigation & Settings) ---
with st.sidebar:
    st.header("📂 Navigation")
    mode = st.radio("View Mode", ["Dashboard", "Taxes"], horizontal=True)
    
    st.divider()
    active_owner = st.selectbox("Active Owner", sorted(st.session_state.owner_db.keys()))
    conf = st.session_state.owner_db[active_owner]
    
    st.divider()
    st.header("📅 Select Period")
    report_type = st.selectbox("Context", ["By Month", "Full Year", "YTD"])
    
    today = date.today()
    if report_type == "By Month":
        c1, c2 = st.columns(2)
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        sel_month = c1.selectbox("Month", months, index=today.month-1)
        sel_year = c2.selectbox("Year", [2026, 2025], index=0)
        start_date = date(sel_year, months.index(sel_month)+1, 1)
    else:
        sel_year = st.selectbox("Year", [2026, 2025], index=0)
        start_date = date(sel_year, 1, 1)

    with st.expander("🔌 API", expanded=False):
        st.text_input("Client ID", value="0oaszuo22iOg...")
        if st.button("🔄 Save & Run", type="primary", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

# --- 3. LOGIC & CALCULATIONS ---
data = get_mimic_data(active_owner)
df_all = pd.DataFrame(data)

# --- 4. DISPLAY ---
if mode == "Dashboard":
    # (Dashboard logic remains as previously perfected)
    st.title(f"Master Statement: {active_owner}")
    st.info("Switch to 'Taxes' mode in the sidebar to see the collection breakdown.")

elif mode == "Taxes":
    st.markdown(f"<div style='text-align: center;'><h1 style='margin-bottom:0;'>Tax Collection Report</h1><h2 style='color:#FFD700;'>{active_owner}</h2></div>", unsafe_allow_html=True)
    
    if conf['type'] == "Draft":
        st.warning("⚠️ This account is set to 'Draft'. In this configuration, the owner is typically responsible for direct tax remittance. Below is the income summary for your records.")
    
    # TAX CALCULATION LOGIC (Specific for Payout Accounts)
    # Hospitality: 6%, State: 4%, City: 2% (Example rates)
    tax_rows = []
    total_tax_collected = 0
    
    for addr in df_all["Addr"].unique():
        p_df = df_all[df_all["Addr"] == addr]
        p_name = p_df["Prop"].iloc[0]
        p_city = p_df["City"].iloc[0]
        
        # Calculate totals for this property
        total_fare = p_df["Fare"].sum()
        
        # Breakdown
        state_tax = round(total_fare * 0.04, 2)
        hospitality_tax = round(total_fare * 0.06, 2)
        city_tax = round(total_fare * 0.02, 2)
        p_total_tax = state_tax + hospitality_tax + city_tax
        
        tax_rows.append({
            "Property": p_name,
            "Address": addr,
            "City": p_city,
            "Total Payout Received": f"${total_fare:,.2f}",
            "State Tax (4%)": state_tax,
            "Hospitality Tax (6%)": hospitality_tax,
            "City Tax (2%)": city_tax,
            "Total Collected": p_total_tax
        })
        total_tax_collected += p_total_tax

    # Grand Total Tax Metric
    st.metric("Total Taxes Collected (To be Remitted)", f"${total_tax_collected:,.2f}")
    
    # Display Table
    t_cfg = {
        "State Tax (4%)": st.column_config.NumberColumn(format="$%.2f"),
        "Hospitality Tax (6%)": st.column_config.NumberColumn(format="$%.2f"),
        "City Tax (2%)": st.column_config.NumberColumn(format="$%.2f"),
        "Total Collected": st.column_config.NumberColumn(format="$%.2f")
    }
    
    st.dataframe(pd.DataFrame(tax_rows), use_container_width=True, hide_index=True, column_config=t_cfg)
    
    st.divider()
    st.markdown("### 📋 Remittance Instructions")
    st.write(f"The total amount of **${total_tax_collected:,.2f}** was collected from {active_owner}'s payouts and is held for tax remittance to the respective jurisdictions.")
