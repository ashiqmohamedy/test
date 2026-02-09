import streamlit as st
import requests
import json

# Setup
TOPIC = "ashiq_webhook_test_2026_xyz"
URL = f"https://ntfy.sh/{TOPIC}/json?poll=1"

st.set_page_config(page_title="Webhook Listener", layout="wide")
st.title("🪝 Live Webhook Inspector")

# Use a button to refresh manually or let the script rerun
if st.button('🔄 Refresh Now'):
    st.rerun()

try:
    # Fetch data without an infinite loop inside the script
    r = requests.get(URL, timeout=10)

    if r.status_code == 200:
        lines = r.text.strip().split('\n')
        # Skip the first line if it's the "open" notification from ntfy
        messages = [json.loads(line) for line in lines if line]

        if not messages:
            st.info("No webhooks found. Send one to see it here!")
        else:
            # Display webhooks
            for msg in reversed(messages):
                # We skip the "open" message ntfy sends initially
                if msg.get('event') == 'message':
                    try:
                        # ntfy message content is in msg['message']
                        payload = json.loads(msg.get('message'))
                        with st.expander(f"📥 Received: {msg.get('time')}"):
                            st.json(payload)
                    except:
                        with st.expander(f"📄 Text: {msg.get('time')}"):
                            st.write(msg.get('message'))
    else:
        st.error(f"Server Error: {r.status_code}")

except Exception as e:
    st.error(f"Connection Error: {e}")

# This magic line tells Streamlit to rerun the whole script every 10 seconds
st.empty()
st.write("---")
st.caption("Auto-refreshing every 10 seconds...")
import time

time.sleep(10)
st.rerun()