import streamlit as st
import requests
import json
import time

# Setup
TOPIC = "ashiq_webhook_test_2026_xyz"
URL = f"https://ntfy.sh/{TOPIC}/json?poll=1"

st.set_page_config(page_title="Webhook Listener", layout="wide")

# Initialize a 'clear_time' in the session state if it doesn't exist
if 'clear_before' not in st.session_state:
    st.session_state.clear_before = 0

# --- SIDEBAR CONTROLS ---
with st.sidebar:
    st.header("Settings")

    # Virtual Clear Button
    if st.button("🗑️ Clear UI View"):
        # Set the filter to current time (seconds since epoch)
        st.session_state.clear_before = time.time()
        st.success("UI Cleared!")
        time.sleep(0.5)
        st.rerun()

    # Reset button to see everything again
    if st.button("⏪ Restore All History"):
        st.session_state.clear_before = 0
        st.rerun()

    st.write("---")
    refresh_speed = st.slider("Refresh rate (seconds)", 2, 20, 5)

# --- MAIN UI ---
st.title("🪝 Live Webhook Inspector")

try:
    r = requests.get(URL, timeout=10)

    if r.status_code == 200:
        lines = r.text.strip().split('\n')
        messages = [json.loads(line) for line in lines if line]

        # 1. Filter for actual messages
        # 2. Filter for messages that arrived AFTER our 'clear' click
        valid_messages = [
            m for m in messages
            if m.get('event') == 'message' and m.get('time', 0) > st.session_state.clear_before
        ]

        if not valid_messages:
            st.info("No new webhooks. Send one to see it here!")
        else:
            st.subheader(f"Showing {len(valid_messages)} New Requests")
            for msg in reversed(valid_messages):
                try:
                    payload = json.loads(msg.get('message'))
                    readable_time = time.strftime('%H:%M:%S', time.localtime(msg.get('time')))
                    with st.expander(f"📥 Received: {readable_time}"):
                        st.json(payload)
                except:
                    with st.expander(f"📄 Text: {msg.get('time')}"):
                        st.write(msg.get('message'))
    else:
        st.warning("Could not connect to ntfy.sh")

except Exception as e:
    st.error(f"Connection Error: {e}")

# Auto-refresh logic
time.sleep(refresh_speed)
st.rerun()