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

# Custom CSS for the Top Header Card
st.markdown("""
    <style>
        .block-container { padding-top: 2rem !important; max-width: 98% !important; }
        .header-card {
            background-color: rgba(16, 185, 129, 0.05);
            border: 1px solid rgba(16, 185, 129, 0.2);
            padding: 1.5rem;
            border-radius: 10px;
            margin-bottom: 2rem;
            margin-top: 1rem;
        }
        .endpoint-label {
            color: #10b981;
            font-size: 0.8rem;
            font-weight: 700;
            text-transform: uppercase;
            margin-bottom: 0.5rem;
        }
        .brand-title { font-size: 1.6rem !important; font-weight: 800 !important; color: #10b981; font-family: 'Courier New', Courier, monospace !important; margin-bottom: 0px !important; }
        .brand-sep { border: 0; height: 2px; background: linear-gradient(to right, #10b981, transparent); margin-bottom: 1rem !important; }
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

# --- 4. TOP BODY SECTION (The "Header Card") ---
# This sits at the top of the main section, safe from the RHS wrapper
header_container = st.container()
with header_container:
    st.markdown(f"""
        <div class="header-card">
            <div class="endpoint-label">📡 Active Webhook Endpoint</div>
            <p style="font-size: 0.9rem; color: #666;">Point your external system to the URL below to capture live data for this session.</p>
        </div>
    """, unsafe_allow_html=True)
    # We use st.code here so the "Copy" button is still available
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