import streamlit as st
import requests
import json
import time
import base64

# --- CONFIGURATION ---
TOPIC = "wh_receiver_8824"  # Replace 8824 with any 4 random digits
URL = f"https://ntfy.sh/{TOPIC}/json?poll=1"

# --- UI SETUP ---
st.set_page_config(page_title="Webhook Tester", layout="wide")
st.title("🪝 Webhook Tester")

if 'clear_before' not in st.session_state:
    st.session_state.clear_before = 0

# --- DATA FETCHING ---
try:
    r = requests.get(URL, timeout=10)
    messages = []
    if r.status_code == 200:
        raw_lines = r.text.strip().split('\n')
        messages = [json.loads(line) for line in raw_lines if line]

    # Filter logic
    valid_messages = [m for m in messages if
                      m.get('event') == 'message' and m.get('time', 0) > st.session_state.clear_before]

    # --- TOP HEADER SECTION (New Placement) ---
    col_url, col_meta = st.columns([2, 1])

    with col_url:
        st.markdown("**Your Webhook Endpoint:**")
        st.code(f"https://ntfy.sh/{TOPIC}", language="text")
        st.caption("Point your application to this URL to start testing.")

    with col_meta:
        if valid_messages:
            last_msg_time = valid_messages[-1].get('time')
            seconds_ago = int(time.time() - last_msg_time)

            m1, m2 = st.columns(2)
            m1.metric("Total Count", len(valid_messages))
            m2.metric("Last Ping", f"{seconds_ago}s ago")
        else:
            st.metric("Total Count", 0)
            st.caption("Waiting for first request...")

    st.divider()  # Visual break between header and logs

    # --- SIDEBAR (Controls Only) ---
    with st.sidebar:
        st.header("Controls")
        if st.button("🗑️ Clear Logs"):
            st.session_state.clear_before = time.time()
            st.rerun()
        st.write("---")
        refresh_speed = st.slider("Refresh rate (seconds)", 2, 20, 5)

    # --- LOGS SECTION ---
    if not valid_messages:
        st.info(f"No webhooks detected. Send a POST request to the URL above.")
    else:
        for msg in reversed(valid_messages):
            try:
                full_data = json.loads(msg.get('message'))
                payload = full_data.get('payload', full_data)
                headers = full_data.get('headers', {})

                auth_header = headers.get('Authorization', '')
                label_suffix = " 🔒" if auth_header.startswith('Basic ') else ""
                timestamp = time.strftime('%H:%M:%S', time.localtime(msg.get('time')))

                with st.expander(f"📥 Webhook received at {timestamp}{label_suffix}"):
                    c1, c2 = st.columns(2)
                    with c1:
                        st.markdown("**Body**")
                        st.json(payload)
                    with c2:
                        st.markdown("**Headers**")
                        st.json(headers)
                        if auth_header.startswith('Basic '):
                            try:
                                encoded = auth_header.split(' ')[1]
                                decoded = base64.b64decode(encoded).decode('utf-8')
                                st.info(f"Auth Credentials: `{decoded}`")
                            except:
                                pass
            except:
                st.write("Raw Message:", msg.get('message'))

    # Auto-refresh
    time.sleep(refresh_speed)
    st.rerun()

except Exception as e:
    st.error(f"Connection Error: {e}")