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

# Aggressive CSS to remove all top gaps
st.markdown("""
    <style>
        /* Remove gap at the top of the main body */
        .block-container {
            padding-top: 0rem !important;
            padding-bottom: 0rem !important;
            margin-top: -30px !important;
        }
        /* Remove gap at the top of the sidebar */
        [data-testid="stSidebarUserContent"] {
            padding-top: 1rem !important;
        }
        /* Hide the default sidebar navigation/header space */
        [data-testid="stSidebarNav"] {
            display: none;
        }
        /* Tighten up the title spacing */
        h1 {
            margin-top: -20px !important;
            padding-top: 0px !important;
        }
        h3 {
            margin-top: -10px !important;
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

        col_clr, col_rst = st.columns(2)
        if col_clr.button("🗑️ Clear", use_container_width=True):
            st.session_state.clear_before = time.time()
            st.session_state.selected_msg = None
            st.rerun()
        if col_rst.button("🔄 Reset", use_container_width=True):
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
                # Simplified Tile Label
                tile_label = f"{has_auth} Received at {ts}"

                if st.button(tile_label, key=m_id, use_container_width=True):
                    st.session_state.selected_msg = msg

    # --- MAIN BODY: detail view ---
    st.title("🪝 Webhook Tester")

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

            st.markdown(f"#### 📦 Payload ID: `{selected.get('id')}`")
            st.json(payload, expanded=True)

            c1, c2 = st.columns(2)
            with c1:
                auth_h = headers.get('Authorization', '')
                if "Basic" in auth_h:
                    try:
                        decoded = base64.b64decode(auth_h.replace("Basic ", "")).decode('utf-8')
                        st.success(f"**Auth:** `{decoded}`")
                    except:
                        pass

            with c2:
                st.download_button("💾 Download", json.dumps(payload, indent=4), f"{selected.get('id')}.json")

            with st.status("🌐 Full Headers"):
                st.json(headers)

        except Exception:
            st.error("Malformed JSON Entry")
            st.code(selected.get('message'))
    else:
        st.info("👈 Select a webhook from the sidebar to view details.")

    # --- AUTO-REFRESH ---
    time.sleep(2)
    st.rerun()

except Exception as e:
    pass