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


def make_bold(text):
    return text.replace("0", "0").replace("1", "1").replace("2", "2").replace("3", "3").replace("4", "4").replace("5",
                                                                                                                  "5").replace(
        "6", "6").replace("7", "7").replace("8", "8").replace("9", "9")


# --- 2. UI SETUP ---
st.set_page_config(page_title="Webhook Tester", layout="wide")

st.markdown("""
    <style>
        .block-container { padding-top: 5rem !important; max-width: 98% !important; }
        .brand-title { font-size: 1.6rem !important; font-weight: 800 !important; color: #10b981; font-family: 'Courier New', Courier, monospace !important; margin-bottom: 0px !important; letter-spacing: -1px; }
        .brand-sep { border: 0; height: 2px; background: linear-gradient(to right, #10b981, transparent); margin-bottom: 1rem !important; margin-top: 5px !important; }
        [data-testid="stSidebarUserContent"] { padding-top: 1rem !important; }
        .stButton > button { height: 32px !important; border-radius: 4px !important; font-family: 'Courier New', Courier, monospace !important; font-size: 11px !important; }
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

# 4. SIDEBAR: HEADER & ENDPOINT
with st.sidebar:
    st.markdown('<p class="brand-title">WEBHOOK_TESTER</p>', unsafe_allow_html=True)
    st.markdown('<div class="brand-sep"></div>', unsafe_allow_html=True)

    # --- THIS IS THE PART YOU ARE LOOKING FOR ---
    st.write("### 📡 Webhook Endpoint")
    st.info(f"Send your POST requests to:")
    st.code(f"https://ntfy.sh/{TOPIC}", language="text")
    st.caption("Copy this URL into your application settings.")
    # --------------------------------------------

    st.divider()

    if st.button("🔄 Reset Feed", use_container_width=True):
        st.session_state.clear_before = time.time()
        st.session_state.selected_msg = None
        st.session_state.viewed_ids = set()
        st.session_state.current_feed = []
        st.rerun()

# 5. Data Fetching
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

# 6. Sidebar Feed
with st.sidebar:
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

            # Simple bolding logic for the button label
            is_new = m_id not in st.session_state.viewed_ids
            label = f"{'🔵' if is_new else '  '} {ts} | ID: {m_id[:6]}"

            if st.button(label, key=m_id, use_container_width=True):
                st.session_state.selected_msg = msg
                st.session_state.viewed_ids.add(m_id)

# 7. Main Body
if st.session_state.selected_msg:
    sel = st.session_state.selected_msg
    try:
        content = json.loads(sel.get('message'))
        payload = content.get('payload', content)

        col1, col2 = st.columns([3, 1])
        col1.markdown(f"**Viewing Request:** `{sel.get('id')}`")
        col2.download_button("💾 Download", json.dumps(payload, indent=4), f"{sel.get('id')}.json")

        st.json(payload)
        with st.expander("Full Headers"):
            st.json(content.get('headers', {}))
    except:
        st.error("Could not parse JSON payload.")
else:
    st.info("👈 Select a webhook from the sidebar to inspect it.")

# 8. Loop
time.sleep(2)
st.rerun()