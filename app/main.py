import pathlib
import sys

ROOT = pathlib.Path(__file__).parent
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

import streamlit as st
from arkmeds_client.client import ArkmedsClient
from ui.filters import render_filters, show_active_filters
from ui import register_pages  # noqa: E402

# Configure the main page
st.set_page_config(page_title="Tela Principal", page_icon="🏠", layout="wide")

# Initialize pages and global settings
register_pages()

# Main page content
client = ArkmedsClient.from_session()
render_filters(client)
show_active_filters(client)

st.header("📊 Indicadores – Em construção")
