import os
import re
import sys
import unicodedata

_SURR = re.compile(r"[\ud800-\udfff]")
_NONBMP = re.compile(r"[\U00010000-\U0010ffff]")


def _strip(text: str) -> str:
    txt = _SURR.sub("", text)
    txt = _NONBMP.sub("", txt)
    return "".join(c for c in txt if unicodedata.category(c) not in ("So", "Sk"))


def emoji_allowed() -> bool:
    cli_flag = "--allow-unsafe-emoji" in sys.argv
    env_flag = os.getenv("ALLOW_EMOJI", "0") == "1"
    return cli_flag and env_flag


def safe_label(text: str) -> str:
    return text if emoji_allowed() else _strip(text)
