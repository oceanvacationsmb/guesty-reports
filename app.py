import streamlit as st
import pandas as pd
from datetime import datetime, date

# --- 1. DATABASE & INITIALIZATION ---
if 'owner_db' not in st.session_state:
    st.session_state.owner_db = {
        "ERAN": {"pct": 12.0, "type": "Draft"},
        "SMITH": {"pct": 15.0, "type": "Payout"},
    }

# --- 2. LOCK TABLE UI (CSS Injection) ---
st.markdown("""
    <style>
    /* Prevent table expansion/resizing and horizontal shifts */
    [data-testid="stElementToolbar"] {display: none;}
    [data-testid="stTable"] {pointer-events: none;}
    .stDataFrame {pointer-events: auto !important;}
    </style>
    """, unsafe_allow_html=True)

# --- 3. MIMIC RESERVATIONS ---
def get_mimic_reservations():
    return [
        {"ID": "RES-55421", "In": date(2026, 2, 1), "Out": date(2026, 2, 5), "Fare": 1200.0, "Clean": 150.0, "Exp": 25.0},
        {"ID": "RES-55429", "In": date(2026, 2, 10), "Out": date(2026, 2, 14), "Fare": 850.50, "Clean": 100.0, "Exp": 0.0},
        {"ID": "RES-55435", "In": date(2026, 2, 18), "Out": date(2026, 2, 22), "Fare": 2100.75, "Clean": 180.0, "Exp": 45.10}
    ]

# --- 4. SIDEBAR (Restored API & Settings) ---
st.set_page_config(page_title="PMC Statement", layout="wide")

with st.sidebar:
    st.header("📊 View Report")
    active_owner = st.selectbox("Switch Active Owner", sorted(st.session_state.owner_db.keys()), key='active_owner')
    
    st.divider()
    st.header("📅 Select Period")
    report_type = st.selectbox("Quick Select", ["By Month", "Date Range", "Year to Date (YTD)", "Full Year"])
    # ... (Date logic logic remains active)
    
    st.divider()
    st.header("⚙️ Settings")
    with st.expander("Manage Owners"):
        edit_list = list(st.session_state.owner_db.keys())
        target_owner = st.selectbox("Edit/Delete", ["+ Add New"] + edit_list)
        name_input = st.text_input("Owner Name", value="" if target_owner == "+ Add New" else target_owner).upper().strip()
        conf_data = st.session_state.owner_db.get(target_owner, {"pct": 12.0, "type": "Draft"})
        upd_pct = st.number_input("Commission %", 0.0, 100.0, float(conf_data["pct"]))
        upd_type = st.selectbox("Settlement Style", ["Draft", "Payout"], index=0 if conf_data["type"] == "Draft" else 1)
        if st.button("💾 Save"):
            st.session_state.owner_db[name_input] = {"pct": upd_pct, "type": upd_type}
            st.rerun()

    st.markdown("<br><br>", unsafe_allow_html=True)
    # RESTORED API CONNECTION SECTION
    with st.expander("🔌 Connection Settings"):
        st.text_input("Client ID", value="0oaszuo22iOg2lk1P5d7")
        st.text_input("Client Secret", type="password")
        if st.button("🗑️ Reset Cache"):
            st.cache_data.clear()
            st.rerun()

# --- 5. CALCULATIONS ---
conf = st.session_state.owner_db[active_owner]
owner_pct = conf['pct']
rows = []
t_gross = t_comm = t_exp = t_cln = t_net_payout = 0
source_data = get_mimic_reservations()

for r in source_data:
    fare, clean, exp = r['Fare'], r['Clean'], r['Exp']
    comm = round(fare * (owner_pct / 100), 2)
    
    if conf['type'] == "Draft":
        gross_rev = fare + clean
        net_payout = fare - clean - comm - exp
    else:
        gross_rev = fare
        net_payout = fare - comm - exp

    t_gross += gross_rev
    t_comm += comm
    t_cln += clean
    t_exp += exp
    t_net_payout += net_payout

    rows.append({
        "ID": r['ID'], 
        "Check-in/Out": f"{r['In'].strftime('%m/%d')} - {r['Out'].strftime('%m/%d')}", 
        "Gross Revenue": gross_rev,
        "Accommodation": fare, 
        "Cleaning": clean,
        "Commission": comm, 
        "Expenses": exp, 
        "Invoice": f"https://app.guesty.com/reservations/{r['ID']}",
        "Net Payout": round(net_payout, 2)
    })

# --- 6. DISPLAY ---
st.markdown(f"<div style='text-align: center;'><h2 style='color: #FFD700;'>Reservation Report: {active_owner}</h2></div>", unsafe_allow_html=True)

if conf['type'] == "Payout":
    c1, c2, c4, c5 = st.columns(4)
    c1.metric("Gross Revenue", f"${t_gross:,.2f}")
    c2.metric(f"Commission ({owner_pct:.0f}%)", f"${t_comm:,.2f}")
    c4.metric("Total Expenses", f"${t_exp:,.2f}")
    c5.metric("NET PAYOUT", f"${t_net_payout:,.2f}")
    order = ["ID", "Check-in/Out", "Accommodation", "Commission", "Expenses", "Invoice", "Net Payout"]
else:
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Gross Revenue", f"${t_gross:,.2f}")
    c2.metric(f"Commission ({owner_pct:.0f}%)", f"${t_comm:,.2f}")
    c3.metric("Cleaning Total", f"${t_cln:,.2f}")
    c4.metric("Total Expenses", f"${t_exp:,.2f}")
    c5.metric("DRAFT AMOUNT", f"${(t_comm + t_cln + t_exp):,.2f}")
    order = ["ID", "Check-in/Out", "Gross Revenue", "Accommodation", "Cleaning", "Commission", "Expenses", "Invoice", "Net Payout"]

st.divider()

config = {col: st.column_config.NumberColumn(format="$%.2f") for col in ["Net Payout", "Accommodation", "Cleaning", "Commission", "Expenses", "Gross Revenue"]}
config["Invoice"] = st.column_config.LinkColumn(display_text="🔗 View")

st.dataframe(pd.DataFrame(rows), use_container_width=True, column_config=config, column_order=order, hide_index=True)
