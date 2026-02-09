import streamlit as st
import requests
import json
import time
import base64

# --- CONFIGURATION ---
TOPIC = "wh_receiver_8824"  # Replace 8824 with any 4 random digits
URL = f"https://ntfy.sh/{TOPIC}/json?poll=1"

# --- UI SETUP ---
# Restoring your original branding
st.set_page_config(page_title="Webhook Tester", layout="wide")
st.title("Webhook Tester")

if 'clear_before' not in st.session_state:
    st.session_state.clear_before = 0

# --- SIDEBAR ---
with st.sidebar:
    st.header("Controls")
    if st.button("🗑️ Clear Logs"):
        st.session_state.clear_before = time.time()
        st.rerun()
    st.write("---")
    refresh_speed = st.slider("Refresh rate (seconds)", 2, 20, 5)

with st.sidebar:
    st.header("Endpoint")
    st.code(f"https://ntfy.sh/{TOPIC}", language="text")
    st.caption("Copy this URL into your application's webhook settings.")

# --- MAIN LOGIC ---
try:
    r = requests.get(URL, timeout=10)
    if r.status_code == 200:
        messages = [json.loads(line) for line in r.text.strip().split('\n') if line]
        valid_messages = [m for m in messages if
                          m.get('event') == 'message' and m.get('time', 0) > st.session_state.clear_before]

        if not valid_messages:
            st.info("Waiting for webhooks... Send a POST request to ntfy.sh/" + TOPIC)
        else:
            for msg in reversed(valid_messages):
                try:
                    full_data = json.loads(msg.get('message'))
                    payload = full_data.get('payload', full_data)
                    headers = full_data.get('headers', {})

                    # Determine Auth Status for the label
                    auth_header = headers.get('Authorization', '')
                    label_suffix = ""

                    if auth_header.startswith('Basic '):
                        label_suffix = " (🔒 Auth Found)"

                    timestamp = time.strftime('%H:%M:%S', time.localtime(msg.get('time')))

                    with st.expander(f"📥 Webhook received at {timestamp}{label_suffix}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown("**Body**")
                            st.json(payload)
                        with col2:
                            st.markdown("**Headers**")
                            st.json(headers)

                            # Small decoding section only if Auth is present
                            if auth_header.startswith('Basic '):
                                try:
                                    encoded = auth_header.split(' ')[1]
                                    decoded = base64.b64decode(encoded).decode('utf-8')
                                    st.info(f"Decoded Credentials: `{decoded}`")
                                except:
                                    pass
                except:
                    st.write("Raw Message:", msg.get('message'))

    time.sleep(refresh_speed)
    st.rerun()
except Exception as e:
    st.error(f"Connection Error: {e}")