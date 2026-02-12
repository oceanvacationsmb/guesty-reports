import streamlit as st
import pandas as pd
import requests
from datetime import date, timedelta

# --- 1. SETUP & SESSION STATE ---
st.set_page_config(page_title="PMC MASTER SUITE", layout="wide")

if 'owner_db' not in st.session_state:
    st.session_state.owner_db = {
        "ERAN": {"pct": 12.0, "type": "DRAFT"},
        "SMITH": {"pct": 15.0, "type": "PAYOUT"},
    }

# --- 2. API ENGINE (GUESTY) ---
def get_guesty_token(client_id, client_secret):
    """Fetch the Bearer token from Guesty OAuth2."""
    url = "https://open-api.guesty.com/oauth2/token"
    payload = {"clientId": client_id, "clientSecret": client_secret}
    try:
        response = requests.post(url, json=payload, timeout=10)
        return response.json().get("access_token")
    except Exception as e:
        st.error(f"AUTHENTICATION FAILED: {e}")
        return None

def fetch_guesty_reservations(token, start, end):
    """Fetch real reservations from Guesty Open API."""
    url = "https://open-api.guesty.com/v1/reservations"
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    params = {
        "createdAfter": start.strftime("%Y-%m-%d"),
        "createdBefore": end.strftime("%Y-%m-%d"),
        "limit": 100
    }
    try:
        response = requests.get(url, headers=headers, params=params, timeout=15)
        # In a real scenario, we'd map Guesty fields to our internal format
        return response.json().get("results", [])
    except Exception as e:
        st.sidebar.error(f"DATA FETCH FAILED: {e}")
        return []

# --- 3. SIDEBAR CONTROLS ---
with st.sidebar:
    st.header("📂 NAVIGATION")
    mode = st.radio("SELECT REPORT TYPE", ["OWNER STATEMENTS", "PMC REPORT"], index=0)
    
    st.divider()
    st.header("🔌 API CONNECTION")
    c_id = st.text_input("CLIENT ID", type="password", help="Found in Guesty > Integrations > Open API")
    c_sec = st.text_input("CLIENT SECRET", type="password")
    
    if st.button("🔄 FETCH REAL DATA", type="primary", use_container_width=True):
        token = get_guesty_token(c_id, c_sec)
        if token:
            st.session_state.api_token = token
            st.success("CONNECTED TO GUESTY")
            st.rerun()

    st.divider()
    st.header("📅 PERIOD & OWNER")
    active_owner = st.selectbox("ACTIVE OWNER", sorted(st.session_state.owner_db.keys()))
    report_context = st.selectbox("CONTEXT", ["BY MONTH", "YTD", "CUSTOM"], index=0)
    
    # Simple date logic for 2026
    start_date, end_date = date(2026, 2, 1), date(2026, 2, 28)

    with st.expander("👤 OWNER SETTINGS"):
        target = st.selectbox("EDIT", list(st.session_state.owner_db.keys()))
        n_pct = st.number_input("COMM %", 0.0, 100.0, float(st.session_state.owner_db[target]["pct"]))
        if st.button("💾 SAVE"):
            st.session_state.owner_db[target]["pct"] = n_pct
            st.rerun()

# --- 4. DATA PROCESSING ---
# Use real API data if available, otherwise fallback to Mimic for demo
raw_data = []
if 'api_token' in st.session_state:
    raw_data = fetch_guesty_reservations(st.session_state.api_token, start_date, end_date)

# Fallback/Mimic Logic for testing (Matches your previous logic)
if not raw_data:
    if active_owner == "ERAN":
        raw_data = [
            {"ID": "RES-101", "Fare": 1200.0, "Cln": 150.0, "Exp": 25.0},
            {"ID": "RES-201", "Fare": 2500.0, "Cln": 200.0, "Exp": 150.0}
        ]
    else:
        raw_data = [{"ID": "RES-301", "Fare": 1500.0, "Cln": 100.0, "Exp": 10.0}]

# --- 5. REPORT RENDERING ---
conf = st.session_state.owner_db[active_owner]
is_draft = conf['type'] == "DRAFT"

rows = []
for r in raw_data:
    f, c, e = r.get('Fare', 0), r.get('Cln', 0), r.get('Exp', 0)
    cm = round(f * (conf['pct'] / 100), 2)
    
    if is_draft:
        top_rev = f + c
        net_rev = top_rev - c - cm - e # GROSS - CLN - PMC - EXP
        row = {"ID": r['ID'], "GROSS PAYOUT": top_rev, "CLEANING": c, "PMC COMM": cm, "EXPENSED": e, "NET REVENUE": net_rev}
    else:
        net_rev = f - cm - e # ACC - PMC - EXP
        row = {"ID": r['ID'], "ACCOMMODATION": f, "PMC COMM": cm, "EXPENSED": e, "NET REVENUE": net_rev}
    rows.append(row)

df = pd.DataFrame(rows)

# Display Metrics
st.title(f"OWNER STATEMENT: {active_owner}")
m1, m2, m3, m4 = st.columns(4)
total_rev = df[df.columns[1]].sum() # Second column is always the top-line revenue
m1.metric("TOTAL REVENUE", f"${total_rev:,.2f}")
m2.metric("TOTAL COMM", f"${df['PMC COMM'].sum():,.2f}")
m3.metric("TOTAL EXPENSES", f"${df['EXPENSED'].sum():,.2f}")
m4.metric("NET TO OWNER", f"${df['NET REVENUE'].sum():,.2f}", delta_color="normal")

st.divider()
st.dataframe(df, use_container_width=True, hide_index=True)
