import streamlit as st
import pandas as pd
from datetime import date, timedelta

# --- 1. SETUP ---
st.set_page_config(page_title="PMC MASTER SUITE", layout="wide")

# Custom CSS to ensure the PDF looks professional and removes web-specific margins
st.markdown("""
    <style>
    @media print {
        [data-testid="stSidebar"], .stButton, header, footer {
            display: none !important;
        }
        .main .block-container {
            padding: 0 !important;
        }
    }
    </style>
""", unsafe_allow_html=True)

if 'owner_db' not in st.session_state:
    st.session_state.owner_db = {
        "ERAN": {"pct": 12.0, "type": "DRAFT"},
        "SMITH": {"pct": 15.0, "type": "PAYOUT"},
    }

def get_mimic_data(owner):
    if owner == "ERAN":
        return [
            {"ID": "RES-101", "Prop": "SUNSET VILLA", "Addr": "742 EVERGREEN TERRACE", "In": date(2026, 2, 1), "Out": date(2026, 2, 5), "Fare": 1200.0, "Cln": 150.0, "Exp": 25.0},
            {"ID": "RES-201", "Prop": "BEACH HOUSE", "Addr": "123 OCEAN DRIVE", "In": date(2026, 2, 5), "Out": date(2026, 2, 8), "Fare": 2500.0, "Cln": 200.0, "Exp": 150.0}
        ]
    return [{"ID": "RES-301", "Prop": "MOUNTAIN LODGE", "Addr": "55 PEAK ROAD", "In": date(2026, 2, 1), "Out": date(2026, 2, 5), "Fare": 1500.0, "Cln": 100.0, "Exp": 10.0}]

# --- 2. SIDEBAR ---
with st.sidebar:
    st.header("📂 NAVIGATION")
    mode = st.radio("SELECT REPORT TYPE", ["STATEMENTS", "TAX REPORT", "PMC REPORT"], index=0)
    
    st.divider()
    active_owner = st.selectbox("SWITCH ACTIVE OWNER", sorted(st.session_state.owner_db.keys()))
    conf = st.session_state.owner_db[active_owner]
    
    st.divider()
    st.header("📅 SELECT PERIOD")
    report_type = st.selectbox("CONTEXT", ["BY MONTH", "FULL YEAR", "YTD", "BETWEEN DATES"], index=0)
    
    today = date.today()
    if report_type == "BY MONTH":
        c1, c2 = st.columns(2)
        months = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
        sel_month = c1.selectbox("MONTH", months, index=today.month-1)
        sel_year = c2.selectbox("YEAR", [2026, 2025], index=0)
        start_date = date(sel_year, months.index(sel_month)+1, 1)
        end_date = (start_date + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    else:
        start_date, end_date = date(today.year, 1, 1), today

    st.divider()
    with st.expander("👤 OWNER MANAGEMENT"):
        target = st.selectbox("EDIT/DELETE", ["+ ADD NEW"] + list(st.session_state.owner_db.keys()))
        curr = st.session_state.owner_db.get(target, {"pct": 12.0, "type": "DRAFT"})
        n_name = st.text_input("NAME", value="" if target == "+ ADD NEW" else target).upper().strip()
        n_pct = st.number_input("COMM %", 0.0, 100.0, float(curr["pct"]))
        if st.button("💾 SAVE SETTINGS"):
            st.session_state.owner_db[n_name] = {"pct": n_pct, "type": "DRAFT"}
            st.rerun()

    with st.expander("🔌 API CONNECTION", expanded=True):
        st.text_input("CLIENT ID", value="0oaszuo22iOg...", type="password")
        st.text_input("CLIENT SECRET (KEY)", type="password") 
        st.button("🔄 SAVE & RUN", type="primary", use_container_width=True)

# --- 3. CALCULATION ENGINE ---
owner_data = get_mimic_data(active_owner)
o_comm = sum(round(r['Fare'] * (conf['pct'] / 100), 2) for r in owner_data)
o_cln = sum(r['Cln'] for r in owner_data)
o_exp = sum(r['Exp'] for r in owner_data)
o_fare = sum(r['Fare'] for r in owner_data)

# --- 4. MAIN CONTENT ---
if mode == "STATEMENTS":
    # EXPORT ACTION
    c_title, c_export = st.columns([4, 1])
    with c_export:
        if st.button("📄 EXPORT PDF"):
            st.info("💡 Press Ctrl+P (or Cmd+P) and select 'Save as PDF' to export the clean view below.")

    st.markdown(f"<div style='text-align: center;'><h1>OWNER STATEMENT</h1><h2 style='color:#FFD700;'>{active_owner}</h2><p>{start_date} TO {end_date}</p></div>", unsafe_allow_html=True)
    
    # Summary Metrics
    if conf['type'] == "DRAFT":
        m = st.columns(5)
        m[0].metric("GROSS PAYOUT", f"${(o_fare + o_cln):,.2f}")
        m[1].metric("CLEANING", f"${o_cln:,.2f}")
        m[2].metric("PMC COMM", f"${o_comm:,.2f}")
        m[3].metric("EXPENSED", f"${o_exp:,.2f}")
        m[4].metric("🏦 DRAFT AMT", f"${(o_comm + o_cln + o_exp):,.2f}")
    else:
        m = st.columns(4)
        m[0].metric("ACCOMMODATION", f"${o_fare:,.2f}")
        m[1].metric("PMC COMM", f"${o_comm:,.2f}")
        m[2].metric("EXPENSED", f"${o_exp:,.2f}")
        m[3].metric("💸 ACH TO OWNER", f"${(o_fare - o_comm - o_exp):,.2f}")

    st.divider()

    # Property Details
    df_p = pd.DataFrame(owner_data)
    for addr in df_p["Addr"].unique():
        sub = df_p[df_p["Addr"] == addr]
        st.markdown(f"### 🏠 {sub['Prop'].iloc[0]} \n *{addr}*")
        
        # Build Table rows
        table_rows = []
        for _, r in sub.iterrows():
            cm = round(r['Fare'] * (conf['pct'] / 100), 2)
            if conf['type'] == "DRAFT":
                row = {"STAY": f"{r['In']} - {r['Out']}", "GROSS": r['Fare']+r['Cln'], "CLN": r['Cln'], "PMC": cm, "EXP": r['Exp'], "NET": (r['Fare']+r['Cln']) - r['Cln'] - cm - r['Exp']}
            else:
                row = {"STAY": f"{r['In']} - {r['Out']}", "ACC": r['Fare'], "PMC": cm, "EXP": r['Exp'], "NET": r['Fare'] - cm - r['Exp']}
            table_rows.append(row)
        
        st.table(pd.DataFrame(table_rows)) # Using st.table for better PDF rendering than st.dataframe
