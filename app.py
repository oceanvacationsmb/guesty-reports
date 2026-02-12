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

@st.cache_data(ttl=86400)
def get_guesty_token(cid, csec):
    url = "https://open-api.guesty.com/oauth2/token"
    payload = {"grant_type": "client_credentials", "scope": "open-api", 
               "client_id": cid.strip(), "client_secret": csec.strip()}
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    try:
        res = requests.post(url, data=payload, headers=headers)
        return res.json().get("access_token") if res.status_code == 200 else None
    except: return None

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
    
    st.divider()
    st.header("📅 Select Period")
    report_type = st.selectbox("Quick Select", ["By Month", "Date Range", "Year to Date (YTD)", "Full Year"])
    
    today = date.today()
    if report_type == "By Month":
        sel_year = st.selectbox("Select Year", [2026, 2025, 2024], index=0)
        month_names = ["January", "February", "March", "April", "May", "June", 
                       "July", "August", "September", "October", "November", "December"]
        sel_month = st.selectbox("Select Month", month_names, index=today.month-1)
        month_num = month_names.index(sel_month) + 1
        start_date, end_date = date(sel_year, month_num, 1), date(sel_year, month_num, 28)
    elif report_type == "Date Range":
        start_date = st.date_input("Start Date", date(today.year, today.month, 1))
        end_date = st.date_input("End Date", today)
    else:
        start_date, end_date = date(today.year, 1, 1), today

# --- 4. CALCULATIONS ---
conf = st.session_state.owner_db[active_owner]
owner_pct = conf['pct']
rows = []
t_fare = t_comm = t_exp = t_cln = 0

source_data = get_mimic_reservations()
status_msg = f"Mode: {conf['type']} | Commission: {owner_pct}%"

# --- 5. CENTERED YELLOW HEADERS ---
st.markdown(f"""
    <div style="text-align: center;">
        <h1 style="margin-bottom: 0;">PMC Statement</h1>
        <h2 style="margin-top: 10px; margin-bottom: 5px; color: #FFD700; font-weight: bold;">
            Reservation Report: {active_owner}
        </h2>
        <p style="color: #FFD700; font-size: 1.2rem; font-weight: bold; margin-top: 0;">
            {status_msg}
        </p>
    </div>
    <br>
    """, unsafe_allow_html=True)

for r in source_data:
    fare, clean, exp = r['Fare'], r['Clean'], r['Exp']
    comm = round(fare * (owner_pct / 100), 2)
    t_fare, t_comm, t_cln, t_exp = t_fare + fare, t_comm + comm, t_cln + clean, t_exp + exp

    row = {
        "ID": r['ID'], 
        "Check-in/Out": f"{r['In'].strftime('%m/%d')} - {r['Out'].strftime('%m/%d')}", 
        "Accommodation": fare, 
        "Commission": comm, 
        "Cleaning": clean,
        "Expenses": exp, 
        "Invoice": f"https://app.guesty.com/reservations/{r['ID']}"
    }
    
    # NEW FORMULA FIX:
    if conf['type'] == "Draft":
        row["Net Payout"] = (comm + clean + exp)
    else:
        # Net Payout = Accommodation - Commission - Expenses
        row["Net Payout"] = (fare - comm - exp)
        
    rows.append(row)

df = pd.DataFrame(rows)

# --- 6. SUMMARY METRICS ---
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Gross Revenue", f"${t_fare:,.2f}")
c2.metric(f"Commission ({owner_pct:.0f}%)", f"${t_comm:,.2f}")
c3.metric("Cleaning Total", f"${t_cln:,.2f}")
c4.metric("Total Expenses", f"${t_exp:,.2f}")

with c5:
    if conf['type'] == "Draft":
        final_val = (t_comm + t_cln + t_exp)
        st.metric("TOTAL TO DRAFT", f"${final_val:,.2f}")
    else:
        # Summary matches table formula: Total Fare - Total Comm - Total Exp
        final_val = (t_fare - t_comm - t_exp)
        st.metric("NET PAYOUT", f"${final_val:,.2f}")

st.divider()

# --- 7. TABLE (Dynamic Visibility) ---
if conf['type'] == "Payout":
    order = ["ID", "Check-in/Out", "Accommodation", "Commission", "Expenses", "Invoice", "Net Payout"]
else:
    order = ["ID", "Check-in/Out", "Accommodation", "Cleaning", "Commission", "Expenses", "Invoice", "Net Payout"]

config = {col: st.column_config.NumberColumn(format="$%,.2f") for col in ["Net Payout", "Accommodation", "Cleaning", "Commission", "Expenses"]}
config["Invoice"] = st.column_config.LinkColumn(display_text="🔗 View")

st.dataframe(df, use_container_width=True, column_config=config, column_order=order, hide_index=True)
