import streamlit as st

cfg = st.secrets["arkmeds"]
EMAIL = cfg.get("email")
PASSWORD = cfg.get("password")
BASE_URL = cfg.get("base_url")
TOKEN = cfg.get("token")
