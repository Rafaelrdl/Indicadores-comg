import os
import re
import sys
import unicodedata

_SURROGATE_RE = re.compile(r"[\ud800-\udfff]")


def is_windows_narrow() -> bool:
    return os.name == "nt" and sys.maxunicode == 0xFFFF


def strip_emojis(text: str) -> str:
    # remove surrogates + symbols/emoji categories (So & Sk)
    no_surr = _SURROGATE_RE.sub("", text)
    return "".join(
        ch for ch in no_surr if unicodedata.category(ch) not in ("So", "Sk")
    )


def safe_label(text: str) -> str:
    """Return label safe for Streamlit on Windows narrow builds."""
    if os.getenv("ALLOW_EMOJI", "1") == "0" or is_windows_narrow():
        return strip_emojis(text)
    return text
