import streamlit as st
import pandas as pd
from datetime import date, timedelta

# --- 1. SETUP & PERSISTENCE ---
st.set_page_config(page_title="PMC Master Control", layout="wide")

if 'owner_db' not in st.session_state:
    st.session_state.owner_db = {
        "ERAN": {"pct": 12.0, "type": "Draft"},
        "SMITH": {"pct": 15.0, "type": "Payout"},
    }

def get_mimic_data(owner):
    if owner == "ERAN":
        return [
            {"ID": "RES-101", "Fare": 1200.0, "Cln": 150.0, "Exp": 25.0},
            {"ID": "RES-201", "Fare": 2500.0, "Cln": 200.0, "Exp": 150.0}
        ]
    return [{"ID": "RES-301", "Fare": 1500.0, "Cln": 100.0, "Exp": 10.0}]

# --- 2. SIDEBAR ---
with st.sidebar:
    st.header("📂 Navigation")
    mode = st.radio("Select Report Type", ["Owner Statements", "Tax Report", "PMC REPORT"], index=0)
    
    st.divider()
    active_owner = st.selectbox("Switch Owner", sorted(st.session_state.owner_db.keys()))
    conf = st.session_state.owner_db[active_owner]
    
    st.divider()
    report_type = st.selectbox("Context", ["By Month", "Full Year", "YTD", "Between Dates"])
    # ... (Date logic remains same as previous version)
    start_date, end_date = date(2026, 2, 1), date(2026, 2, 28)

    with st.expander("🔌 API", expanded=True):
        st.text_input("Client ID", value="0oaszuo22iOg...")
        if st.button("🔄 Save & Run", type="primary", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

# --- 3. GLOBAL PMC CALCULATION ---
# This runs regardless of view to populate the PMC Report
pmc_summary = []
total_ov2 = 0

for name, settings in st.session_state.owner_db.items():
    owner_data = get_mimic_data(name)
    o_comm, o_cln, o_exp, o_fare = 0, 0, 0, 0
    
    for r in owner_data:
        f, c, e = r['Fare'], r['Cln'], r['Exp']
        o_comm += round(f * (settings['pct'] / 100), 2)
        o_cln += c
        o_exp += e
        o_fare += f
    
    net_rev = o_fare - (o_cln if settings['type'] == "Draft" else 0) - o_comm - o_exp
    draft_val = (o_comm + o_cln + o_exp) if settings['type'] == "Draft" else 0
    ach_val = net_rev if settings['type'] == "Payout" else 0
    
    pmc_summary.append({
        "Owner": name,
        "Type": settings['type'],
        "Draft Amount": draft_val,
        "ACH to Owner": ach_val,
        "PMC Commission": o_comm
    })
    total_ov2 += o_comm

# --- 4. MAIN CONTENT ---

if mode == "PMC REPORT":
    st.markdown(f"<div style='text-align: center;'><h1>Internal PMC Control Report</h1><p>{start_date} to {end_date}</p></div>", unsafe_allow_html=True)
    
    # OVERALL PMC METRICS
    m1, m2 = st.columns(2)
    m1.metric("Total Management Fees", f"${total_ov2:,.2f}")
    m2.metric("TRANSFER TO OV2", f"${total_ov2:,.2f}", delta="Ready for Transfer", delta_color="normal")
    
    st.divider()
    
    # ACTION TABLE
    st.subheader("📋 Required Financial Actions")
    pmc_df = pd.DataFrame(pmc_summary)
    
    # Formatting the table for clarity
    st.dataframe(
        pmc_df, 
        use_container_width=True, 
        hide_index=True,
        column_config={
            "Draft Amount": st.column_config.NumberColumn(format="$%.2f", help="Money to pull from owner"),
            "ACH to Owner": st.column_config.NumberColumn(format="$%.2f", help="Money to send to owner"),
            "PMC Commission": st.column_config.NumberColumn(format="$%.2f", help="Internal Revenue")
        }
    )
    
    st.success(f"Total for Transfer to OV2: **${total_ov2:,.2f}**")

elif mode == "Owner Statements":
    # (Existing Owner Statement Logic)
    st.title(f"Statement: {active_owner}")
    # ... 

else: # Tax Report
    st.title("Tax Compliance Report")
    # ...
