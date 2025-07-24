import streamlit as st
from arkmeds_client.client import ArkmedsClient

from app.ui.filters import render_filters, show_active_filters

st.set_page_config(page_title="Técnicos", page_icon="👷", layout="wide")

client = ArkmedsClient.from_session()
render_filters(client)
show_active_filters(client)

st.header("👷 Técnicos – Em construção")
