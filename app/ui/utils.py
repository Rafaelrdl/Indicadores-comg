import sys
import streamlit as st

EMOJI_OK = (
    sys.platform != "win32" or getattr(sys, "getwindowsversion", lambda: None)().build >= 9200
    if hasattr(sys, "getwindowsversion")
    else True
)


def safe_label(label: str) -> str:
    allow = st.secrets.get("app", {}).get("allow_emoji", True)
    if allow and EMOJI_OK:
        return label
    return (
        label.encode("utf-16", "surrogatepass").decode("utf-16").encode("ascii", "ignore").decode()
    )
