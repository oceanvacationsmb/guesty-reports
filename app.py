import streamlit as st
import pandas as pd
from datetime import datetime, date
import time

# --- 1. DATABASE (Added Email field) ---
if 'owner_db' not in st.session_state:
    st.session_state.owner_db = {
        "ERAN": {"pct": 20.0, "type": "Draft", "email": "eran@example.com"},
        "SMITH": {"pct": 15.0, "type": "Payout", "email": "smith@payout.com"},
    }

# --- 2. MOCK DATA & CALCULATIONS (Abbreviated for focus) ---
def get_mock_reservations():
    return [
        {"ID": "RES-55421", "Dates": date(2026, 2, 5), "Fare": 1200.0, "Clean": 150.0, "Exp": 25.0, "Invoice": "https://link"},
        {"ID": "RES-55435", "Dates": date(2026, 2, 18), "Fare": 2100.75, "Clean": 180.0, "Exp": 45.10, "Invoice": "https://link"}
    ]

# UI Setup
st.set_page_config(page_title="Owner Portal", layout="wide")
active_owner = st.sidebar.selectbox("Owner", sorted(st.session_state.owner_db.keys()))
conf = st.session_state.owner_db[active_owner]

# Process Data
raw_res = get_mock_reservations()
rows = []
for res in raw_res:
    fare, comm = res['Fare'], round(res['Fare'] * (conf['pct'] / 100), 2)
    row = {"ID": res['ID'], "Accommodation": float(fare), "Commission": float(comm), "Expenses": float(res['Exp'])}
    if conf['type'] == "Draft":
        row["Net Payout"] = float(fare + res['Clean'])
    rows.append(row)
df = pd.DataFrame(rows)

# --- 3. RENDER TABLE ---
st.header(f"Settlement Report: {active_owner}")
st.dataframe(df, use_container_width=True, hide_index=True)

# --- 4. EMAIL BUTTON LOGIC ---
st.divider()
st.subheader("📬 Send Report")

# Get email from DB
target_email = conf.get("email", "No Email Found")

c1, c2 = st.columns([1, 3])
with c1:
    if st.button(f"📧 Email to {active_owner}", use_container_width=True):
        if "@" not in target_email:
            st.error("Invalid email address. Please update in settings.")
        else:
            with st.spinner(f"Sending report to {target_email}..."):
                # Simulating network delay
                time.sleep(2) 
                st.success(f"✅ Report sent successfully to {target_email}!")
                st.balloons()

with c2:
    st.info(f"**Recipient:** {target_email} | **Format:** PDF Attachment (Simulated)")

# --- 5. SETTINGS (To manage emails) ---
with st.sidebar.expander("⚙️ Manage Owner Emails"):
    for owner, data in st.session_state.owner_db.items():
        new_email = st.text_input(f"Email for {owner}", value=data['email'], key=f"mail_{owner}")
        st.session_state.owner_db[owner]['email'] = new_email
