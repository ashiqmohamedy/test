import streamlit as st
from fastapi import FastAPI, Request
import uvicorn
import threading
import json

# 1. Setup FastAPI to listen for the "Real" Webhook
api = FastAPI()

# This list will hold our data in memory
if 'webhook_data' not in st.session_state:
    st.session_state.webhook_data = []


@api.post("/receiver")
async def get_webhook(request: Request):
    payload = await request.json()
    # In a real cloud app, you'd save this to a file or DB
    with open("data.json", "a") as f:
        f.write(json.dumps(payload) + "\n")
    return {"status": "received"}


# 2. Start the API in the background
def run_api():
    uvicorn.run(api, host="0.0.0.0", port=8000)


if "api_thread" not in st.session_state:
    thread = threading.Thread(target=run_api, daemon=True)
    thread.start()
    st.session_state.api_thread = True

# 3. Streamlit UI Logic
st.title("Live Webhook Listener")

if st.button("Refresh Data"):
    try:
        with open("data.json", "r") as f:
            lines = f.readlines()
            st.session_state.webhook_data = [json.loads(l) for l in lines]
    except FileNotFoundError:
        st.write("No data received yet.")

st.write("### Incoming Payloads:")
st.json(st.session_state.webhook_data)