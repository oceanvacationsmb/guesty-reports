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
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    try:
        res = requests.post(url, data=payload, headers=headers)
        return res.json().get("access_token") if res.status_code == 200 else None
    except: return None

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
    
    st.divider()
    st.header("📅 Select Period")
    report_type = st.selectbox("Quick Select", ["By Month", "Date Range", "Year to Date (YTD)", "Full Year"])
    
    today = date.today()
    # Logic for Date Filtering
    if report_type == "By Month":
        month_names = ["January", "February", "March", "April", "May", "June", 
                       "July", "August", "September", "October", "November", "December"]
        sel_month = st.selectbox("Select Month", month_names, index=today.month-1)
        month_num = month_names.index(sel_month) + 1
        start_date = date(today.year, month_num, 1)
        # Handle end of year wrap-around
        if month_num == 12: end_date = date(today.year, 12, 31)
        else: end_date = date(today.year, month_num + 1, 1)
        
    elif report_type == "Date Range":
        start_date = st.date_input("Start Date", date(today.year, today.month, 1))
        end_date = st.date_input("End Date", today)
        
    elif report_type == "Year to Date (YTD)":
        start_date = date(today.year, 1, 1)
        end_date = today
        
    else: # Full Year
        sel_year = st.selectbox("Select Year", [today.year, today.year-1], index=0)
        start_date = date(sel_year, 1, 1)
        end_date = date(sel_year, 12, 31)

    st.divider()
    st.header("⚙️ Settings")
    with st.expander("Manage Owners"):
        edit_list = list(st.session_state.owner_db.keys())
        target_owner = st.selectbox("Edit/Delete", ["+ Add New"] + edit_list)
        name_input = st.text_input("Owner Name", value="" if target_owner == "+ Add New" else target_owner).upper().strip()
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

# --- 3. CALCULATIONS & LIVE FETCH ---
token = get_guesty_token(c_id, c_secret)

if token:
    # Pulling reservations filtering by checkIn date 
    res_url = "https://open-api.guesty.com/v1/reservations"
    headers = {"Authorization": f"Bearer {token}"}
    # Guesty filter format: {"checkIn":{"$gte":"2026-01-01","$lte":"2026-01-31"}}
    params = {
        "limit": 100, 
        "fields": "confirmationCode money checkIn",
        "filters": f'{{"checkIn":{{"$gte":"{start_date}","$lte":"{end_date}"}}}}'
    }
    
    res = requests.get(res_url, headers=headers, params=params)
    raw_api_data = res.json().get("results", []) if res.status_code == 200 else []
    
    conf = st.session_state.owner_db[active_owner]
    rows = []
    t_fare = t_comm = t_exp = t_cln = 0

    for r in raw_api_data:
        money = r.get("money", {})
        fare = float(money.get("fare", 0))
        clean = float(money.get("cleaningFee", 0))
        comm = round(fare * (conf['pct'] / 100), 2)
        
        t_fare += fare
        t_comm += comm
        t_cln += clean
        
        row = {
            "ID": r.get("confirmationCode"),
            "Date": r.get("checkIn")[:10],
            "Accommodation": fare,
            "Commission": comm,
            "Expenses": 0.0,
            "Invoice": f"https://app.guesty.com/reservations/{r.get('confirmationCode')}"
        }
        if conf['type'] == "Draft":
            row["Net Payout"] = fare + clean
            row["Cleaning"] = clean
        else:
            row["Net Payout"] = fare - comm
        rows.append(row)

    df = pd.DataFrame(rows)

    # --- 4. RENDER (YOUR METRICS & TABLE) ---
    st.header(f"Settlement Report: {active_owner} ({conf['pct']}%)")
    st.caption(f"Showing reservations from {start_date} to {end_date}")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Gross Revenue", f"${t_fare:,.2f}")
    c2.metric(f"Commission", f"${t_comm:,.2f}")
    c3.metric("Total Expenses", f"$0.00")
    with c4:
        total_val = (t_fare + t_cln) if conf['type'] == "Draft" else (t_fare - t_comm)
        st.metric("TOTAL TO DRAFT" if conf['type'] == "Draft" else "NET PAYOUT", f"${total_val:,.2f}")

    st.divider()

    order = ["ID", "Date", "Net Payout", "Accommodation", "Cleaning", "Commission", "Expenses", "Invoice"]
    config = {
        "Net Payout": st.column_config.NumberColumn(format="$%,.2f"),
        "Accommodation": st.column_config.NumberColumn(format="$%,.2f"),
        "Cleaning": st.column_config.NumberColumn(format="$%,.2f"),
        "Commission": st.column_config.NumberColumn(format="$%,.2f"),
        "Expenses": st.column_config.NumberColumn(format="$%,.2f"),
        "Invoice": st.column_config.LinkColumn(display_text="🔗 View")
    }

    if not df.empty:
        st.dataframe(df, use_container_width=True, column_config=config, column_order=order, hide_index=True)
        st.download_button("📥 Download Statement", df.to_csv(index=False), file_name=f"{active_owner}_Report.csv", use_container_width=True)
    else:
        st.warning("No data found for this period.")
else:
    st.info("👋 Please enter your API Secret in the sidebar.")
