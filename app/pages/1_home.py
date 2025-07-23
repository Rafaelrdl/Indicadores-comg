import streamlit as st
from arkmeds_client.auth import ArkmedsAuth
from arkmeds_client.client import ArkmedsClient

from ui.filters import render_filters, show_active_filters

st.set_page_config(page_title="Indicadores", page_icon="🏠")

client = ArkmedsClient(ArkmedsAuth.from_secrets())
render_filters(client)
show_active_filters(client)

st.header("📊 Indicadores – Em construção")
