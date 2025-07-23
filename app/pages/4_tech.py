import streamlit as st

from app.arkmeds_client.auth import ArkmedsAuth
from app.arkmeds_client.client import ArkmedsClient
from app.ui.filters import render_filters, show_active_filters

st.set_page_config(page_title="Técnicos", page_icon="👷")

client = ArkmedsClient(ArkmedsAuth.from_secrets())
render_filters(client)
show_active_filters(client)

st.header("👷 Técnicos – Em construção")
