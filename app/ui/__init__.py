import streamlit as st

from .css import inject_global_css
from .filters import render_filters

PAGES = {
    "\ud83c\udfe0 Indicadores": "ui/home.py",
    "\ud83d\udccb Ordens de Servi\u00e7o": "ui/os.py",
    "\ud83d\udd28 Equipamentos": "ui/equip.py",
    "\ud83d\udc77 T\u00e9cnicos": "ui/tech.py",
}


def register_pages() -> None:
    inject_global_css()

    if "filters" not in st.session_state:
        st.session_state["filters"] = {}

    st.sidebar.title("Menu")
    for title, path in PAGES.items():
        st.sidebar.page_link(path, label=title)

    render_filters()
