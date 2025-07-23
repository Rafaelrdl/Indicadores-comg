from datetime import date

import streamlit as st


def register_pages() -> None:

    if "filters" not in st.session_state:
        st.session_state["filters"] = {
            "dt_ini": date.today().replace(day=1),
            "dt_fim": date.today(),
            "tipo_id": None,
            "estado_ids": [],
            "responsavel_id": None,
        }
        st.session_state["filtros_version"] = 0

    st.sidebar.title("Menu")

