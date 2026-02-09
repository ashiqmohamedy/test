import streamlit as st
import requests
import json
import time

# Make sure the TOPIC matches your send_test.py exactly
TOPIC = "ashiq_webhook_test_2026_xyz"

# The "?poll=1" is the magic part that fetches history
URL = f"https://ntfy.sh/{TOPIC}/json?poll=1"

st.set_page_config(page_title="Webhook Listener", layout="wide")
st.title("🪝 Live Webhook Inspector")

# Create a container so we can clear and refresh the UI properly
log_placeholder = st.empty()

while True:
    try:
        # Fetching from the ntfy cache
        r = requests.get(URL, timeout=10)

        if r.status_code == 200:
            # ntfy returns messages as separate JSON lines
            lines = r.text.strip().split('\n')
            messages = [json.loads(line) for line in lines if line]

            with log_placeholder.container():
                if not messages:
                    st.info("No webhooks found. Send one to see it here!")
                else:
                    # Show newest first
                    for msg in reversed(messages):
                        # ntfy stores the webhook payload in the 'message' field
                        try:
                            # Try to parse the payload if it's JSON
                            payload = json.loads(msg.get('message'))
                            with st.expander(f"📥 Received: {msg.get('time')} (ID: {msg.get('id')})"):
                                st.json(payload)
                        except:
                            # Fallback if it's just plain text
                            with st.expander(f"📄 Text Message: {msg.get('time')}"):
                                st.write(msg.get('message'))
        else:
            st.error(f"Server returned status {r.status_code}")

    except Exception as e:
        st.error(f"Connection Error: {e}")

    # Wait 5 seconds before checking for new webhooks
    time.sleep(5)