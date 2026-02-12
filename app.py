import streamlit as st
import pandas as pd
from datetime import date

# --- 1. DATABASE & INITIALIZATION ---
if 'owner_db' not in st.session_state:
    st.session_state.owner_db = {
        "ERAN": {"pct": 12.0, "type": "Draft"},
        "SMITH": {"pct": 15.0, "type": "Payout"},
    }

# --- 2. DATA LOADERS (Mimic for now) ---
def get_mimic_reservations():
    return [
        {"ID": "RES-55421", "In": date(2026, 2, 1), "Out": date(2026, 2, 5), "Fare": 1200.0, "Clean": 150.0, "Exp": 25.0},
        {"ID": "RES-55429", "In": date(2026, 2, 10), "Out": date(2026, 2, 14), "Fare": 850.50, "Clean": 100.0, "Exp": 0.0},
        {"ID": "RES-55435", "In": date(2026, 2, 18), "Out": date(2026, 2, 22), "Fare": 2100.75, "Clean": 180.0, "Exp": 45.10}
    ]

def get_mimic_tax_data():
    return [
        {"State": "FL", "City": "Miami", "County": "Miami-Dade", "Property": "Ocean View Villa", "Address": "123 Coast Hwy", "Income": 5000.00},
        {"State": "FL", "City": "Miami", "County": "Miami-Dade", "Property": "City Loft", "Address": "456 Brickell Ave", "Income": 3200.00},
        {"State": "CO", "City": "Aspen", "County": "Pitkin", "Property": "Mountain Retreat", "Address": "789 Peak Rd", "Income": 4500.00}
    ]

# --- 3. SIDEBAR NAVIGATION & SETTINGS ---
st.set_page_config(page_title="PMC Statement", layout="wide")

with st.sidebar:
    st.header("📂 Navigation")
    view_mode = st.radio("Choose View:", ["Statement Dashboard", "Taxes"])
    
    st.divider()
    st.header("📊 Filter Report")
    active_owner = st.selectbox("Switch Active Owner", sorted(st.session_state.owner_db.keys()))
    conf = st.session_state.owner_db[active_owner]
    
    st.divider()
    with st.expander("⚙️ Manage Owners"):
        # (Previous owner management logic remains here)
        pass
        
    with st.expander("🔌 Connection Settings"):
        st.text_input("Client ID", value="0oaszuo22iOg2lk1P5d7")
        st.text_input("Client Secret", type="password")

# --- 4. VIEW LOGIC: TAXES ---
if view_mode == "Taxes":
    st.markdown(f"<div style='text-align: center;'><h1 style='margin-bottom: 0;'>Taxes Compliance Report</h1><h2 style='color: #FFD700;'>Owner: {active_owner}</h2></div><br>", unsafe_allow_html=True)
    
    if conf['type'] != "Payout":
        st.warning("⚠️ The Taxes report is only generated for owners on 'Payout' settings.")
    else:
        df_tax = pd.DataFrame(get_mimic_tax_data())
        
        # Summary Metrics
        t1, t2 = st.columns(2)
        t1.metric("Total Taxable Income", f"${df_tax['Income'].sum():,.2f}")
        t2.metric("Total Jurisdictions", len(df_tax['County'].unique()))
        
        st.divider()
        st.dataframe(
            df_tax, 
            use_container_width=True, 
            column_config={"Income": st.column_config.NumberColumn(format="$%.2f")},
            column_order=["State", "City", "County", "Property", "Address", "Income"],
            hide_index=True
        )

# --- 5. VIEW LOGIC: STATEMENT DASHBOARD ---
else:
    st.markdown(f"<div style='text-align: center;'><h1 style='margin-bottom: 0;'>PMC Statement</h1><h2 style='color: #FFD700;'>Reservation Report: {active_owner}</h2></div><br>", unsafe_allow_html=True)
    
    # Calculation logic for Statement
    rows = []
    t_gross = t_comm = t_exp = t_cln = t_net_payout = 0
    source_data = get_mimic_reservations()
    owner_pct = conf['pct']

    for r in source_data:
        fare, clean, exp = r['Fare'], r['Clean'], r['Exp']
        comm = round(fare * (owner_pct / 100), 2)
        
        if conf['type'] == "Draft":
            gross_rev, net_payout = fare + clean, fare - clean - comm - exp
        else:
            gross_rev, net_payout = fare, fare - comm - exp

        t_gross += gross_rev; t_comm += comm; t_cln += clean; t_exp += exp; t_net_payout += net_payout
        rows.append({"ID": r['ID'], "Check-in/Out": f"{r['In'].strftime('%m/%d')} - {r['Out'].strftime('%m/%d')}", "Gross Revenue": gross_rev, "Accommodation": fare, "Cleaning": clean, "Commission": comm, "Expenses": exp, "Invoice": f"https://app.guesty.com/reservations/{r['ID']}", "Net Payout": round(net_payout, 2)})

    # Summary Display
    if conf['type'] == "Payout":
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Gross Revenue", f"${t_gross:,.2f}")
        c2.metric(f"Commission ({owner_pct}%)", f"${t_comm:,.2f}")
        c3.metric("Total Expenses", f"${t_exp:,.2f}")
        c4.metric("NET PAYOUT", f"${t_net_payout:,.2f}")
        order = ["ID", "Check-in/Out", "Accommodation", "Commission", "Expenses", "Invoice", "Net Payout"]
    else:
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Gross Revenue", f"${t_gross:,.2f}")
        c2.metric(f"Commission ({owner_pct}%)", f"${t_comm:,.2f}")
        c3.metric("Cleaning Total", f"${t_cln:,.2f}")
        c4.metric("Total Expenses", f"${t_exp:,.2f}")
        c5.metric("DRAFT AMOUNT", f"${(t_comm + t_cln + t_exp):,.2f}")
        order = ["ID", "Check-in/Out", "Gross Revenue", "Accommodation", "Cleaning", "Commission", "Expenses", "Invoice", "Net Payout"]

    st.divider()
    config = {col: st.column_config.NumberColumn(format="$%.2f") for col in ["Net Payout", "Accommodation", "Cleaning", "Commission", "Expenses", "Gross Revenue"]}
    config["Invoice"] = st.column_config.LinkColumn(display_text="🔗 View")
    st.dataframe(pd.DataFrame(rows), use_container_width=True, column_config=config, column_order=order, hide_index=True)
