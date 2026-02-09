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

# --- UI SETUP ---
st.set_page_config(page_title="Webhook Tester", layout="wide")

# Professional CSS for API Log density and sidebar structure
st.markdown("""
    <style>
        .block-container {
            padding-top: 3rem !important;
            max-width: 98% !important;
        }
        h1 {
            font-size: 1.5rem !important;
            font-weight: 700 !important;
            margin-bottom: 0.5rem !important;
        }
        /* JSON display styling */
        div[data-testid="stJson"] {
            line-height: 1.1 !important;
        }

        /* Professional Sidebar Button Styling */
        .stButton > button {
            height: 34px !important;
            margin-bottom: -12px !important;
            border-radius: 4px !important;
            text-align: left !important;
            font-family: 'Courier New', Courier, monospace !important;
            font-size: 12px !important;
            border: 1px solid #f0f2f6 !important;
            background-color: white !important;
        }

        /* Highlight for 'POST' text inside button */
        .stButton > button:hover {
            border-color: #ff4b4b !important;
            color: #ff4b4b !important;
        }

        [data-testid="stHorizontalBlock"] {
            gap: 0.5rem !important;
        }
    </style>
""", unsafe_allow_html=True)

# Initialize session states
if 'clear_before' not in st.session_state:
    st.session_state.clear_before = 0
if 'selected_msg' not in st.session_state:
    st.session_state.selected_msg = None

# --- DATA FETCHING ---
try:
    r = requests.get(URL, timeout=10)
    messages = []
    if r.status_code == 200:
        raw_lines = r.text.strip().split('\n')
        messages = [json.loads(line) for line in raw_lines if line]

    valid_messages = [m for m in messages if
                      m.get('event') == 'message' and m.get('time', 0) > st.session_state.clear_before]

    valid_messages.sort(key=lambda x: x.get('time', 0), reverse=True)

    # --- SIDEBAR: The API Log Feed ---
    with st.sidebar:
        st.markdown("### 🪝 Webhook Feed")

        col_clr, col_rst = st.columns(2)
        with col_clr:
            if st.button("🗑️ Clear", use_container_width=True):
                st.session_state.clear_before = time.time()
                st.session_state.selected_msg = None
                st.rerun()
        with col_rst:
            if st.button("🔄 Reset", use_container_width=True):
                for key in list(st.session_state.keys()): del st.session_state[key]
                st.rerun()

        st.divider()

        if not valid_messages:
            st.info("Awaiting data...")
        else:
            for msg in valid_messages:
                m_id = msg.get('id', 'N/A')
                utc_time = datetime.fromtimestamp(msg.get('time'), pytz.utc)
                ts = utc_time.astimezone(pytz.timezone(USER_TZ)).strftime('%H:%M:%S')

                # Check for Auth
                has_auth = "🔒" if "Authorization" in msg.get('message', '') else "⚡"

                # Professional Label: METHOD | TIME | ICON
                # We use fixed-width spacing for a tabular feel
                log_label = f"POST | {ts} | {has_auth}"

                if st.button(log_label, key=m_id, use_container_width=True):
                    st.session_state.selected_msg = msg

    # --- MAIN BODY: detail view ---
    st.title("Webhook Tester")

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

            st.markdown(f"**Payload ID:** `{selected.get('id')}`")
            st.json(payload, expanded=True)

            c1, c2 = st.columns([3, 1])
            with c1:
                auth_h = headers.get('Authorization', '')
                if "Basic" in auth_h:
                    try:
                        decoded = base64.b64decode(auth_h.replace("Basic ", "")).decode('utf-8')
                        st.success(f"**Auth:** `{decoded}`")
                    except:
                        pass

            with c2:
                st.download_button("💾 Download", json.dumps(payload, indent=4), f"{selected.get('id')}.json",
                                   use_container_width=True)

            with st.status("🌐 Full Headers", expanded=False):
                st.json(headers)

        except Exception:
            pass
    else:
        st.info("👈 Select a request from the feed to view details.")

    time.sleep(2)
    st.rerun()

except Exception:
    pass