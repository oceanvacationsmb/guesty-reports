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
            {"ID": "RES-101", "Prop": "SUNSET VILLA", "Fare": 1200.0, "Cln": 150.0, "Exp": 25.0},
            {"ID": "RES-201", "Prop": "BEACH HOUSE", "Fare": 2500.0, "Cln": 200.0, "Exp": 150.0}
        ]
    return [{"ID": "RES-301", "Prop": "MOUNTAIN LODGE", "Fare": 1500.0, "Cln": 100.0, "Exp": 10.0}]

# --- 2. SIDEBAR ---
with st.sidebar:
    st.header("📂 NAVIGATION")
    mode = st.radio("SELECT REPORT TYPE", ["OWNER STATEMENTS", "TAX REPORT", "PMC REPORT"], index=0)
    active_owner = st.selectbox("SWITCH ACTIVE OWNER", sorted(st.session_state.owner_db.keys()))
    conf = st.session_state.owner_db[active_owner]
    today, start_date, end_date = date.today(), date(2026, 2, 1), date(2026, 2, 28)

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
        top_rev = o_fare + o_cln  # GROSS PAYOUT
        net_rev = top_rev - o_cln - o_comm - o_exp
        draft_amt = o_comm + o_cln + o_exp
        ach_amt = 0
    else:
        top_rev = o_fare  # ACCOMMODATION
        net_rev = o_fare - o_comm - o_exp # CORRECTED PAYOUT MATH
        draft_amt = 0
        ach_amt = net_rev
    
    all_owners_data.append({
        "OWNER": name, "TYPE": settings['type'], "REVENUE": top_rev, "PCT": settings['pct'],
        "COMM": o_comm, "EXP": o_exp, "CLN": o_cln, "NET": net_rev, "DRAFT": draft_amt, "ACH": ach_amt
    })
    total_ov2 += o_comm

# --- 4. MAIN CONTENT ---
if mode == "OWNER STATEMENTS":
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
    rows = []
    for _, r in df_p.iterrows():
        f, c, e = r['Fare'], r['Cln'], r['Exp']
        cm = round(f * (conf['pct'] / 100), 2)
        
        if conf['type'] == "DRAFT":
            rev_val = f + c
            nr = rev_val - c - cm - e
            rev_header = "GROSS PAYOUT"
        else:
            rev_val = f
            nr = f - cm - e # CORRECTED ROW MATH
            rev_header = "ACCOMMODATION"
            
        row = {"ID": r['ID'], rev_header: rev_val, "CLEANING": c, "PMC COMM": cm, "EXPENSED": e, "NET REVENUE": nr}
        rows.append(row)
    
    # Define column order based on type
    if conf['type'] == "DRAFT":
        disp_cols = ["ID", "GROSS PAYOUT", "CLEANING", "PMC COMM", "EXPENSED", "NET REVENUE"]
    else:
        disp_cols = ["ID", "ACCOMMODATION", "PMC COMM", "EXPENSED", "NET REVENUE"]

    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True, column_order=disp_cols, column_config={
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
