import streamlit as st
import requests
import json
import time
import base64
from datetime import datetime
import pytz

# --- CONFIGURATION ---
TOPIC = "wh_receiver_a1b2-c3d4-e5f6-g7h8"
URL = f"https://ntfy.sh/{TOPIC}/json?poll=1"
# SET YOUR TIMEZONE HERE (e.g., 'Asia/Kolkata', 'America/New_York', 'Europe/London')
USER_TZ = 'Asia/Kolkata'

# --- UI SETUP ---
st.set_page_config(page_title="Webhook Tester", layout="wide")
st.title("🪝 Webhook Tester")

if 'clear_before' not in st.session_state:
    st.session_state.clear_before = 0

# --- SIDEBAR ---
with st.sidebar:
    st.header("Settings")
    is_paused = st.toggle("⏸️ Pause Live Stream", value=False)
    if st.button("🗑️ Clear Logs"):
        st.session_state.clear_before = time.time()
        st.rerun()
    if st.button("🔄 Hard Reset App"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
    st.write("---")
    refresh_speed = st.slider("Refresh rate (seconds)", 2, 20, 5)

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

    st.markdown("---")
    search_query = st.text_input("🔍 Search Logs", placeholder="Filter by keyword...").lower()

    # --- LOGS DISPLAY ---
    if not valid_messages:
        st.info("No webhooks found in current session.")
    else:
        filtered_messages = [m for m in valid_messages if search_query in m.get('message', '').lower()]

        for msg in reversed(filtered_messages[-50:]):
            try:
                full_content = json.loads(msg.get('message'))

                if isinstance(full_content, dict) and "headers" in full_content:
                    payload = full_content.get('payload', {})
                    headers = full_content.get('headers', {})
                else:
                    payload = full_content
                    headers = {"Notice": "Standard payload"}

                # --- LOCAL TIME CONVERSION ---
                utc_time = datetime.fromtimestamp(msg.get('time'), pytz.utc)
                local_time = utc_time.astimezone(pytz.timezone(USER_TZ))
                timestamp = local_time.strftime('%H:%M:%S')

                auth_header = headers.get('Authorization', '')
                lock_icon = " 🔒" if "Basic" in auth_header else ""

                with st.expander(f"📥 Webhook received at {timestamp}{lock_icon}"):
                    st.markdown("### 📦 JSON Body")
                    st.json(payload)

                    act_col1, act_col2 = st.columns([1, 1])
                    with act_col1:
                        st.download_button(label="💾 Download JSON", data=json.dumps(payload, indent=4),
                                           file_name=f"webhook_{timestamp}.json", key=f"dl_{msg.get('time')}")

                    with act_col2:
                        if "Basic" in auth_header:
                            try:
                                encoded = auth_header.replace("Basic ", "")
                                decoded = base64.b64decode(encoded).decode('utf-8')
                                st.success(f"**Verified Credentials:** `{decoded}`")
                            except:
                                pass

                    with st.status("🌐 View HTTP Headers", expanded=False):
                        st.json(headers)

            except Exception:
                # SILENT FIX: Ignore non-JSON or heartbeat messages
                pass

    if not is_paused:
        time.sleep(refresh_speed)
        st.rerun()
    else:
        st.info("⏸️ Stream Paused.")

except Exception as e:
    st.error(f"Connection Error: {e}")