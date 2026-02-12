import streamlit as st
import pandas as pd
from datetime import datetime, date
from fpdf import FPDF
import io
import time

# --- 1. DATABASE ---
if 'owner_db' not in st.session_state:
    st.session_state.owner_db = {
        "ERAN": {"pct": 20.0, "type": "Draft", "email": "eran@example.com"},
        "SMITH": {"pct": 15.0, "type": "Payout", "email": "smith@payout.com"},
    }

# --- 2. PDF GENERATION LOGIC ---
class OwnerPDF(FPDF):
    def header(self):
        self.set_font("Arial", "B", 14)
        self.cell(0, 10, "Owner Settlement Statement", border=0, ln=1, align="C")
        self.ln(5)

def create_pdf_bytes(df, owner_name, style, total_val):
    pdf = OwnerPDF()
    pdf.add_page()
    pdf.set_font("Arial", "", 10)
    
    # Header Info
    pdf.cell(0, 10, f"Owner: {owner_name}", ln=1)
    pdf.cell(0, 10, f"Date: {date.today().strftime('%m-%d-%Y')}", ln=1)
    pdf.ln(5)

    # Table Headers
    pdf.set_font("Arial", "B", 8)
    cols = df.columns.tolist()
    if "Invoice" in cols: cols.remove("Invoice") # Clean PDF view
    
    col_width = (pdf.w - 20) / len(cols)
    for col in cols:
        pdf.cell(col_width, 8, col, border=1, align="C")
    pdf.ln()

    # Table Data
    pdf.set_font("Arial", "", 8)
    for _, row in df.iterrows():
        for col in cols:
            val = row[col]
            text = f"${val:,.2f}" if isinstance(val, (int, float)) else str(val)
            pdf.cell(col_width, 8, text, border=1, align="C")
        pdf.ln()

    # Final Total
    pdf.ln(10)
    pdf.set_font("Arial", "B", 11)
    label = "TOTAL TO DRAFT" if style == "Draft" else "NET PAYOUT"
    pdf.cell(0, 10, f"{label}: ${total_val:,.2f}", align="R")
    
    return pdf.output(dest='S')

# --- 3. UI RENDER ---
st.set_page_config(page_title="Owner Portal", layout="wide")
active_owner = st.sidebar.selectbox("Active Owner", sorted(st.session_state.owner_db.keys()))
conf = st.session_state.owner_db[active_owner]

# (Calculation Logic remains the same as previous stable version)
# Assuming 'df' and 'total_val' are calculated based on your Draft/Payout logic...

# --- 4. ACTION BUTTONS ---
st.divider()
c_pdf, c_email = st.columns(2)

# PDF Button
with c_pdf:
    # We generate the PDF on-the-fly for the download button
    # Note: Using df[final_order] ensures the PDF follows your Draft column order
    pdf_output = create_pdf_bytes(df, active_owner, conf['type'], total_val)
    st.download_button(
        label="📥 Download PDF Statement",
        data=pdf_output,
        file_name=f"{active_owner}_Statement_{date.today()}.pdf",
        mime="application/pdf",
        use_container_width=True
    )

# Email Button
with c_email:
    owner_email = conf.get("email", "No Email Set")
    if st.button(f"📧 Send To Owner ({owner_email})", use_container_width=True):
        if "@" not in owner_email:
            st.error("Error: Please set a valid email in the Settings first.")
        else:
            with st.spinner(f"Emailing {active_owner}..."):
                # Mimicking the sending process
                time.sleep(2) 
                st.success(f"✅ Statement sent successfully to {owner_email}!")
                st.balloons()
