import streamlit as st
import pandas as pd
import requests
from datetime import datetime, date

# --- 1. DATABASE & API LOGIC ---
if 'owner_db' not in st.session_state:
    st.session_state.owner_db = {
        "ERAN": {"pct": 20.0, "type": "Draft"},
        "SMITH": {"pct": 15.0, "type": "Payout"},
    }

@st.cache_data(ttl=86400)
def get_guesty_token(cid, csec):
    url = "https://open-api.guesty.com/oauth2/token"
    payload = {"grant_type": "client_credentials", "scope": "open-api", 
               "client_id": cid.strip(), "client_secret": csec.strip()}
    headers = {"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"}
    try:
        res = requests.post(url, data=payload, headers=headers)
        return res.json().get("access_token") if res.status_code == 200 else None
    except: return None

def fetch_live_data(token):
    url = "https://open-api.guesty.com/v1/reservations"
    headers = {"Authorization": f"Bearer {token}"}
    # Pulling up to 100 to ensure we cover the selected month
    params = {"limit": 100, "fields": "confirmationCode money checkIn"}
    try:
        res = requests.get(url, headers=headers, params=params)
        return res.json().get("results", [])
    except: return []

# --- 2. DASHBOARD UI ---
st.set_page_config(page_title="Owner Portal", layout="wide")
st.title("🛡️ Guesty Automated Settlement Dashboard")

with st.sidebar:
    st.header("🔌 Live Link")
    c_id = st.text_input("Client ID", value="0oaszuo22iOg2lk1P5d7")
    c_secret = st.text_input("Client Secret", type="password")
    
    st.divider()
    st.header("📊 View Report")
    active_owner = st.selectbox("Switch Active Owner", sorted(st.session_state.owner_db.keys()))
    
    # --- MONTH PICKER (NAME BASED) ---
    month_names = ["January", "February", "March", "April", "May", "June", 
                   "July", "August", "September", "October", "November", "December"]
    current_month_idx = date.today().month - 1
    selected_month_name = st.selectbox("Select Month", month_names, index=current_month_idx)
    selected_month_num = month_names.index(selected_month_name) + 1

    st.divider()
    st.header("⚙️ Settings")
    with st.expander("Manage Owners"):
        edit_list = list(st.session_state.owner_db.keys())
        target_owner = st.selectbox("Edit/Delete", ["+ Add New"] + edit_list)
        name_val = "" if target_owner == "+ Add New" else target_owner
        name_input = st.text_input("Owner Name", value=name_val).upper().strip()
        
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

# --- 3. CALCULATIONS & FILTERING ---
token = get_guesty_token(c_id, c_secret)

if not token:
    st.info("👋 Enter your Client Secret in the sidebar to sync live data.")
else:
    raw_api_data = fetch_live_data(token)
    conf = st.session_state.owner_db[active_owner]
    rows = []
    t_fare = t_comm = t_exp = t_cln = 0

    for res in raw_api_data:
        check_in_str = res.get("checkIn", "")
        if not check_in_str: continue
        
        # Convert Guesty date string to Python date object
        dt_obj = datetime.strptime(check_in_str[:10], "%Y-%m-%d").date()
        
        # FILTER: Only include if it matches the selected month
        if dt_obj.month == selected_month_num:
            money = res.get("money", {})
            fare = float(money.get("fare", 0))
            clean = float(money.get("cleaningFee", 0))
            
            comm = round(fare * (conf['pct'] / 100), 2)
            t_fare += fare
            t_comm += comm
            t_cln += clean
            
            row = {
                "ID": res.get("confirmationCode"), 
                "Date": dt_obj.strftime("%b %d, %y"), 
                "Accommodation": float(fare), 
                "Commission": float(comm), 
                "Expenses": 0.0, 
                "Invoice": f"https://app.guesty.com/reservations/{res.get('confirmationCode')}"
            }
            if conf['type'] == "Draft":
                row["Net Payout"] = float(fare + clean)
                row["Cleaning"] = float(clean)
            else:
                row["Net Payout"] = float(fare - comm)
            rows.append(row)

    df = pd.DataFrame(rows)

    # --- 4. RENDER ---
    st.header(f"{selected_month_name} Report: {active_owner} ({conf['pct']}%)")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Gross Revenue", f"${t_fare:,.2f}")
    c2.metric(f"Commission", f"${t_comm:,.2f}")
    c3.metric("Total Expenses", f"$0.00")
    with c4:
        total_val = (t_fare + t_cln) if conf['type'] == "Draft" else (t_fare - t_comm)
        st.metric("TOTAL TO DRAFT" if conf['type'] == "Draft" else "NET PAYOUT", f"${total_val:,.2f}")

    st.divider()

    order = ["ID", "Date", "Net Payout", "Accommodation", "Cleaning", "Commission", "Expenses", "Invoice"] if conf['type'] == "Draft" else ["ID", "Date", "Net Payout", "Accommodation", "Commission", "Expenses", "Invoice"]
    
    config = {
        "Net Payout": st.column_config.NumberColumn(format="$%,.2f"),
        "Accommodation": st.column_config.NumberColumn(format="$%,.2f"),
        "Cleaning": st.column_config.NumberColumn(format="$%,.2f"),
        "Commission": st.column_config.NumberColumn(format="$%,.2f"),
        "Expenses": st.column_config.NumberColumn(format="$%,.2f"),
        "Invoice": st.column_config.LinkColumn("Invoice", display_text="🔗 View")
    }

    if not df.empty:
        st.dataframe(df, use_container_width=True, column_config=config, column_order=order, hide_index=True)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(f"📥 Download {selected_month_name} CSV", data=csv, file_name=f"{active_owner}_{selected_month_name}.csv", use_container_width=True)
    else:
        st.warning(f"No reservations found for {selected_month_name}.")
