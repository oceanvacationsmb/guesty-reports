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

def get_data():
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
    st.header("⚙️ Settings")
    with st.expander("Manage Owners", expanded=True):
        edit_list = list(st.session_state.owner_db.keys())
        target = st.selectbox("Edit/Delete", ["+ Add New"] + edit_list)
        
        # Logic to pull existing data or blank for new
        current = st.session_state.owner_db.get(target, {"pct": 12.0, "type": "Draft"})
        
        new_name = st.text_input("Owner Name", value="" if target == "+ Add New" else target).upper().strip()
        new_pct = st.number_input("Commission %", 0.0, 100.0, float(current["pct"]))
        new_type = st.selectbox("Settlement Style", ["Draft", "Payout"], index=0 if current["type"] == "Draft" else 1)
        
        c_save, c_del = st.columns(2)
        if c_save.button("💾 Save Changes"):
            if new_name:
                st.session_state.owner_db[new_name] = {"pct": new_pct, "type": new_type}
                if target != "+ Add New" and target != new_name:
                    del st.session_state.owner_db[target]
                st.rerun()
        
        if target != "+ Add New" and c_del.button("🗑️ Delete", type="primary"):
            del st.session_state.owner_db[target]
            st.rerun()

    with st.expander("🔌 API Connection"):
        st.text_input("Client ID", value="0oaszuo22iOg...")
        st.text_input("Client Secret", type="password")

# --- 3. MAIN CONTENT ---
if mode == "Dashboard":
    rows = []
    vals = {"gross": 0, "comm": 0, "exp": 0, "cln": 0, "net": 0}
    
    for r in get_data():
        f, c, e = r['Fare'], r['Cleaning'], r['Exp']
        cm = round(f * (conf['pct'] / 100), 2)
        
        # Formula Logic
        if conf['type'] == "Draft":
            rev = f + c
            net = f - c - cm - e
        else:
            rev = f
            net = f - cm - e
        
        vals["gross"]+=rev; vals["comm"]+=cm; vals["cln"]+=c; vals["exp"]+=e; vals["net"]+=net
        
        # Conditional Invoice Link
        link = f"https://app.guesty.com/reservations/{r['ID']}" if e > 0 else None
        
        rows.append({
            "ID": r['ID'], "Check-in/Out": f"{r['In'].strftime('%m/%d')}", 
            "Gross Revenue": rev, "Accommodation": f, "Cleaning": c, 
            "Commission": cm, "Expenses": e, "Invoice": link, "Net Payout": round(net, 2)
        })

    st.markdown(f"<div style='text-align: center;'><h1 style='margin-bottom:0'>PMC Statement</h1><h2 style='color:#FFD700'>Owner: {active_owner}</h2></div>", unsafe_allow_html=True)

    # Metric Columns
    if conf['type'] == "Draft":
        cols = st.columns(5)
        cols[0].metric("Gross Revenue", f"${vals['gross']:,.2f}")
        cols[1].metric(f"Comm ({conf['pct']}%)", f"${vals['comm']:,.2f}")
        cols[2].metric("Cleaning Total", f"${vals['cln']:,.2f}")
        cols[3].metric("Total Expenses", f"${vals['exp']:,.2f}")
        cols[4].metric("DRAFT AMOUNT", f"${(vals['comm'] + vals['cln'] + vals['exp']):,.2f}")
        order = ["ID", "Check-in/Out", "Gross Revenue", "Accommodation", "Cleaning", "Commission", "Expenses", "Invoice", "Net Payout"]
    else:
        cols = st.columns(4)
        cols[0].metric("Gross Revenue", f"${vals['gross']:,.2f}")
        cols[1].metric(f"Comm ({conf['pct']}%)", f"${vals['comm']:,.2f}")
        cols[2].metric("Total Expenses", f"${vals['exp']:,.2f}")
        cols[3].metric("NET PAYOUT", f"${vals['net']:,.2f}")
        order = ["ID", "Check-in/Out", "Accommodation", "Commission", "Expenses", "Invoice", "Net Payout"]

    st.divider()
    
    t_config = {col: st.column_config.NumberColumn(format="$%.2f") for col in ["Net Payout", "Accommodation", "Cleaning", "Commission", "Expenses", "Gross Revenue"]}
    t_config["Invoice"] = st.column_config.LinkColumn("Invoice", display_text="🔗 View")
    
    st.dataframe(pd.DataFrame(rows), use_container_width=True, column_order=order, hide_index=True, column_config=t_config)

else:
    st.header("⚖️ Tax Compliance Report")
    # Tax Mimic Logic
    st.info(f"Showing location breakdown for {active_owner}")
    tax_df = pd.DataFrame([{"State": "FL", "City": "Miami", "County": "Miami-Dade", "Property": "Ocean View", "Address": "123 Coast Hwy", "Income": 5000.00}])
    st.dataframe(tax_df, use_container_width=True, hide_index=True)
