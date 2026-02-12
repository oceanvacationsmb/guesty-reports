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

# Logic to simulate data fetching (this will be replaced by your real API call later)
@st.cache_data
def fetch_guesty_data(c_id, c_secret, start, end):
    # This mimics the process of reaching out to Guesty
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
    
    st.divider()
    st.header("📅 Select Period")
    report_type = st.selectbox("Quick Select", ["By Month", "Full Year", "Year to Date (YTD)", "Date Range"])
    
    # Date calculations
    today = date.today()
    if report_type == "By Month":
        c1, c2 = st.columns(2)
        sel_year = c1.selectbox("Year", [2026, 2025, 2024], index=0)
        month_names = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
        sel_month = c2.selectbox("Month", month_names, index=today.month-1)
        start_date, end_date = date(sel_year, month_names.index(sel_month) + 1, 1), date(sel_year, month_names.index(sel_month) + 1, 28)
    else:
        start_date, end_date = date(today.year, 1, 1), today

    st.divider()
    st.header("⚙️ Settings")
    
    with st.expander("👤 Manage Owners"):
        target = st.selectbox("Edit/Delete", ["+ Add New"] + list(st.session_state.owner_db.keys()))
        curr = st.session_state.owner_db.get(target, {"pct": 12.0, "type": "Draft"})
        n_name = st.text_input("Name", value="" if target == "+ Add New" else target).upper().strip()
        n_pct = st.number_input("Comm %", 0.0, 100.0, float(curr["pct"]))
        n_type = st.selectbox("Style", ["Draft", "Payout"], index=0 if curr["type"] == "Draft" else 1)
        
        cs1, cs2 = st.columns(2)
        if cs1.button("💾 Save Owner"):
            if n_name:
                st.session_state.owner_db[n_name] = {"pct": n_pct, "type": n_type}
                if target != "+ Add New" and target != n_name: del st.session_state.owner_db[target]
                st.rerun()
        if target != "+ Add New" and cs2.button("🗑️ Delete", type="primary"):
            del st.session_state.owner_db[target]; st.rerun()

    with st.expander("🔌 API Connection", expanded=True):
        client_id = st.text_input("Client ID", value="0oaszuo22iOg...")
        client_secret = st.text_input("Client Secret", type="password")
        
        # THE SAVE AND PROCESS BUTTON
        if st.button("💾 Save & Fetch Data", type="primary"):
            st.cache_data.clear() # Force a fresh run
            st.success("API Credentials Saved. Processing data...")
            # In a real scenario, this would trigger the requests.post(token_url)
            st.rerun()

# --- 3. REPORT RENDERING ---
# This part handles the visual display of the data
if mode == "Dashboard":
    # Get the data (Freshly triggered by the API button)
    source_data = fetch_guesty_data(client_id, client_secret, start_date, end_date)
    
    rows, v = [], {"gross": 0, "comm": 0, "exp": 0, "cln": 0, "net": 0}
    for r in source_data:
        f, c, e = r['Fare'], r['Cleaning'], r['Exp']
        cm = round(f * (conf['pct'] / 100), 2)
        rev = f + c if conf['type'] == "Draft" else f
        net = f - c - cm - e if conf['type'] == "Draft" else f - cm - e
        v["gross"]+=rev; v["comm"]+=cm; v["cln"]+=c; v["exp"]+=e; v["net"]+=net
        link = f"https://app.guesty.com/reservations/{r['ID']}" if e > 0 else None
        rows.append({"ID": r['ID'], "Check-in/Out": f"{r['In'].strftime('%m/%d')}", "Gross Revenue": rev, "Accommodation": f, "Cleaning": c, "Commission": cm, "Expenses": e, "Invoice": link, "Net Payout": round(net, 2)})

    st.markdown(f"<div style='text-align: center;'><h1 style='margin-bottom:0;'>PMC Statement</h1><h2 style='color:#FFD700;'>Owner: {active_owner}</h2><p>Range: {start_date} to {end_date}</p></div><br>", unsafe_allow_html=True)

    # Metric Cards
    m_cols = st.columns(5 if conf['type'] == "Draft" else 4)
    m_cols[0].metric("Gross Revenue", f"${v['gross']:,.2f}")
    m_cols[1].metric(f"Comm ({conf['pct']}%)", f"${v['comm']:,.2f}")
    if conf['type'] == "Draft":
        m_cols[2].metric("Cleaning", f"${v['cln']:,.2f}")
        m_cols[3].metric("Expenses", f"${v['exp']:,.2f}")
        m_cols[4].metric("DRAFT AMOUNT", f"${(v['comm'] + v['cln'] + v['exp']):,.2f}")
        order = ["ID", "Check-in/Out", "Gross Revenue", "Accommodation", "Cleaning", "Commission", "Expenses", "Invoice", "Net Payout"]
    else:
        m_cols[2].metric("Expenses", f"${v['exp']:,.2f}")
        m_cols[3].metric("NET PAYOUT", f"${v['net']:,.2f}")
        order = ["ID", "Check-in/Out", "Accommodation", "Commission", "Expenses", "Invoice", "Net Payout"]

    st.divider()
    t_cfg = {col: st.column_config.NumberColumn(format="$%.2f") for col in ["Net Payout", "Accommodation", "Cleaning", "Commission", "Expenses", "Gross Revenue"]}
    t_cfg["Invoice"] = st.column_config.LinkColumn("Invoice", display_text="🔗 View")
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True, column_config=t_cfg, column_order=order)

else:
    # Tax view remains stable
    st.header("⚖️ Tax Compliance Report")
    tax_df = pd.DataFrame([{"State": "FL", "City": "Miami", "County": "Miami-Dade", "Property": "Ocean View", "Address": "123 Coast Hwy", "Income": 5000.00}])
    st.dataframe(tax_df, use_container_width=True, hide_index=True)
