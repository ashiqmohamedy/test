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

# 3. Session State
if 'initialized' not in st.session_state:
    st.session_state.session_gate = time.time()
    st.session_state.feed_data, st.session_state.seen_ids = [], set()
    st.session_state.selected_msg, st.session_state.viewed_ids = None, set()
    st.session_state.initialized = True

# Dynamic CSS for the Persistent Highlight
active_id = st.session_state.selected_msg.get('id') if st.session_state.selected_msg else None

st.markdown(f"""
    <style>
        .block-container {{ padding-top: 5.5rem !important; max-width: 98% !important; }}
        div[data-testid="stJson"] > div {{ overflow: visible !important; max-height: none !important; }}
        div[data-testid="stJson"] {{ line-height: 1.0 !important; }}
        hr {{ margin-top: 0.5rem !important; margin-bottom: 0.8rem !important; }}

        /* Sidebar Branding */
        .brand-title {{ font-size: 1.6rem !important; font-weight: 800 !important; color: #10b981; font-family: 'Courier New', Courier, monospace !important; margin-bottom: 0px !important; letter-spacing: -1px; }}
        .brand-sep {{ border: 0; height: 2px; background: linear-gradient(to right, #10b981, transparent); margin-bottom: 1rem !important; margin-top: 5px !important; }}

        /* General Sidebar Button Style */
        .stButton > button {{ 
            height: 32px !important; 
            margin-bottom: -18px !important; 
            border-radius: 4px !important; 
            text-align: left !important; 
            font-family: 'Courier New', Courier, monospace !important; 
            font-size: 10.5px !important; 
            border: none !important; 
            background-color: transparent !important; 
            padding-left: 8px !important;
            box-shadow: none !important;
            white-space: nowrap !important;
            overflow: hidden !important;
            transition: all 0.2s ease;
        }}

        /* Persistent Active State for the specific ID */
        div[data-testid="stSidebar"] div[data-key="m_{active_id}"] button {{
            background-color: rgba(16, 185, 129, 0.2) !important;
            color: #10b981 !important;
            border-left: 4px solid #10b981 !important;
            font-weight: bold !important;
        }}

        .stButton > button:hover {{ background-color: rgba(16, 185, 129, 0.1) !important; color: #10b981 !important; }}

        .endpoint-label {{ font-family: 'Courier New', Courier, monospace; font-size: 14px; font-weight: 700; color: #10b981; margin-top: 10px !important; white-space: nowrap; }}
        .id-pill {{ background-color: #1e1e1e; padding: 2px 8px; border-radius: 12px; border: 1px solid #333; font-family: monospace; color: #10b981; font-size: 12px; }}
    </style>
""", unsafe_allow_html=True)

# --- 4. TOP HEADER ---
col1, col2, col3 = st.columns([1.6, 4, 3])
status_icon = "🟢"
with col1:
    st.markdown(f'<p class="endpoint-label">{status_icon} ACTIVE ENDPOINT</p>', unsafe_allow_html=True)
with col2:
    st.code(f"https://ntfy.sh/{TOPIC}", language="text")
st.divider()

# --- 5. DATA FETCHING ---
try:
    r = requests.get(URL, timeout=5, verify=False)
    if r.status_code == 200:
        raw_lines = r.text.strip().split('\n')
        for line in raw_lines:
            if not line: continue
            msg = json.loads(line)
            m_id, m_time = msg.get('id'), float(msg.get('time', 0))
            if (
                    msg.get('event') == 'message' and m_time > st.session_state.session_gate and m_id not in st.session_state.seen_ids):
                source_ip = "No IP"
                try:
                    inner = json.loads(msg.get('message', '{}'))
                    source_ip = inner.get('payload', inner).get('sannavServerIp', 'No IP')
                except:
                    pass
                msg['extracted_ip'] = source_ip
                st.session_state.feed_data.append(msg)
                st.session_state.seen_ids.add(m_id)
        st.session_state.feed_data.sort(key=lambda x: x.get('time', 0), reverse=True)
except:
    status_icon = "🔴"

# --- 6. SIDEBAR ---
with st.sidebar:
    st.markdown('<p class="brand-title">WEBHOOK_TESTER</p>', unsafe_allow_html=True)
    st.markdown('<div class="brand-sep"></div>', unsafe_allow_html=True)
    if st.button("🔄 Reset", use_container_width=True):
        st.session_state.feed_data, st.session_state.seen_ids = [], set()
        st.session_state.selected_msg, st.session_state.viewed_ids = None, set()
        st.session_state.session_gate = time.time()
        st.rerun()
    st.divider()
    search = st.text_input("Filter", placeholder="🔍 Filter...", key="s_bar", label_visibility="collapsed").lower()

    for msg in st.session_state.feed_data:
        if search and search not in msg.get('message', '').lower(): continue
        m_id = msg.get('id', 'N/A')
        dt_obj = datetime.fromtimestamp(msg.get('time'), pytz.utc).astimezone(pytz.timezone(USER_TZ))
        ts_str = dt_obj.strftime('%d-%b-%y, %H:%M:%S')

        label = f"{'🔵' if m_id not in st.session_state.viewed_ids else '  '} {ts_str} | {msg.get('extracted_ip')}"

        # Unique key used by CSS for persistent highlighting
        if st.button(label, key=f"m_{m_id}", use_container_width=True):
            st.session_state.selected_msg = msg
            st.session_state.viewed_ids.add(m_id)
            st.rerun()

# --- 7. MAIN CONTENT ---
if st.session_state.selected_msg:
    sel = st.session_state.selected_msg
    if float(sel.get('time', 0)) > st.session_state.session_gate:
        full = json.loads(sel.get('message'))
        p, h = full.get('payload', full), full.get('headers', {"Info": "Direct payload"})
        c_m, c_d = st.columns([4, 1])
        with c_m:
            st.markdown(f"Viewing Request: <span class='id-pill'>{sel.get('id')}</span>", unsafe_allow_html=True)
        with c_d:
            st.download_button("💾 Download JSON", json.dumps(p, indent=4), f"wh_{sel.get('id')}.json",
                               "application/json", use_container_width=True)
        st.markdown("**📦 JSON Body**")
        st.json(p)
        with st.expander("🌐 View HTTP Headers", expanded=False):
            st.json(h)
    else:
        st.session_state.selected_msg = None; st.rerun()
else:
    st.info("👈 Select a webhook from the sidebar to begin.")

time.sleep(4);
st.rerun()