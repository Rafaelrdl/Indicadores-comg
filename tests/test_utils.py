import importlib
import os
import sys


def test_safe_label_windows(monkeypatch):
    monkeypatch.setattr(os, "name", "nt", raising=False)
    monkeypatch.setattr(sys, "maxunicode", 0xFFFF, raising=False)
    mod = importlib.import_module("app.ui.utils")
    importlib.reload(mod)
    assert mod.safe_label("🏠 Home") == " Home"


def test_strip_surrogates(monkeypatch):
    monkeypatch.setenv("ALLOW_EMOJI", "0")
    from ui.utils import safe_label
    raw = "🏠 Home"
    cleaned = safe_label(raw)
    assert cleaned.strip() == "Home"
