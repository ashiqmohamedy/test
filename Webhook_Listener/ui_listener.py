import streamlit as st
import requests
import json
import time
import base64

# --- CONFIGURATION ---
TOPIC = "wh_receiver_8824"
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

    valid_messages = [m for m in messages if
                      m.get('event') == 'message' and m.get('time', 0) > st.session_state.clear_before]

    # --- MAIN BODY HEADER ---
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

    st.markdown("---")

    # --- SEARCH & FILTER SECTION ---
    search_query = st.text_input("🔍 Search Logs", placeholder="Filter by keyword, ID, or header value...").lower()

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
        # Filter the messages based on search query
        filtered_messages = []
        for msg in valid_messages:
            raw_content = msg.get('message', '').lower()
            if search_query in raw_content:
                filtered_messages.append(msg)

        if not filtered_messages and search_query:
            st.warning(f"No results matching '{search_query}'")
        else:
            for msg in reversed(filtered_messages):
                try:
                    full_data = json.loads(msg.get('message'))
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