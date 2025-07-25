import pathlib
import sys

ROOT = pathlib.Path(__file__).parent
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

import streamlit as st
from arkmeds_client.client import ArkmedsClient
from app.ui.filters import render_filters, show_active_filters
from app.ui import register_pages  # noqa: E402

# Initialize filters in session state first
if "filters" not in st.session_state:
    from datetime import date
    st.session_state["filters"] = {
        "dt_ini": date.today().replace(day=1),
        "dt_fim": date.today(),
        "tipo_id": None,
        "estado_ids": [],
        "responsavel_id": None,
    }

# Configure the main page
st.set_page_config(page_title="Tela Principal", page_icon="🏠", layout="wide")

# Initialize pages and global settings
register_pages()

# Main page content
try:
    client = ArkmedsClient.from_session()
    render_filters(client)
    show_active_filters(client)
except Exception as e:
    st.error(f"Erro ao conectar com o cliente Arkmeds: {str(e)}")
    st.info("Verifique as credenciais em .streamlit/secrets.toml")

st.header("📊 Indicadores")
