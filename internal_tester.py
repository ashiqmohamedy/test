import streamlit as st
import json
import time
import os
from datetime import datetime
import pytz
from flask import Flask, request, jsonify
from flask_cors import CORS
from threading import Thread

# --- 1. CONFIGURATION & SESSION STATE ---
USER_TZ = 'Asia/Kolkata'
DB_FILE = "webhook_db.json"

if 'viewed_ids' not in st.session_state:
    st.session_state.viewed_ids = set()
if 'selected_msg' not in st.session_state:
    st.session_state.selected_msg = None

# --- 2. THE BACKGROUND LISTENER (FLASK) ---
app = Flask(__name__)
CORS(app)  # Enables Java App (RestTemplate) to POST without security blocks


@app.route('/webhook', methods=['POST'])
def handle_webhook():
    try:
        data = request.json
        # Append arrival to our local "database" file
        entry = {
            "id": str(int(time.time() * 1000)),  # Millisecond ID for uniqueness
            "time": time.time(),
            "payload": data
        }
        with open(DB_FILE, "a") as f:
            f.write(json.dumps(entry) + "\n")
        return jsonify({"status": "received", "id": entry["id"]}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


def run_server():
    # host='0.0.0.0' allows other machines on your network to reach this
    app.run(host='0.0.0.0', port=8050, debug=False, use_reloader=False)


# Start the Flask thread only once per session
if 'server_started' not in st.session_state:
    thread = Thread(target=run_server)
    thread.daemon = True
    thread.start()
    st.session_state.server_started = True

# --- 3. UI SETUP ---
st.set_page_config(page_title="Pro Internal Receiver", layout="wide")

st.markdown("""
    <style>
        .block-container { padding-top: 5rem !important; max-width: 98% !important; }
        div[data-testid="stJson"] > div { overflow: visible !important; max-height: none !important; }

        /* Sidebar Styles */
        .brand-title { font-size: 1.6rem !important; font-weight: 800 !important; color: #3b82f6; font-family: monospace; }
        .brand-sep { border: 0; height: 2px; background: linear-gradient(to right, #3b82f6, transparent); margin-bottom: 1rem; }

        /* Button Styling */
        .stButton > button { 
            height: 34px !important; 
            text-align: left !important; 
            font-family: monospace !important; 
            font-size: 11px !important;
            margin-bottom: -15px !important;
        }
        .unread-msg > div > button { font-weight: 800 !important; color: #ffffff !important; }
        .read-msg > div > button { font-weight: 400 !important; color: #aaaaaa !important; font-style: italic; }

        .id-pill { background-color: #1e1e1e; padding: 2px 8px; border-radius: 12px; color: #3b82f6; font-size: 12px; border: 1px solid #333; font-family: monospace; }
    </style>
""", unsafe_allow_html=True)


# --- 4. DATA LOADING ---
def load_data():
    data = []
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            for line in f:
                if line.strip():
                    data.append(json.loads(line))
    return sorted(data, key=lambda x: x['time'], reverse=True)


feed_data = load_data()

# --- 5. HEADER ---
col_head, col_info = st.columns([1, 1])
with col_head:
    st.markdown('<p class="brand-title">INTERNAL_TESTER</p>', unsafe_allow_html=True)
    st.markdown('<div class="brand-sep"></div>', unsafe_allow_html=True)
with col_info:
    st.success(f"**API Active:** `http://localhost:8050/webhook`")

# --- 6. MAIN LAYOUT ---
col_sidebar, col_main = st.columns([1, 2.5])

with col_sidebar:
    st.subheader("Payload Feed")
    if st.button("🗑️ Clear All Logs", use_container_width=True):
        if os.path.exists(DB_FILE):
            os.remove(DB_FILE)
        st.session_state.selected_msg = None
        st.session_state.viewed_ids = set()
        st.rerun()

    st.divider()

    if not feed_data:
        st.info("Waiting for data from your Java App...")

    for msg in feed_data:
        m_id = msg['id']
        dt = datetime.fromtimestamp(msg['time'], pytz.timezone(USER_TZ))
        ts_str = dt.strftime('%H:%M:%S')
        is_unread = m_id not in st.session_state.viewed_ids

        # Display logic for Bold/Italic
        st.markdown(f'<div class="{"unread-msg" if is_unread else "read-msg"}">', unsafe_allow_html=True)
        if st.button(f"{'🔵' if is_unread else '  '} {ts_str} | Data Received", key=f"btn_{m_id}",
                     use_container_width=True):
            st.session_state.selected_msg = msg
            st.session_state.viewed_ids.add(m_id)
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

with col_main:
    if st.session_state.selected_msg:
        sel = st.session_state.selected_msg
        st.markdown(f"**Request ID:** <span class='id-pill'>{sel['id']}</span>", unsafe_allow_html=True)
        st.markdown("**📦 JSON Content**")
        st.json(sel['payload'])

        if st.button("Close View"):
            st.session_state.selected_msg = None
            st.rerun()
    else:
        st.info("👈 Select an entry to inspect the payload.")

# --- 7. AUTO-REFRESH ---
# This ensures the UI updates when the background Flask server receives data
time.sleep(3)
st.rerun()