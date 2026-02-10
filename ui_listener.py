import streamlit as st
import requests
import json
import time
from datetime import datetime
import pytz
import urllib3

# Silences the insecure request warning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- 1. CONFIGURATION ---
TOPIC = "wh_receiver_a1b2-c3d4-e5f6-g7h8"
URL = f"https://ntfy.sh/{TOPIC}/json?poll=1"
USER_TZ = 'Asia/Kolkata'

# --- 2. UI SETUP ---
st.set_page_config(page_title="Webhook Tester", layout="wide")

st.markdown("""
    <style>
        .block-container { padding-top: 5rem !important; max-width: 98% !important; }
        .brand-title { font-size: 1.6rem !important; font-weight: 800 !important; color: #10b981; font-family: 'Courier New', Courier, monospace !important; margin-bottom: 0px !important; letter-spacing: -1px; }
        .brand-sep { border: 0; height: 2px; background: linear-gradient(to right, #10b981, transparent); margin-bottom: 1rem !important; margin-top: 5px !important; }
        .stButton > button { 
            height: 32px !important; 
            margin-bottom: -18px !important; 
            border-radius: 4px !important; 
            text-align: left !important; 
            font-family: 'Courier New', Courier, monospace !important; 
            font-size: 11px !important; 
            border: none !important; 
            background-color: transparent !important; 
            padding-left: 5px !important; 
            box-shadow: none !important;
        }
        .stButton > button:hover { background-color: rgba(16, 185, 129, 0.1) !important; color: #10b981 !important; }
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
# 'clear_before' is the key to the Reset function
if 'clear_before' not in st.session_state:
    st.session_state.clear_before = 0.0
if 'selected_msg' not in st.session_state:
    st.session_state.selected_msg = None
if 'viewed_ids' not in st.session_state:
    st.session_state.viewed_ids = set()

# --- 4. TOP HEADER ---
st.markdown('<p class="endpoint-label">📡 ACTIVE ENDPOINT</p>', unsafe_allow_html=True)
st.code(f"https://ntfy.sh/{TOPIC}", language="text")
st.divider()

# --- 5. DATA FETCHING (Strict Timestamp Filtering) ---
feed = []
try:
    # Use verify=False for SSL issues; timeout 5s
    r = requests.get(URL, timeout=5, verify=False)
    if r.status_code == 200:
        lines = r.text.strip().split('\n')
        for line in lines:
            if not line: continue
            msg = json.loads(line)

            # STICKY FILTER: Only accept messages newer than the 'clear_before' timestamp
            msg_time = float(msg.get('time', 0))
            if msg.get('event') == 'message' and msg_time > st.session_state.clear_before:
                feed.append(msg)

        # Sort newest at the top
        feed.sort(key=lambda x: x.get('time', 0), reverse=True)
except:
    pass

# --- 6. SIDEBAR ---
with st.sidebar:
    st.markdown('<p class="brand-title">WEBHOOK_TESTER</p>', unsafe_allow_html=True)
    st.markdown('<div class="brand-sep"></div>', unsafe_allow_html=True)

    # RESET BUTTON: Captures current time to 'hide' all existing messages
    if st.button("🔄 Reset", use_container_width=True):
        st.session_state.clear_before = time.time()
        st.session_state.selected_msg = None
        st.session_state.viewed_ids = set()
        st.rerun()

    st.divider()
    search_query = st.text_input(label="Search", placeholder="🔍 Filter...", key="search_bar",
                                 label_visibility="collapsed").lower()

    # Render Feed
    for msg in feed:
        if search_query and search_query not in msg.get('message', '').lower(): continue

        m_id = msg.get('id', 'N/A')
        ts = datetime.fromtimestamp(msg.get('time'), pytz.utc).astimezone(pytz.timezone(USER_TZ)).strftime('%H:%M:%S')
        is_new = m_id not in st.session_state.viewed_ids

        btn_label = f"{'🔵' if is_new else '  '} {ts} | ID: {m_id[:6]}"

        # Using a unique key and st.rerun to ensure RHS updates immediately
        if st.button(btn_label, key=f"feed_btn_{m_id}", use_container_width=True):
            st.session_state.selected_msg = msg
            st.session_state.viewed_ids.add(m_id)
            st.rerun()

# --- 7. MAIN CONTENT ---
if st.session_state.selected_msg:
    sel = st.session_state.selected_msg
    # Only show if it hasn't been "Reset" away
    if float(sel.get('time', 0)) > st.session_state.clear_before:
        try:
            content = json.loads(sel.get('message'))
            st.markdown(f"**Viewing Request:** `{sel.get('id')}`")
            st.json(content.get('payload', content))
        except:
            st.json(sel.get('message'))
    else:
        st.session_state.selected_msg = None
        st.rerun()
else:
    st.info("👈 Select a webhook from the sidebar to begin.")

# --- 8. STABLE REFRESH LOOP ---
# Slowed down slightly to 4 seconds to improve click stability
time.sleep(4)
st.rerun()