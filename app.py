import streamlit as st
import pandas as pd
from datetime import datetime, date

# --- 1. DATABASE ---
if 'owner_db' not in st.session_state:
    st.session_state.owner_db = {
        "ERAN": {"pct": 20.0, "type": "Draft"},
        "SMITH": {"pct": 15.0, "type": "Payout"},
    }

# --- 2. MOCK DATA ---
def get_mock_reservations():
    return [
        {"ID": "RES-55421", "Dates": date(2026, 2, 1), "Fare": 1200.0, "Clean": 150.0, "Exp": 25.0, "Invoice": "https://guesty.com/inv/1"},
        {"ID": "RES-55429", "Dates": date(2026, 2, 10), "Fare": 850.50, "Clean": 100.0, "Exp": 0.0, "Invoice": None},
        {"ID": "RES-55435", "Dates": date(2026, 2, 18), "Fare": 2100.75, "Clean": 180.0, "Exp": 45.10, "Invoice": "https://guesty.com/inv/2"}
    ]

# --- 3. DASHBOARD UI ---
st.set_page_config(page_title="Owner Portal", layout="wide")
st.title("🛡️ Guesty Automated Settlement Dashboard")

with st.sidebar:
    st.header("📊 View Report")
    active_owner = st.selectbox("Switch Active Owner", sorted(st.session_state.owner_db.keys()))
    # ... (Settings logic remains as before)

# --- 4. CALCULATIONS ---
conf = st.session_state.owner_db[active_owner]
owner_pct = conf['pct']
raw_res = get_mock_reservations()
rows = []

# Totals for the footer
t_fare = t_comm = t_exp = t_cln = t_net = 0

for res in raw_res:
    fare, clean = res['Fare'], res['Clean']
    comm = round(fare * (owner_pct / 100), 2)
    net_p = fare + clean
    
    t_fare += fare
    t_comm += comm
    t_exp += res['Exp']
    t_cln += clean
    t_net += net_p
    
    row = {
        "ID": res['ID'], 
        "Date": res['Dates'].strftime("%b %d, %y"), 
        "Accommodation": float(fare), 
        "Commission": float(comm), 
        "Expenses": float(res['Exp']), 
        "Invoice": res['Invoice']
    }
    if conf['type'] == "Draft":
        row["Net Payout"] = float(net_p)
        row["Cleaning"] = float(clean)
    rows.append(row)

# Create Dataframe
df = pd.DataFrame(rows)

# --- 5. ADD TOTAL ROW ---
total_row = {
    "ID": "TOTAL",
    "Date": "",
    "Accommodation": t_fare,
    "Commission": t_comm,
    "Expenses": t_exp,
    "Invoice": ""
}
if conf['type'] == "Draft":
    total_row["Net Payout"] = t_net
    total_row["Cleaning"] = t_cln

df = pd.concat([df, pd.DataFrame([total_row])], ignore_index=True)

# --- 6. RENDER ---
st.header(f"Settlement Report: {active_owner} ({owner_pct}%)")

# Determine column order
if conf['type'] == "Draft":
    final_order = ["ID", "Date", "Net Payout", "Accommodation", "Cleaning", "Commission", "Expenses", "Invoice"]
else:
    final_order = ["ID", "Date", "Accommodation", "Commission", "Expenses", "Invoice"]

# Table Config with Decimal formatting
column_config = {
    "Net Payout": st.column_config.NumberColumn("Net Payout", format="$%.2f"),
    "Accommodation": st.column_config.NumberColumn("Accommodation", format="$%.2f"),
    "Cleaning": st.column_config.NumberColumn("Cleaning", format="$%.2f"),
    "Commission": st.column_config.NumberColumn("Commission", format="$%.2f"),
    "Expenses": st.column_config.NumberColumn("Expenses", format="$%.2f"),
    "Invoice": st.column_config.LinkColumn("Invoice", display_text="🔗 View")
}

st.dataframe(
    df, 
    use_container_width=True, 
    column_config=column_config, 
    column_order=final_order, 
    hide_index=True
)

# Export
csv = df.to_csv(index=False).encode('utf-8')
st.download_button(f"📥 Download CSV Statement", data=csv, file_name=f"{active_owner}_Report.csv", use_container_width=True)
