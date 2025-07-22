from datetime import date

import streamlit as st

from .css import inject_global_css
from .utils import safe_label

PAGES = {
    "\ud83c\udfe0 Indicadores": "ui/home.py",
    "\ud83d\udccb Ordens de Servi\u00e7o": "ui/os.py",
    "\ud83d\udd28 Equipamentos": "ui/equip.py",
    "\ud83d\udc77 T\u00e9cnicos": "ui/tech.py",
}


def register_pages() -> None:
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

    st.sidebar.title("Menu")
    for title, path in PAGES.items():
        st.sidebar.page_link(path, label=safe_label(title))

