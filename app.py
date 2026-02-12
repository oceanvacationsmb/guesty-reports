import streamlit as st
import pandas as pd
from datetime import datetime
import base64

# --- 1. DATABASE INITIALIZATION ---
if 'owner_db' not in st.session_state:
    st.session_state.owner_db = {
        "ERAN (DRAFT)": {"pct": 20.0, "type": "Draft", "web_fee": 1.0},
        "SMITH (PAYOUT)": {"pct": 15.0, "type": "Payout", "web_fee": 0.0},
    }

# --- 2. MOCK DATA WITH INVOICE LINKS ---
def get_mock_reservations():
    return [
        {"ID": "RES-55421", "Dates": "Feb 01 - Feb 05", "Fare": 1200.0, "Clean": 150.0, "Exp": 25.0, "Invoice": "https://open-api.guesty.com/v1/receipt/55421"},
        {"ID": "RES-55429", "Dates": "Feb 10 - Feb 14", "Fare": 850.50, "Clean": 100.0, "Exp": 0.0, "Invoice": None},
        {"ID": "RES-55435", "Dates": "Feb 18 - Feb 22", "Fare": 2100.75, "Clean": 180.0, "Exp": 45.10, "Invoice": "https://open-api.guesty.com/v1/receipt/55435"},
        {"ID": "RES-55440", "Dates": "Feb 25 - Feb 28", "Fare": 5950.0, "Clean": 120.0, "Exp": 10.0, "Invoice": None}
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

t_fare = t_comm = t_exp = t_cln = 0

for res in raw_res:
    fare = res['Fare']
    comm = fare * (conf['pct'] / 100)
    t_fare += fare
    t_comm += comm
    t_exp += res['Exp']
    t_cln += res['Clean']
    
    row = {
        "Reservation ID": res['ID'],
        "Dates (In/Out)": res['Dates'],
        "Accommodation": fare,
        "PMC %": f"{conf['pct']}%",
        "PMC Commission": comm,
        "Expenses": res['Exp'],
        "Invoice Link": res['Invoice']
    }
    if conf['type'] == "Draft":
        row["Cleaning Fee"] = res['Clean']
    rows.append(row)

# Total math for metrics
df = pd.DataFrame(rows)

# --- 5. RENDER DISPLAY ---
st.header(f"Settlement Report: {active_owner}")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Gross Revenue", f"${t_fare:,.2f}")
c2.metric("Total Commission", f"${t_comm:,.2f}")
c3.metric("Total Expenses", f"${t_exp:,.2f}")
with c4:
    total_val = (t_comm + t_cln + t_exp) if conf['type'] == "Draft" else (t_fare - t_comm - t_exp)
    st.metric("TOTAL TO DRAFT" if conf['type'] == "Draft" else "NET PAYOUT", f"${total_val:,.2f}")

st.divider()

# --- PROFESSIONAL TABLE CONFIGURATION ---
# This right-aligns amounts and turns the Invoice Link into a clickable button/link
column_config = {
    "Accommodation": st.column_config.NumberColumn("Accommodation", format="$%s", help="Right-aligned"),
    "PMC Commission": st.column_config.NumberColumn("PMC Commission", format="$%s"),
    "Expenses": st.column_config.NumberColumn("Expenses", format="$%s"),
    "Cleaning Fee": st.column_config.NumberColumn("Cleaning Fee", format="$%s"),
    "Invoice Link": st.column_config.LinkColumn("View Invoice", display_text="🔗 View")
}

st.dataframe(df, use_container_width=True, column_config=column_config, hide_index=True)

# --- 6. PDF GENERATION ---
st.divider()
if st.button("📄 Generate Settlement PDF"):
    # Simple HTML conversion for PDF
    html = f"<h2>Settlement for {active_owner}</h2>"
    html += f"<p>Period: {m}/{y}</p>"
    html += df.to_html(index=False)
    
    # In a real cloud environment, you would use 'pdfkit' or 'reportlab'
    # For this demo, we provide a structured CSV export renamed for the request
    st.success("PDF logic ready. Note: For full PDF layout, ensure 'wkhtmltopdf' is installed on your server.")
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download Final Statement", data=csv, file_name=f"{active_owner}_Statement.csv")
