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
def generate_pdf(owner_name, start_date, end_date, summary, prop_breakdown):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    
    # Title & Header
    pdf.cell(190, 10, "OWNER STATEMENT", ln=True, align='C')
    pdf.set_font("Arial", 'B', 14)
    pdf.set_text_color(255, 215, 0) # Gold color for name
    pdf.cell(190, 10, f"{owner_name}", ln=True, align='C')
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", '', 10)
    pdf.cell(190, 8, f"{start_date} TO {end_date}", ln=True, align='C')
    pdf.ln(10)

    # Metrics Summary Section
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(190, 10, "EXECUTIVE SUMMARY", ln=True)
    pdf.set_font("Arial", '', 10)
    
    # Create metric "boxes"
    col_width = 190 / len(summary)
    for label in summary.keys():
        pdf.cell(col_width, 8, label, border=1, align='C')
    pdf.ln()
    for val in summary.values():
        pdf.cell(col_width, 8, f"${val:,.2f}", border=1, align='C')
    pdf.ln(15)

    # Property Details Section
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(190, 10, "PROPERTY BREAKDOWN", ln=True)
    
    for prop, rows in prop_breakdown.items():
        pdf.ln(2)
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(190, 8, f"Property: {prop}", ln=True)
        
        # Table Headers
        pdf.set_font("Arial", 'B', 8)
        pdf.set_fill_color(240, 240, 240)
        cols = list(rows[0].keys())
        w = 190 / len(cols)
        for col in cols:
            pdf.cell(w, 8, col, border=1, fill=True)
        pdf.ln()
        
        # Table Rows
        pdf.set_font("Arial", '', 8)
        for row in rows:
            for val in row.values():
                display_val = f"${val:,.2f}" if isinstance(val, (int, float)) else str(val)
                pdf.cell(w, 7, display_val, border=1)
            pdf.ln()
        pdf.ln(5)

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
    if report_type == "BY MONTH":
        c1, c2 = st.columns(2)
        months = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
        sel_month = c1.selectbox("MONTH", months, index=today.month-1)
        sel_year = c2.selectbox("YEAR", [2026, 2025], index=0)
        start_date = date(sel_year, months.index(sel_month)+1, 1)
        end_date = (start_date + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    elif report_type == "BETWEEN DATES":
        c1, c2 = st.columns(2)
        start_date = c1.date_input("START DATE", today - timedelta(days=30))
        end_date = c2.date_input("END DATE", today)
    else:
        start_date, end_date = date(today.year, 1, 1), today

    st.divider()
    with st.expander("👤 OWNER MANAGEMENT", expanded=False):
        target = st.selectbox("EDIT/DELETE", ["+ ADD NEW"] + list(st.session_state.owner_db.keys()))
        curr = st.session_state.owner_db.get(target, {"pct": 12.0, "type": "DRAFT"})
        n_name = st.text_input("NAME", value="" if target == "+ ADD NEW" else target).upper().strip()
        n_pct = st.number_input("COMM %", 0.0, 100.0, float(curr["pct"]))
        n_style = st.selectbox("STYLE", ["DRAFT", "PAYOUT"], index=0 if curr["type"] == "DRAFT" else 1)
        if st.button("💾 SAVE SETTINGS"):
            st.session_state.owner_db[n_name] = {"pct": n_pct, "type": n_style}
            st.rerun()

    with st.expander("🔌 API CONNECTION", expanded=True):
        st.text_input("CLIENT ID", value="0oaszuo22iOg...", type="password")
        st.text_input("CLIENT SECRET (KEY)", value="", type="password") 
        if st.button("🔄 SAVE & RUN", type="primary", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

# --- 4. CALCULATION ENGINE ---
all_owners_data = []
total_ov2 = 0
current_owner_summary = {}
current_owner_props = {}

for name, settings in st.session_state.owner_db.items():
    owner_data = get_mimic_data(name)
    o_comm, o_cln, o_exp, o_fare = 0, 0, 0, 0
    prop_rows = {}
    
    for r in owner_data:
        f, c, e = r['Fare'], r['Cln'], r['Exp']
        cm = round(f * (settings['pct'] / 100), 2)
        o_comm += cm; o_cln += c; o_exp += e; o_fare += f
        
        # Prepare table row
        if name == active_owner:
            stay = f"{r['In'].strftime('%m/%d')} - {r['Out'].strftime('%m/%d')}"
            if settings['type'] == "DRAFT":
                row = {"ID": r['ID'], "STAY": stay, "GROSS": f+c, "CLN": c, "COMM": cm, "EXP": e, "NET": (f+c)-c-cm-e}
            else:
                row = {"ID": r['ID'], "STAY": stay, "ACC": f, "COMM": cm, "EXP": e, "NET": f-cm-e}
            
            if r['Prop'] not in prop_rows: prop_rows[r['Prop']] = []
            prop_rows[r['Prop']].append(row)
    
    is_draft = settings['type'] == "DRAFT"
    top_rev = o_fare + o_cln if is_draft else o_fare
    net_rev = (o_fare + o_cln) - o_cln - o_comm - o_exp if is_draft else o_fare - o_comm - o_exp
    
    summary = {
        "REVENUE": top_rev,
        "PMC COMM": o_comm,
        "EXPENSED": o_exp,
        "NET REVENUE": net_rev
    }
    if is_draft: summary["DRAFT AMT"] = o_comm + o_cln + o_exp
    else: summary["ACH TOTAL"] = net_rev

    if name == active_owner:
        current_owner_summary = summary
        current_owner_props = prop_rows

    all_owners_data.append({"OWNER": name, "TYPE": settings['type'], "NET": net_rev, "COMM": o_comm})
    total_ov2 += o_comm

# --- 5. MAIN CONTENT ---
if mode == "STATEMENTS":
    col_t, col_btn = st.columns([4, 1])
    with col_t:
        st.markdown(f"<div style='text-align: center;'><h1>OWNER STATEMENT</h1><h2 style='color:#FFD700;'>{active_owner}</h2><p>{start_date} TO {end_date}</p></div>", unsafe_allow_html=True)
    
    with col_btn:
        pdf_data = generate_pdf(active_owner, start_date, end_date, current_owner_summary, current_owner_props)
        st.download_button(
            label="📥 EXPORT TO PDF",
            data=pdf_data,
            file_name=f"Statement_{active_owner}_{sel_month if 'sel_month' in locals() else 'Report'}.pdf",
            mime="application/pdf"
        )

    st.divider()
    # Metrics display
    cols = st.columns(len(current_owner_summary))
    for i, (k, v) in enumerate(current_owner_summary.items()):
        cols[i].metric(k, f"${v:,.2f}")

    st.divider()
    for prop, rows in current_owner_props.items():
        st.subheader(f"🏠 {prop}")
        st.table(pd.DataFrame(rows)) # Using st.table for better visual alignment with PDF

elif mode == "PMC REPORT":
    st.title("PMC INTERNAL CONTROL REPORT")
    st.metric("TRANSFER TO OV2", f"${total_ov2:,.2f}")
    st.dataframe(pd.DataFrame(all_owners_data), use_container_width=True, hide_index=True)
