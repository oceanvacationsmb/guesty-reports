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

# Mimic Data Source
def get_mimic_data():
    return [
        {"ID": "RES-55421", "In": date(2026, 2, 1), "Out": date(2026, 2, 5), "Fare": 1200.0, "Cleaning": 150.0, "Exp": 25.0},
        {"ID": "RES-55429", "In": date(2026, 2, 10), "Out": date(2026, 2, 14), "Fare": 850.50, "Cleaning": 100.0, "Exp": 0.0},
        {"ID": "RES-55435", "In": date(2026, 2, 18), "Out": date(2026, 2, 22), "Fare": 2100.75, "Cleaning": 180.0, "Exp": 45.10}
    ]

# --- 2. SIDEBAR ---
with st.sidebar:
    st.header("📂 Navigation")
    mode = st.radio("View", ["Dashboard", "Taxes"], horizontal=True)
    
    st.divider()
    st.header("📊 Filter View")
    active_owner = st.selectbox("Switch Active Owner", sorted(st.session_state.owner_db.keys()))
    conf = st.session_state.owner_db[active_owner]
    
    st.divider()
    st.header("📅 Select Period")
    report_type = st.selectbox("Quick Select", ["By Month", "Full Year", "Year to Date (YTD)", "Date Range"])
    
    today = date.today()
    if report_type == "By Month":
        c1, c2 = st.columns(2)
        sel_year = c1.selectbox("Year", [2026, 2025, 2024], index=0)
        month_names = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
        sel_month = c2.selectbox("Month", month_names, index=today.month-1)
        start_date, end_date = date(sel_year, month_names.index(sel_month) + 1, 1), date(sel_year, month_names.index(sel_month) + 1, 28)
    elif report_type == "Full Year":
        sel_year = st.selectbox("Select Year", [2026, 2025, 2024], index=0)
        start_date, end_date = date(sel_year, 1, 1), date(sel_year, 12, 31)
    elif report_type == "Year to Date (YTD)":
        start_date, end_date = date(today.year, 1, 1), today
    else:
        start_date = st.date_input("Start Date", date(today.year, today.month, 1))
        end_date = st.date_input("End Date", today)

    st.divider()
    with st.expander("👤 Manage Owners"):
        target = st.selectbox("Edit/Delete", ["+ Add New"] + list(st.session_state.owner_db.keys()))
        curr = st.session_state.owner_db.get(target, {"pct": 12.0, "type": "Draft"})
        n_name = st.text_input("Name", value="" if target == "+ Add New" else target).upper().strip()
        n_pct = st.number_input("Comm %", 0.0, 100.0, float(curr["pct"]))
        n_type = st.selectbox("Style", ["Draft", "Payout"], index=0 if curr["type"] == "Draft" else 1)
        
        cs1, cs2 = st.columns(2)
        if cs1.button("💾 Save"):
            if n_name:
                st.session_state.owner_db[n_name] = {"pct": n_pct, "type": n_type}
                if target != "+ Add New" and target != n_name: del st.session_state.owner_db[target]
                st.rerun()
        if target != "+ Add New" and cs2.button("🗑️ Delete", type="primary"):
            del st.session_state.owner_db[target]; st.rerun()

    with st.expander("🔌 API"):
        st.text_input("Client ID", value="0oaszuo22iOg...")
        st.text_input("Client Secret", type="password")

# --- 3. REPORT DISPLAY ---
if mode == "Dashboard":
    rows, v = [], {"gross": 0, "comm": 0, "exp": 0, "cln": 0, "net": 0}
    
    for r in get_mimic_data():
        f, c, e = r['Fare'], r['Cleaning'], r['Exp']
        cm = round(f * (conf['pct'] / 100), 2)
        rev = f + c if conf['type'] == "Draft" else f
        net = f - c - cm - e if conf['type'] == "Draft" else f - cm - e
        
        v["gross"]+=rev; v["comm"]+=cm; v["cln"]+=c; v["exp"]+=e; v["net"]+=net
        link = f"https://app.guesty.com/reservations/{r['ID']}" if e > 0 else None
        
        rows.append({
            "ID": r['ID'], "Check-in/Out": f"{r['In'].strftime('%m/%d')}", 
            "Gross Revenue": rev, "Accommodation": f, "Cleaning": c, 
            "Commission": cm, "Expenses": e, "Invoice": link, "Net Payout": round(net, 2)
        })

    st.markdown(f"<div style='text-align: center;'><h1 style='margin-bottom:0'>PMC Statement</h1><h2 style='color:#FFD700'>Owner: {active_owner}</h2><p>{start_date.strftime('%B %Y')}</p></div><br>", unsafe_allow_html=True)

    # Metrics
    if conf['type'] == "Draft":
        cols = st.columns(5)
        cols[0].metric("Gross Revenue", f"${v['gross']:,.2f}")
        cols[1].metric(f"Comm ({conf['pct']}%)", f"${v['comm']:,.2f}")
        cols[2].metric("Cleaning", f"${v['cln']:,.2f}")
        cols[3].metric("Expenses", f"${v['exp']:,.2f}")
        cols[4].metric("DRAFT AMOUNT", f"${(v['comm'] + v['cln'] + v['exp']):,.2f}")
        order = ["ID", "Check-in/Out", "Gross Revenue", "Accommodation", "Cleaning", "Commission", "Expenses", "Invoice", "Net Payout"]
    else:
        cols = st.columns(4)
        cols[0].metric("Gross Revenue", f"${v['gross']:,.2f}")
        cols[1].metric(f"Comm ({conf['pct']}%)", f"${v['comm']:,.2f}")
        cols[2].metric("Expenses", f"${v['exp']:,.2f}")
        cols[3].metric("NET PAYOUT", f"${v['net']:,.2f}")
        order = ["ID", "Check-in/Out", "Accommodation", "Commission", "Expenses", "Invoice", "Net Payout"]

    st.divider()
    t_cfg = {col: st.column_config.NumberColumn(format="$%.2f") for col in ["Net Payout", "Accommodation", "Cleaning", "Commission", "Expenses", "Gross Revenue"]}
    t_cfg["Invoice"] = st.column_config.LinkColumn("Invoice", display_text="🔗 View")
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True, column_config=t_cfg, column_order=order)

else:
    st.header("⚖️ Tax Compliance Report")
    st.info(f"Location breakdown for {active_owner}")
    tax_df = pd.DataFrame([{"State": "FL", "City": "Miami", "County": "Miami-Dade", "Property": "Ocean View", "Address": "123 Coast Hwy", "Income": 5000.00}])
    st.dataframe(tax_df, use_container_width=True, hide_index=True)
