import streamlit as st
import pandas as pd
from datetime import date, timedelta

# --- 1. SETUP & PERSISTENCE ---
st.set_page_config(page_title="PMC Master Suite", layout="wide")

# Persistent Owner Database
if 'owner_db' not in st.session_state:
    st.session_state.owner_db = {
        "ERAN": {"pct": 12.0, "type": "Draft"},
        "SMITH": {"pct": 15.0, "type": "Payout"},
    }

def get_mimic_data(owner):
    if owner == "ERAN":
        return [
            {"ID": "RES-101", "Prop": "Sunset Villa", "Addr": "742 Evergreen Terrace", "In": date(2026, 2, 1), "Out": date(2026, 2, 5), "Fare": 1200.0, "Cln": 150.0, "Exp": 25.0},
            {"ID": "RES-201", "Prop": "Beach House", "Addr": "123 Ocean Drive", "In": date(2026, 2, 5), "Out": date(2026, 2, 8), "Fare": 2500.0, "Cln": 200.0, "Exp": 150.0}
        ]
    return [{"ID": "RES-301", "Prop": "Mountain Lodge", "Addr": "55 Peak Road", "In": date(2026, 2, 1), "Out": date(2026, 2, 5), "Fare": 1500.0, "Cln": 100.0, "Exp": 10.0}]

# --- 2. SIDEBAR (PERMANENT ELEMENTS) ---
with st.sidebar:
    st.header("📂 Navigation")
    mode = st.radio("Select Report Type", ["Owner Statements", "Tax Report", "PMC REPORT"], index=0)
    
    st.divider()
    st.header("👤 Active Owner")
    active_owner = st.selectbox("Switch Active Owner", sorted(st.session_state.owner_db.keys()))
    conf = st.session_state.owner_db[active_owner]
    
    st.divider()
    st.header("📅 Select Period")
    report_type = st.selectbox("Context", ["By Month", "Full Year", "YTD", "Between Dates"], index=0)
    
    today = date.today()
    if report_type == "By Month":
        c1, c2 = st.columns(2)
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        sel_month = c1.selectbox("Month", months, index=today.month-1)
        sel_year = c2.selectbox("Year", [2026, 2025], index=0)
        start_date = date(sel_year, months.index(sel_month)+1, 1)
        end_date = (start_date + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    elif report_type == "Between Dates":
        c1, c2 = st.columns(2)
        start_date = c1.date_input("Start Date", today - timedelta(days=30))
        end_date = c2.date_input("End Date", today)
    elif report_type == "Full Year":
        sel_year = st.selectbox("Year", [2026, 2025], index=0)
        start_date, end_date = date(sel_year, 1, 1), date(sel_year, 12, 31)
    else: # YTD
        start_date, end_date = date(today.year, 1, 1), today

    st.divider()
    st.header("⚙️ Settings")
    with st.expander("👤 Owner Management"):
        target = st.selectbox("Edit/Delete", ["+ Add New"] + list(st.session_state.owner_db.keys()))
        curr = st.session_state.owner_db.get(target, {"pct": 12.0, "type": "Draft"})
        n_name = st.text_input("Name", value="" if target == "+ Add New" else target).upper().strip()
        n_pct = st.number_input("Comm %", 0.0, 100.0, float(curr["pct"]))
        n_style = st.selectbox("Style", ["Draft", "Payout"], index=0 if curr["type"] == "Draft" else 1)
        
        b1, b2 = st.columns(2)
        if b1.button("💾 Save Settings"):
            st.session_state.owner_db[n_name] = {"pct": n_pct, "type": n_style}
            if target != "+ Add New" and target != n_name: del st.session_state.owner_db[target]
            st.rerun()
        if target != "+ Add New" and b2.button("🗑️ Delete", type="primary"):
            del st.session_state.owner_db[target]; st.rerun()

    with st.expander("🔌 API Connection", expanded=True):
        st.text_input("Client ID", value="0oaszuo22iOg...")
        st.text_input("Client Secret", type="password")
        if st.button("🔄 Save & Run", type="primary", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

# --- 3. GLOBAL LOGIC ---
all_owners_data = []
total_ov2 = 0

for name, settings in st.session_state.owner_db.items():
    owner_data = get_mimic_data(name)
    o_comm, o_cln, o_exp, o_fare = 0, 0, 0, 0
    for r in owner_data:
        f, c, e = r['Fare'], r['Cln'], r['Exp']
        o_comm += round(f * (settings['pct'] / 100), 2)
        o_cln += c; o_exp += e; o_fare += f
    
    net_rev = o_fare - (o_cln if settings['type'] == "Draft" else 0) - o_comm - o_exp
    draft_val = (o_comm + o_cln + o_exp) if settings['type'] == "Draft" else 0
    ach_val = net_rev if settings['type'] == "Payout" else 0
    
    all_owners_data.append({
        "Owner": name, "Type": settings['type'], 
        "Draft Amount": draft_val, "ACH to Owner": ach_val, 
        "Comm (OV2)": o_comm, "Net Revenue": net_rev,
        "Cleaning": o_cln, "Expenses": o_exp, "Gross Payout": o_fare + (o_cln if settings['type']=="Draft" else 0)
    })
    total_ov2 += o_comm

# --- 4. MAIN CONTENT ---
if mode == "PMC REPORT":
    st.markdown(f"<div style='text-align: center;'><h1>PMC Internal Report</h1><p>{start_date} to {end_date}</p></div>", unsafe_allow_html=True)
    m1, m2 = st.columns(2)
    m1.metric("Total OV2 Commission", f"${total_ov2:,.2f}")
    m2.metric("TRANSFER TO OV2", f"${total_ov2:,.2f}", delta="Action Ready")
    st.divider()
    st.dataframe(pd.DataFrame(all_owners_data)[["Owner", "Type", "Draft Amount", "ACH to Owner", "Comm (OV2)"]], use_container_width=True, hide_index=True)

elif mode == "Owner Statements":
    st.markdown(f"<div style='text-align: center;'><h1>Owner Statement</h1><h2 style='color:#FFD700;'>{active_owner}</h2><p>{start_date} to {end_date}</p></div>", unsafe_allow_html=True)
    
    # Active Owner Summary
    summary = next(item for item in all_owners_data if item["Owner"] == active_owner)
    cols = st.columns(5)
    cols[0].metric("Gross Payout", f"${summary['Gross Payout']:,.2f}")
    cols[1].metric("Total Comm", f"${summary['Comm (OV2)']:,.2f}")
    cols[2].metric("Expenses", f"${summary['Expenses']:,.2f}")
    cols[3].metric("Net Revenue", f"${summary['Net Revenue']:,.2f}")
    
    if conf['type'] == "Draft":
        cols[4].metric("🏦 DRAFT FROM OWNER", f"${summary['Draft Amount']:,.2f}", delta_color="inverse")
    else:
        cols[4].metric("💸 ACH TO OWNER", f"${summary['ACH to Owner']:,.2f}")
    
    st.divider()
    # Detailed Property Tables (Logic remains same...)
    st.write("### Property Breakdown")
    st.dataframe(pd.DataFrame(get_mimic_data(active_owner)), use_container_width=True)

else: # Tax Report
    st.title("Tax Report")
    st.info("Tax jurisdiction breakdown active.")
