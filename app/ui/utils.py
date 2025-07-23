import os
import re
import sys
import unicodedata

_SURR = re.compile(r"[\ud800-\udfff]")


def _strip(text: str) -> str:
    no_surr = _SURR.sub("", text)
    return "".join(
        ch for ch in no_surr if unicodedata.category(ch) not in ("So", "Sk")
    )


def safe_label(text: str) -> str:
    """Retorna label seguro em builds Windows narrow; respeita env ALLOW_EMOJI."""
    if os.getenv("ALLOW_EMOJI", "1") == "0" or (
        os.name == "nt" and sys.maxunicode == 0xFFFF
    ):
        return _strip(text)
    return text
