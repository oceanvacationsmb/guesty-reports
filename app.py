import streamlit as st
import pandas as pd
from datetime import datetime, date

# --- 1. DATABASE & MOCK DATA ---
if 'owner_db' not in st.session_state:
    st.session_state.owner_db = {
        "ERAN": {"pct": 20.0, "type": "Draft"},
        "SMITH": {"pct": 20.0, "type": "Payout"},
    }

def get_mock_reservations():
    # Using the exact numbers from your screenshot
    return [
        {"ID": "RES-55421", "In": date(2026, 2, 5), "Out": date(2026, 2, 9), "Fare": 1200.0, "Clean": 150.0, "Exp": 25.0, "Invoice": "https://link"},
        {"ID": "RES-55429", "In": date(2026, 2, 10), "Out": date(2026, 2, 14), "Fare": 850.50, "Clean": 100.0, "Exp": 0.0, "Invoice": None},
        {"ID": "RES-55435", "In": date(2026, 2, 18), "Out": date(2026, 2, 22), "Fare": 2100.75, "Clean": 180.0, "Exp": 45.10, "Invoice": "https://link"}
    ]

# --- 2. UI SETUP & CSS ---
st.set_page_config(page_title="Owner Portal", layout="wide")

# CSS to make headers Bold and Centered
st.markdown("""
    <style>
    th { text-align: center !important; font-weight: bold !important; }
    td { text-align: center !important; }
    </style>
""", unsafe_allow_html=True)

active_owner = st.sidebar.selectbox("Owner", sorted(st.session_state.owner_db.keys()))

# --- 3. CALCULATIONS (Rounding for Red Arrow Fix) ---
conf = st.session_state.owner_db[active_owner]
raw_res = get_mock_reservations()
rows = []

for res in raw_res:
    # Rounding here prevents the "red arrow" overflow
    fare = round(float(res['Fare']), 2)
    clean = round(float(res['Clean']), 2)
    comm = round(fare * (conf['pct'] / 100), 2)
    
    # Date format as requested: 02-05-2026 - 02-09-2026
    date_range = f"{res['In'].strftime('%m-%d-%Y')} - {res['Out'].strftime('%m-%d-%Y')}"
    
    row = {
        "ID": res['ID'],
        "Dates": date_range,
        "Accommodation": fare,
        "Commission": comm,
        "Expenses": round(float(res['Exp']), 2),
        "Invoice": res['Invoice']
    }
    if conf['type'] == "Draft":
        row["Net Payout"] = round(fare + clean, 2)
        row["Cleaning"] = clean
    rows.append(row)

df = pd.DataFrame(rows)

# --- 4. RENDER TABLE WITH COMMA FORMAT ---
st.header(f"Settlement Report: {active_owner}")

if conf['type'] == "Draft":
    final_order = ["ID", "Dates", "Net Payout", "Accommodation", "Cleaning", "Commission", "Expenses", "Invoice"]
else:
    final_order = ["ID", "Dates", "Accommodation", "Commission", "Expenses", "Invoice"]

# FIX: Added the comma to the format string: "$%,.2f"
column_config = {
    "Net Payout": st.column_config.NumberColumn("Net Payout", format="$%,.2f"),
    "Accommodation": st.column_config.NumberColumn("Accommodation", format="$%,.2f"),
    "Cleaning": st.column_config.NumberColumn("Cleaning", format="$%,.2f"),
    "Commission": st.column_config.NumberColumn("Commission", format="$%,.2f"),
    "Expenses": st.column_config.NumberColumn("Expenses", format="$%,.2f"),
    "Invoice": st.column_config.LinkColumn("Invoice", display_text="🔗 View")
}

st.dataframe(
    df, 
    use_container_width=True, 
    column_config=column_config, 
    column_order=final_order, 
    hide_index=True,
    on_select="ignore" # Locks the table
)
