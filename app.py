import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import calendar
import json

# --- 1. GUESTY API CONNECTION (FRESH TOKEN EVERY TIME) ---
def get_guesty_token():
    url = "https://open-api.guesty.com/oauth2/token"
    
    if "CLIENT_ID" not in st.secrets or "CLIENT_SECRET" not in st.secrets:
        st.error("Missing API Keys in Streamlit Secrets!")
        return None
        
    payload = {
        "grant_type": "client_credentials",
        "client_id": st.secrets["CLIENT_ID"].strip(),
        "client_secret": st.secrets["CLIENT_SECRET"].strip()
    }
    
    # We use a standard header for the token request
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    
    response = requests.post(url, data=payload, headers=headers)
    
    if response.status_code != 200:
        st.error(f"Guesty rejected the keys: {response.text}")
        return None
        
    return response.json().get("access_token")

def fetch_data(month, year):
    token = get_guesty_token()
    if not token: return []
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }
    
    # Calculate month dates
    start_date = f"{year}-{month:02d}-01"
    last_day = calendar.monthrange(year, month)[1]
    end_date = f"{year}-{month:02d}-{last_day}"
    
    # Guesty's preferred filter format
    filters = [
        {"field": "checkInDate", "operator": "$gte", "value": start_date},
        {"field": "checkInDate", "operator": "$lte", "value": end_date}
    ]
    
    # Build the URL with the filter
    filter_param = json.dumps(filters)
    url = f"https://open-api.guesty.com/v1/reservations?limit=100&filters={filter_param}"
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        st.error(f"Could not pull data: {response.status_code}")
        return []
        
    return response.json().get("results", [])

# --- 2. THE WEBSITE LAYOUT ---
st.set_page_config(page_title="Guesty Report System", layout="wide")
st.title("🏡 Guesty Automated Monthly Report")

col1, col2, col3 = st.columns(3)
with col1:
    owner = st.selectbox("Select Owner", ["ERAN MARON", "YEN FRENCH"])
with col2:
    m = st.selectbox
