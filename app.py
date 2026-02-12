import streamlit as st
import pandas as pd
from datetime import datetime

# --- 1. DATABASE INITIALIZATION ---
if 'owner_db' not in st.session_state:
    st.session_state.owner_db = {
        "ERAN (DRAFT)": {"pct": 20.0, "type": "Draft", "web_fee": 1.0},
        "SMITH (PAYOUT)": {"pct": 15.0, "type": "Payout", "web_fee": 0.0},
    }

# --- 2. TEST RESERVATIONS ---
def get_mock_reservations():
    return [
        {"ID": "RES-55421", "Dates": "Feb 01 - Feb 05", "Fare": 1200.0, "Clean": 150.0, "Exp": 25.0, "Invoice": "https://open-api.guesty.com/v1/receipt/55421"},
        {"ID": "RES-55429", "Dates": "Feb 10 - Feb 14", "Fare": 850.50, "Clean": 100.0, "Exp": 0.0, "Invoice": None},
        {"ID": "RES-55435", "Dates": "Feb 18 - Feb 22", "Fare": 2100.75, "Clean": 180.0, "Exp": 45.10, "Invoice": "https://open-api.guesty.com/v1/receipt/55435"}
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
    
    with st.expander("⚙️ Settings: Add/Edit Owners"):
        edit_list = list(st.session_state.owner_db.keys())
        target_owner = st.selectbox("Choose Owner to Modify", ["+ Add New"] + edit_list)
        # (Setting management logic remains the same)

# --- 4. CALCULATION & REORDERING ---
conf = st.session_state.owner_db[active_owner]
raw_res = get_mock_reservations()
rows = []

for res in raw_res:
    fare = res['Fare']
    comm = fare * (conf['pct'] / 100)
    
    # Build columns in requested order
    row = {
        "Reservation ID": res['ID'],
        "Dates (In/Out)": res['Dates'],
        "Accommodation": fare,
        "PMC Commission": comm
    }
    
    if conf['type'] == "Draft":
        row["Cleaning Fee"] = res['Clean']
    
    # Expenses must be last
    row["Expenses"] = res['Exp']
    row["Invoice Link"] = res['Invoice']
    rows.append(row)

df = pd.DataFrame(rows)

# --- 5. RENDER DISPLAY ---
st.header(f"Settlement Report: {active_owner}")

# Professional Table Config: Right-aligned & 2 Decimals
column_config = {
    "Accommodation": st.column_config.NumberColumn("Accommodation", format="$%,.2f"),
    "PMC Commission": st.column_config.NumberColumn("PMC Commission", format="$%,.2f"),
    "Cleaning Fee": st.column_config.NumberColumn("Cleaning Fee", format="$%,.2f"),
    "Expenses": st.column_config.NumberColumn("Expenses", format="$%,.2f"),
    "Invoice Link": st.column_config.LinkColumn("View Invoice", display_text="🔗 View")
}

st.dataframe(df, use_container_width=True, column_config=column_config, hide_index=True)

# Export as formatted CSV
csv = df.to_csv(index=False).encode('utf-8')
st.download_button(f"📥 Download {active_owner} Statement", data=csv, file_name=f"{active_owner}_Statement.csv")
