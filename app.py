import streamlit as st
import pandas as pd
from datetime import datetime, date

# --- 1. DATABASE ---
if 'owner_db' not in st.session_state:
    st.session_state.owner_db = {
        "ERAN": {"pct": 20.0, "type": "Draft"},
        "SMITH": {"pct": 15.0, "type": "Payout"},
    }

# --- 2. MOCK DATA ---
def get_mock_reservations():
    return [
        {"ID": "RES-55421", "Dates": date(2026, 2, 1), "Fare": 1200.0, "Clean": 150.0, "Exp": 25.0, "Invoice": "https://guesty.com/inv/1"},
        {"ID": "RES-55429", "Dates": date(2026, 2, 10), "Fare": 850.50, "Clean": 100.0, "Exp": 0.0, "Invoice": None},
        {"ID": "RES-55435", "Dates": date(2026, 2, 18), "Fare": 2100.75, "Clean": 180.0, "Exp": 45.10, "Invoice": "https://guesty.com/inv/2"}
    ]

# --- 3. DASHBOARD UI ---
st.set_page_config(page_title="Owner Portal", layout="wide")
st.title("🛡️ Guesty Automated Settlement Dashboard")

with st.sidebar:
    st.header("📊 View Report")
    active_owner = st.selectbox("Switch Active Owner", sorted(st.session_state.owner_db.keys()))
    
    st.divider()
    st.header("📅 Select Period")
    report_type = st.selectbox("Quick Select", ["By Month", "Date Range", "Year to Date (YTD)", "Full Year"])
    
    today = date.today()
    start_date, end_date = date(today.year, today.month, 1), today

    st.divider()
    st.header("⚙️ Settings")
    with st.expander("Manage Owners"):
        edit_list = list(st.session_state.owner_db.keys())
        target_owner = st.selectbox("Edit/Delete", ["+ Add New"] + edit_list)
        
        name_val = "" if target_owner == "+ Add New" else target_owner
        name_input = st.text_input("Owner Name", value=name_val).upper().replace("DRAFT", "").strip()
        
        current_pct = st.session_state.owner_db.get(target_owner, {"pct": 20.0})["pct"]
        current_type = st.session_state.owner_db.get(target_owner, {"type": "Draft"})["type"]

        upd_pct = st.number_input("Commission %", 0.0, 100.0, float(current_pct))
        upd_type = st.selectbox("Settlement Style", ["Draft", "Payout"], index=0 if current_type == "Draft" else 1)
        
        c_save, c_del = st.columns(2)
        if c_save.button("💾 Save"):
            st.session_state.owner_db[name_input] = {"pct": upd_pct, "type": upd_type}
            st.rerun()
        if target_owner != "+ Add New" and c_del.button("🗑️ Delete", type="primary"):
            del st.session_state.owner_db[target_owner]
            st.rerun()

# --- 4. CALCULATIONS ---
conf = st.session_state.owner_db[active_owner]
owner_pct = conf['pct']
raw_res = get_mock_reservations()
rows = []
t_fare = t_comm = t_exp = t_cln = 0

for res in raw_res:
    fare, clean = res['Fare'], res['Clean']
    comm = round(fare * (owner_pct / 100), 2)
    t_fare += fare
    t_comm += comm
    t_exp += res['Exp']
    t_cln += clean
    
    row = {
        "MOTEK": res['ID'], 
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

# --- 5. RENDER ---
st.header(f"Settlement Report: {active_owner} ({owner_pct}%)")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Gross Revenue", f"${t_fare:,.2f}")
c2.metric(f"Commission ({owner_pct}%)", f"${t_comm:,.2f}")
c3.metric("Total Expenses", f"${t_exp:,.2f}")
with c4:
    total_val = (t_comm + t_cln + t_exp) if conf['type'] == "Draft" else (t_fare - t_comm - t_exp)
    st.metric("TOTAL TO DRAFT" if conf['type'] == "Draft" else "NET PAYOUT", f"${total_val:,.2f}")

st.divider()

if conf['type'] == "Draft":
    final_order = ["ID", "Date", "Net Payout", "Accommodation", "Cleaning", "Commission", "Expenses", "Invoice"]
else:
    final_order = ["ID", "Date", "Accommodation", "Commission", "Expenses", "Invoice"]

column_config = {
    "Net Payout": st.column_config.NumberColumn("Net Payout", format="$%.2f"),
    "Accommodation": st.column_config.NumberColumn("Accommodation", format="$%.2f"),
    "Cleaning": st.column_config.NumberColumn("Cleaning", format="$%.2f"),
    "Commission": st.column_config.NumberColumn("Commission", format="$%.2f"),
    "Expenses": st.column_config.NumberColumn("Expenses", format="$%.2f"),
    "Invoice": st.column_config.LinkColumn("Invoice", display_text="🔗 View")
}

st.dataframe(df, use_container_width=True, column_config=column_config, column_order=final_order, hide_index=True)

# Export
csv = df.to_csv(index=False).encode('utf-8')
st.download_button(f"📥 Download CSV Statement", data=csv, file_name=f"{active_owner}_Report.csv", use_container_width=True)
