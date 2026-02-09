import streamlit as st
import requests
import time
import json

TOPIC = "ashiq_webhook_test_2026_xyz"
# We add /json and ?poll=1 to get the cached history
URL = f"https://ntfy.sh/{TOPIC}/json?poll=1"

st.title("🪝 Webhook Monitor (ntfy.sh Edition)")

log_placeholder = st.empty()

while True:
    try:
        # ntfy.sh returns one JSON object per line for history
        r = requests.get(URL, timeout=5)
        if r.status_code == 200:
            # Split the lines and parse each as JSON
            messages = [json.loads(line) for line in r.text.strip().split('\n') if line]

            with log_placeholder.container():
                for msg in reversed(messages):
                    # The actual webhook data is in the 'message' field
                    # ntfy.sh stores the data as a string, so we try to parse it back to JSON
                    try:
                        clean_data = json.loads(msg.get('message'))
                        with st.expander(f"Received: {msg.get('time')}"):
                            st.json(clean_data)
                    except:
                        st.write(msg.get('message'))
        else:
            st.warning("No data found on this topic yet.")
    except Exception as e:
        st.error(f"Error: {e}")

    time.sleep(5)