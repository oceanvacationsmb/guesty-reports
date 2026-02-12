import streamlit as st
import pandas as pd
from datetime import datetime, date
from fpdf import FPDF
import io

# --- 1. DATABASE & MOCK DATA ---
if 'owner_db' not in st.session_state:
    st.session_state.owner_db = {
        "ERAN": {"pct": 20.0, "type": "Draft"},
        "SMITH": {"pct": 15.0, "type": "Payout"},
    }

def get_mock_reservations():
    return [
        {"ID": "RES-55421", "Dates": date(2026, 2, 1), "Fare": 1200.0, "Clean": 150.0, "Exp": 25.0, "Invoice": "https://guesty.com/inv/1"},
        {"ID": "RES-55429", "Dates": date(2026, 2, 10), "Fare": 850.50, "Clean": 100.0, "Exp": 0.0, "Invoice": None},
        {"ID": "RES-55435", "Dates": date(2026, 2, 18), "Fare": 2100.75, "Clean": 180.0, "Exp": 45.10, "Invoice": "https://guesty.com/inv/2"}
    ]

# --- 2. PDF GENERATION ENGINE ---
def generate_pdf(df, owner_name, owner_pct, total_val, style):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    
    # Header
    pdf.cell(0, 10, f"Settlement Report: {owner_name}", ln=True, align='C')
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 10, f"Generated on: {date.today().strftime('%b %d, %Y')} | Commission: {owner_pct}%", ln=True, align='C')
    pdf.ln(5)

    # Table Setup
    cols = df.columns.tolist()
    # Remove Invoice link for PDF table clarity, or keep as text
    if "Invoice" in cols: cols.remove("Invoice")
    
    # Auto-calculate column widths
    pdf.set_font("Arial", "B", 8)
    col_width = (pdf.w - 20) / len(cols) 

    # Render Header Row
    for col in cols:
        pdf.cell(col_width, 8, col, border=1, align='C')
    pdf.ln()

    # Render Data Rows
    pdf.set_font("Arial", "", 8)
    for _, row in df.iterrows():
        for col in cols:
            val = row[col]
            # Format numbers with commas for the PDF
            if isinstance(val, (int, float)):
                text = f"${val:,.2f}"
            else:
                text = str(val)
            pdf.cell(col_width, 8, text, border=1, align='C')
        pdf.ln()

    # Footer Total
    pdf.ln(5)
    pdf.set_font("Arial", "B", 10)
    label = "TOTAL TO DRAFT" if style == "Draft" else "NET PAYOUT"
    pdf.cell(0, 10, f"{label}: ${total_val:,.2f}", ln=True, align='R')
    
    return pdf.output(dest='S') # Return as byte string

# --- 3. DASHBOARD UI ---
st.set_page_config(page_title="Owner Portal", layout="wide")
active_owner = st.sidebar.selectbox("Active Owner", sorted(st.session_state.owner_db.keys()))

# --- 4. CALCULATIONS ---
conf = st.session_state.owner_db[active_owner]
raw_res = get_mock_reservations()
rows = []
t_fare = t_comm = t_exp = t_cln = 0

for res in raw_res:
    fare, clean = res['Fare'], res['Clean']
    comm = round(fare * (conf['pct'] / 100), 2)
    t_fare += fare ; t_comm += comm ; t_exp += res['Exp'] ; t_cln += clean
    
    row = {
        "ID": res['ID'], 
        "Date": res['Dates'].strftime("%b %d, %y"), 
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
total_val = (t_comm + t_cln + t_exp) if conf['type'] == "Draft" else (t_fare - t_comm - t_exp)

# --- 5. RENDER ---
st.header(f"Settlement Report: {active_owner}")

# Table Config
if conf['type'] == "Draft":
    final_order = ["ID", "Date", "Net Payout", "Accommodation", "Cleaning", "Commission", "Expenses", "Invoice"]
else:
    final_order = ["ID", "Date", "Accommodation", "Commission", "Expenses", "Invoice"]

column_config = {
    "Net Payout": st.column_config.NumberColumn(format="$%,.2f"),
    "Accommodation": st.column_config.NumberColumn(format="$%,.2f"),
    "Cleaning": st.column_config.NumberColumn(format="$%,.2f"),
    "Commission": st.column_config.NumberColumn(format="$%,.2f"),
    "Expenses": st.column_config.NumberColumn(format="$%,.2f"),
}

st.dataframe(df, use_container_width=True, column_config=column_config, column_order=final_order, hide_index=True)

# PDF Export Button
pdf_bytes = generate_pdf(df[final_order], active_owner, conf['pct'], total_val, conf['type'])

st.download_button(
    label="📥 Download PDF Statement",
    data=pdf_bytes,
    file_name=f"{active_owner}_Settlement_{date.today()}.pdf",
    mime="application/pdf",
    use_container_width=True
)
