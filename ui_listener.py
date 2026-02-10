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

# 3. Session State Management
if 'initialized' not in st.session_state:
    st.session_state.session_gate = time.time()
    st.session_state.feed_data, st.session_state.seen_ids = [], set()
    st.session_state.selected_msg, st.session_state.viewed_ids = None, set()
    st.session_state.initialized = True

# --- DYNAMIC CSS ---
active_id = st.session_state.selected_msg.get('id') if st.session_state.selected_msg else "NONE"

st.markdown(f"""
    <style>
        .block-container {{ padding-top: 5.5rem !important; max-width: 98% !important; }}

        /* 1. Kill JSON internal scrollbars */
        div[data-testid="stJson"], div[data-testid="stJson"] > div, div[data-testid="stJson"] pre {{
            overflow: visible !important;
            max-height: none !important;
        }}
        div[data-testid="stJson"] {{ line-height: 1.0 !important; }}

        hr {{ margin-top: 0.5rem !important; margin-bottom: 0.8rem !important; }}

        /* Sidebar Branding */
        .brand-title {{ font-size: 1.6rem !important; font-weight: 800 !important; color: #10b981; font-family: 'Courier New', Courier, monospace !important; margin-bottom: 0px !important; letter-spacing: -1px; }}