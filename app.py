import streamlit as st
import pandas as pd
import requests
from datetime import datetime, date, timedelta

# --- 1. DATABASE & INITIALIZATION ---
if 'owner_db' not in st.session_state:
    st.session_state.owner_db = {
        "ERAN": {"pct": 12.0, "type": "Draft"},
        "SMITH": {"pct": 15.0, "type": "Payout"},
    }

# --- 2. MIMIC RESERVATIONS ---
def get_mimic_reservations():
    return [
        {"ID": "RES-55421", "In": date(2026, 2, 1), "Out": date(2026, 2, 5), "Fare": 1200.0, "Clean": 150.0, "Exp": 25.0},
        {"ID": "RES-55429", "In": date(2026, 2, 10), "Out": date(2026, 2, 14), "Fare": 850.50, "Clean": 100.0, "Exp": 0.0},
        {"ID": "RES-55435", "In": date(2026, 2, 18), "Out": date(2026, 2, 22), "Fare": 2100.75, "Clean": 180.0, "Exp": 45.10}
    ]

# --- 3. SIDEBAR ---
st.set_page_config(page_title="PMC Statement", layout="wide")

with st.sidebar:
    st.header("📊 View Report")
    active_owner = st.selectbox("Switch Active Owner", sorted(st.session_state.owner_db.keys()), key='active_owner')
    
    st.divider()
    st.header("📅 Select Period")
    # Date logic here...
    
    st.divider()
    st.header("⚙️ Settings")
    with st.expander("Manage Owners"):
        # Owner management logic...
        pass

    st.markdown("<br><br>", unsafe_allow_html=True)
    with st.expander("🔌 Connection Settings"):
        c_id = st.text_input("Client ID", value="0oaszuo22iOg2lk1P5d7")
        c_secret = st.text_input("Client Secret", type="password")

# --- 4. CALCULATIONS ---
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
        "Res ID": r['ID'], # UPDATED COLUMN NAME
        "Check-in/Out": f"{r['In'].strftime('%m/%d')} - {r['Out'].strftime('%m/%d')}", 
        "Gross Revenue": gross_rev,
        "Accommodation": fare, 
        "Cleaning": clean,
        "Commission": comm, 
        "Expenses": exp, 
        "Invoice": f"https://app.guesty.com/reservations/{r['ID']}",
        "Net Payout": round(net_payout, 2)
    })

# --- 5. CENTERED YELLOW HEADERS ---
st.markdown(f"""
    <div style="text-align: center;">
        <h1 style="margin-bottom: 0;">PMC Statement</h1>
        <h2 style="margin-top: 10px; margin-bottom: 5px; color: #FFD700; font-weight: bold;">
            Reservation Report: {active_owner}
        </h2>
    </div>
    <br>
    """, unsafe_allow_html=True)

# --- 6. SUMMARY METRICS ---
# Metric logic here...

st.divider()

# --- 7. TABLE ---
if conf['type'] == "Payout":
    order = ["Res ID", "Check-in/Out", "Accommodation", "Commission", "Expenses", "Invoice", "Net Payout"]
else:
    order = ["Res ID", "Check-in/Out", "Gross Revenue", "Accommodation", "Cleaning", "Commission", "Expenses", "Invoice", "Net Payout"]

config = {
    col: st.column_config.NumberColumn(format="$%.2f") 
    for col in ["Net Payout", "Accommodation", "Cleaning", "Commission", "Expenses", "Gross Revenue"]
}
config["Invoice"] = st.column_config.LinkColumn(display_text="🔗 View")

st.dataframe(pd.DataFrame(rows), use_container_width=True, column_config=config, column_order=order, hide_index=True)
