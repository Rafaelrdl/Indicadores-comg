import importlib
import types
import sys
import streamlit as st


def test_safe_label_windows(monkeypatch):
    monkeypatch.setattr(sys, "platform", "win32", raising=False)
    monkeypatch.setattr(
        sys,
        "getwindowsversion",
        lambda: types.SimpleNamespace(build=1000),
        raising=False,
    )
    mod = importlib.import_module("app.ui.utils")
    importlib.reload(mod)
    monkeypatch.setattr(mod, "st", types.SimpleNamespace(secrets={"app": {"allow_emoji": True}}))
    assert mod.safe_label("🏠 Home") == " Home"

