import streamlit as st
import pandas as pd
from datetime import date, timedelta

# --- 1. SETUP ---
st.set_page_config(page_title="PMC MASTER SUITE", layout="wide")

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
    mode = st.radio("SELECT REPORT TYPE", ["STATEMENTS", "TAX REPORT", "PMC REPORT", "PMC SALES",], index=0)
    
    st.divider()
    active_owner = st.selectbox("SWITCH ACTIVE OWNER", sorted(st.session_state.owner_db.keys()))
    conf = st.session_state.owner_db[active_owner]
    
    st.divider()
    st.header("📅 SELECT PERIOD")
    report_type = st.selectbox("CONTEXT", ["BY MONTH", "FULL YEAR", "YTD", "BETWEEN DATES"], index=0)
    
    today = date.today()
    # Date logic for start_date and end_date
    if report_type == "BY MONTH":
        c1, c2 = st.columns(2)
        months = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
        sel_month = c1.selectbox("MONTH", months, index=today.month-1)
        sel_year = c2.selectbox("YEAR", [2026, 2025], index=0)
        start_date = date(sel_year, months.index(sel_month)+1, 1)
        end_date = (start_date + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    elif report_type == "BETWEEN DATES":
        c1, c2 = st.columns(2)
        start_date = c1.date_input("START DATE", today - timedelta(days=30))
        end_date = c2.date_input("END DATE", today)
    else:
        start_date, end_date = date(today.year, 1, 1), today

    st.divider()
    with st.expander("👤 OWNER MANAGEMENT", expanded=False):
        target = st.selectbox("EDIT/DELETE", ["+ ADD NEW"] + list(st.session_state.owner_db.keys()))
        curr = st.session_state.owner_db.get(target, {"pct": 12.0, "type": "DRAFT"})
        n_name = st.text_input("NAME", value="" if target == "+ ADD NEW" else target).upper().strip()
        n_pct = st.number_input("COMM %", 0.0, 100.0, float(curr["pct"]))
        n_style = st.selectbox("STYLE", ["DRAFT", "PAYOUT"], index=0 if curr["type"] == "DRAFT" else 1)
        if st.button("💾 SAVE SETTINGS"):
            st.session_state.owner_db[n_name] = {"pct": n_pct, "type": n_style}
            st.rerun()

    # UPDATED: Added CLIENT SECRET (Key) field to match your requirement
    with st.expander("🔌 API CONNECTION", expanded=True):
        st.text_input("CLIENT ID", value="0oaszuo22iOg...", type="password")
        st.text_input("CLIENT SECRET (KEY)", value="", type="password") 
        if st.button("🔄 SAVE & RUN", type="primary", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

# --- 3. CALCULATION ENGINE ---
all_owners_data = []
total_ov2 = 0
for name, settings in st.session_state.owner_db.items():
    owner_data = get_mimic_data(name)
    o_comm, o_cln, o_exp, o_fare = 0, 0, 0, 0
    for r in owner_data:
        f, c, e = r['Fare'], r['Cln'], r['Exp']
        o_comm += round(f * (settings['pct'] / 100), 2)
        o_cln += c; o_exp += e; o_fare += f
    
    is_draft = settings['type'] == "DRAFT"
    if is_draft:
        top_rev = o_fare + o_cln
        net_rev = top_rev - o_cln - o_comm - o_exp
        draft_amt = o_comm + o_cln + o_exp
        ach_amt = 0
    else:
        top_rev = o_fare
        net_rev = o_fare - o_comm - o_exp
        draft_amt = 0
        ach_amt = net_rev
    
    all_owners_data.append({
        "OWNER": name, "TYPE": settings['type'], "REVENUE": top_rev, "PCT": settings['pct'],
        "COMM": o_comm, "EXP": o_exp, "CLN": o_cln, "NET": net_rev, "DRAFT": draft_amt, "ACH": ach_amt
    })
    total_ov2 += o_comm

# --- 4. MAIN CONTENT (STATEMENTS) ---
if mode == "STATEMENTS":
    st.markdown(f"<div style='text-align: center;'><h1>OWNER STATEMENT</h1><h2 style='color:#FFD700;'>{active_owner}</h2><p>{start_date} TO {end_date}</p></div>", unsafe_allow_html=True)
    
    s = next(item for item in all_owners_data if item["OWNER"] == active_owner)
    
    if conf['type'] == "DRAFT":
        m1, m2, m3, m4, m5, m6 = st.columns(6)
        m1.metric("GROSS PAYOUT", f"${s['REVENUE']:,.2f}")
        m2.metric("TOTAL CLEANING", f"${s['CLN']:,.2f}")
        m3.metric(f"PMC COMM ({s['PCT']}%)", f"${s['COMM']:,.2f}")
        m4.metric("EXPENSED", f"${s['EXP']:,.2f}")
        m5.metric("NET REVENUE", f"${s['NET']:,.2f}")
        m6.metric("🏦 DRAFT FROM OWNER", f"${s['DRAFT']:,.2f}")
    else:
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("ACCOMMODATION", f"${s['REVENUE']:,.2f}")
        m2.metric(f"PMC COMM ({s['PCT']}%)", f"${s['COMM']:,.2f}")
        m3.metric("EXPENSED", f"${s['EXP']:,.2f}")
        m4.metric("NET REVENUE", f"${s['NET']:,.2f}")
        m5.metric("💸 ACH TO OWNER", f"${s['ACH']:,.2f}")

    st.divider()

    df_p = pd.DataFrame(get_mimic_data(active_owner))
    for addr in df_p["Addr"].unique():
        sub = df_p[df_p["Addr"] == addr]
        st.markdown(f"#### 🏠 {sub['Prop'].iloc[0]} \n *{addr}*")
        rows = []
        for _, r in sub.iterrows():
            f, c, e = r['Fare'], r['Cln'], r['Exp']
            cm = round(f * (conf['pct'] / 100), 2)
            if conf['type'] == "DRAFT":
                gp = f + c
                nr = gp - c - cm - e
                row = {"ID": r['ID'], "STAY": f"{r['In'].strftime('%m/%d')} - {r['Out'].strftime('%m/%d')}", "GROSS PAYOUT": gp, "CLEANING": c, "PMC COMM": cm, "EXPENSED": e, "NET REVENUE": nr}
            else:
                nr = f - cm - e
                row = {"ID": r['ID'], "STAY": f"{r['In'].strftime('%m/%d')} - {r['Out'].strftime('%m/%d')}", "ACCOMMODATION": f, "PMC COMM": cm, "EXPENSED": e, "NET REVENUE": nr}
            rows.append(row)
        
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True, column_config={
            "GROSS PAYOUT": st.column_config.NumberColumn(format="$%.2f"),
            "ACCOMMODATION": st.column_config.NumberColumn(format="$%.2f"),
            "CLEANING": st.column_config.NumberColumn(format="$%.2f"),
            "PMC COMM": st.column_config.NumberColumn(format="$%.2f"),
            "EXPENSED": st.column_config.NumberColumn(format="$%.2f"),
            "NET REVENUE": st.column_config.NumberColumn(format="$%.2f")
        })

elif mode == "PMC REPORT":
    st.title("PMC INTERNAL CONTROL REPORT")
    st.metric("TRANSFER TO OV2", f"${total_ov2:,.2f}")
    st.dataframe(pd.DataFrame(all_owners_data), use_container_width=True, hide_index=True)
