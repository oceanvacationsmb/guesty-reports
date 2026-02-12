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
    # Updated navigation menu as requested
    mode = st.radio(
        "Select Report Type", 
        ["Owner Statements", "Tax Report"], 
        index=0
    )
    
    st.divider()
    st.header("👤 Active Owner")
    active_owner = st.selectbox("Switch Owner", sorted(st.session_state.owner_db.keys()))
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
    with st.expander("⚙️ Owner Settings"):
        target = st.selectbox("Edit/Delete", ["+ Add New"] + list(st.session_state.owner_db.keys()))
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

# --- 4. MAIN CONTENT ---
if mode == "Owner Statements":
    st.markdown(f"<div style='text-align: center;'><h1 style='margin-bottom:0;'>Owner Statement</h1><h2 style='color:#FFD700;'>{active_owner}</h2></div>", unsafe_allow_html=True)
    
    # Grand Total Logic
    st.subheader("📊 Grand Total Summary")
    cols = st.columns(6 if conf['type'] == "Draft" else 5)
    cols[0].metric("Gross Payout", f"${grand['gross_payout']:,.2f}")
    cols[1].metric(f"Total Comm", f"${grand['comm']:,.2f}")
    
    if conf['type'] == "Draft":
        cols[2].metric("Total Cleaning", f"${grand['cln']:,.2f}")
        cols[3].metric("Total Expenses", f"${grand['exp']:,.2f}")
        cols[4].metric("Net Revenue", f"${grand['net_rev']:,.2f}")
        cols[5].metric("🏦 DRAFT FROM OWNER", f"${(grand['comm'] + grand['cln'] + grand['exp']):,.2f}", delta="Action: Draft", delta_color="inverse")
    else:
        cols[2].metric("Total Expenses", f"${grand['exp']:,.2f}")
        cols[3].metric("Net Revenue", f"${grand['net_rev']:,.2f}")
        cols[4].metric("💸 ACH TO OWNER", f"${grand['net_rev']:,.2f}", delta="Action: Payout")

    st.divider()

    # Individual Property Tables
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
            p_rows.append({
                "ID": r['ID'], "Dates": f"{r['In'].strftime('%m/%d')}", "Gross Payout": p_gp, 
                "Fare": f, "Cleaning": c, "Comm": cm, "Exp": e, "Net Revenue": round(p_nr, 2)
            })
        
        st.dataframe(pd.DataFrame(p_rows), use_container_width=True, hide_index=True)
        st.divider()

else: # Tax Report Mode
    st.markdown(f"<div style='text-align: center;'><h1 style='margin-bottom:0;'>Tax Report</h1><h2 style='color:#FFD700;'>{active_owner}</h2></div>", unsafe_allow_html=True)
    
    # Example Tax Table
    st.info(f"Breakdown of taxes collected for {active_owner}")
    tax_data = []
    for addr in df_all["Addr"].unique():
        p_df = df_all[df_all["Addr"] == addr]
        tax_data.append({
            "Property": p_df['Prop'].iloc[0],
            "Address": addr,
            "State Tax": f"${(p_df['Fare'].sum() * 0.06):,.2f}",
            "Local Tax": f"${(p_df['Fare'].sum() * 0.02):,.2f}",
            "Total Collected": f"${(p_df['Fare'].sum() * 0.08):,.2f}"
        })
    
    st.dataframe(pd.DataFrame(tax_data), use_container_width=True, hide_index=True)
