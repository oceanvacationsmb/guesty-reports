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

def get_mimic_data(owner):
    # Simulating multiple properties per owner
    if owner == "ERAN":
        return [
            {"ID": "RES-101", "Property": "Sunset Villa", "Address": "742 Evergreen Terrace", "In": date(2026, 2, 1), "Out": date(2026, 2, 5), "Fare": 1200.0, "Cleaning": 150.0, "Exp": 25.0},
            {"ID": "RES-201", "Property": "Beach House", "Address": "123 Ocean Drive", "In": date(2026, 2, 5), "Out": date(2026, 2, 8), "Fare": 2500.0, "Cleaning": 200.0, "Exp": 150.0}
        ]
    return [{"ID": "RES-301", "Property": "Mountain Lodge", "Address": "55 Peak Road", "In": date(2026, 2, 1), "Out": date(2026, 2, 5), "Fare": 1500.0, "Cleaning": 100.0, "Exp": 10.0}]

# --- 2. SIDEBAR (Filters & Settings) ---
with st.sidebar:
    st.header("📂 Navigation")
    mode = st.radio("View", ["Dashboard", "Taxes"], horizontal=True)
    
    st.divider()
    active_owner = st.selectbox("Switch Active Owner", sorted(st.session_state.owner_db.keys()))
    conf = st.session_state.owner_db[active_owner]
    
    # DATE PERIOD SECTION
    st.header("📅 Select Period")
    report_type = st.selectbox("Quick Select", ["By Month", "Full Year", "YTD", "Date Range"])
    today = date.today()
    if report_type == "By Month":
        c1, c2 = st.columns(2)
        sel_year = c1.selectbox("Year", [2026, 2025], index=0)
        month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        sel_month = c2.selectbox("Month", month_names, index=today.month-1)
        start_date, end_date = date(sel_year, month_names.index(sel_month)+1, 1), date(sel_year, month_names.index(sel_month)+1, 28)
    else:
        start_date, end_date = date(today.year, 1, 1), today

    st.divider()
    st.header("⚙️ Settings")
    with st.expander("👤 Manage Owners"):
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

    with st.expander("🔌 API Connection"):
        st.text_input("Client ID", value="0oaszuo22iOg...")
        st.text_input("Client Secret", type="password")
        if st.button("🔄 Save & Fetch Data", type="primary"):
            st.cache_data.clear()
            st.rerun()

# --- 3. LOGIC & SUMMARY CALCULATION ---
data = get_mimic_data(active_owner)
df_all = pd.DataFrame(data)

# Pre-calculate Global Grand Totals
grand_v = {"gross": 0, "comm": 0, "exp": 0, "cln": 0, "net": 0}
for _, r in df_all.iterrows():
    f, c, e = r['Fare'], r['Cleaning'], r['Exp']
    cm = round(f * (conf['pct'] / 100), 2)
    rev = f + c if conf['type'] == "Draft" else f
    net = f - c - cm - e if conf['type'] == "Draft" else f - cm - e
    grand_v["gross"]+=rev; grand_v["comm"]+=cm; grand_v["cln"]+=c; grand_v["exp"]+=e; grand_v["net"]+=net

# --- 4. MAIN DISPLAY ---
if mode == "Dashboard":
    st.markdown(f"<div style='text-align: center;'><h1 style='margin-bottom:0;'>PMC Master Statement</h1><h2 style='color:#FFD700;'>{active_owner}</h2><p>{start_date.strftime('%B %Y')}</p></div>", unsafe_allow_html=True)

    # --- GRAND TOTAL SUMMARY ---
    st.markdown("### 📊 Grand Total Summary (All Properties)")
    g_cols = st.columns(5 if conf['type'] == "Draft" else 4)
    g_cols[0].metric("Total Gross", f"${grand_v['gross']:,.2f}")
    g_cols[1].metric(f"Total Comm ({conf['pct']}%)", f"${grand_v['comm']:,.2f}")
    if conf['type'] == "Draft":
        g_cols[2].metric("Total Cleaning", f"${grand_v['cln']:,.2f}")
        g_cols[3].metric("Total Expenses", f"${grand_v['exp']:,.2f}")
        g_cols[4].metric("DRAFT TOTAL", f"${(grand_v['comm'] + grand_v['cln'] + grand_v['exp']):,.2f}", delta_color="inverse")
    else:
        g_cols[2].metric("Total Expenses", f"${grand_v['exp']:,.2f}")
        g_cols[3].metric("NET PAYOUT TOTAL", f"${grand_v['net']:,.2f}")
    
    st.divider()

    # --- INDIVIDUAL PROPERTY TABLES ---
    for addr in df_all["Address"].unique():
        prop_df = df_all[df_all["Address"] == addr]
        p_name = prop_df["Property"].iloc[0]
        
        st.markdown(f"#### 🏠 {p_name}")
        st.caption(f"📍 {addr}")

        p_rows, p_v = [], {"gross": 0, "comm": 0, "exp": 0, "cln": 0, "net": 0}
        for _, r in prop_df.iterrows():
            f, c, e = r['Fare'], r['Cleaning'], r['Exp']
            cm = round(f * (conf['pct'] / 100), 2)
            rev = f + c if conf['type'] == "Draft" else f
            net = f - c - cm - e if conf['type'] == "Draft" else f - cm - e
            p_v["gross"]+=rev; p_v["comm"]+=cm; p_v["cln"]+=c; p_v["exp"]+=e; p_v["net"]+=net
            
            p_rows.append({
                "ID": r['ID'], "Dates": f"{r['In'].strftime('%m/%d')} - {r['Out'].strftime('%m/%d')}", 
                "Gross": rev, "Fare": f, "Clean": c, "Comm": cm, "Exp": e, 
                "Invoice": f"https://app.guesty.com/reservations/{r['ID']}" if e > 0 else None, 
                "Net": round(net, 2)
            })

        # Mini Table for Property
        t_cfg = {col: st.column_config.NumberColumn(format="$%.2f") for col in ["Net", "Fare", "Clean", "Comm", "Exp", "Gross"]}
        t_cfg["Invoice"] = st.column_config.LinkColumn("Invoice", display_text="🔗 View")
        st.dataframe(pd.DataFrame(p_rows), use_container_width=True, hide_index=True, column_config=t_cfg)
        st.divider()

else:
    st.header("⚖️ Tax Compliance Report")
    st.info(f"Showing jurisdiction data for {active_owner}")
    # (Tax logic placeholder)
