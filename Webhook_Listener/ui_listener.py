import streamlit as st
import requests
import json
import time
import base64

# --- CONFIGURATION ---
TOPIC = "ashiq_webhook_test_2026_xyz"
URL = f"https://ntfy.sh/{TOPIC}/json?poll=1"
# Set your expected credentials here
EXPECTED_USER = "admin"
EXPECTED_PASS = "secret123"

st.set_page_config(page_title="Webhook Auth Validator", layout="wide")

if 'clear_before' not in st.session_state:
    st.session_state.clear_before = 0

st.title("🔐 Webhook Authentication Validator")

# --- SIDEBAR ---
with st.sidebar:
    st.header("Validation Rules")
    st.info(f"Expected User: {EXPECTED_USER}\n\nExpected Pass: {EXPECTED_PASS}")
    if st.button("🗑️ Clear View"):
        st.session_state.clear_before = time.time()
        st.rerun()

# --- MAIN LOGIC ---
try:
    r = requests.get(URL, timeout=10)
    if r.status_code == 200:
        messages = [json.loads(line) for line in r.text.strip().split('\n') if line]
        valid_messages = [m for m in messages if
                          m.get('event') == 'message' and m.get('time', 0) > st.session_state.clear_before]

        if not valid_messages:
            st.info("Waiting for webhooks...")
        else:
            for msg in reversed(valid_messages):
                try:
                    full_data = json.loads(msg.get('message'))
                    payload = full_data.get('payload', full_data)
                    headers = full_data.get('headers', {})

                    auth_header = headers.get('Authorization', '')

                    # Logic for Validation
                    status_text = "🔓 No Auth"
                    status_color = "secondary"  # Gray

                    if auth_header.startswith('Basic '):
                        try:
                            encoded = auth_header.split(' ')[1]
                            decoded = base64.b64decode(encoded).decode('utf-8')
                            u, p = decoded.split(':')

                            if u == EXPECTED_USER and p == EXPECTED_PASS:
                                status_text = f"✅ Authorized: {u}"
                                status_color = "success"  # Green
                            else:
                                status_text = f"❌ Unauthorized Attempt: {u}"
                                status_color = "error"  # Red
                        except:
                            status_text = "⚠️ Malformed Auth Header"
                            status_color = "warning"

                    # UI Display
                    with st.expander(
                            f"{status_text} | Time: {time.strftime('%H:%M:%S', time.localtime(msg.get('time')))}"):
                        if status_color == "success":
                            st.success("Authentication Verified")
                        elif status_color == "error":
                            st.error("Authentication Failed: Credentials Mismatch")

                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown("**Body Payload**")
                            st.json(payload)
                        with col2:
                            st.markdown("**Decoded Headers**")
                            st.json(headers)
                except:
                    st.write("Non-JSON Data Received:", msg.get('message'))

    time.sleep(5)
    st.rerun()
except Exception as e:
    st.error(f"Error connecting to data source: {e}")