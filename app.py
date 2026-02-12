import streamlit as st
import pandas as pd
from datetime import datetime

# --- 1. DATABASE INITIALIZATION ---
if 'owner_db' not in st.session_state:
    st.session_state.owner_db = {
        "ERAN": {"pct": 20.0, "type": "Draft"},
        "SMITH": {"pct": 15.0, "type": "Payout"},
    }

# --- 2. TEST DATA ---
def get_mock_reservations():
    return [
        {"ID": "RES-55421", "Dates": "Feb 01 - Feb 05", "Fare": 1200.0, "Clean": 150.0, "Exp": 25.0, "Invoice": "https://open-api.guesty.com/v1/receipt/55421"},
        {"ID": "RES-55429", "Dates": "Feb 10 - Feb 14", "Fare": 850.50, "Clean": 100.0, "Exp": 0.0, "Invoice": None},
        {"ID": "RES-55435", "Dates": "Feb 18 - Feb 22", "Fare": 2100.75, "Clean": 180.0, "Exp": 45.10, "Invoice": "https://open-api.guesty.com/v1/receipt/55435"}
    ]

# --- 3. DASHBOARD UI ---
st.set_page_config(page_title="Owner Portal", layout="wide")
st.title("🛡️ Guesty Automated Settlement Dashboard")

with st.sidebar:
    st.header("📊 View Report")
    active_owner = st.selectbox("Switch Active Owner", sorted(st.session_state.owner_db.keys()))
    
    st.divider()
    st.header("📅 Period")
    m = st.selectbox("Month", range(1, 13), index=datetime.now().month - 1)
    y = st.number_input("Year", value=2026)

    st.divider()
    st.header("⚙️ Settings")
    with st.expander("Manage Owners"):
        edit_list = list(st.session_state.owner_db.keys())
        target_owner = st.selectbox("Select Owner to Edit/Delete", ["+ Add New"] + edit_list)
        
        # Strip "(DRAFT)" from names automatically
        raw_name = st.text_input("Owner Name", value="" if target_owner == "+ Add New" else target_owner)
        name_input = raw_name.upper().replace("(DRAFT)", "").replace("DRAFT", "").strip()
        
        current_pct = st.session_state.owner_db.get(target_owner, {"pct": 20.0})["pct"] if target_owner != "+ Add New" else 20.0
        current_type = st.session_state.owner_db.get(target_owner, {"type": "Draft"})["type"] if target_owner != "+ Add New" else "Draft"

        upd_pct = st.number_input("Commission %", 0.0, 100.0, float(current_pct))
        upd_type = st.selectbox("Settlement Style", ["Draft", "Payout"], index=0 if current_type == "Draft" else 1)
        
        col_save, col_del = st.columns(2)
        with col_save:
            if st.button("💾 Save Settings"):
                st.session_state.owner_db[name_input] = {"pct": upd_pct, "type": upd_type}
                st.rerun()
        
        with col_del:
            # Delete option only available for existing owners
            if target_owner != "+ Add New":
                if st.button("🗑️ Delete Owner", type="primary"):
                    del st.session_state.owner_db[target_owner]
                    st.rerun()

# --- 4. CALCULATIONS ---
conf = st.session_state.owner_db[active_owner]
owner_pct = conf['pct']
raw_res = get_mock_reservations()
rows = []

t_fare = t_comm = t_exp = t_cln = t_channel_net = 0

for res in raw_res:
    fare = res['Fare']
    clean = res['Clean']
    comm = round(fare * (owner_pct / 100), 2)
    channel_payout = fare + clean
    
    t_fare += fare
    t_comm += comm
    t_exp += res['Exp']
    t_cln += clean
    t_channel_net += channel_payout
    
    row = {
        "Reservation ID": res['ID'],
        "Dates (In/Out)": res['Dates'],
        "Accommodation": float(fare),
        "Commission": float(comm),
        "Expenses": float(res['Exp']),
        "Invoice": res['Invoice']
    }
    
    if conf['type'] == "Draft":
        row["Net Payout"] = float(channel_payout)
        row["Cleaning"] = float(clean)
    
    rows.append(row)

df = pd.DataFrame(rows)

# --- 5. CLEAN SUMMARY DISPLAY ---
st.header(f"Settlement Report: {active_owner} ({owner_pct}%)")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Gross Revenue", f"${t_fare:,.2f}")
c2.metric(f"Commission ({owner_pct}%)", f"${t_comm:,.2f}")
c3.metric("Total Expenses", f"${t_exp:,.2f}")

with c4:
    if conf['type'] == "Draft":
        total_val = t_comm + t_cln + t_exp
        st.metric("TOTAL TO DRAFT", f"${total_val:,.2f}")
    else:
        total_val = t_fare - t_comm - t_exp
        st.metric("NET PAYOUT", f"${total_val:,.2f}")

st.divider()

# --- 6. TABLE ORDER & CONFIG ---
# Order for Draft: Net payout -> Accommodation -> cleaning -> commission -> expense
if conf['type'] == "Draft":
    final_order = ["Reservation ID", "Dates (In/Out)", "Net Payout", "Accommodation", "Cleaning", "Commission", "Expenses", "Invoice"]
else:
    final_order = ["Reservation ID", "Dates (In/Out)", "Accommodation", "Commission", "Expenses", "Invoice"]

column_config = {
    "Net Payout": st.column_config.NumberColumn("Net Payout", format="$%.2f", width="small"),
    "Accommodation": st.column_config.NumberColumn("Accommodation", format="$%.2f", width="small"),
    "Cleaning": st.column_config.NumberColumn("Cleaning", format="$%.2f", width="small"),
    "Commission": st.column_config.NumberColumn("Commission", format="$%.2f", width="small"),
    "Expenses": st.column_config.NumberColumn("Expenses", format="$%.2f", width="small"),
    "Invoice": st.column_config.LinkColumn("Invoice", display_text="🔗 View", width="small")
}

st.dataframe(
    df, 
    use_container_width=True, 
    column_config=column_config, 
    column_order=final_order, 
    hide_index=True,
    on_select="ignore"
)

# Export (JPG-style CSV per preference)
csv = df.to_csv(index=False).encode('utf-8')
st.download_button(f"📥 Download {active_owner} Statement", data=csv, file_name=f"{active_owner}_Statement.csv")
