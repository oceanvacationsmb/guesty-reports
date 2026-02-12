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
    mode = st.radio("SELECT REPORT TYPE", ["OWNER STATEMENTS", "TAX REPORT", "PMC REPORT"], index=0)
    st.divider()
    active_owner = st.selectbox("SWITCH ACTIVE OWNER", sorted(st.session_state.owner_db.keys()))
    conf = st.session_state.owner_db[active_owner]
    st.divider()
    st.header("📅 SELECT PERIOD")
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
    
    # --- FIXED LOGIC ---
    if is_draft:
        top_revenue = o_fare + o_cln  # GROSS PAYOUT
        # Net = Gross - Cln - Comm - Exp (which is essentially Fare - Comm - Exp)
        net_revenue = top_revenue - o_cln - o_comm - o_exp
        draft_total = o_comm + o_cln + o_exp
        ach_total = 0
    else:
        top_revenue = o_fare  # ACCOMMODATION
        net_revenue = o_fare - o_comm - o_exp
        draft_total = 0
        ach_total = net_revenue
    
    all_owners_data.append({
        "OWNER": name, "TYPE": settings['type'], "REVENUE": top_revenue, "PCT": settings['pct'],
        "COMM": o_comm, "EXP": o_exp, "CLN": o_cln, "NET": net_revenue, "DRAFT": draft_total, "ACH": ach_total
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
    for addr in df_p["Addr"].unique():
        sub = df_p[df_p["Addr"] == addr]
        st.markdown(f"#### 🏠 {sub['Prop'].iloc[0]} \n *{addr}*")
        rows = []
        for _, r in sub.iterrows():
            f, c, e = r['Fare'], r['Cln'], r['Exp']
            cm = round(f * (conf['pct'] / 100), 2)
            
            # Row Logic Fix
            if conf['type'] == "DRAFT":
                gp = f + c
                nr = gp - c - cm - e
                rev_col_name = "GROSS PAYOUT"
            else:
                gp = f
                nr = f - cm - e
                rev_col_name = "ACCOMMODATION"
                
            stay_dates = f"{r['In'].strftime('%m/%d')} - {r['Out'].strftime('%m/%d')}"
            row = {"ID": r['ID'], "CHECK-IN/OUT": stay_dates, rev_col_name: gp, "CLEANING": c, "PMC COMM": cm, "EXPENSED": e, "INVOICE": f"https://app.guesty.com/reservations/{r['ID']}" if e > 0 else None, "NET REVENUE": nr}
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
