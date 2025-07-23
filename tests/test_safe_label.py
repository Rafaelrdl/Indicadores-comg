from ui.utils import safe_label, is_windows_narrow


def test_safe_label_removes_surrogates(monkeypatch):
    win_narrow_mock = True
    label = "🏠 Home"  # U+1F3E0
    if win_narrow_mock:
        monkeypatch.setenv("ALLOW_EMOJI", "0")
    cleaned = safe_label(label) if win_narrow_mock else label
    assert "🏠" not in cleaned
    assert cleaned.strip() == "Home"
