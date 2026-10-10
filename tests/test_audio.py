"""Unit tests for the audio subsystem and thread safety."""

import threading

from laptop_remote.core import audio


class TestAudioControls:
    def test_get_volume_structure(self):
        vol_info = audio.get_volume()
        assert isinstance(vol_info, dict)
        assert "volume" in vol_info
        assert "muted" in vol_info
        assert 0 <= vol_info["volume"] <= 100
        assert isinstance(vol_info["muted"], bool)

    def test_set_volume_clamping(self):
        res_high = audio.set_volume(150)
        assert res_high["volume"] == 100

        res_low = audio.set_volume(-20)
        assert res_low["volume"] == 0

        res_mid = audio.set_volume(42)
        assert res_mid["volume"] == 42

    def test_set_volume_type_coercion(self):
        res_str = audio.set_volume("75")
        assert res_str["volume"] == 75

        res_float = audio.set_volume(33.7)
        assert res_float["volume"] == 34

        # Garbage value falls back to previous volume without crashing
        res_invalid = audio.set_volume("invalid_volume")
        assert res_invalid["volume"] == 34

    def test_toggle_mute(self):
        initial = audio.get_volume()["muted"]
        toggled = audio.toggle_mute()
        assert toggled["muted"] == (not initial)

        # Restore original state
        restored = audio.toggle_mute()
        assert restored["muted"] == initial

    def test_concurrent_audio_access(self):
        """Verify thread safety with audio_lock under concurrent updates."""
        errors = []

        def worker(vol):
            try:
                for _ in range(20):
                    audio.set_volume(vol)
                    info = audio.get_volume()
                    assert 0 <= info["volume"] <= 100
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker, args=(v,)) for v in (10, 30, 50, 70, 90)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors
