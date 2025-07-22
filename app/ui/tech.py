import streamlit as st

from app.arkmeds_client.auth import ArkmedsAuth
from app.arkmeds_client.client import ArkmedsClient

from .filters import render_filters, show_active_filters

client = ArkmedsClient(ArkmedsAuth.from_secrets())
render_filters(client)
show_active_filters(client)

st.header("\ud83d\udc77 T\u00e9cnicos \u2013 Em constru\u00e7\u00e3o")
