import streamlit as st
import json
import time
from datetime import datetime
import pytz
from flask import Flask, request, jsonify
from threading import Thread

# --- 1. THE BACKGROUND LISTENER (FLASK) ---
# We use Flask because it's lightweight and works well in a thread
app = Flask(__name__)
if 'shared_data' not in st.session_state:
    st.session_state.shared_data = []


@app.route('/webhook', methods=['POST'])
def handle_webhook():
    try:
        data = request.json
        # We store this in a temporary file because threads can't
        # easily talk to Streamlit Session State
        with open("webhook_db.json", "a") as f:
            entry = {
                "id": str(int(time.time())),
                "time": time.time(),
                "payload": data
            }
            f.write(json.dumps(entry) + "\n")
        return jsonify({"status": "received"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


def run_server():
    # Runs on port 8050 to avoid conflict with Streamlit
    app.run(port=8050, debug=False, use_reloader=False)


# Start the background listener only once
if 'server_started' not in st.session_state:
    thread = Thread(target=run_server)
    thread.daemon = True
    thread.start()
    st.session_state.server_started = True

# --- 2. UI SETUP ---
st.set_page_config(page_title="Pro Internal Receiver", layout="wide")
USER_TZ = 'Asia/Kolkata'

st.markdown("""
    <style>
        .block-container { padding-top: 5.5rem !important; }
        .id-pill { background-color: #1e1e1e; padding: 2px 8px; border-radius: 12px; color: #3b82f6; font-size: 12px; border: 1px solid #333; }
        .stButton > button { text-align: left !important; font-family: monospace !important; }
    </style>
""", unsafe_allow_html=True)

# --- 3. DATA SYNC ---
if 'viewed_ids' not in st.session_state:
    st.session_state.viewed_ids = set()


def load_data():
    data = []
    try:
        with open("webhook_db.json", "r") as f:
            for line in f:
                data.append(json.loads(line))
    except:
        pass
    return sorted(data, key=lambda x: x['time'], reverse=True)


feed = load_data()

# --- 4. UI RENDER ---
st.title("📥 Internal Webhook Dashboard")
st.info("Direct your App to POST to: `http://<YOUR_SERVER_IP>:8050/webhook`")

col_list, col_view = st.columns([1, 2])

with col_list:
    st.subheader("Payload Feed")
    if st.button("🗑️ Clear Logs"):
        open("webhook_db.json", "w").close()
        st.rerun()

    for msg in feed:
        m_id = msg['id']
        ts = datetime.fromtimestamp(msg['time'], pytz.timezone(USER_TZ)).strftime('%H:%M:%S')
        is_unread = m_id not in st.session_state.viewed_ids

        label = f"{'🔵' if is_unread else '  '} {ts} | Received"
        if st.button(label, key=m_id, use_container_width=True):
            st.session_state.selected_msg = msg
            st.session_state.viewed_ids.add(m_id)
            st.rerun()

with col_view:
    if 'selected_msg' in st.session_state and st.session_state.selected_msg:
        sel = st.session_state.selected_msg
        st.markdown(f"**Request ID:** <span class='id-pill'>{sel['id']}</span>", unsafe_allow_html=True)
        st.json(sel['payload'])
    else:
        st.write("Select an entry to view details.")

# Refresh every 3 seconds to check the file
time.sleep(3)
st.rerun()