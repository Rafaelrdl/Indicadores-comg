import streamlit as st


def inject_global_css() -> None:
    st.markdown(
        """
        <style>
          section[data-testid='stSidebar'] { order:2; border-left:1px solid #eee; }
          div.block-container             { padding-right:2rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )