import streamlit as st
import requests
import json
import time
import base64

TOPIC = "ashiq_webhook_test_2026_xyz"
URL = f"https://ntfy.sh/{TOPIC}/json?poll=1"

st.set_page_config(page_title="Webhook Inspector Pro", layout="wide")

if 'clear_before' not in st.session_state:
    st.session_state.clear_before = 0

st.title("🪝 Webhook & Auth Inspector")

try:
    r = requests.get(URL, timeout=10)
    if r.status_code == 200:
        messages = [json.loads(line) for line in r.text.strip().split('\n') if line]
        valid_messages = [m for m in messages if
                          m.get('event') == 'message' and m.get('time', 0) > st.session_state.clear_before]

        if not valid_messages:
            st.info("Waiting for webhooks (Authenticated or Basic)...")
        else:
            for msg in reversed(valid_messages):
                # ntfy stores headers in the 'attachment' or we can pass them in the message
                # For this setup, we assume you send headers as part of your test script
                try:
                    full_data = json.loads(msg.get('message'))
                    payload = full_data.get('payload', full_data)
                    headers = full_data.get('headers', {})

                    auth_header = headers.get('Authorization', 'None')
                    auth_type = "🔓 Unauthenticated"

                    # Decode Basic Auth if present
                    if auth_header.startswith('Basic '):
                        encoded_credentials = auth_header.split(' ')[1]
                        decoded = base64.b64decode(encoded_credentials).decode('utf-8')
                        auth_type = f"🔐 Basic Auth: {decoded}"

                    with st.expander(
                            f"{auth_type} | Received: {time.strftime('%H:%M:%S', time.localtime(msg.get('time')))}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write("**Payload**")
                            st.json(payload)
                        with col2:
                            st.write("**Headers**")
                            st.json(headers)
                except:
                    st.write(msg.get('message'))

    time.sleep(5)
    st.rerun()
except Exception as e:
    st.error(f"Error: {e}")