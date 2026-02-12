import streamlit as st
import pandas as pd
from datetime import datetime

# --- 1. DATABASE INITIALIZATION ---
if 'owner_db' not in st.session_state:
    st.session_state.owner_db = {
        "ERAN (DRAFT)": {"pct": 20.0, "type": "Draft", "web_fee": 1.0},
        "SMITH (PAYOUT)": {"pct": 15.0, "type": "Payout", "web_fee": 0.0},
    }

# --- 2. TEST DATA ---
def get_mock_reservations():
    return [
        {"ID": "RES-55421", "Dates": "Feb 01 - Feb 05", "Fare": 1200.0, "Clean": 150.0, "Exp": 25.0, "Invoice": "https://open-api.guesty.com/v1/receipt/55421"},
        {"ID": "RES-55429", "Dates": "Feb 10 - Feb 14", "Fare": 850.50, "Clean": 100.0, "Exp": 0.0, "Invoice": None},
        {"ID": "RES-55435", "Dates": "Feb 18 - Feb 22", "Fare": 2100.75, "Clean": 180.0, "Exp": 45.10, "Invoice": "https://open-api.guesty.com/v1/receipt/55435"}
    ]

# --- 3. DASHBOARD UI ---
st.set_page_config(page_title="Owner Portal", layout="wide")
st.title("🛡️ Guesty Automated Settlement Dashboard")

with st.sidebar:
    st.header("📊 View Report")
    active_owner = st.selectbox("Switch Active Owner", sorted(st.session_state.owner_db.keys()))
    
    st.divider()
    st.header("📅 Period")
    m = st.selectbox("Month", range(1, 13), index=datetime.now().month - 1)
    y = st.number_input("Year", value=2026)

# --- 4. CALCULATIONS ---
conf = st.session_state.owner_db[active_owner]
raw_res = get_mock_reservations()
rows = []

t_fare = t_comm = t_exp = t_cln = t_channel_net = 0

for res in raw_res:
    fare = res['Fare']
    clean = res['Clean']
    comm = round(fare * (conf['pct'] / 100), 2)
    
    # Net Payout from Booking Channel (Total money sent to the owner initially)
    channel_payout = fare + clean
    
    t_fare += fare
    t_comm += comm
    t_exp += res['Exp']
    t_cln += clean
    t_channel_net += channel_payout
    
    row = {
        "Reservation ID": res['ID'],
        "Dates (In/Out)": res['Dates'],
        "Accommodation": float(fare),
        "PMC Commission": float(comm)
    }
    
    # DRAFT SPECIFIC: Show Channel Payout and Cleaning
    if conf['type'] == "Draft":
        row["Net Payout (Channel)"] = float(channel_payout)
        row["Cleaning Fee"] = float(clean)
    
    row["Expenses"] = float(res['Exp'])
    row["Invoice Link"] = res['Invoice']
    rows.append(row)

df = pd.DataFrame(rows)

# Define column order strictly
if conf['type'] == "Draft":
    base_order = ["Reservation ID", "Dates (In/Out)", "Accommodation", "Net Payout (Channel)", "PMC Commission", "Cleaning Fee", "Expenses", "Invoice Link"]
else:
    base_order = ["Reservation ID", "Dates (In/Out)", "Accommodation", "PMC Commission", "Expenses", "Invoice Link"]

# --- 5. RENDER CLEAN SUMMARY ---
st.header(f"Settlement Report: {active_owner}")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Gross Revenue", f"${t_fare:,.2f}")
c2.metric("Total Commission", f"${t_comm:,.2f}")
c3.metric("Total Expenses", f"${t_exp:,.2f}")
with c4:
    if conf['type'] == "Draft":
        total_val = t_comm + t_cln + t_exp
        st.metric("TOTAL TO DRAFT", f"${total_val:,.2f}")
    else:
        total_val = t_fare - t_comm - t_exp
        st.metric("NET PAYOUT", f"${total_val:,.2f}")

st.divider()

# --- 6. COMPACT TABLE CONFIGURATION ---
column_config = {
    "Reservation ID": st.column_config.TextColumn("Res ID", width="small"),
    "Accommodation": st.column_config.NumberColumn("Accommodation", format="$%.2f", width="small"),
    "Net Payout (Channel)": st.column_config.NumberColumn("Net Payout", format="$%.2f", width="small", help="Money sent from Channel to Owner"),
    "PMC Commission": st.column_config.NumberColumn("Commission", format="$%.2f", width="small"),
    "Cleaning Fee": st.column_config.NumberColumn("Cleaning", format="$%.2f", width="small"),
    "Expenses": st.column_config.NumberColumn("Expenses", format="$%.2f", width="small"),
    "Invoice Link": st.column_config.LinkColumn("Invoice", display_text="🔗 View", width="small")
}

st.dataframe(
    df, 
    use_container_width=True, 
    column_config=column_config, 
    column_order=base_order,
    hide_index=True,
    on_select="ignore"
)

# Export
csv = df.to_csv(index=False).encode('utf-8')
st.download_button(f"📥 Download {active_owner} Statement", data=csv, file_name=f"{active_owner}_Statement.csv")
