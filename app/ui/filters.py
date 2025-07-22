import streamlit as st


def render_filters() -> dict:
    st.sidebar.date_input("Data in\u00edcio")
    st.sidebar.date_input("Data fim")
    return {}
