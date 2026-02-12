import streamlit as st
import pandas as pd
from datetime import date

# --- 1. SETUP & PERSISTENCE ---
st.set_page_config(page_title="PMC Statement", layout="wide")

if 'owner_db' not in st.session_state:
    st.session_state.owner_db = {
        "ERAN": {"pct": 12.0, "type": "Draft"},
        "SMITH": {"pct": 15.0, "type": "Payout"},
    }

# Updated Mimic Data to include multiple properties
def get_mimic_data(owner):
    if owner == "ERAN":
        return [
            {"ID": "RES-101", "Property": "Sunset Villa", "Address": "742 Evergreen Terrace", "In": date(2026, 2, 1), "Out": date(2026, 2, 5), "Fare": 1200.0, "Cleaning": 150.0, "Exp": 25.0},
            {"ID": "RES-102", "Property": "Sunset Villa", "Address": "742 Evergreen Terrace", "In": date(2026, 2, 10), "Out": date(2026, 2, 14), "Fare": 800.0, "Cleaning": 150.0, "Exp": 0.0},
            {"ID": "RES-201", "Property": "Beach House", "Address": "123 Ocean Drive", "In": date(2026, 2, 5), "Out": date(2026, 2, 8), "Fare": 2500.0, "Cleaning": 200.0, "Exp": 150.0}
        ]
    return [
        {"ID": "RES-301", "Property": "Mountain Lodge", "Address": "55 Peak Road", "In": date(2026, 2, 1), "Out": date(2026, 2, 5), "Fare": 1500.0, "Cleaning": 100.0, "Exp": 10.0}
    ]

# --- 2. SIDEBAR (Navigation & API) ---
with st.sidebar:
    st.header("📂 Navigation")
    mode = st.radio("View", ["Dashboard", "Taxes"], horizontal=True)
    
    st.divider()
    active_owner = st.selectbox("Switch Active Owner", sorted(st.session_state.owner_db.keys()))
    conf = st.session_state.owner_db[active_owner]
    
    st.divider()
    with st.expander("👤 Manage Owners"):
        # ... (Previous Management Logic)
        pass

    with st.expander("🔌 API Connection"):
        client_id = st.text_input("Client ID", value="0oaszuo22iOg...")
        if st.button("💾 Save & Fetch Data", type="primary"):
            st.cache_data.clear()
            st.rerun()

# --- 3. MAIN CONTENT ---
if mode == "Dashboard":
    st.markdown(f"<div style='text-align: center;'><h1 style='margin-bottom:0;'>PMC Statement</h1><h2 style='color:#FFD700;'>Owner: {active_owner}</h2></div><br>", unsafe_allow_html=True)

    data = get_mimic_data(active_owner)
    df_all = pd.DataFrame(data)
    
    # Grouping by Property Address
    properties = df_all["Address"].unique()

    for addr in properties:
        prop_df = df_all[df_all["Address"] == addr]
        prop_name = prop_df["Property"].iloc[0]
        
        st.subheader(f"🏠 {prop_name}")
        st.caption(f"📍 {addr}")

        rows, v = [], {"gross": 0, "comm": 0, "exp": 0, "cln": 0, "net": 0}
        
        for _, r in prop_df.iterrows():
            f, c, e = r['Fare'], r['Cleaning'], r['Exp']
            cm = round(f * (conf['pct'] / 100), 2)
            rev = f + c if conf['type'] == "Draft" else f
            net = f - c - cm - e if conf['type'] == "Draft" else f - cm - e
            
            v["gross"]+=rev; v["comm"]+=cm; v["cln"]+=c; v["exp"]+=e; v["net"]+=net
            link = f"https://app.guesty.com/reservations/{r['ID']}" if e > 0 else None
            
            rows.append({
                "ID": r['ID'], "Dates": f"{r['In'].strftime('%m/%d')} - {r['Out'].strftime('%m/%d')}", 
                "Gross": rev, "Fare": f, "Clean": c, "Comm": cm, "Exp": e, "Invoice": link, "Net": round(net, 2)
            })

        # Summary for THIS property
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Prop. Gross", f"${v['gross']:,.2f}")
        m2.metric("Prop. Comm", f"${v['comm']:,.2f}")
        m3.metric("Prop. Exp", f"${v['exp']:,.2f}")
        m4.metric("Prop. Net", f"${v['net']:,.2f}")

        # Table for THIS property
        t_cfg = {col: st.column_config.NumberColumn(format="$%.2f") for col in ["Net", "Fare", "Clean", "Comm", "Exp", "Gross"]}
        t_cfg["Invoice"] = st.column_config.LinkColumn("Invoice", display_text="🔗 View")
        
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True, column_config=t_cfg)
        st.divider()

else:
    st.header("⚖️ Tax Compliance Report")
    # Taxes view remains location-based
    st.info(f"Breakdown for {active_owner}")
    st.dataframe(pd.DataFrame([{"State": "FL", "City": "Miami", "County": "Miami-Dade", "Address": "123 Coast Hwy", "Income": 5000.00}]), use_container_width=True, hide_index=True)
