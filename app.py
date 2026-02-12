import streamlit as st
import pandas as pd
from datetime import datetime

# --- 1. DATABASE INITIALIZATION ---
if 'owner_db' not in st.session_state:
    st.session_state.owner_db = {
        "ERAN (DRAFT)": {"pct": 20.0, "type": "Draft", "web_fee": 1.0},
        "SMITH (PAYOUT)": {"pct": 15.0, "type": "Payout", "web_fee": 0.0},
    }

# --- 2. EXPANDED TEST RESERVATIONS ---
def get_mock_reservations():
    return [
        {"ID": "RES-55421", "Dates": "Feb 01 - Feb 05", "Fare": 1200.0, "Clean": 150.0, "Exp": 25.0},
        {"ID": "RES-55429", "Dates": "Feb 10 - Feb 14", "Fare": 850.50, "Clean": 100.0, "Exp": 0.0},
        {"ID": "RES-55435", "Dates": "Feb 18 - Feb 22", "Fare": 2100.75, "Clean": 180.0, "Exp": 45.10},
        {"ID": "RES-55440", "Dates": "Feb 25 - Feb 28", "Fare": 5950.0, "Clean": 120.0, "Exp": 10.0},
        {"ID": "RES-55445", "Dates": "Mar 01 - Mar 04", "Fare": 1500.0, "Clean": 150.0, "Exp": 0.0}
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

# --- 4. CALCULATION & FORMATTING ---
conf = st.session_state.owner_db[active_owner]
raw_res = get_mock_reservations()
rows = []

# Raw totals for math
t_fare = t_comm = t_exp = t_cln = 0

for res in raw_res:
    fare = res['Fare']
    comm = fare * (conf['pct'] / 100)
    
    t_fare += fare
    t_comm += comm
    t_exp += res['Exp']
    t_cln += res['Clean']
    
    # Store formatted strings for the table
    row = {
        "Reservation ID": res['ID'],
        "Dates (In/Out)": res['Dates'],
        "Accommodation": f"${fare:,.2f}",
        "PMC %": f"{conf['pct']}%",
        "PMC Commission": f"${comm:,.2f}",
        "Expenses": f"${res['Exp']:,.2f}"
    }
    if conf['type'] == "Draft":
        row["Cleaning Fee"] = f"${res['Clean']:,.2f}"
    rows.append(row)

# Add the Total Row
total_row = {
    "Reservation ID": "TOTAL",
    "Dates (In/Out)": "-",
    "Accommodation": f"${t_fare:,.2f}",
    "PMC %": "-",
    "PMC Commission": f"${t_comm:,.2f}",
    "Expenses": f"${t_exp:,.2f}"
}
if conf['type'] == "Draft":
    total_row["Cleaning Fee"] = f"${t_cln:,.2f}"

rows.append(total_row)
df_display = pd.DataFrame(rows)

# --- 5. RENDER DISPLAY ---
st.header(f"Settlement Report: {active_owner}")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Gross Revenue", f"${t_fare:,.2f}")
c2.metric("Total Commission", f"${t_comm:,.2f}")
c3.metric("Total Expenses", f"${t_exp:,.2f}")

with c4:
    if conf['type'] == "Draft":
        st.metric("TOTAL TO DRAFT", f"${(t_comm + t_cln + t_exp):,.2f}")
    else:
        st.metric("NET PAYOUT", f"${(t_fare - t_comm - t_exp):,.2f}")

st.divider()
st.dataframe(df_display, use_container_width=True)

csv = df_display.to_csv(index=False).encode('utf-8')
st.download_button(f"📥 Export {active_owner} CSV", data=csv, file_name=f"{active_owner}.csv")
