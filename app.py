import streamlit as st
import pandas as pd
from datetime import date, timedelta

# --- 1. SETUP ---
st.set_page_config(page_title="PMC Master Suite", layout="wide")

if 'owner_db' not in st.session_state:
    st.session_state.owner_db = {
        "ERAN": {"pct": 12.0, "type": "Draft"},
        "SMITH": {"pct": 15.0, "type": "Payout"},
    }

# Mock Tax Rates (Example: Florida/Miami style breakdown)
TAX_RATES = {
    "State": 0.06,   # 6%
    "County": 0.01,  # 1%
    "City": 0.03,    # 3%
    "Local/TDT": 0.03 # 3% (Tourist Development Tax)
}

def get_mimic_data(owner):
    if owner == "ERAN":
        return [
            {"ID": "RES-101", "Prop": "Sunset Villa", "Addr": "742 Evergreen Terrace", "In": date(2026, 2, 1), "Out": date(2026, 2, 5), "Fare": 1200.0, "Cln": 150.0, "Exp": 25.0},
            {"ID": "RES-201", "Prop": "Beach House", "Addr": "123 Ocean Drive", "In": date(2026, 2, 5), "Out": date(2026, 2, 8), "Fare": 2500.0, "Cln": 200.0, "Exp": 150.0}
        ]
    return [{"ID": "RES-301", "Prop": "Mountain Lodge", "Addr": "55 Peak Road", "In": date(2026, 2, 1), "Out": date(2026, 2, 5), "Fare": 1500.0, "Cln": 100.0, "Exp": 10.0}]

# --- 2. SIDEBAR ---
with st.sidebar:
    st.header("📂 Navigation")
    mode = st.radio("Select Report Type", ["Owner Statements", "Tax Report", "PMC REPORT"], index=0)
    
    st.divider()
    active_owner = st.selectbox("Switch Active Owner", sorted(st.session_state.owner_db.keys()))
    conf = st.session_state.owner_db[active_owner]
    
    st.divider()
    st.header("📅 Select Period")
    # Date logic for context
    today, start_date, end_date = date.today(), date(2026, 2, 1), date(2026, 2, 28)

# --- 3. CALCULATION ENGINE ---
owner_data = get_mimic_data(active_owner)
total_accommodation = sum(r['Fare'] for r in owner_data)

tax_table_data = []
total_tax_due = 0

for jurisdiction, rate in TAX_RATES.items():
    amount = total_accommodation * rate
    total_tax_due += amount
    tax_table_data.append({
        "Jurisdiction": jurisdiction,
        "Rate": f"{rate*100:.1f}%",
        "Total Collected": amount,
        "Pay To": f"Department of Revenue ({jurisdiction} Office)",
        "Frequency": "Monthly"
    })

# --- 4. MAIN CONTENT ---
if mode == "Tax Report":
    st.markdown(f"<div style='text-align: center;'><h1>Tax Compliance Report</h1><h2 style='color:#FFD700;'>{active_owner}</h2><p>Period: {start_date} to {end_date}</p></div>", unsafe_allow_html=True)
    
    # Tax Summary Metrics
    t1, t2, t3 = st.columns(3)
    t1.metric("Total Accommodation", f"${total_accommodation:,.2f}")
    t2.metric("Combined Tax Rate", f"{sum(TAX_RATES.values())*100:.1f}%")
    t3.metric("Total Tax Due", f"${total_tax_due:,.2f}", delta="Ready for Filing", delta_color="off")
    
    st.divider()
    
    st.subheader("📌 Tax Breakdown & Payment Instructions")
    st.dataframe(pd.DataFrame(tax_table_data), use_container_width=True, hide_index=True, column_config={
        "Total Collected": st.column_config.NumberColumn(format="$%.2f"),
        "Pay To": st.column_config.TextColumn("Payment Entity")
    })
    
    st.info(f"💡 This report is based on the **${total_accommodation:,.2f}** in accommodation revenue reported for {active_owner} during this period.")

elif mode == "Owner Statements":
    st.title("Owner Statement")
    # (Previous Owner Statement Logic...)

elif mode == "PMC REPORT":
    st.title("PMC Internal Control")
    # (Previous PMC Report Logic...)
