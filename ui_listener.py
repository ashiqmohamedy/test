import streamlit as st
import requests
import json
import time
from datetime import datetime
import pytz
import urllib3

# This silences the insecure request warning caused by verify=False
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- 1. CONFIGURATION ---
TOPIC = "wh_receiver_a1b2-c3d4-e5f6-g7h8"
URL = f"https://ntfy.sh/{TOPIC}/json?poll=1"
USER_TZ = 'Asia/Kolkata'

# --- 2. UI SETUP ---
st.set_page_config(page_title="Webhook Tester", layout="wide")

st.markdown("""
    <style>
        .block-container { padding-top: 2rem !important; max-width: 98% !important; }
        .brand-title { font-size: 1.6rem !important; font-weight: 800 !important; color: #10b981; font-family: 'Courier New', Courier, monospace !important; margin-bottom: 0px !important; letter-spacing: -1px; }
        .brand-sep { border: 0; height: 2px; background: linear-gradient(to right, #10b981, transparent); margin-bottom: 1rem !important; margin-top: 5px !important; }

        /* Sidebar Buttons: Borderless & Transparent */
        .stButton > button { 
            height: 32px !important; 
            margin-bottom: -18px !important; 
            border-radius: 0px !important; 
            text-align: left !important; 
            font-family: 'Courier New', Courier, monospace !important; 
            font-size: 11px !important; 
            border: none !important; 
            background-color: transparent !important; 
            padding-left: 5px !important; 
            box-shadow: none !important;
        }
        .stButton > button:hover { background-color: rgba(16, 185, 129, 0.1) !important; color: #10b981 !important; border: none !important; }
    </style>
""", unsafe_allow_html=True)

# 3. State Management
if 'selected_msg' not in st.session_state:
    st.session_state.selected_msg = None
if 'viewed_ids' not in st.session_state:
    st.session_state.viewed_ids = set()

# --- 4. DATA FETCHING (The SSL Fix) ---
feed = []
try:
    # verify=False is the Python equivalent of 'curl -k'
    # It bypasses the SSL revocation check failure
    response = requests.get(URL, timeout=10, verify=False)
    if response.status_code == 200:
        lines = response.text.strip().split('\n')
        for line in lines:
            if not line: continue
            msg = json.loads(line)
            if msg.get('event') == 'message':
                feed.append(msg)
        # Sort by time, newest at the top
        feed.sort(key=lambda x: x.get('time', 0), reverse=True)
except Exception as e:
    st.sidebar.error(f"⚠️ Connection Error: {e}")

# --- 5. SIDEBAR ---
with st.sidebar:
    st.markdown('<p class="brand-title">WEBHOOK_TESTER</p>', unsafe_allow_html=True)
    st.markdown('<div class="brand-sep"></div>', unsafe_allow_html=True)

    if st.button("🔄 Reset View", use_container_width=True):
        st.session_state.selected_msg = None
        st.session_state.viewed_ids = set()
        st.rerun()

    st.divider()
    search_query = st.text_input(label="Search", placeholder="🔍 Filter...", key="search_bar",
                                 label_visibility="collapsed").lower()

    if not feed:
        st.caption("Awaiting data from ntfy.sh...")
    else:
        for msg in feed:
            if search_query and search_query not in msg.get('message', '').lower(): continue

            m_id = msg.get('id', 'N/A')
            ts = datetime.fromtimestamp(msg.get('time'), pytz.utc).astimezone(pytz.timezone(USER_TZ)).strftime(
                '%H:%M:%S')

            is_new = m_id not in st.session_state.viewed_ids
            label = f"{'🔵' if is_new else '  '} {ts} | ID: {m_id[:6]}"

            if st.button(label, key=m_id, use_container_width=True):
                st.session_state.selected_msg = msg
                st.session_state.viewed_ids.add(m_id)

# --- 6. MAIN CONTENT ---
if st.session_state.selected_msg:
    sel = st.session_state.selected_msg
    try:
        # Display the payload
        msg_content = json.loads(sel.get('message'))
        st.markdown(f"**Viewing Request:** `{sel.get('id')}`")
        st.json(msg_content.get('payload', msg_content))
    except:
        # Fallback for non-JSON or flat JSON
        st.json(sel.get('message'))
else:
    st.info("👈 Select a webhook from the sidebar to inspect details.")

# --- 7. AUTO-REFRESH ---
time.sleep(2)
st.rerun()