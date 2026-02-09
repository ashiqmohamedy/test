import streamlit as st
import requests
import json
import time
from datetime import datetime
import pytz

# --- 1. DYNAMIC CONFIGURATION ---
query_params = st.query_params
if "topic" in query_params:
    TOPIC = query_params["topic"]
else:
    TOPIC = "wh_receiver_a1b2-c3d4-e5f6-g7h8"

URL = f"https://ntfy.sh/{TOPIC}/json?poll=1"
USER_TZ = 'Asia/Kolkata'

# --- 2. UI SETUP ---
st.set_page_config(page_title="Webhook Tester", layout="wide")

st.markdown("""
    <style>
        /* Minimalist top padding */
        .block-container { padding-top: 1.5rem !important; max-width: 98% !important; }

        /* Label styling to align with the code box */
        .endpoint-label {
            font-family: 'Courier New', Courier, monospace;
            font-size: 13px;
            font-weight: 700;
            color: #10b981;
            margin-top: 12px;
        }

        .brand-title { font-size: 1.6rem !important; font-weight: 800 !important; color: #10b981; font-family: 'Courier New', Courier, monospace !important; margin-bottom: 0px !important; }
        .brand-sep { border: 0; height: 2px; background: linear-gradient(to right, #10b981, transparent); margin-bottom: 1rem !important; }

        /* Reduce gap between code box and divider */
        div[data-testid="stCode"] { margin-bottom: -10px !important; }
    </style>
""", unsafe_allow_html=True)

# 3. Initialize State
if 'clear_before' not in st.session_state:
    st.session_state.clear_before = time.time()
if 'selected_msg' not in st.session_state:
    st.session_state.selected_msg = None
if 'viewed_ids' not in st.session_state:
    st.session_state.viewed_ids = set()
if 'current_feed' not in st.session_state:
    st.session_state.current_feed = []

# --- 4. LEAN TOP SECTION ---
# Using columns to keep everything on one horizontal line
head_col1, head_col2 = st.columns([1, 6])

with head_col1:
    st.markdown('<p class="endpoint-label">📡 ACTIVE ENDPOINT</p>', unsafe_allow_html=True)

with head_col2:
    # Standard code block provides the 'Copy' button natively
    st.code(f"https://ntfy.sh/{TOPIC}", language="text")

st.divider()

# 5. SIDEBAR: BRAND & RESET
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

    # 6. Sidebar Feed
    search_query = st.text_input(label="Search", placeholder="🔍 Filter...", key="search_bar",
                                 label_visibility="collapsed").lower()

    # Fetch Data
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

# 7. MAIN CONTENT AREA
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
        with st.expander("Full HTTP Headers"):
            st.json(content.get('headers', {}))
    except:
        st.error("Could not parse JSON payload.")
else:
    st.info("👈 Select a webhook from the sidebar to inspect it.")

# 8. Loop
time.sleep(2)
st.rerun()