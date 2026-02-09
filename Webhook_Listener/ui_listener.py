import streamlit as st
import requests
import json
import time
import base64

# --- CONFIGURATION ---
TOPIC = "wh_receiver_8824"  # Professional topic name
URL = f"https://ntfy.sh/{TOPIC}/json?poll=1"

# --- UI SETUP ---
st.set_page_config(page_title="Webhook Tester", layout="wide")
st.title("🪝 Webhook Tester")

# Initialize session state for clearing logs
if 'clear_before' not in st.session_state:
    st.session_state.clear_before = 0

# --- DATA FETCHING ---
try:
    r = requests.get(URL, timeout=10)
    messages = []
    if r.status_code == 200:
        raw_lines = r.text.strip().split('\n')
        messages = [json.loads(line) for line in raw_lines if line]

    # Filter only messages that arrived AFTER the last "Clear" click
    valid_messages = [m for m in messages if
                      m.get('event') == 'message' and m.get('time', 0) > st.session_state.clear_before]

    # --- MAIN BODY HEADER ---
    # Placing the URL and Metrics front and center
    col_url, col_meta = st.columns([2, 1])

    with col_url:
        st.subheader("Target Endpoint")
        st.code(f"https://ntfy.sh/{TOPIC}", language="text")
        st.caption("🚀 Configure your application to send POST requests to this URL.")

    with col_meta:
        st.subheader("Stats")
        if valid_messages:
            last_msg_time = valid_messages[-1].get('time')
            seconds_ago = int(time.time() - last_msg_time)

            m1, m2 = st.columns(2)
            m1.metric("Requests", len(valid_messages))
            m2.metric("Last Ping", f"{seconds_ago}s ago")
        else:
            st.metric("Requests", 0)
            st.caption("Awaiting first signal...")

    st.markdown("---")  # Horizontal separator

    # --- SIDEBAR (Settings Only) ---
    with st.sidebar:
        st.header("Settings")
        if st.button("🗑️ Clear Logs"):
            st.session_state.clear_before = time.time()
            st.rerun()
        st.write("")
        refresh_speed = st.slider("Refresh rate (seconds)", 2, 20, 5)

    # --- LOGS DISPLAY ---
    if not valid_messages:
        st.info("No webhooks found in current session.")
    else:
        for msg in reversed(valid_messages):
            try:
                full_data = json.loads(msg.get('message'))
                # Handle nested payloads or raw data
                payload = full_data.get('payload', full_data)
                headers = full_data.get('headers', {})

                auth_header = headers.get('Authorization', '')
                lock_icon = " 🔒" if auth_header.startswith('Basic ') else ""
                timestamp = time.strftime('%H:%M:%S', time.localtime(msg.get('time')))

                with st.expander(f"📥 Received at {timestamp}{lock_icon}"):
                    c1, c2 = st.columns(2)
                    with c1:
                        st.markdown("**JSON Body**")
                        st.json(payload)
                    with c2:
                        st.markdown("**HTTP Headers**")
                        st.json(headers)
                        # Automatic Basic Auth Decoding
                        if auth_header.startswith('Basic '):
                            try:
                                encoded = auth_header.split(' ')[1]
                                decoded = base64.b64decode(encoded).decode('utf-8')
                                st.success(f"**Verified Auth:** `{decoded}`")
                            except:
                                pass
            except:
                st.warning(f"Non-JSON Payload: {msg.get('message')}")

    # Auto-refresh loop
    time.sleep(refresh_speed)
    st.rerun()

except Exception as e:
    st.error(f"Connection Error: {e}")