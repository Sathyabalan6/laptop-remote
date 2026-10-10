"""Unit tests for active window and media preset detection."""

from laptop_remote.core import window


class TestWindowPresetDetection:
    def test_youtube_preset_detection(self, monkeypatch):
        monkeypatch.setattr(window, "_get_active_window_title", lambda: "Lofi Beats - YouTube - Google Chrome")
        assert window.detect_active_preset() == "youtube_hotstar"

    def test_hotstar_preset_detection(self, monkeypatch):
        monkeypatch.setattr(window, "_get_active_window_title", lambda: "Disney+ Hotstar - Brave")
        assert window.detect_active_preset() == "youtube_hotstar"

    def test_vlc_preset_detection(self, monkeypatch):
        monkeypatch.setattr(window, "_get_active_window_title", lambda: "VLC media player")
        assert window.detect_active_preset() == "vlc"

    def test_netflix_preset_detection(self, monkeypatch):
        monkeypatch.setattr(window, "_get_active_window_title", lambda: "Stranger Things - Netflix - Firefox")
        assert window.detect_active_preset() == "universal"

    def test_prime_video_preset_detection(self, monkeypatch):
        monkeypatch.setattr(window, "_get_active_window_title", lambda: "The Boys - Prime Video")
        assert window.detect_active_preset() == "universal"

    def test_unknown_app_returns_none(self, monkeypatch):
        monkeypatch.setattr(window, "_get_active_window_title", lambda: "Visual Studio Code - laptop-remote")
        assert window.detect_active_preset() is None

    def test_none_window_title_returns_none(self, monkeypatch):
        monkeypatch.setattr(window, "_get_active_window_title", lambda: None)
        assert window.detect_active_preset() is None
