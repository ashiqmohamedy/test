import streamlit as st
import requests
import json
import time
import base64
from datetime import datetime
import pytz

# --- CONFIGURATION ---
TOPIC = "wh_receiver_a1b2-c3d4-e5f6-g7h8"
URL = f"https://ntfy.sh/{TOPIC}/json?poll=1"
USER_TZ = 'Asia/Kolkata'


def make_bold(text):
    return text.replace("0", "𝟎").replace("1", "𝟏").replace("2", "𝟐").replace("3", "𝟑").replace("4", "𝟒").replace("5",
                                                                                                                  "𝟓").replace(
        "6", "𝟔").replace("7", "𝟕").replace("8", "𝟖").replace("9", "𝟗").replace("P", "𝐏").replace("O", "𝐎").replace("S",
                                                                                                                    "𝐒").replace(
        "T", "𝐓")


# --- UI SETUP ---
st.set_page_config(page_title="Webhook Tester", layout="wide")

st.markdown("""
    <style>
        .block-container { padding-top: 5rem !important; max-width: 98% !important; }
        .brand-title { font-size: 1.6rem !important; font-weight: 800 !important; color: #10b981; font-family: 'Courier New', Courier, monospace !important; margin-bottom: 0px !important; letter-spacing: -1px; }
        .brand-sep { border: 0; height: 2px; background: linear-gradient(to right, #10b981, transparent); margin-bottom: 1rem !important; margin-top: 5px !important; }
        [data-testid="stSidebarUserContent"] { padding-top: 1rem !important; }
        div[data-testid="stTextInput"] { margin-top: -15px !important; }
        div[data-testid="stJson"] { line-height: 1.1 !important; }
        .stButton > button { height: 32px !important; margin-bottom: -18px !important; border-radius: 0px !important; text-align: left !important; font-family: 'Courier New', Courier, monospace !important; font-size: 11px !important; border: none !important; background-color: transparent !important; padding-left: 5px !important; }
        .stButton > button:hover { background-color: rgba(16, 185, 129, 0.1) !important; color: #10b981 !important; }
        [data-testid="stHorizontalBlock"] { gap: 0.5rem !important; margin-bottom: -5px !important; }
    </style>
""", unsafe_allow_html=True)

if 'clear_before' not in st.session_state:
    st.session_state.clear_before = time.time()  # Start fresh on first load
if 'selected_msg' not in st.session_state:
    st.session_state.selected_msg = None
if 'viewed_ids' not in st.session_state:
    st.session_state.viewed_ids = set()

# --- DATA FETCHING ---
try:
    r = requests.get(URL, timeout=10)
    valid_messages = []
    if r.status_code == 200:
        raw_lines = r.text.strip().split('\n')
        for line in raw_lines:
            if not line: continue
            msg = json.loads(line)

            # CRITICAL FILTER: Only accept messages sent AFTER the 'Clear' button was last pressed
            if msg.get('event') == 'message' and msg.get('time', 0) > st.session_state.clear_before:
                valid_messages.append(msg)

    # Sort: Newest at the top
    valid_messages.sort(key=lambda x: x.get('time', 0), reverse=True)

    # --- SIDEBAR ---
    with st.sidebar:
        st.markdown('<p class="brand-title">WEBHOOK_TESTER</p>', unsafe_allow_html=True)
        st.markdown('<div class="brand-sep"></div>', unsafe_allow_html=True)

        col_clr, col_rst = st.columns(2)
        with col_clr:
            if st.button("🗑️ Clear", use_container_width=True):
                # Update the timestamp threshold to 'right now'
                st.session_state.clear_before = time.time()
                st.session_state.selected_msg = None
                # We don't clear viewed_ids so we remember old ones if they reappear
                st.rerun()
        with col_rst:
            if st.button("🔄 Reset", use_container_width=True):
                for key in list(st.session_state.keys()): del st.session_state[key]
                st.rerun()

        st.divider()
        search_query = st.text_input("", placeholder="🔍 Filter feed...", label_visibility="collapsed").lower()

        if not valid_messages:
            st.info("Awaiting new data...")
        else:
            filtered_messages = [m for m in valid_messages if search_query in m.get('message', '').lower()]

            for msg in filtered_messages:
                m_id = msg.get('id', 'N/A')
                utc_time = datetime.fromtimestamp(msg.get('time'), pytz.utc)
                ts = utc_time.astimezone(pytz.timezone(USER_TZ)).strftime('%H:%M:%S')

                source_ip = "Unknown"
                try:
                    inner_data = json.loads(msg.get('message', '{}'))
                    if "payload" in inner_data:
                        source_ip = inner_data["payload"].get("sannavServerIp", "Unknown")
                    else:
                        source_ip = inner_data.get("sannavServerIp", "Unknown")
                except:
                    pass

                is_new = m_id not in st.session_state.viewed_ids
                auth_icon = "🔒" if "Authorization" in msg.get('message', '') else " "

                if is_new:
                    label_text = f"{ts}: {source_ip}"
                    log_label = f"🔵 {make_bold(label_text)} {auth_icon}"
                else:
                    log_label = f"   {ts}: {source_ip} {auth_icon}"

                if st.button(log_label, key=m_id, use_container_width=True):
                    st.session_state.selected_msg = msg
                    st.session_state.viewed_ids.add(m_id)

    # --- MAIN BODY ---
    selected = st.session_state.selected_msg
    if selected:
        try:
            full_content = json.loads(selected.get('message'))
            if isinstance(full_content, dict) and "headers" in full_content:
                payload = full_content.get('payload', {})
                headers = full_content.get('headers', {})
            else:
                payload = full_content
                headers = {"Notice": "Standard payload"}

            c_meta, c_dl = st.columns([3, 1])
            with c_meta:
                st.markdown(f"**Payload ID:** `{selected.get('id')}`")
            with c_dl:
                st.download_button("💾 Download JSON", json.dumps(payload, indent=4), f"{selected.get('id')}.json",
                                   use_container_width=True)

            st.markdown("**📦 JSON Body**")
            st.json(payload, expanded=True)
            st.divider()
            with st.expander("🌐 Full HTTP Headers", expanded=True):
                st.json(headers)
        except Exception:
            st.error("Error parsing payload details.")
    else:
        st.info("👈 Select a request from the filtered feed to inspect details.")

    time.sleep(2)
    st.rerun()

except Exception:
    pass