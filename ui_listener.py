import streamlit as st
import requests
import json
import time
from datetime import datetime
import pytz

# --- 1. DYNAMIC CONFIGURATION ---
query_params = st.query_params
TOPIC = query_params.get("topic", "wh_receiver_a1b2-c3d4-e5f6-g7h8")
URL = f"https://ntfy.sh/{TOPIC}/json?poll=1"
USER_TZ = 'Asia/Kolkata'

# --- 2. UI SETUP ---
st.set_page_config(page_title="Webhook Tester", layout="wide")

st.markdown("""
    <style>
        /* Increased padding-top to 4rem to clear the top-right buttons */
        .block-container { padding-top: 4rem !important; max-width: 98% !important; }

        .endpoint-label {
            font-family: 'Courier New', Courier, monospace;
            font-size: 13px;
            font-weight: 700;
            color: #10b981;
            margin-top: 8px;
            white-space: nowrap;
        }

        /* This limits the width of the code box so it isn't unnecessarily long */
        div[data-testid="stCode"] { 
            max-width: 500px !important; 
            margin-bottom: -10px !important; 
        }

        .brand-title { font-size: 1.6rem !important; font-weight: 800 !important; color: #10b981; font-family: 'Courier New', Courier, monospace !important; margin-bottom: 0px !important; }
        .brand-sep { border: 0; height: 2px; background: linear-gradient(to right, #10b981, transparent); margin-bottom: 1rem !important; }
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

# --- 4. THE COMPACT HEADER ---
# Adjusted column ratios: 1.2 for label, 8.8 for the rest to keep it tight
h_col1, h_col2 = st.columns([1.2, 8.8])

with h_col1:
    st.markdown('<p class="endpoint-label">📡 ACTIVE ENDPOINT</p>', unsafe_allow_html=True)

with h_col2:
    # The CSS max-width above ensures this doesn't stretch across the whole screen
    st.code(f"https://ntfy.sh/{TOPIC}", language="text")

st.divider()

# 5. SIDEBAR
with st.sidebar:
    st.markdown('<p class="brand-title">WEBHOOK_TESTER</p>', unsafe_allow_html=True)
    st.markdown('<div class="brand-sep"></div>', unsafe_allow_html=True)

    if st.button("🔄 Reset Feed", use_container_width=True):
        st.session_state.clear_before = time.time()
        st.session_state.selected_msg = None
        st.session_state.viewed_ids = set()
        st.session_state.current_feed = []
        st.rerun()

    st.divider()
    search_query = st.text_input(label="Search", placeholder="🔍 Filter...", key="search_bar",
                                 label_visibility="collapsed").lower()

    # Data Fetching
    try:
        r = requests.get(URL, timeout=2)
        if r.status_code == 200:
            new_valid_list = []
            raw_lines = r.text.strip().split('\n')
            for line in raw_lines:
                if not line: continue
                msg = json.loads(line)
                if msg.get('event') == 'message' and msg.get('time', 0) > st.session_state.clear_before:
                    new_valid_list.append(msg)
            new_valid_list.sort(key=lambda x: x.get('time', 0), reverse=True)
            st.session_state.current_feed = new_valid_list
    except:
        pass

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

# 6. MAIN CONTENT
if st.session_state.selected_msg:
    sel = st.session_state.selected_msg
    try:
        content = json.loads(sel.get('message'))
        payload = content.get('payload', content)
        col1, col2 = st.columns([3, 1])
        col1.markdown(f"**Viewing Request:** `{sel.get('id')}`")
        col2.download_button("💾 Download", json.dumps(payload, indent=4), f"{sel.get('id')}.json",
                             use_container_width=True)
        st.json(payload)
    except:
        st.error("Parse Error")
else:
    st.info("👈 Select a webhook from the sidebar.")

# 7. Loop
time.sleep(2)
st.rerun()