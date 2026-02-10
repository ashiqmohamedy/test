import streamlit as st
import json
import time
import os
from datetime import datetime
import pytz
from flask import Flask, request, jsonify
from flask_cors import CORS
from threading import Thread

# --- 1. CONFIGURATION ---
USER_TZ = 'Asia/Kolkata'
DB_FILE = "webhook_db.json"

# --- 2. THE BACKGROUND HTTPS LISTENER (FLASK) ---
app = Flask(__name__)
CORS(app)


@app.route('/webhook', methods=['POST'])
def handle_webhook():
    try:
        data = request.json
        entry = {
            "id": str(int(time.time() * 1000)),
            "time": time.time(),
            "payload": data
        }
        with open(DB_FILE, "a") as f:
            f.write(json.dumps(entry) + "\n")
        return jsonify({"status": "received", "id": entry["id"]}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


def run_server():
    try:
        # port 443 is the default for https://
        # ssl_context='adhoc' generates a self-signed certificate on the fly
        app.run(host='0.0.0.0', port=443, ssl_context='adhoc', debug=False, use_reloader=False)
    except Exception as e:
        st.error(f"Critical Error: Could not start HTTPS server on port 443. {e}")
        # Fallback to 8443 if 443 is busy
        app.run(host='0.0.0.0', port=8443, ssl_context='adhoc', debug=False, use_reloader=False)


# Start background server thread
if 'server_started' not in st.session_state:
    thread = Thread(target=run_server)
    thread.daemon = True
    thread.start()
    st.session_state.server_started = True

# --- 3. UI SETUP ---
st.set_page_config(page_title="Internal HTTPS Webhook Dashboard", layout="wide")

st.markdown("""
    <style>
        .block-container { padding-top: 5rem !important; }
        .brand-title { font-size: 1.6rem !important; font-weight: 800 !important; color: #10b981; font-family: monospace; }
        .brand-sep { border: 0; height: 2px; background: linear-gradient(to right, #10b981, transparent); margin-bottom: 1rem; }
        .id-pill { background-color: #1e1e1e; padding: 2px 8px; border-radius: 12px; color: #10b981; font-size: 12px; border: 1px solid #333; font-family: monospace; }
        .stButton > button { height: 34px !important; text-align: left !important; font-family: monospace !important; font-size: 11px !important; margin-bottom: -15px !important; }
        .unread-msg > div > button { font-weight: 800 !important; color: #ffffff !important; }
        .read-msg > div > button { font-weight: 400 !important; color: #aaaaaa !important; font-style: italic; }
    </style>
""", unsafe_allow_html=True)

# --- 4. DATA LOGIC ---
if 'viewed_ids' not in st.session_state:
    st.session_state.viewed_ids = set()


def load_data():
    data = []
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            for line in f:
                if line.strip(): data.append(json.loads(line))
    return sorted(data, key=lambda x: x['time'], reverse=True)


feed_data = load_data()

# --- 5. RENDER UI ---
st.markdown('<p class="brand-title">HTTPS_WEBHOOK_TESTER</p>', unsafe_allow_html=True)
st.markdown('<div class="brand-sep"></div>', unsafe_allow_html=True)

# Connection Help
st.success(f"**HTTPS API Listener is ACTIVE** on Port 443")
st.info(f"Target URL for your App: `https://{os.environ.get('COMPUTERNAME', 'localhost')}/webhook`")

col_side, col_main = st.columns([1, 2.5])

with col_side:
    if st.button("🗑️ Clear Logs", use_container_width=True):
        if os.path.exists(DB_FILE): os.remove(DB_FILE)
        st.session_state.selected_msg = None
        st.rerun()

    st.divider()
    if not feed_data:
        st.write("Waiting for HTTPS data...")

    for msg in feed_data:
        m_id = msg['id']
        ts = datetime.fromtimestamp(msg['time'], pytz.timezone(USER_TZ)).strftime('%H:%M:%S')
        is_unread = m_id not in st.session_state.viewed_ids

        st.markdown(f'<div class="{"unread-msg" if is_unread else "read-msg"}">', unsafe_allow_html=True)
        if st.button(f"{'🔵' if is_unread else '  '} {ts} | Received", key=f"btn_{m_id}", use_container_width=True):
            st.session_state.selected_msg = msg
            st.session_state.viewed_ids.add(m_id)
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

with col_main:
    if st.session_state.get('selected_msg'):
        sel = st.session_state.selected_msg
        st.markdown(f"**Request ID:** <span class='id-pill'>{sel['id']}</span>", unsafe_allow_html=True)
        st.json(sel['payload'])
    else:
        st.info("👈 Incoming payloads will appear in the sidebar.")

# Auto-refresh UI every 3 seconds
time.sleep(3)
st.rerun()