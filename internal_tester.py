import streamlit as st
import json
import time
from datetime import datetime
import pytz

# --- 1. CONFIGURATION ---
USER_TZ = 'Asia/Kolkata'

# --- 2. UI SETUP ---
st.set_page_config(page_title="Internal Webhook Tester", layout="wide")

# Persistent Highlight & Formatting CSS
st.markdown("""
    <style>
        .block-container { padding-top: 5.5rem !important; max-width: 98% !important; }
        div[data-testid="stJson"] > div { overflow: visible !important; max-height: none !important; }
        div[data-testid="stJson"] { line-height: 1.0 !important; }
        .brand-title { font-size: 1.6rem !important; font-weight: 800 !important; color: #3b82f6; font-family: 'Courier New', Courier, monospace !important; margin-bottom: 0px !important; }
        .brand-sep { border: 0; height: 2px; background: linear-gradient(to right, #3b82f6, transparent); margin-bottom: 1rem !important; }
        .stButton > button { height: 32px !important; margin-bottom: -18px !important; border-radius: 4px !important; text-align: left !important; font-family: 'Courier New', Courier, monospace !important; font-size: 10.5px !important; border: none !important; background-color: transparent !important; }
        .unread-msg > div > button { font-weight: 800 !important; color: #ffffff !important; }
        .read-msg > div > button { font-weight: 400 !important; color: #aaaaaa !important; font-style: italic; }
        .id-pill { background-color: #1e1e1e; padding: 2px 8px; border-radius: 12px; border: 1px solid #333; font-family: monospace; color: #3b82f6; font-size: 12px; }
    </style>
""", unsafe_allow_html=True)

# 3. Session State
if 'feed_data' not in st.session_state:
    st.session_state.feed_data = []
    st.session_state.selected_msg = None
    st.session_state.viewed_ids = set()

# --- 4. THE MAGIC: DIRECT RECEIVER ---
# This captures data sent to your Streamlit URL via the /?data= query param
query_params = st.query_params
if "payload" in query_params:
    try:
        raw_data = query_params["payload"]
        msg_id = str(int(time.time()))  # Generate an ID based on arrival
        new_entry = {
            "id": msg_id,
            "time": time.time(),
            "message": raw_data,
            "extracted_ip": "Direct Post"
        }
        # Add to feed if not just a page refresh
        if not st.session_state.feed_data or st.session_state.feed_data[0]['message'] != raw_data:
            st.session_state.feed_data.insert(0, new_entry)
            st.query_params.clear()  # Clear param so refresh doesn't duplicate
            st.rerun()
    except:
        pass

# --- 5. TOP HEADER ---
col1, col2 = st.columns([2, 5])
with col1:
    st.markdown('### 📥 INTERNAL RECEIVER')
with col2:
    # Instructions for the user
    st.info("Direct your App to POST to your Streamlit App URL directly.")

st.divider()

# --- 6. SIDEBAR ---
with st.sidebar:
    st.markdown('<p class="brand-title">INTERNAL_TESTER</p>', unsafe_allow_html=True)
    st.markdown('<div class="brand-sep"></div>', unsafe_allow_html=True)
    if st.button("🔄 Clear All", use_container_width=True):
        st.session_state.feed_data = []
        st.session_state.selected_msg = None
        st.session_state.viewed_ids = set()
        st.rerun()
    st.divider()

    for msg in st.session_state.feed_data:
        m_id = msg['id']
        ts = datetime.fromtimestamp(msg['time'], pytz.timezone(USER_TZ)).strftime('%H:%M:%S')
        is_unread = m_id not in st.session_state.viewed_ids

        st.markdown(f'<div class="{"unread-msg" if is_unread else "read-msg"}">', unsafe_allow_html=True)
        if st.button(f"{'🔵' if is_unread else '  '} {ts} | Incoming Data", key=f"m_{m_id}", use_container_width=True):
            st.session_state.selected_msg = msg
            st.session_state.viewed_ids.add(m_id)
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# --- 7. MAIN CONTENT ---
if st.session_state.selected_msg:
    sel = st.session_state.selected_msg
    st.markdown(f"Viewing Request: <span class='id-pill'>{sel['id']}</span>", unsafe_allow_html=True)
    st.markdown("**📦 Raw Payload**")
    try:
        # Try to show as JSON if possible
        parsed = json.loads(sel['message'])
        st.json(parsed)
    except:
        st.code(sel['message'])
else:
    st.info("👈 Waiting for internal data...")