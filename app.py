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

# Mimic data with multiple properties
def get_mimic_data(owner):
    if owner == "ERAN":
        return [
            {"ID": "RES-101", "Prop": "Sunset Villa", "Addr": "742 Evergreen Terrace", "In": date(2026, 2, 1), "Out": date(2026, 2, 5), "Fare": 1200.0, "Cln": 150.0, "Exp": 25.0},
            {"ID": "RES-102", "Prop": "Sunset Villa", "Addr": "742 Evergreen Terrace", "In": date(2026, 2, 12), "Out": date(2026, 2, 15), "Fare": 900.0, "Cln": 150.0, "Exp": 0.0},
            {"ID": "RES-201", "Prop": "Beach House", "Addr": "123 Ocean Drive", "In": date(2026, 2, 5), "Out": date(2026, 2, 8), "Fare": 2500.0, "Cln": 200.0, "Exp": 150.0}
        ]
    return [{"ID": "RES-301", "Prop": "Mountain Lodge", "Addr": "55 Peak Road", "In": date(2026, 2, 1), "Out": date(2026, 2, 5), "Fare": 1500.0, "Cln": 100.0, "Exp": 10.0}]

# --- 2. SIDEBAR ---
with st.sidebar:
    st.header("📂 Navigation")
    mode = st.radio("View Mode", ["Dashboard", "Taxes"], horizontal=True)
    
    st.divider()
    active_owner = st.selectbox("Active Owner", sorted(st.session_state.owner_db.keys()))
    conf = st.session_state.owner_db[active_owner]
    
    st.divider()
    st.header("📅 Period Selection")
    report_type = st.selectbox("Select Context", ["By Month", "Full Year", "YTD"])
    
    today = date.today()
    if report_type == "By Month":
        c1, c2 = st.columns(2)
        sel_year = c1.selectbox("Year", [2026, 2025], index=0)
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        sel_month = c2.selectbox("Month", months, index=today.month-1)
        start_date = date(sel_year, months.index(sel_month)+1, 1)
    else:
        sel_year = st.selectbox("Year", [2026, 2025], index=0)
        start_date = date(sel_year, 1, 1)

    st.divider()
    with st.expander("👤 Owner Settings"):
        target = st.selectbox("Action", ["+ Add New"] + list(st.session_state.owner_db.keys()))
        curr = st.session_state.owner_db.get(target, {"pct": 12.0, "type": "Draft"})
        n_name = st.text_input("Name", value="" if target == "+ Add New" else target).upper().strip()
        n_pct = st.number_input("Comm %", 0.0, 100.0, float(curr["pct"]))
        n_style = st.selectbox("Style", ["Draft", "Payout"], index=0 if curr["type"] == "Draft" else 1)
        
        b1, b2 = st.columns(2)
        if b1.button("💾 Save"):
            st.session_state.owner_db[n_name] = {"pct": n_pct, "type": n_style}
            if target != "+ Add New" and target != n_name: del st.session_state.owner_db[target]
            st.rerun()
        if target != "+ Add New" and b2.button("🗑️ Delete", type="primary"):
            del st.session_state.owner_db[target]; st.rerun()

    with st.expander("🔌 API"):
        st.text_input("Client ID", value="0oaszuo22iOg...")
        if st.button("🔄 Save & Run", type="primary"):
            st.cache_data.clear()
            st.rerun()

# --- 3. LOGIC ---
data = get_mimic_data(active_owner)
df_all = pd.DataFrame(data)

# Calculate Grand Totals
grand = {"gross": 0, "comm": 0, "exp": 0, "cln": 0, "net": 0}
for _, r in df_all.iterrows():
    f, c, e = r['Fare'], r['Cln'], r['Exp']
    cm = round(f * (conf['pct'] / 100), 2)
    rev = f + c if conf['type'] == "Draft" else f
    net = f - (c if conf['type'] == "Draft" else 0) - cm - e
    grand["gross"]+=rev; grand["comm"]+=cm; grand["cln"]+=c; grand["exp"]+=e; grand["net"]+=net

# --- 4. DISPLAY ---
if mode == "Dashboard":
    st.markdown(f"<div style='text-align: center;'><h1 style='margin-bottom:0;'>Master Statement</h1><h2 style='color:#FFD700;'>{active_owner}</h2></div>", unsafe_allow_html=True)

    # GRAND SUMMARY
    st.subheader("📊 Grand Total Summary")
    cols = st.columns(5 if conf['type'] == "Draft" else 4)
    cols[0].metric("Total Gross", f"${grand['gross']:,.2f}")
    cols[1].metric(f"Total Comm", f"${grand['comm']:,.2f}")
    if conf['type'] == "Draft":
        cols[2].metric("Total Cleaning", f"${grand['cln']:,.2f}")
        cols[3].metric("Total Expenses", f"${grand['exp']:,.2f}")
        cols[4].metric("DRAFT TOTAL", f"${(grand['comm'] + grand['cln'] + grand['exp']):,.2f}")
    else:
        cols[2].metric("Total Expenses", f"${grand['exp']:,.2f}")
        cols[3].metric("NET PAYOUT", f"${grand['net']:,.2f}")

    st.divider()

    # PROPERTY TABLES
    for addr in df_all["Addr"].unique():
        p_df = df_all[df_all["Addr"] == addr]
        st.markdown(f"#### 🏠 {p_df['Prop'].iloc[0]}")
        st.caption(f"📍 {addr}")
        
        rows = []
        for _, r in p_df.iterrows():
            f, c, e = r['Fare'], r['Cln'], r['Exp']
            cm = round(f * (conf['pct'] / 100), 2)
            net = f - (c if conf['type'] == "Draft" else 0) - cm - e
            rows.append({
                "ID": r['ID'], "Dates": f"{r['In'].strftime('%m/%d')}", "Fare": f, "Comm": cm, "Exp": e, 
                "Invoice": f"https://app.guesty.com/reservations/{r['ID']}" if e > 0 else None, "Net": round(net, 2)
            })
        
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True, 
                     column_config={"Net": st.column_config.NumberColumn(format="$%.2f"), "Invoice": st.column_config.LinkColumn("Invoice", display_text="🔗 View")})
else:
    st.title("⚖️ Taxes Report")
    st.write("Detailed location-based reporting...")
