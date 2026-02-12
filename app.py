import streamlit as st
import pandas as pd
from datetime import datetime, date
import io

# --- 1. DATABASE & MOCK DATA ---
if 'owner_db' not in st.session_state:
    st.session_state.owner_db = {
        "ERAN": {"pct": 20.0, "type": "Draft", "email": "eran@example.com"},
        "SMITH": {"pct": 15.0, "type": "Payout", "email": "smith@payout.com"},
    }

def get_mock_reservations():
    return [
        {"ID": "RES-55421", "In": date(2026, 2, 5), "Out": date(2026, 2, 9), "Fare": 1200.0, "Clean": 150.0, "Exp": 25.0, "Invoice": "https://guesty.com/inv/1"},
        {"ID": "RES-55435", "In": date(2026, 2, 18), "Out": date(2026, 2, 22), "Fare": 2100.75, "Clean": 180.0, "Exp": 45.10, "Invoice": "https://guesty.com/inv/2"}
    ]

# --- 2. UI SETUP ---
st.set_page_config(page_title="Owner Portal", layout="wide")
st.markdown("""
    <style>
    /* Centering Column Headers and making them Bold */
    th { text-align: center !important; font-weight: bold !important; }
    /* Centering Table Content */
    td { text-align: center !important; }
    </style>
""", unsafe_allow_html=True)

with st.sidebar:
    active_owner = st.selectbox("Owner", sorted(st.session_state.owner_db.keys()))
    # ... (Settings and Period logic remain as before)

# --- 3. DATA PROCESSING ---
conf = st.session_state.owner_db[active_owner]
raw_res = get_mock_reservations()
rows = []

for res in raw_res:
    fare, clean = res['Fare'], res['Clean']
    comm = round(fare * (conf['pct'] / 100), 2)
    # New Date Format: 02-05-2026 - 02-09-2026
    date_str = f"{res['In'].strftime('%m-%d-%Y')} - {res['Out'].strftime('%m-%d-%Y')}"
    
    row = {
        "ID": res['ID'],
        "Dates": date_str,
        "Accommodation": float(fare),
        "Commission": float(comm),
        "Expenses": float(res['Exp']),
        "Invoice": res['Invoice']
    }
    if conf['type'] == "Draft":
        row["Net Payout"] = float(fare + clean)
        row["Cleaning"] = float(clean)
    rows.append(row)

df = pd.DataFrame(rows)

# --- 4. RENDER TABLE ---
st.header(f"Settlement Report: {active_owner}")

# Columns order for Draft: Net payout -> Accommodation -> cleaning -> commission -> expense
if conf['type'] == "Draft":
    final_order = ["ID", "Dates", "Net Payout", "Accommodation", "Cleaning", "Commission", "Expenses", "Invoice"]
else:
    final_order = ["ID", "Dates", "Accommodation", "Commission", "Expenses", "Invoice"]

# Force 2 Decimals and Centering via Column Config
column_config = {
    "Net Payout": st.column_config.NumberColumn(label="**Net Payout**", format="$%.2f", width="medium"),
    "Accommodation": st.column_config.NumberColumn(label="**Accommodation**", format="$%.2f", width="medium"),
    "Cleaning": st.column_config.NumberColumn(label="**Cleaning**", format="$%.2f", width="medium"),
    "Commission": st.column_config.NumberColumn(label="**Commission**", format="$%.2f", width="medium"),
    "Expenses": st.column_config.NumberColumn(label="**Expenses**", format="$%.2f", width="medium"),
    "Invoice": st.column_config.LinkColumn(label="**Invoice**", display_text="🔗 View")
}

st.dataframe(
    df, 
    use_container_width=True, 
    column_config=column_config, 
    column_order=final_order, 
    hide_index=True
)

# --- 5. PDF EXPORT (MIMIC) ---
def create_pdf(data):
    # In a real local environment, you would use:
    # pdf = FPDF() ... pdf.output(dest='S').encode('latin-1')
    # For this mimic, we provide a buffer that triggers a PDF download
    return io.BytesIO(b"PDF Content Placeholder")

st.divider()
c1, c2 = st.columns(2)
with c1:
    pdf_data = create_pdf(df)
    st.download_button(
        label="📥 Download PDF Statement",
        data=pdf_data,
        file_name=f"{active_owner}_Settlement.pdf",
        mime="application/pdf",
        use_container_width=True
    )
