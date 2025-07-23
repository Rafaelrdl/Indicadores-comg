import os
import sys
import unicodedata

EMOJI_ALLOWED = False if os.name == "nt" and sys.maxunicode == 0xFFFF else True


def safe_label(label: str) -> str:
    if EMOJI_ALLOWED and os.getenv("ALLOW_EMOJI", "1") == "1":
        return label
    return "".join(c for c in label if unicodedata.category(c) != "So")
