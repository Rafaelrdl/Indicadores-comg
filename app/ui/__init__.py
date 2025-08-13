from datetime import date

import streamlit as st

from .css import inject_global_css


def register_pages() -> None:
    """Configure Streamlit and initialize session state."""
    st.set_page_config(page_title="Dashboard Arkmeds", page_icon="🩺", layout="wide")
    inject_global_css()

    if "filters" not in st.session_state:
        st.session_state["filters"] = {
            "dt_ini": date.today().replace(day=1),
            "dt_fim": date.today(),
            "tipo_id": None,
            "estado_ids": [],
            "responsavel_id": None,
        }
        st.session_state["filtros_version"] = 0
