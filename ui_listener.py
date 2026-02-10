import streamlit as st
import requests
import json
import time
from datetime import datetime
import pytz
import urllib3

# Silences the insecure request warning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- 1. CONFIGURATION ---
TOPIC = "wh_receiver_a1b2-c3d4-e5f6-g7h8"
URL = f"https://ntfy.sh/{TOPIC}/json?poll=1"
USER_TZ = 'Asia/Kolkata'

# --- 2. UI SETUP ---
st.set_page_config(page_title="Webhook Tester", layout="wide")

st.markdown("""
    <style>
        /* 1. Adjusted Padding to show header clearly */
        .block-container { 
            padding-top: 5.5rem !important; 
            max-width: 98% !important; 
        }

        /* 2. Remove Internal JSON Scrollbar and compact lines */
        div[data-testid="stJson"] > div {
            overflow: visible !important;
            max-height: none !important;
        }
        div[data-testid="stJson"] { 
            line-height: 1.0 !important; 
        }

        /* 3. Compact Header Spacing */
        hr { margin-top: 0.5rem !important; margin-bottom: 0.8rem !important; }

        /* Sidebar Styles - DO NOT CHANGE */
        .brand-title { font-size: 1.6rem !important; font-weight: 800 !important; color: #10b981; font-family: 'Courier New', Courier, monospace !important; margin-bottom: 0px !important; letter-spacing: -1px; }
        .brand-sep { border: 0; height: 2px; background: linear-gradient(to right, #10b981, transparent); margin-bottom: 1rem !important; margin-top: 5px !important; }

        .stButton > button { 
            height: 32px !important; 
            margin-bottom: -18px !important; 
            border-radius: 4px !important; 
            text-align: left !important; 
            font-family: 'Courier New', Courier, monospace !important; 
            font-size: 10.5px !important; 
            border: none !important; 
            background-color: transparent !important; 
            padding-left: 2px !important; 
            box-shadow: none !important;
            white-space: nowrap !important;
            overflow: hidden !important;
        }
        .stButton > button:hover { background-color: rgba(16, 185, 129, 0.1) !important; color: #10b981 !important; }

        /* Viewing Panel Compactness */
        [data-testid="stVerticalBlock"] > div { padding-bottom: 0px !important; margin-bottom: -10px !important; }

        .header-container {
            font-family: 'Courier New', Courier, monospace;
            font-size: 14px;
            font-weight: 700;
            color: #10b981;
            display: flex;
            align-items: center;
            gap: 15px;
        }
        .url-box {
            background-color: #1e1e1e;
            padding: 4px 10px;
            border-radius: 4px;
            color: #ffffff;
            font-weight: 400;
            font-size: 13px;
        }
    </style>
""", unsafe_allow_html=True)

# 3. Session State Management
if 'initialized' not in st.session_state:
    st.session_state.session_gate = time.time()
    st.session_state.feed_data = []
    st.session_state.seen_ids = set()
    st.session_state.selected_msg = None
    st.session_state.viewed_ids = set()
    st.session_state.initialized = True

# --- 4. TOP HEADER (Fixed Overlap) ---
st.markdown(f"""
    <div class="header-container">
        <span>📡 ACTIVE ENDPOINT</span>
        <span class="url-box">https://ntfy.sh/{TOPIC}</span>
    </div>
""", unsafe_allow_html=True)

st.divider()

# --- 5. DATA FETCHING ---
try:
    r = requests.get(URL, timeout=5, verify=False)
    if r.status_code == 200:
        raw_lines = r.text.strip().split('\n')
        for line in raw_lines:
            if not line: continue
            msg = json.loads(line)
            m_id = msg.get('id')
            m_time = float(msg.get('time', 0))

            if (msg.get('event') == 'message' and
                    m_time > st.session_state.session_gate and
                    m_id not in st.session_state.seen_ids):

                source_ip = "Unknown IP"
                try:
                    inner_msg = json.loads(msg.get('message', '{}'))
                    payload = inner_msg.get('payload', inner_msg)
                    source_ip = payload.get('sannavServerIp', 'No IP')
                except:
                    pass

                msg['extracted_ip'] = source_ip
                st.session_state.feed_data.append(msg)
                st.session_state.seen_ids.add(m_id)

        st.session_state.feed_data.sort(key=lambda x: x.get('time', 0), reverse=True)
except:
    pass

# --- 6. SIDEBAR ---
with st.sidebar:
    st.markdown('<p class="brand-title">WEBHOOK_TESTER</p>', unsafe_allow_html=True)
    st.markdown('<div class="brand-sep"></div>', unsafe_allow_html=True)

    if st.button("🔄 Reset", use_container_width=True):
        st.session_state.session_gate = time.time()
        st.session_state.feed_data = []
        st.session_state.seen_ids = set()
        st.session_state.selected_msg = None
        st.session_state.viewed_ids = set()
        st.rerun()

    st.divider()
    search_query = st.text_input(label="Search", placeholder="🔍 Filter...", key="search_bar",
                                 label_visibility="collapsed").lower()

    if not st.session_state.feed_data:
        st.markdown(
            '<p style="font-size:11px; color:grey; padding-left:10px; margin-top:20px;">Listening for new payloads...</p>',
            unsafe_allow_html=True)
    else:
        for msg in st.session_state.feed_data:
            if search_query and search_query not in msg.get('message', '').lower(): continue
            m_id = msg.get('id', 'N/A')
            dt_obj = datetime.fromtimestamp(msg.get('time'), pytz.utc).astimezone(pytz.timezone(USER_TZ))
            date_str = dt_obj.strftime('%d-%b-%y')
            time_str = dt_obj.strftime('%H:%M:%S')
            is_new = m_id not in st.session_state.viewed_ids
            ip_label = msg.get('extracted_ip', 'No IP')

            label = f"{'🔵' if is_new else '  '} {date_str}, {time_str} | {ip_label}"
            if st.button(label, key=f"msg_{m_id}", use_container_width=True):
                st.session_state.selected_msg = msg
                st.session_state.viewed_ids.add(m_id)
                st.rerun()

# --- 7. MAIN CONTENT ---
if st.session_state.selected_msg:
    sel = st.session_state.selected_msg
    if float(sel.get('time', 0)) > st.session_state.session_gate:
        try:
            full_content = json.loads(sel.get('message'))
            payload = full_content.get('payload', full_content)
            headers = full_content.get('headers', {"Info": "Direct payload received"})

            col_meta, col_dl = st.columns([4, 1])
            with col_meta:
                st.markdown(f"**Viewing Request:** `{sel.get('id')}`")
            with col_dl:
                st.download_button(
                    label="💾 Download JSON",
                    data=json.dumps(payload, indent=4),
                    file_name=f"webhook_{sel.get('id')}.json",
                    mime="application/json",
                    use_container_width=True
                )

            st.markdown("**📦 JSON Body**")
            st.json(payload)

            with st.expander("🌐 View HTTP Headers", expanded=False):
                st.json(headers)
        except Exception as e:
            st.error(f"Error parsing content")
            st.json(sel.get('message'))
    else:
        st.session_state.selected_msg = None
        st.rerun()
else:
    st.info("👈 Select a webhook from the sidebar to begin.")

# --- 8. STABLE REFRESH ---
time.sleep(4)
st.rerun()