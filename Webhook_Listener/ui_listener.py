import streamlit as st
import requests
import time

URL = "https://jsonbin.org/ashiq-unique-123/webhooks"

st.title("🪝 Webhook Inspector (Live)")

log_placeholder = st.empty()

while True:
    try:
        r = requests.get(URL, timeout=5)
        if r.status_code == 200:
            data = r.json()
            with log_placeholder.container():
                if isinstance(data, list):
                    for item in reversed(data):
                        with st.expander(f"New Request Received"):
                            st.json(item)
                else:
                    st.write("Data format is not a list yet.")
        else:
            log_placeholder.info("Waiting for first webhook...")
    except:
        pass
    time.sleep(5)