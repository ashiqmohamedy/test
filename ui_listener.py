import streamlit as st
import requests
import json
import time
import base64

# --- CONFIGURATION ---
# Professional secret topic name to ensure privacy in a public cloud
TOPIC = "wh_receiver_a1b2-c3d4-e5f6-g7h8"
URL = f"https://ntfy.sh/{TOPIC}/json?poll=1"

# --- UI SETUP ---
st.set_page_config(page_title="Webhook Tester", layout="wide")
st.title("🪝 Webhook Tester")

# Initialize session state for virtual clearing
if 'clear_before' not in st.session_state:
    st.session_state.clear_before = 0

# --- SIDEBAR (Controls & Hard Reset) ---
with st.sidebar:
    st.header("Settings")

    # Pause Toggle: Stops the auto-refresh loop for deep inspection
    is_paused = st.toggle("⏸️ Pause Live Stream", value=False)

    # Clear Logs: Hides existing webhooks from the current view
    if st.button("🗑️ Clear Logs"):
        st.session_state.clear_before = time.time()
        st.rerun()

    # Hard Reset: Wipes all session variables (Search, Pause, etc.)
    if st.button("🔄 Hard Reset App"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

    st.write("---")
    refresh_speed = st.slider("Refresh rate (seconds)", 2, 20, 5)
    st.caption("Lower speed = faster updates, higher CPU.")

# --- DATA FETCHING ---
try:
    # We always fetch data, but we only refresh the UI logic if not paused
    r = requests.get(URL, timeout=10)
    messages = []
    if r.status_code == 200:
        raw_lines = r.text.strip().split('\n')
        messages = [json.loads(line) for line in raw_lines if line]

    # Filter messages based on the 'Clear Logs' timestamp
    valid_messages = [m for m in messages if
                      m.get('event') == 'message' and m.get('time', 0) > st.session_state.clear_before]

    # --- MAIN BODY HEADER ---
    col_url, col_meta = st.columns([2, 1])
    with col_url:
        st.subheader("Target Endpoint")
        st.code(f"https://ntfy.sh/{TOPIC}", language="text")
        st.caption("🚀 Send your POST requests to this URL.")

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
            st.caption("Awaiting data...")

    st.markdown("---")

    # Global Search: Scans the entire JSON string for keywords
    search_query = st.text_input("🔍 Search Logs", placeholder="Filter by user_id, order_no, etc...").lower()

    # --- LOGS DISPLAY ---
    if not valid_messages:
        st.info("No webhooks detected in this session.")
    else:
        # Filter based on search query
        filtered_messages = [m for m in valid_messages if search_query in m.get('message', '').lower()]

        # Show only latest 50 for performance safety
        for msg in reversed(filtered_messages[-50:]):
            try:
                full_content = json.loads(msg.get('message'))

                # Handling Tunneled vs Raw payloads
                if isinstance(full_content, dict) and "headers" in full_content:
                    payload = full_content.get('payload', {})
                    headers = full_content.get('headers', {})
                else:
                    payload = full_content
                    headers = {"Notice": "Standard payload (no tunneled headers)"}

                auth_header = headers.get('Authorization', '')
                lock_icon = " 🔒" if "Basic" in auth_header else ""
                timestamp_raw = msg.get('time')
                timestamp = time.strftime('%H:%M:%S', time.localtime(timestamp_raw))

                # VERTICAL LAYOUT START
                with st.expander(f"📥 Received at {timestamp}{lock_icon}"):
                    st.markdown("### 📦 JSON Body")
                    st.json(payload)

                    # Action Row: Download and Auth Info
                    act_col1, act_col2 = st.columns([1, 1])
                    with act_col1:
                        st.download_button(
                            label="💾 Download JSON",
                            data=json.dumps(payload, indent=4),
                            file_name=f"webhook_{timestamp_raw}.json",
                            key=f"dl_{timestamp_raw}"
                        )

                    with act_col2:
                        if "Basic" in auth_header:
                            try:
                                encoded = auth_header.replace("Basic ", "")
                                decoded = base64.b64decode(encoded).decode('utf-8')
                                st.success(f"**Verified Credentials:** `{decoded}`")
                            except:
                                st.error("Auth Decode Error")

                    # Metadata
                    with st.status("🌐 View HTTP Headers", expanded=False):
                        st.json(headers)

            except Exception as e:
                st.warning(f"Raw Entry: {msg.get('message')}")

    # --- AUTO-REFRESH LOOP ---
    if not is_paused:
        time.sleep(refresh_speed)
        st.rerun()
    else:
        st.info("⏸️ Stream Paused. Resume to see live updates.")

except Exception as e:
    st.error(f"Connection Error: {e}. Please check your internet or ntfy.sh status.")