import streamlit as st
import requests
import json
import time

# 1. Setup - We use a unique "Bucket" ID (Change 'ashiq-test-123' to something unique)
BUCKET_ID = "ashiq-test-webhook-2026"
STORAGE_URL = f"https://kvdb.io/{BUCKET_ID}/history"

st.set_page_config(page_title="Live Webhook Monitor", layout="wide")
st.title("🪝 Live Webhook Monitor")

# --- UI Layout ---
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Controls")
    refresh_rate = st.slider("Refresh Rate (seconds)", 2, 30, 5)
    if st.button("Clear All Data"):
        requests.delete(STORAGE_URL)
        st.success("Cleared!")


# --- Data Fetching Logic ---
def fetch_data():
    try:
        response = requests.get(STORAGE_URL)
        if response.status_code == 200:
            return response.json()
        return []
    except:
        return []


# --- Auto-Refreshing View ---
with col2:
    st.subheader("Incoming Webhooks")
    data_placeholder = st.empty()

    # This loop keeps the UI alive
    while True:
        webhooks = fetch_data()
        with data_placeholder.container():
            if not webhooks:
                st.info("Waiting for data... Send a POST request to the URL below.")
            else:
                for idx, item in enumerate(reversed(webhooks)):
                    with st.expander(f"Webhook #{len(webhooks) - idx}"):
                        st.json(item)

        time.sleep(refresh_rate)
        # We don't use st.rerun() here to avoid a loop crash