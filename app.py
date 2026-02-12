import streamlit as st
import pandas as pd
from datetime import datetime, date
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders

# --- 1. SETTINGS & DATABASE ---
if 'owner_db' not in st.session_state:
    st.session_state.owner_db = {
        "ERAN": {"pct": 20.0, "type": "Draft", "email": "eran@example.com"},
        "SMITH": {"pct": 15.0, "type": "Payout", "email": "smith@example.com"},
    }

# --- EMAIL CONFIG (Use Environment Variables for safety) ---
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "your-system@email.com"
SENDER_PASSWORD = "your-app-password" # Not your login password!

# --- 2. PDF GENERATION LOGIC ---
def send_owner_email(owner_name, owner_email, dataframe, period_label):
    try:
        # 1. Create Email Container
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = owner_email
        msg['Subject'] = f"Settlement Report - {owner_name} - {period_label}"
        
        body = f"Hello {owner_name},\n\nPlease find your settlement report for {period_label} attached.\n\nBest regards,\nManagement Team"
        msg.attach(MIMEText(body, 'plain'))

        # 2. Convert Dataframe to CSV (Simple PDF Alternative for now)
        # To send a real PDF, we'd use 'pdfkit.from_string' here.
        filename = f"{owner_name}_Report.csv"
        attachment = dataframe.to_csv(index=False).encode('utf-8')

        part = MIMEBase('application', 'octet-stream')
        part.set_payload(attachment)
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f"attachment; filename= {filename}")
        msg.attach(part)

        # 3. Send Email
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        st.error(f"Failed to send email: {e}")
        return False

# --- 3. UI RENDER (Add to your existing Sidebar/Summary) ---
# (Assuming 'df' and 'period_label' are defined from your previous logic)

st.divider()
col_btn, col_status = st.columns([1, 2])

with col_btn:
    if st.button("📧 Send To Owner", use_container_width=True):
        email_addr = st.session_state.owner_db[active_owner].get("email")
        if email_addr:
            with st.spinner(f"Sending to {email_addr}..."):
                success = send_owner_email(active_owner, email_addr, df, period_label)
                if success:
                    st.success(f"Report sent successfully to {active_owner}!")
        else:
            st.error("No email address found for this owner in Guesty/Settings.")
