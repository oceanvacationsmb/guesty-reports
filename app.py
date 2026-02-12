import streamlit as st
import pandas as pd
from datetime import date, datetime

# --- 1. SETUP & PERSISTENCE ---
st.set_page_config(page_title="PMC Statement", layout="wide")

if 'owner_db' not in st.session_state:
    st.session_state.owner_db = {
        "ERAN": {"pct": 12.0, "type": "Draft"},
        "SMITH": {"pct": 15.0, "type": "Payout"},
    }

def get_data():
    return [
        {"ID": "RES-55421", "In": date(2026, 2, 1), "Out": date(2026, 2, 5), "Fare": 1200.0, "Cleaning": 150.0, "Exp": 25.0},
        {"ID": "RES-55429", "In": date(2026, 2, 10), "Out": date(2026, 2, 14), "Fare": 850.50, "Cleaning": 100.0, "Exp": 0.0},
    ]

# --- 2. SIDEBAR ---
with st.sidebar:
    st.header("📂 Navigation")
    mode = st.radio("View", ["Dashboard", "Taxes"], horizontal=True)
    
    st.divider()
    st.header("📊 Filter View")
    active_owner = st.selectbox("Switch Active Owner", sorted(st.session_state.owner_db.keys()))
    conf = st.session_state.owner_db[active_owner]
    
    # --- DATE PERIOD SECTION (RESTORED) ---
    st.divider()
    st.header("📅 Select Period")
    report_type = st.selectbox("Quick Select", ["By Month", "Date Range", "Year to Date (YTD)", "Full Year"])
    
    today = date.today()
    if report_type == "By Month":
        sel_year = st.selectbox("Year", [2026, 2025, 2024], index=0)
        month_names = ["January", "February", "March", "April", "May", "June", 
                       "July", "August", "September", "October", "November", "December"]
        sel_month = st.selectbox("Month", month_names, index=today.month-1)
        start_date = date(sel_year, month_names.index(sel_month) + 1, 1)
        end_date = date(sel_year, month_names.index(sel_month) + 1, 28) # Approximation
    elif report_type == "Date Range":
        start_date = st.date_input("Start Date", date(today.year, today.month, 1))
        end_date = st.date_input("End Date", today)
    elif report_type == "Year to Date (YTD)":
        start_date, end_date = date(today.year, 1, 1), today
    else: # Full Year
        start_date, end_date = date(today.year, 1, 1), date(today.year, 12, 31)

    st.divider()
    st.header("⚙️ Settings")
    
    # OWNER MANAGEMENT
    with st.expander("👤 Manage Owners"):
        edit_list = list(st.session_state.owner_db.keys())
        target = st.selectbox("Select Action", ["+ Add New"] + edit_list)
        current = st.session_state.owner_db.get(target, {"pct": 12.0, "type": "Draft"})
        
        new_name = st.text_input("Owner Name", value="" if target == "+ Add New" else target).upper().strip()
        new_pct = st.number_input("Commission %", 0.0, 100.0, float(current["pct"]))
        new_type = st.selectbox("Settlement Style", ["Draft", "Payout"], index=0 if current["type"] == "Draft" else 1)
        
        c1, c2 = st.columns(2)
        if c1.button("💾 Save Owner"):
            if new_name:
                st.session_state.owner_db[new_name] = {"pct": new_pct, "type": new_type}
                if target != "+ Add New" and target != new_name:
                    del st.session_state.owner_db[target]
                st.rerun()
        if target != "+ Add New" and c2.button("🗑️ Delete", type="primary"):
            del st.session_state.owner_db[target]
            st.rerun()

    # API CONNECTION
    with st.expander("🔌 API Connection"):
        st.text_input("Client ID", value="0oaszuo22iOg...")
        st.text_input("Client Secret", type="password")
        if st.button("🔄 Save & Validate API"):
            st.success("Credentials Locked!")

# --- 3. MAIN CONTENT ---
if mode == "Dashboard":
    rows = []
    vals = {"gross": 0, "comm": 0, "exp": 0, "cln": 0, "net": 0}
    
    for r in get_data():
        f, c, e = r['Fare'], r['Cleaning'], r['Exp']
        cm = round(f * (conf['pct'] / 100), 2)
        rev = f + c if conf['type'] == "Draft" else f
        net = f - c - cm - e if conf['type'] == "Draft" else f - cm - e
        
        vals["gross"]+=rev; vals["comm"]+=cm; vals["cln"]+=c; vals["exp"]+=e; vals["net"]+=net
        link = f"https://app.guesty.com/reservations/{r['ID']}" if e > 0 else None
        
        rows.append({"ID": r['ID'], "Check-in/Out": f"{r['In'].strftime('%m/%d')}", "Gross Revenue": rev, "Accommodation": f, "Cleaning": c, "Commission": cm, "Expenses": e, "Invoice": link, "Net Payout": round(net, 2)})

    st.markdown(f"<div style='text-align: center;'><h1 style='margin-bottom:0'>PMC Statement</h1><h2 style='color:#FFD700'>Owner: {active_owner}</h2></div><br>", unsafe_allow_html=True)

    if conf['type'] == "Draft":
        cols = st.columns(5)
        cols[0].metric("Gross Revenue", f"${vals['gross']:,.2f}")
        cols[1].metric(f"Comm ({conf['pct']}%)", f"${vals['comm']:,.2f}")
        cols[2].metric("Cleaning Total", f"${vals['cln']:,.2f}")
        cols[3].metric("Total Expenses", f"${vals['exp']:,.2f}")
        cols[4].metric("DRAFT AMOUNT", f"${(vals['comm'] + vals['cln'] + vals['exp']):,.2f}")
    else:
        cols = st.columns(4)
        cols[0].metric("Gross Revenue", f"${vals['gross']:,.2f}")
        cols[1].metric(f"Comm ({conf['pct']}%)", f"${vals['comm']:,.2f}")
        cols[2].metric("Total Expenses", f"${vals['exp']:,.2f}")
        cols[3].metric("NET PAYOUT", f"${vals['net']:,.2f}")

    st.divider()
    t_config = {col: st.column_config.NumberColumn(format="$%.2f") for col in ["Net Payout", "Accommodation", "Cleaning", "Commission", "Expenses", "Gross Revenue"]}
    t_config["Invoice"] = st.column_config.LinkColumn("Invoice", display_text="🔗 View")
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True, column_config=t_config)

else:
    st.header("⚖️ Tax Compliance Report")
    tax_df = pd.DataFrame([{"State": "FL", "City": "Miami", "County": "Miami-Dade", "Property": "Ocean View", "Address": "123 Coast Hwy", "Income": 5000.00}])
    st.dataframe(tax_df, use_container_width=True, hide_index=True)
