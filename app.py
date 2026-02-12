import streamlit as st
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io

# --- 1. SETTINGS & STYLING ---
st.set_page_config(page_title="Guesty Owner Statements", layout="wide")
st.title("📊 Guesty Owner Statement Generator")

# --- 2. THE BUSINESS RULES ---
def calculate_statement(owner, accommodation, cleaning, expenses, is_website_booking):
    # Eran's Special Rules
    if "ERAN" in owner.upper():
        rate = 0.12
        web_fee = (accommodation * 0.01) if is_website_booking else 0
        pmc = accommodation * rate
        total_deductions = pmc + cleaning + expenses + web_fee
        # Eran's logic: He gets the payout, we draft the fees
        net_owner = (accommodation + cleaning) - total_deductions 
        return {
            "rate_label": "12%",
            "pmc": pmc,
            "web_fee": web_fee,
            "deductions": total_deductions,
            "net": net_owner,
            "type": "DRAFT FROM OWNER"
        }
    # Standard Rules (Yen, etc.)
    else:
        rate = 0.15
        pmc = accommodation * rate
        total_deductions = pmc + cleaning + expenses
        # Others: We send them what's left
        net_owner = accommodation - total_deductions
        return {
            "rate_label": "15%",
            "pmc": pmc,
            "web_fee": 0,
            "deductions": total_deductions,
            "net": net_owner,
            "type": "PAYOUT TO OWNER"
        }

# --- 3. THE WEBSITE INTERFACE ---
st.subheader("Manual Data Entry (Testing Mode)")
col1, col2 = st.columns(2)

with col1:
    owner = st.selectbox("Select Owner", ["ERAN MARON", "YEN FRENCH"])
    acc_amt = st.number_input("Accommodation Amount ($)", value=1005.00)
    clean_amt = st.number_input("Cleaning Fee ($)", value=500.00)

with col2:
    exp_amt = st.number_input("Expenses ($)", value=55.00)
    is_web = st.checkbox("Is this a Website Booking? (Adds 1% for Eran)")
    inv_link = st.text_input("Expense Invoice Link", "https://guesty.com/your-invoice-link")

# Calculate Results
results = calculate_statement(owner, acc_amt, clean_amt, exp_amt, is_web)

# --- 4. DISPLAY THE SUMMARY ---
st.write("---")
st.header(f"Summary for {owner}")
c_acc, c_pmc, c_web, c_net = st.columns(4)

c_acc.metric("Total Accommodation", f"${acc_amt:,.2f}")
c_pmc.metric(f"PMC ({results['rate_label']})", f"-${results['pmc']:,.2f}")
if owner == "ERAN MARON":
    c_web.metric("Website Fee (1%)", f"-${results['web_fee']:,.2f}")
c_net.metric("NET OWNER REVENUE", f"${results['net']:,.2f}")

st.warning(f"Note: This is a **{results['type']}** model.")

# --- 5. PDF GENERATOR ---
def create_pdf():
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, 750, f"Owner Statement: {owner}")
    
    p.setFont("Helvetica", 12)
    p.drawString(50, 720, f"Accommodation: ${acc_amt:,.2f}")
    p.drawString(50, 700, f"Cleaning Fee: ${clean_amt:,.2f}")
    p.drawString(50, 680, f"Expenses: ${exp_amt:,.2f}")
    p.drawString(50, 660, f"Total Deductions: -${results['deductions']:,.2f}")
    
    p.line(50, 640, 550, 640)
    p.drawString(50, 620, f"NET OWNER REVENUE: ${results['net']:,.2f}")
    
    p.setFont("Helvetica-Oblique", 10)
    p.drawString(50, 580, f"Expense Invoice Link: {inv_link}")
    
    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer

st.download_button(
    label="Download PDF Statement",
    data=create_pdf(),
    file_name=f"Statement_{owner}.pdf",
    mime="application/pdf"
)
