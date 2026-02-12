import streamlit as st
import pandas as pd
from datetime import date, timedelta
from fpdf import FPDF
import io

# --- 1. SETUP ---
st.set_page_config(page_title="PMC MASTER SUITE", layout="wide")

if 'owner_db' not in st.session_state:
    st.session_state.owner_db = {
        "ERAN": {"pct": 12.0, "type": "DRAFT"},
        "SMITH": {"pct": 15.0, "type": "PAYOUT"},
    }

# --- 2. PDF GENERATION ENGINE ---
def create_pdf(owner_name, start_date, end_date, summary, property_data, conf_type):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    
    # Header
    pdf.cell(190, 10, "OWNER STATEMENT", ln=True, align='C')
    pdf.set_font("Arial", '', 12)
    pdf.cell(190, 10, f"OWNER: {owner_name}", ln=True, align='C')
    pdf.cell(190, 10, f"PERIOD: {start_date} TO {end_date}", ln=True, align='C')
    pdf.ln(10)
    
    # Summary Table
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Arial", 'B', 10)
    for key in summary.keys():
        pdf.cell(38, 10, key, border=1, align='C', fill=True)
    pdf.ln()
    pdf.set_font("Arial", '', 10)
    for val in summary.values():
        pdf.cell(38, 10, f"${val:,.2f}", border=1, align='C')
    pdf.ln(20)
    
    # Property Details
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 10, "PROPERTY BREAKDOWN", ln=True)
    pdf.ln(2)
    
    pdf.set_font("Arial", '', 9)
    for prop_name, reservations in property_data.items():
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(190, 8, f"Property: {prop_name}", ln=True)
        pdf.set_font("Arial", '', 9)
        
        # Table Header based on type
        headers = ["ID", "STAY", "FARE", "CLN", "COMM", "EXP", "NET"]
        col_widths = [25, 40, 25, 25, 25, 25, 25]
        
        for i, h in enumerate(headers):
            pdf.cell(col_widths[i], 8, h, border=1, fill=True)
        pdf.ln()
        
        for res in reservations:
            pdf.cell(25, 8, res['ID'], border=1)
            pdf.cell(40, 8, res['STAY'], border=1)
            pdf.cell(25, 8, f"{res['FARE']:.2f}", border=1)
            pdf.cell(25, 8, f"{res['CLN']:.2f}", border=1)
            pdf.cell(25, 8, f"{res['COMM']:.2f}", border=1)
            pdf.cell(25, 8, f"{res['EXP']:.2f}", border=1)
            pdf.cell(25, 8, f"{res['NET']:.2f}", border=1)
        pdf.ln(10)

    return pdf.output(dest='S').encode('latin-1')

def get_mimic_data(owner):
    if owner == "ERAN":
        return [
            {"ID": "RES-101", "Prop": "SUNSET VILLA", "Addr": "742 EVERGREEN TERRACE", "In": date(2026, 2, 1), "Out": date(2026, 2, 5), "Fare": 1200.0, "Cln": 150.0, "Exp": 25.0},
            {"ID": "RES-201", "Prop": "BEACH HOUSE", "Addr": "123 OCEAN DRIVE", "In": date(2026, 2, 5), "Out": date(2026, 2, 8), "Fare": 2500.0, "Cln": 200.0, "Exp": 150.0}
        ]
    return [{"ID": "RES-301", "Prop": "MOUNTAIN LODGE", "Addr": "55 PEAK ROAD", "In": date(2026, 2, 1), "Out": date(2026, 2, 5), "Fare": 1500.0, "Cln": 100.0, "Exp": 10.0}]

# --- 3. SIDEBAR ---
with st.sidebar:
    st.header("📂 NAVIGATION")
    mode = st.radio("SELECT REPORT TYPE", ["STATEMENTS", "TAX REPORT", "PMC REPORT"], index=0)
    
    st.divider()
    active_owner = st.selectbox("SWITCH ACTIVE OWNER", sorted(st.session_state.owner_db.keys()))
    conf = st.session_state.owner_db[active_owner]
    
    st.divider()
    st.header("📅 SELECT PERIOD")
    report_type = st.selectbox("CONTEXT", ["BY MONTH", "FULL YEAR", "YTD", "BETWEEN DATES"], index=0)
    
    today = date.today()
    start_date, end_date = date(2026, 2, 1), date(2026, 2, 28)

    with st.expander("🔌 API CONNECTION", expanded=True):
        st.text_input("CLIENT ID", value="0oaszuo22iOg...", type="password")
        st.text_input("CLIENT SECRET (KEY)", type="password") 
        st.button("🔄 SAVE & RUN", type="primary", use_container_width=True)

# --- 4. CALCULATION ENGINE ---
owner_res = get_mimic_data(active_owner)
o_comm, o_cln, o_exp, o_fare = 0, 0, 0, 0
prop_breakdown = {}

for r in owner_res:
    f, c, e = r['Fare'], r['Cln'], r['Exp']
    cm = round(f * (conf['pct'] / 100), 2)
    o_comm += cm; o_cln += c; o
