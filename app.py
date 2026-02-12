import streamlit as st
import pandas as pd
from datetime import datetime

# --- 1. DATABASE INITIALIZATION ---
if 'owner_db' not in st.session_state:
    st.session_state.owner_db = {
        "ERAN (DRAFT)": {"pct": 20.0, "type": "Draft", "web_fee": 1.0},
        "SMITH (PAYOUT)": {"pct": 15.0, "type": "Payout", "web_fee": 0.0},
    }

# --- 2. GENERATE TEST RESERVATIONS ---
def get_mock_reservations():
    return [
        {"ID": "RES-55421", "Dates": "Feb 01 - Feb 05", "Fare": 1200.0, "Clean": 150.0, "Exp": 25.0},
        {"ID": "RES-55429", "Dates": "Feb 10 - Feb 14", "Fare": 850.50, "Clean": 100.0, "Exp": 0.0},
        {"ID": "RES-55435", "Dates": "Feb 18 - Feb 22", "Fare": 2100.75, "Clean": 180.0, "Exp": 45.10},
        {"ID": "RES-55440", "Dates": "Feb 25 - Feb 28", "Fare": 5950.0, "Clean": 120.0, "Exp": 10.0}
    ]

# --- 3. DASHBOARD UI ---
st.set_page_config(page_title="Owner Settlement", layout="wide")
st.title("🛡️ Guesty Automated Settlement Dashboard")

with st.sidebar:
    st.header("📊 View Report")
    active_owner = st.selectbox("Switch Active Owner", sorted(st.session_state.owner_db.keys()))
    
    st.divider()
    st.header("📅 Period")
    m = st.selectbox("Month", range(1, 13), index=datetime.now().month - 1)
    y = st.number_input("Year", value=2026)
    
    st.divider()
    with st.expander("⚙️ Settings: Add/Edit Owners"):
        edit_list = list(st.session_state.owner_db.keys())
        target_owner = st.selectbox("Choose Owner to Modify", ["+ Add New"] + edit_list)
        
        name_input = target_owner if target_owner != "+ Add New" else st.text_input("New Owner Name").upper()
        current_pct = st.session_state.owner_db.get(target_owner, {"pct": 20.0})["pct"] if target_owner != "+ Add New" else 20.0
        current_type = st.session_state.owner_db.get(target_owner, {"type": "Draft"})["type"] if target_owner != "+ Add New" else "Draft"

        new_pct = st.number_input(f"Commission %", 0.0, 100.0, float(current_pct))
        new_type = st.selectbox(f"Style", ["Draft", "Payout"], index=0 if current_type == "Draft" else 1)
        
        if st.button("💾 Save Owner Settings"):
            st.session_state.owner_db[name_input] = {"pct": new_pct, "type": new_type, "web_fee": 0.0}
            st.rerun()

# --- 4. CALCULATION & FORMATTING LOGIC ---
conf = st.session_state.owner_db[active_owner]
raw_res = get_mock_reservations()
rows = []

for res in raw_res:
    fare = res['Fare']
    pct = conf['pct']
    comm_amt = fare * (pct / 100)
    
    # Core Data with formatting for the table display
    row = {
        "Reservation ID": res['ID'],
        "Dates (In/Out)": res['Dates'],
        "Accommodation": f"{fare:,.2f}",
        "PMC %": f"{pct:,.1f}%",
        "PMC Commission": f"{comm_amt:,.2f}",
        "Expenses": f"{res['Exp']:,.2f}"
    }
    
    if conf['type'] == "Draft":
        row["Cleaning Fee"] = f"{res['Clean']:,.2f}"
    
    rows.append(row)

df_display = pd.DataFrame(rows)

# --- 5. RENDER DISPLAY ---
st.header(f"Settlement Report: {active_owner}")
st.subheader(f"Type: {conf['type']} | Commission: {conf['pct']}%")

# Metrics Summary (Calculating from raw numbers for accuracy)
c1, c2, c3, c4 = st.columns(4)
total_fare = sum(r['Fare'] for r in raw_res)
total_comm = sum(r['Fare'] * (conf['pct'] / 100) for r in raw_res)
total_exp = sum(r['Exp'] for r in raw_res)

c1.metric("Gross Revenue", f"${total_fare:,.2f}")
c2.metric("Total Commission", f"${total_comm:,.2f}")
c3.metric("Total Expenses", f"${total_exp:,.2f}")

with c4:
    if conf['type'] == "Draft":
        total_clean = sum(r['Clean'] for r in raw_res)
        total_draft = total_comm + total_clean + total_exp
        st.metric("TOTAL TO DRAFT", f"${total_draft:,.2f}")
    else:
        net_payout = total_fare - total_comm - total_exp
        st.metric("NET PAYOUT", f"${net_payout:,.2f}")

st.divider()
# Use st.table or st.dataframe for a clean look
st.dataframe(df_display, use_container_width=True)

# Export (Note: CSVs usually keep raw numbers, but we'll export the formatted version)
csv = df_display.to_csv(index=False).encode('utf-8')
st.download_button(f"📥 Export {active_owner} CSV", data=csv, file_name=f"{active_owner}.csv")
