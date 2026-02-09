import streamlit as st
import requests
import json
import time
from datetime import datetime
import pytz

# --- 1. CONFIGURATION (STATIC & FIXED) ---
TOPIC = "wh_receiver_a1b2-c3d4-e5f6-g7h8"
URL = f"https://ntfy.sh/{TOPIC}/json?poll=1"
USER_TZ = 'Asia/Kolkata'

# --- 2. UI SETUP ---
st.set_page_config(page_title="Webhook Tester", layout="wide")

st.markdown("""
    <style>
        .block-container { padding-top: 5.5rem !important; max-width: 98% !important; }

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

        .endpoint-label {
            font-family: 'Courier New', Courier, monospace;
            font-size: 14px;
            font-weight: 700;
            color: #10b981;
            margin-bottom: 5px !important;
        }
    </style>
""", unsafe_allow_html=True)

# 3. State Management
if 'clear_before' not in st.session_state:
    st.session_state.clear_before = time.time()
if 'selected_msg' not in st.session_state:
    st.session_state.selected_msg = None
if 'viewed_ids' not in st.session_state:
    st.session_state.viewed_ids = set()
if 'current_feed' not in st.session_state:
    st.session_state.current_feed = []

# --- 4. TOP HEADER ---
st.markdown('<p class="endpoint-label">📡 ACTIVE ENDPOINT</p>', unsafe_allow_html=True)
st.code(f"https://ntfy.sh/{TOPIC}", language="text")
st.divider()

# --- 5. DATA FETCHING (CRITICAL: Moved outside of sidebar) ---
try:
    r = requests.get(URL, timeout=2)
    if r.status_code == 200:
        new_valid_list = []
        raw_lines = r.text.strip().split('\n')
        for line in raw_lines:
            if not line: continue
            msg = json.loads(line)
            # Filter by the time of the last Reset
            if msg.get('event') == 'message' and msg.get('time', 0) > st.session_state.clear_before:
                new_valid_list.append(msg)
        new_valid_list.sort(key=lambda x: x.get('time', 0), reverse=True)
        st.session_state.current_feed = new_valid_list
except Exception as e:
    pass

# --- 6. SIDEBAR UI ---
with st.sidebar:
    st.markdown('<p class="brand-title">WEBHOOK_TESTER</p>', unsafe_allow_html=True)
    st.markdown('<div class="brand-sep"></div>', unsafe_allow_html=True)

    if st.button("🔄 Reset", use_container_width=True):
        st.session_state.clear_before = time.time()
        st.session_state.selected_msg = None
        st.session_state.viewed_ids = set()
        st.session_state.current_feed = []
        st.rerun()

    st.divider()
    search_query = st.text_input(label="Search", placeholder="🔍 Filter...", key="search_bar",
                                 label_visibility="collapsed").lower()

    if not st.session_state.current_feed:
        st.caption("Awaiting data...")
    else:
        for msg in st.session_state.current_feed:
            if search_query and search_query not in msg.get('message', '').lower(): continue
            m_id = msg.get('id', 'N/A')
            ts = datetime.fromtimestamp(msg.get('time'), pytz.utc).astimezone(pytz.timezone(USER_TZ)).strftime(
                '%H:%M:%S')
            is_new = m_id not in st.session_state.viewed_ids
            label = f"{'🔵' if is_new else '  '} {ts} | ID: {m_id[:6]}"
            if st.button(label, key=m_id, use_container_width=True):
                st.session_state.selected_msg = msg
                st.session_state.viewed_ids.add(m_id)

# --- 7. MAIN CONTENT ---
if st.session_state.selected_msg:
    sel = st.session_state.selected_msg
    try:
        content = json.loads(sel.get('message'))
        payload = content.get('payload', content)
        st.markdown(f"**Viewing Request:** `{sel.get('id')}`")
        st.json(payload)
    except:
        st.error("Parse Error")
else:
    st.info("👈 Select a webhook from the sidebar.")

# --- 8. AUTO-REFRESH ---
time.sleep(2)
st.rerun()