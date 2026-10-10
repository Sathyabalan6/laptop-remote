"""Unit tests for preset loading/persistence."""

import json
import os

from laptop_remote.core import config


class TestLoadPresets:
    def test_returns_dict(self):
        presets = config.load_presets()
        assert isinstance(presets, dict)

    def test_contains_default_profiles(self):
        presets = config.load_presets()
        for profile in ("universal", "youtube_hotstar", "vlc"):
            assert profile in presets

    def test_universal_has_core_actions(self):
        presets = config.load_presets()
        universal = presets["universal"]
        for action in ("play_pause", "skip_forward", "skip_back", "fullscreen"):
            assert action in universal

    def test_missing_profiles_are_backfilled(self, tmp_path, monkeypatch):
        # Point PRESETS_PATH at a partial file; loader should backfill defaults.
        partial = tmp_path / "presets.json"
        partial.write_text(json.dumps({"universal": {"play_pause": "space"}}))

        monkeypatch.setattr(config, "PRESETS_PATH", str(partial))
        presets = config.load_presets()

        assert "universal" in presets
        assert "vlc" in presets  # backfilled from defaults
        assert presets["universal"]["play_pause"] == "space"

    def test_corrupt_file_falls_back_to_defaults(self, tmp_path, monkeypatch):
        bad = tmp_path / "presets.json"
        bad.write_text("{ this is not valid json")

        monkeypatch.setattr(config, "PRESETS_PATH", str(bad))
        presets = config.load_presets()

        assert presets == config.DEFAULT_PRESETS


class TestSavePresets:
    def test_save_presets_success(self, tmp_path, monkeypatch):
        out_file = tmp_path / "presets.json"
        monkeypatch.setattr(config, "PRESETS_PATH", str(out_file))

        custom = {"custom_app": {"play_pause": "p"}}
        assert config.save_presets(custom) is True
        assert json.loads(out_file.read_text()) == custom

    def test_save_presets_invalid_type(self):
        assert config.save_presets("invalid_string") is False


class TestExecutableDir:
    def test_returns_existing_directory(self):
        d = config.get_executable_dir()
        assert os.path.isdir(d)
