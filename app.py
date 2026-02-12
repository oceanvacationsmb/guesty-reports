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

    st.divider()
    with st.expander("👤 Owner Management"):
        target = st.selectbox("Edit/Delete", ["+ Add New"] + list(st.session_state.owner_db.keys()))
        curr = st.session_state.owner_db.get(target, {"pct": 12.0, "type": "Draft"})
        n_name = st.text_input("Owner Name", value="" if target == "+ Add New" else target).upper().strip()
        n_pct = st.number_input("Commission %", 0.0, 100.0, float(curr["pct"]))
        n_style = st.selectbox("Style", ["Draft", "Payout"], index=0 if curr["type"] == "Draft" else 1)
        
        b1, b2 = st.columns(2)
        if b1.button("💾 Save Settings"):
            st.session_state.owner_db[n_name] = {"pct": n_pct, "type": n_style}
            if target != "+ Add New" and target != n_name: del st.session_state.owner_db[target]
            st.rerun()
        if target != "+ Add New" and b2.button("🗑️ Delete Owner", type="primary"):
            del st.session_state.owner_db[target]; st.rerun()

    with st.expander("🔌 API", expanded=True):
        st.text_input("Client ID", value="0oaszuo22iOg...")
        if st.button("🔄 Save & Run", type="primary", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

# --- 3. CALCULATIONS ---
data = get_mimic_data(active_owner)
df_all = pd.DataFrame(data)

grand = {"gross_payout": 0, "comm": 0, "exp": 0, "cln": 0, "net_rev": 0}
for _, r in df_all.iterrows():
    f, c, e = r['Fare'], r['Cln'], r['Exp']
    cm = round(f * (conf['pct'] / 100), 2)
    gp = f + c if conf['type'] == "Draft" else f
    nr = f - (c if conf['type'] == "Draft" else 0) - cm - e
    grand["gross_payout"]+=gp; grand["comm"]+=cm; grand["cln"]+=c; grand["exp"]+=e; grand["net_rev"]+=nr

# --- 4. DISPLAY ---
if mode == "Dashboard":
    st.markdown(f"<div style='text-align: center;'><h1 style='margin-bottom:0;'>Master Statement</h1><h2 style='color:#FFD700;'>{active_owner}</h2></div>", unsafe_allow_html=True)
    
    st.subheader("📊 Grand Total Summary")
    cols = st.columns(6 if conf['type'] == "Draft" else 5)
    cols[0].metric("Gross Payout", f"${grand['gross_payout']:,.2f}")
    cols[1].metric(f"Total Comm", f"${grand['comm']:,.2f}")
    
    if conf['type'] == "Draft":
        cols[2].metric("Total Cleaning", f"${grand['cln']:,.2f}")
        cols[3].metric("Total Expenses", f"${grand['exp']:,.2f}")
        cols[4].metric("Net Revenue", f"${grand['net_rev']:,.2f}")
        cols[5].metric("🏦 DRAFT FROM OWNER", f"${(grand['comm'] + grand['cln'] + grand['exp']):,.2f}", delta="Draft Total", delta_color="inverse")
    else:
        cols[2].metric("Total Expenses", f"${grand['exp']:,.2f}")
        cols[3].metric("Net Revenue", f"${grand['net_rev']:,.2f}")
        cols[4].metric("💸 ACH TO OWNER", f"${grand['net_rev']:,.2f}", delta="Payout Total")

    st.divider()

    for addr in df_all["Addr"].unique():
        p_df = df_all[df_all["Addr"] == addr]
        st.markdown(f"#### 🏠 {p_df['Prop'].iloc[0]}")
        st.caption(f"📍 {addr}")
        
        p_rows = []
        for _, r in p_df.iterrows():
            f, c, e = r['Fare'], r['Cln'], r['Exp']
            cm = round(f * (conf['pct'] / 100), 2)
            p_gp = f + c if conf['type'] == "Draft" else f
            p_nr = f - (c if conf['type'] == "Draft" else 0) - cm - e
            p_rows.append({"ID": r['ID'], "Dates": f"{r['In'].strftime('%m/%d')}", "Gross Payout": p_gp, "Fare": f, "Cleaning": c, "Comm": cm, "Exp": e, "Invoice": f"https://app.guesty.com/reservations/{r['ID']}" if e > 0 else None, "Net Revenue": round(p_nr, 2)})
        
        st.dataframe(pd.DataFrame(p_rows), use_container_width=True, hide_index=True, column_config={"Gross Payout": st.column_config.NumberColumn(format="$%.2f"), "Net Revenue": st.column_config.NumberColumn(format="$%.2f"), "Invoice": st.column_config.LinkColumn("Invoice", display_text="🔗 View")})
        st.divider()

else:
    st.header("⚖️ Tax Compliance Report")
    st.info(f"Showing location breakdown for {active_owner}")
    tax_df = pd.DataFrame([{"State": "FL", "City": "Miami", "County": "Miami-Dade", "Property": "Ocean View", "Address": "123 Coast Hwy", "Income": 5000.00}])
    st.dataframe(tax_df, use_container_width=True, hide_index=True)
