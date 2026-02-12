import streamlit as st
import pandas as pd
from datetime import date, timedelta

# --- 1. SETUP ---
st.set_page_config(page_title="PMC Master Suite", layout="wide")

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

# --- 2. SIDEBAR (PERMANENT) ---
with st.sidebar:
    st.header("📂 Navigation")
    mode = st.radio("Select Report Type", ["Owner Statements", "Tax Report", "PMC REPORT"], index=0)
    
    st.divider()
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
    else:
        start_date, end_date = date(today.year, 1, 1), today

    st.divider()
    with st.expander("👤 Owner Management"):
        target = st.selectbox("Edit/Delete", ["+ Add New"] + list(st.session_state.owner_db.keys()))
        curr = st.session_state.owner_db.get(target, {"pct": 12.0, "type": "Draft"})
        n_name = st.text_input("Name", value="" if target == "+ Add New" else target).upper().strip()
        n_pct = st.number_input("Comm %", 0.0, 100.0, float(curr["pct"]))
        n_style = st.selectbox("Style", ["Draft", "Payout"], index=0 if curr["type"] == "Draft" else 1)
        if st.button("💾 Save Settings"):
            st.session_state.owner_db[n_name] = {"pct": n_pct, "type": n_style}
            if target != "+ Add New" and target != n_name: del st.session_state.owner_db[target]
            st.rerun()

    with st.expander("🔌 API Connection", expanded=True):
        st.text_input("Client ID", value="0oaszuo22iOg...")
        if st.button("🔄 Save & Run", type="primary", use_container_width=True):
            st.cache_data.clear(); st.rerun()

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
    all_owners_data.append({"Owner": name, "Type": settings['type'], "Draft": draft_val, "ACH": net_rev if settings['type']=="Payout" else 0, "Comm": o_comm, "Net": net_rev, "Gross": o_fare + (o_cln if settings['type']=="Draft" else 0)})
    total_ov2 += o_comm

# --- 4. MAIN CONTENT ---
if mode == "Owner Statements":
    st.markdown(f"<div style='text-align: center;'><h1>Owner Statement</h1><h2 style='color:#FFD700;'>{active_owner}</h2><p>{start_date} to {end_date}</p></div>", unsafe_allow_html=True)
    
    summary = next(item for item in all_owners_data if item["Owner"] == active_owner)
    cols = st.columns(5)
    cols[0].metric("Gross Payout", f"${summary['Gross']:,.2f}")
    cols[1].metric("Total Comm", f"${summary['Comm']:,.2f}")
    cols[2].metric("Net Revenue", f"${summary['Net']:,.2f}")
    if conf['type'] == "Draft":
        cols[3].metric("🏦 DRAFT FROM OWNER", f"${summary['Draft']:,.2f}")
    else:
        cols[3].metric("💸 ACH TO OWNER", f"${summary['ACH']:,.2f}")

    st.divider()
    # RESTORED PROPERTY TABLES WITH EXPENSE LINKS
    raw_data = get_mimic_data(active_owner)
    df_p = pd.DataFrame(raw_data)
    for addr in df_p["Addr"].unique():
        sub = df_p[df_p["Addr"] == addr]
        st.markdown(f"#### 🏠 {sub['Prop'].iloc[0]} \n *{addr}*")
        
        rows = []
        for _, r in sub.iterrows():
            f, c, e = r['Fare'], r['Cln'], r['Exp']
            cm = round(f * (conf['pct'] / 100), 2)
            gp = f + c if conf['type'] == "Draft" else f
            nr = f - (c if conf['type'] == "Draft" else 0) - cm - e
            rows.append({
                "ID": r['ID'], "Dates": f"{r['In'].strftime('%m/%d')}", "Gross Payout": gp,
                "Fare": f, "Cleaning": c, "Comm": cm, "Exp": e,
                "Invoice": f"https://app.guesty.com/reservations/{r['ID']}" if e > 0 else None,
                "Net Revenue": nr
            })
        
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True, column_config={
            "Gross Payout": st.column_config.NumberColumn(format="$%.2f"),
            "Net Revenue": st.column_config.NumberColumn(format="$%.2f"),
            "Invoice": st.column_config.LinkColumn("Invoice", display_text="🔗 View")
        })

elif mode == "PMC REPORT":
    st.title("PMC Internal Report")
    m1, m2 = st.columns(2)
    m1.metric("TRANSFER TO OV2", f"${total_ov2:,.2f}", delta="Total Management Fees")
    st.dataframe(pd.DataFrame(all_owners_data)[["Owner", "Type", "Draft", "ACH", "Comm"]], use_container_width=True, hide_index=True)

else:
    st.title("Tax Report")
    st.info("Location-based tax summary.")
