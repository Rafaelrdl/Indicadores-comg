from ui.utils import safe_label


def test_safe_label_strips_emoji(monkeypatch):
    monkeypatch.setenv("ALLOW_EMOJI", "0")
    assert safe_label("🏠 Home")[0] != "🏠"
    assert safe_label("🏠 Home").strip() == "Home"


def test_safe_label_removes_all_nonbmp(monkeypatch):
    monkeypatch.setenv("ALLOW_EMOJI", "0")
    emo = "📑 Ordens"
    assert safe_label(emo).lstrip().startswith("Ordens")
