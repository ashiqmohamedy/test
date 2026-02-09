import streamlit as st
import json
from datetime import datetime

# Page Configuration
st.set_page_config(page_title="Python Webhook Tester", layout="wide")

# Initialize a list to store incoming requests in the session
if 'history' not in st.session_state:
    st.session_state.history = []

st.title("🪝 Python Webhook Listener UI")
st.write("Send POST requests to this app to see them appear below.")

# Sidebar for controls
if st.sidebar.button("Clear History"):
    st.session_state.history = []
    st.rerun()


# --- THE RECEIVER LOGIC ---
# In a real Streamlit app, we can use query parameters or
# a small Flask thread, but for a simple UI test, we simulate
# the 'Data Viewer' part here.

def add_mock_webhook(payload):
    new_entry = {
        "time": datetime.now().strftime("%H:%M:%S"),
        "body": payload,
        "headers": {"Content-Type": "application/json", "User-Agent": "Python-Tester"}
    }
    st.session_state.history.insert(0, new_entry)


# --- THE UI DISPLAY ---
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Incoming Requests")
    if not st.session_state.history:
        st.info("No webhooks received yet...")

    for i, entry in enumerate(st.session_state.history):
        if st.button(f"Request {entry['time']}", key=i):
            st.session_state.current_view = entry

with col2:
    st.subheader("Inspection Details")
    if 'current_view' in st.session_state:
        view = st.session_state.current_view
        st.write("**Timestamp:**", view['time'])

        st.write("**Headers:**")
        st.json(view['headers'])

        st.write("**JSON Payload:**")
        st.json(view['body'])
    else:
        st.write("Select a request from the left to inspect it.")

# Mock button for testing the UI
if st.sidebar.button("Simulate Incoming Webhook"):
    add_mock_webhook({"event": "user_signup", "user_id": 123, "status": "active"})