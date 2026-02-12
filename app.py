import streamlit as st
import pandas as pd
from datetime import date

# --- 1. SETUP & DATA ---
st.set_page_config(page_title="PMC Statement", layout="wide")

if 'owner_db' not in st.session_state:
    st.session_state.owner_db = {"ERAN": {"pct": 12.0, "type": "Draft"}, "SMITH": {"pct": 15.0, "type": "Payout"}}

def get_data():
    return [{"ID": "RES-55421", "In": date(2026, 2, 1), "Out": date(2026, 2, 5), "Fare": 1200.0, "Clean": 150.0, "Exp": 25.0},
            {"ID": "RES-55429", "In": date(2026, 2, 10), "Out": date(2026, 2, 14), "Fare": 850.50, "Clean": 100.0, "Exp": 0.0}]

# --- 2. SIDEBAR ---
with st.sidebar:
    st.header("📂 Navigation")
    mode = st.radio("View", ["Dashboard", "Taxes"], horizontal=True)
    st.divider()
    
    owner = st.selectbox("Owner", sorted(st.session_state.owner_db.keys()))
    conf = st.session_state.owner_db[owner]
    
    st.header("📅 Period")
    p_type = st.selectbox("Select", ["By Month", "YTD", "Full Year"])
    start_date = date(2026, 1, 1) # Simplified for now
    
    st.divider()
    with st.expander("⚙️ Manage Owners"):
        u_pct = st.number_input("Comm %", 0.0, 100.0, float(conf['pct']))
        u_type = st.selectbox("Style", ["Draft", "Payout"], index=0 if conf['type'] == "Draft" else 1)
        if st.button("💾 Save Settings"):
            st.session_state.owner_db[owner] = {"pct": u_pct, "type": u_type}
            st.rerun()

    with st.expander("🔌 API"):
        st.text_input("Client ID", value="0oaszuo22iOg...")
        st.text_input("Client Secret", type="password")

# --- 3. LOGIC & DISPLAY ---
if mode == "Taxes":
    st.header("⚖️ Tax Compliance Report")
    if conf['type'] != "Payout":
        st.warning("Taxes only available for Payout accounts.")
    else:
        tax_df = pd.DataFrame([{"State": "FL", "City": "Miami", "County": "Miami-Dade", "Address": "123 Coast Hwy", "Income": 5000.00}])
        st.dataframe(tax_df, use_container_width=True, hide_index=True)

else:
    # Calculations
    rows = []
    vals = {"gross": 0, "comm": 0, "exp": 0, "cln": 0, "net": 0}
    
    for r in get_data():
        f, c, e = r['Fare'], r['Clean'], r['Exp']
        cm = round(f * (conf['pct'] / 100), 2)
        rev = f + c if conf['type'] == "Draft" else f
        net = f - c - cm - e if conf['type'] == "Draft" else f - cm - e
        
        vals["gross"]+=rev; vals["comm"]+=cm; vals["cln"]+=c; vals["exp"]+=e; vals["net"]+=net
        rows.append({"ID": r['ID'], "Check-in/Out": f"{r['In'].strftime('%m/%d')}", "Gross Revenue": rev, "Accommodation": f, "Cleaning": c, "Commission": cm, "Expenses": e, "Net Payout": round(net, 2)})

    st.markdown(f"<div style='text-align: center;'><h1 style='margin-bottom:0'>PMC Statement</h1><h2 style='color:#FFD700'>Owner: {owner}</h2></div>", unsafe_allow_html=True)

    cols = st.columns(5 if conf['type'] == "Draft" else 4)
    cols[0].metric("Gross", f"${vals['gross']:,.2f}")
    cols[1].metric("Comm", f"${vals['comm']:,.2f}")
    if conf['type'] == "Draft":
        cols[2].metric("Cleaning", f"${vals['cln']:,.2f}")
        cols[3].metric("Expenses", f"${vals['exp']:,.2f}")
        cols[4].metric("DRAFT AMOUNT", f"${(vals['comm'] + vals['cln'] + vals['exp']):,.2f}")
        order = ["ID", "Check-in/Out", "Gross Revenue", "Accommodation", "Cleaning", "Commission", "Expenses", "Net Payout"]
    else:
        cols[2].metric("Expenses", f"${vals['exp']:,.2f}")
        cols[3].metric("NET PAYOUT", f"${vals['net']:,.2f}")
        order = ["ID", "Check-in/Out", "Accommodation", "Commission", "Expenses", "Net Payout"]

    st.divider()
    st.dataframe(pd.DataFrame(rows), use_container_width=True, column_order=order, hide_index=True, 
                 column_config={col: st.column_config.NumberColumn(format="$%.2f") for col in ["Net Payout", "Accommodation", "Cleaning", "Commission", "Expenses", "Gross Revenue"]})
