import streamlit as st
import pandas as pd
import requests
from datetime import datetime, date, timedelta

# --- 1. DATABASE & API CACHE ---
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

# --- 3. DASHBOARD UI ---
st.set_page_config(page_title="PMC Statement", layout="wide")

with st.sidebar:
    st.header("📊 View Report")
    active_owner = st.selectbox("Switch Active Owner", sorted(st.session_state.owner_db.keys()), key='active_owner')
    conf = st.session_state.owner_db[active_owner]
    owner_pct = conf['pct']

# --- 4. CALCULATIONS ---
rows = []
# Totals for Summary Cards
t_gross = t_comm = t_exp = t_cln = t_net_payout = 0

source_data = get_mimic_reservations()

for r in source_data:
    fare, clean, exp = r['Fare'], r['Clean'], r['Exp']
    comm = round(fare * (owner_pct / 100), 2)
    
    # APPLYING NEW FORMULAS FOR DRAFT OWNERS
    if conf['type'] == "Draft":
        # Gross Revenue = Accommodation + Cleaning
        gross_rev = fare + clean
        # Net Payout = Accommodation - Cleaning - Commission - Expenses
        net_payout = fare - clean - comm - exp
    else:
        # Payout logic remains as previously requested
        gross_rev = fare
        net_payout = fare - comm - exp

    t_gross += gross_rev
    t_comm += comm
    t_cln += clean
    t_exp += exp
    t_net_payout += net_payout

    row = {
        "ID": r['ID'], 
        "Check-in/Out": f"{r['In'].strftime('%m/%d')} - {r['Out'].strftime('%m/%d')}", 
        "Accommodation": fare, 
        "Gross Revenue": gross_rev,
        "Commission": comm, 
        "Cleaning": clean,
        "Expenses": exp, 
        "Net Payout": net_payout,
        "Invoice": f"https://app.guesty.com/reservations/{r['ID']}"
    }
    rows.append(row)

df = pd.DataFrame(rows)

# --- 5. CENTERED YELLOW HEADERS ---
st.markdown(f"""
    <div style="text-align: center;">
        <h1 style="margin-bottom: 0;">PMC Statement</h1>
        <h2 style="margin-top: 10px; margin-bottom: 5px; color: #FFD700; font-weight: bold;">
            Reservation Report: {active_owner}
        </h2>
        <p style="color: #FFD700; font-size: 1.2rem; font-weight: bold; margin-top: 0;">
            Mode: {conf['type']} | Commission: {owner_pct}%
        </p>
    </div>
    <br>
    """, unsafe_allow_html=True)

# --- 6. SUMMARY METRICS ---
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Gross Revenue", f"${t_gross:,.2f}")
c2.metric(f"Commission ({owner_pct:.0f}%)", f"${t_comm:,.2f}")
c3.metric("Cleaning Total", f"${t_cln:,.2f}")
c4.metric("Total Expenses", f"${t_exp:,.2f}")
c5.metric("NET PAYOUT", f"${t_net_payout:,.2f}")

st.divider()

# --- 7. TABLE (Dynamic Visibility) ---
if conf['type'] == "Payout":
    # Payout View: Clean is hidden, Gross Rev is hidden (since it equals Accomm)
    order = ["ID", "Check-in/Out", "Accommodation", "Commission", "Expenses", "Invoice", "Net Payout"]
else:
    # Draft View: Shows the full breakdown including Gross Revenue and Cleaning
    order = ["ID", "Check-in/Out", "Accommodation", "Cleaning", "Gross Revenue", "Commission", "Expenses", "Invoice", "Net Payout"]

config = {col: st.column_config.NumberColumn(format="$%,.2f") for col in ["Net Payout", "Accommodation", "Cleaning", "Commission", "Expenses", "Gross Revenue"]}
config["Invoice"] = st.column_config.LinkColumn(display_text="🔗 View")

st.dataframe(df, use_container_width=True, column_config=config, column_order=order, hide_index=True)
