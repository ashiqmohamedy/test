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

# Initialize session states
if 'clear_before' not in st.session_state:
    st.session_state.clear_before = 0
if 'selected_msg_id' not in st.session_state:
    st.session_state.selected_msg_id = None

# --- DATA FETCHING ---
try:
    r = requests.get(URL, timeout=10)
    messages = []
    if r.status_code == 200:
        raw_lines = r.text.strip().split('\n')
        messages = [json.loads(line) for line in raw_lines if line]

    # Filter messages
    valid_messages = [m for m in messages if
                      m.get('event') == 'message' and m.get('time', 0) > st.session_state.clear_before]

    # Sort messages (Newest first)
    valid_messages.sort(key=lambda x: x.get('time', 0), reverse=True)

    # --- SIDEBAR: Feed & Controls ---
    with st.sidebar:
        st.title("🪝 Webhook Feed")

        # 1. Controls Section
        with st.expander("⚙️ Settings & Controls"):
            is_paused = st.toggle("⏸️ Pause Live Stream", value=False)
            if st.button("🗑️ Clear Logs"):
                st.session_state.clear_before = time.time()
                st.session_state.selected_msg_id = None
                st.rerun()
            refresh_speed = st.slider("Refresh rate (sec)", 2, 20, 5)

        st.divider()

        # 2. Inbound Feed List
        if not valid_messages:
            st.info("Awaiting data...")
            selected_msg = None
        else:
            # Create labels for the radio list
            options = []
            msg_map = {}
            for msg in valid_messages:
                # Local Time Conversion
                utc_time = datetime.fromtimestamp(msg.get('time'), pytz.utc)
                local_time = utc_time.astimezone(pytz.timezone(USER_TZ))
                ts = local_time.strftime('%H:%M:%S')

                # Check for Auth
                has_auth = "🔒" if "Authorization" in msg.get('message', '') else "📥"

                label = f"{has_auth} Received at {ts}"
                options.append(label)
                msg_map[label] = msg

            # The List Selector
            selection = st.radio(
                "Select a message to view details:",
                options,
                label_visibility="collapsed"
            )
            selected_msg = msg_map.get(selection)

    # --- MAIN BODY: Detail View ---
    st.title("Detail View")

    if selected_msg:
        try:
            full_content = json.loads(selected_msg.get('message'))

            # Unwrapping Tunneled format
            if isinstance(full_content, dict) and "headers" in full_content:
                payload = full_content.get('payload', {})
                headers = full_content.get('headers', {})
            else:
                payload = full_content
                headers = {"Notice": "Standard payload"}

            # UI Metrics for current selection
            m1, m2 = st.columns(2)
            m1.metric("Total in Feed", len(valid_messages))
            m2.code(f"ID: {selected_msg.get('id')}")

            st.divider()

            # The JSON Display (Main attraction)
            st.markdown("### 📦 JSON Body")
            st.json(payload, expanded=True)

            # Secondary Details
            col_auth, col_dl = st.columns(2)

            with col_auth:
                auth_header = headers.get('Authorization', '')
                if "Basic" in auth_header:
                    try:
                        encoded = auth_header.replace("Basic ", "")
                        decoded = base64.b64decode(encoded).decode('utf-8')
                        st.success(f"**Verified Auth:** `{decoded}`")
                    except:
                        pass

            with col_dl:
                st.download_button(
                    label="💾 Download Payload",
                    data=json.dumps(payload, indent=4),
                    file_name=f"webhook_{selected_msg.get('id')}.json"
                )

            with st.status("🌐 View Full HTTP Headers"):
                st.json(headers)

        except Exception:
            st.error("Could not parse this specific entry.")
            st.write("Raw data:", selected_msg.get('message'))
    else:
        st.info("Select a webhook from the left sidebar to see the data details.")

    # --- AUTO-REFRESH ---
    if not is_paused:
        time.sleep(refresh_speed)
        st.rerun()

except Exception as e:
    st.error(f"Connection Error: {e}")