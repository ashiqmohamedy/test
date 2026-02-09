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

# Professional CSS: Tightening data density and alignment
st.markdown("""
    <style>
        /* Reduce main header size and spacing */
        .block-container {
            padding-top: 3rem !important;
            max-width: 98% !important;
        }
        h1 {
            font-size: 1.5rem !important;
            font-weight: 700 !important;
            margin-bottom: 0.5rem !important;
            color: #31333F;
        }
        h3 {
            font-size: 1.1rem !important;
            margin-bottom: 0.5rem !important;
        }
        h4 {
            font-size: 1rem !important;
            margin-top: 0px !important;
        }

        /* Reduce gap between JSON lines */
        div[data-testid="stJson"] {
            line-height: 1.1 !important;
            background-color: #f8f9fa;
            border-radius: 4px;
            padding: 10px !important;
        }

        /* Tighten sidebar tile spacing */
        .stButton > button {
            height: 32px !important;
            padding-top: 0px !important;
            padding-bottom: 0px !important;
            margin-bottom: -12px !important;
            font-size: 13px !important;
            border-radius: 4px !important;
        }

        /* Align Sidebar Buttons */
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

    # --- SIDEBAR: The Tile Feed ---
    with st.sidebar:
        st.markdown("### 🪝 Webhook Feed")

        # Aligned Controls
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

                has_auth = "🔒" if "Authorization" in msg.get('message', '') else "📥"
                tile_label = f"{has_auth} {ts}"

                if st.button(tile_label, key=m_id, use_container_width=True):
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

            # The JSON Display
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
        st.info("👈 Select a webhook from the sidebar.")

    time.sleep(2)
    st.rerun()

except Exception:
    pass