import streamlit as st
import pandas as pd
from datetime import datetime, date

# --- 1. DATABASE ---
if 'owner_db' not in st.session_state:
    st.session_state.owner_db = {
        "ERAN": {"pct": 20.0, "type": "Draft"},
        "SMITH": {"pct": 20.0, "type": "Payout"},
    }

# --- 2. MOCK DATA ---
def get_mock_reservations():
    return [
        {"ID": "RES-55421", "Dates": date(2026, 2, 1), "Fare": 1200.0, "Clean": 150.0, "Exp": 25.0, "Invoice": "https://guesty.com/inv/1"},
        {"ID": "RES-55429", "Dates": date(2026, 2, 10), "Fare": 850.50, "Clean": 100.0, "Exp": 0.0, "Invoice": None},
        {"ID": "RES-55435", "Dates": date(2026, 2, 18), "Fare": 2100.75, "Clean": 180.0, "Exp": 45.10, "Invoice": "https://guesty.com/inv/2"}
    ]

# --- 3. UI SETUP & CSS ---
st.set_page_config(page_title="Owner Portal", layout="wide")

# CSS to make headers Bold and Centered
st.markdown("""
    <style>
    /* Target the table headers */
    [data-testid="stTable"] th, [data-testid="stDataFrame"] th {
        text-align: center !important;
        font-weight: bold !important;
        background-color: #1e1e1e !important;
    }
    /* Center the cell content */
    [data-testid="stDataFrame"] div[role="gridcell"] {
        text-align: center !important;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🛡️ Guesty Automated Settlement Dashboard")

with st.sidebar:
    st.header("📊 View Report")
    active_owner = st.selectbox("Switch Active Owner", sorted(st.session_state.owner_db.keys()))
    
    st.divider()
    # Period and Settings logic removed for brevity but remains in your local version
    # ... 

# --- 4. CALCULATIONS (Rounding fix for red arrows) ---
conf = st.session_state.owner_db[active_owner]
owner_pct = conf['pct']
raw_res = get_mock_reservations()
rows = []
t_fare = t_comm = t_exp = t_cln = 0

for res in raw_res:
    fare = round(float(res['Fare']), 2)
    clean = round(float(res['Clean']), 2)
    # Strict rounding to prevent the "red arrow" overflow
    comm = round(fare * (owner_pct / 100), 2)
    
    t_fare += fare
    t_comm += comm
    t_exp += round(float(res['Exp']), 2)
    t_cln += clean
    
    row = {
        "Reservation ID": res['ID'], 
        "Dates": res['Dates'].strftime("%b %d, %y"), 
        "Accommodation": fare, 
        "PMC Commission": comm, 
        "Expenses": round(float(res['Exp']), 2), 
        "Invoice": res['Invoice']
    }
    if conf['type'] == "Draft":
        row["Net Payout"] = round(fare + clean, 2)
        row["Cleaning Fee"] = clean
    rows.append(row)

df = pd.DataFrame(rows)

# --- 5. RENDER ---
st.header(f"Settlement Report: {active_owner} ({owner_pct}%)")

# Summary Metrics
c1, c2, c3, c4 = st.columns(4)
c1.metric("Gross Revenue", f"${t_fare:,.2f}")
c2.metric(f"Commission ({owner_pct}%)", f"${t_comm:,.2f}")
c3.metric("Total Expenses", f"${t_exp:,.2f}")
with c4:
    total_val = (t_comm + t_cln + t_exp) if conf['type'] == "Draft" else (t_fare - t_comm - t_exp)
    st.metric("TOTAL TO DRAFT" if conf['type'] == "Draft" else "NET PAYOUT", f"${round(total_val, 2):,.2f}")

st.divider()

# Column order and Bold Labeling
if conf['type'] == "Draft":
    final_order = ["Reservation ID", "Dates", "Net Payout", "Accommodation", "Cleaning Fee", "PMC Commission", "Expenses", "Invoice"]
else:
    final_order = ["Reservation ID", "Dates", "Accommodation", "PMC Commission", "Expenses", "Invoice"]

column_config = {
    "Net Payout": st.column_config.NumberColumn("Net Payout", format="$%,.2f"),
    "Accommodation": st.column_config.NumberColumn("Accommodation", format="$%,.2f"),
    "Cleaning Fee": st.column_config.NumberColumn("Cleaning Fee", format="$%,.2f"),
    "PMC Commission": st.column_config.NumberColumn("PMC Commission", format="$%,.2f"),
    "Expenses": st.column_config.NumberColumn("Expenses", format="$%,.2f"),
    "Invoice": st.column_config.LinkColumn("Invoice", display_text="🔗 View")
}

# st.dataframe with on_select="ignore" locks the table
st.dataframe(
    df, 
    use_container_width=True, 
    column_config=column_config, 
    column_order=final_order, 
    hide_index=True,
    on_select="ignore" 
)

# Export
csv = df.to_csv(index=False).encode('utf-8')
st.download_button(f"📥 Download CSV Statement", data=csv, file_name=f"{active_owner}_Report.csv", use_container_width=True)
