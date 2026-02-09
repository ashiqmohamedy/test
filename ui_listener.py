import streamlit as st
import requests
import json
import time
import base64
from datetime import datetime
import pytz

# --- 1. CONFIGURATION (Stable & Static) ---
TOPIC = "wh_receiver_a1b2-c3d4-e5f6-g7h8"
URL = f"https://ntfy.sh/{TOPIC}/json?poll=1"
USER_TZ = 'Asia/Kolkata'


def make_bold(text):
    # Mapping for bold unicode numbers for the "New" look
    return text.replace("0", "𝟎").replace("1", "𝟏").replace("2", "𝟐").replace("3", "𝟑").replace("4", "𝟒").replace("5",
                                                                                                                  "𝟓").replace(
        "6", "𝟔").replace("7", "𝟕").replace("8", "𝟖").replace("9", "𝟗")


# --- 2. UI SETUP ---
st.set_page_config(page_title="Webhook Tester", layout="wide")

st.markdown("""
    <style>
        .block-container { padding-top: 2rem !important; max-width: 98% !important; }
        .brand-title { font-size: 1.6rem !important; font-weight: 800 !important; color: #10b981; font-family: 'Courier New', Courier, monospace !important; margin-bottom: 0px !important; letter-spacing: -1px; }
        .brand-sep { border: 0; height: 2px; background: linear-gradient(to right, #10b981, transparent); margin-bottom: 1rem !important; margin-top: 5px !important; }

        /* Sidebar Buttons: Borderless, Transparent, Minimalist */
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

        div[data-testid="stJson"] { line-height: 1.1 !important; }
        [data-testid="stHorizontalBlock"] { gap: 0.5rem !important; margin-bottom: -5px !important; }
    </style>
""", unsafe_allow_html=True)

# 3. Initialize Session State
if 'clear_before' not in st.session_state:
    st.session_state.clear_before = time.time()
if 'selected_msg' not in st.session_state:
    st.session_state.selected_msg = None
if 'viewed_ids' not in st.session_state:
    st.session_state.viewed_ids = set()
if 'current_feed' not in st.session_state:
    st.session_state.current_feed = []

# --- 4. SIDEBAR (Brand & Reset) ---
with st.sidebar:
    st.markdown('<p class="brand-title">WEBHOOK_TESTER</p>', unsafe_allow_html=True)
    st.markdown('<div class="brand-sep"></div>', unsafe_allow_html=True)

    if st.button("🔄 Reset Feed", use_container_width=True):
        st.session_state.clear_before = time.time()
        st.session_state.selected_msg = None
        st.session_state.viewed_ids = set()
        st.session_state.current_feed = []
        st.rerun()

# --- 5. DATA FETCHING (Always active) ---
try:
    r = requests.get(URL, timeout=2)
    if r.status_code == 200:
        new_valid_list = []
        raw_lines = r.text.strip().split('\n')
        for line in raw_lines:
            if not line: continue
            msg = json.loads(line)
            # Only show messages received AFTER the last Reset
            if msg.get('event') == 'message' and msg.get('time', 0) > st.session_state.clear_before:
                new_valid_list.append(msg)

        new_valid_list.sort(key=lambda x: x.get('time', 0), reverse=True)
        st.session_state.current_feed = new_valid_list
except:
    pass

# --- 6. SIDEBAR FEED ---
with st.sidebar:
    st.divider()
    search_query = st.text_input(
        label="Filter incoming webhooks",
        placeholder="🔍 Filter feed...",
        key="search_bar",
        label_visibility="collapsed"
    ).lower()

    if not st.session_state.current_feed:
        st.caption("Awaiting new data...")
    else:
        display_list = [m for m in st.session_state.current_feed if search_query in m.get('message', '').lower()]

        for msg in display_list:
            m_id = msg.get('id', 'N/A')
            utc_time = datetime.fromtimestamp(msg.get('time'), pytz.utc)
            ts = utc_time.astimezone(pytz.timezone(USER_TZ)).strftime('%H:%M:%S')

            # Parse message to find source IP if available
            source_ip = "Payload"
            try:
                inner_data = json.loads(msg.get('message', '{}'))
                source_ip = inner_data.get("payload", inner_data).get("sannavServerIp", "Webhook")
            except:
                pass

            is_new = m_id not in st.session_state.viewed_ids

            if is_new:
                log_label = f"🔵 {make_bold(ts)}: {source_ip}"
            else:
                log_label = f"   {ts}: {source_ip}"

            if st.button(log_label, key=m_id, use_container_width=True):
                st.session_state.selected_msg = msg
                st.session_state.viewed_ids.add(m_id)

# --- 7. MAIN CONTENT AREA ---
if st.session_state.selected_msg:
    try:
        sel = st.session_state.selected_msg
        full_content = json.loads(sel.get('message'))
        payload = full_content.get('payload', full_content)
        headers = full_content.get('headers', {"Info": "Direct payload"})

        c_meta, c_dl = st.columns([3, 1])
        with c_meta:
            st.markdown(f"**Request ID:** `{sel.get('id')}`")
        with c_dl:
            st.download_button("💾 Download JSON", json.dumps(payload, indent=4), f"{sel.get('id')}.json",
                               use_container_width=True)

        st.markdown("**📦 JSON Body**")
        st.json(payload, expanded=True)

        st.divider()
        with st.expander("🌐 View HTTP Headers", expanded=True):
            st.json(headers)
    except:
        st.error("Error parsing payload JSON.")
else:
    st.info("👈 Select a request from the sidebar to begin inspection.")

# --- 8. AUTO-REFRESH ---
time.sleep(2)
st.rerun()