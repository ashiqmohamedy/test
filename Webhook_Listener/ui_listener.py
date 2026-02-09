import streamlit as st
import requests
import json
import time

# Setup
TOPIC = "ashiq_webhook_test_2026_xyz"
URL = f"https://ntfy.sh/{TOPIC}/json?poll=1"

st.set_page_config(page_title="Webhook Listener", layout="wide")

# --- SIDEBAR CONTROLS ---
with st.sidebar:
    st.header("Settings")
    if st.button("🗑️ Clear All Logs"):
        try:
            # We send a DELETE request to ntfy.sh to wipe the cache
            delete_res = requests.delete(f"https://ntfy.sh/{TOPIC}", timeout=5)
            if delete_res.status_code == 200:
                st.success("History cleared!")
                time.sleep(1)
                st.rerun()
            else:
                st.error("Failed to clear. ntfy might be restricted.")
        except Exception as e:
            st.error(f"Error: {e}")

    st.write("---")
    refresh_speed = st.slider("Refresh rate (seconds)", 2, 20, 5)

# --- MAIN UI ---
st.title("🪝 Live Webhook Inspector")

try:
    r = requests.get(URL, timeout=10)

    if r.status_code == 200:
        lines = r.text.strip().split('\n')
        messages = [json.loads(line) for line in lines if line]

        # Filter for actual messages only
        valid_messages = [m for m in messages if m.get('event') == 'message']

        if not valid_messages:
            st.info("No webhooks in history. Send one to see it here!")
        else:
            st.subheader(f"Showing {len(valid_messages)} Requests")
            for msg in reversed(valid_messages):
                try:
                    payload = json.loads(msg.get('message'))
                    # We use the ntfy timestamp
                    readable_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(msg.get('time')))
                    with st.expander(f"📥 Received: {readable_time}"):
                        st.json(payload)
                except:
                    with st.expander(f"📄 Text Payload: {msg.get('time')}"):
                        st.write(msg.get('message'))
    else:
        st.warning("Could not connect to ntfy.sh")

except Exception as e:
    st.error(f"Connection Error: {e}")

# Auto-refresh logic
time.sleep(refresh_speed)
st.rerun()