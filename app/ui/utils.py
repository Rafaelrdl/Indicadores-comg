import os
import sys


def _strip_surrogates(text: str) -> str:
    """Remove qualquer UTF-16 surrogate pair individual ou já combinado."""
    return "".join(c for c in text if ord(c) < 0x10000)


def safe_label(label: str) -> str:
    """Remove emojis/caracteres fora do BMP em ambientes que não suportam."""
    allow = os.getenv("ALLOW_EMOJI", "1") == "1"
    if allow and sys.maxunicode >= 0x10FFFF and os.name != "nt":
        return label
    return _strip_surrogates(label)
