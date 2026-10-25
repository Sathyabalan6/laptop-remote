"""Unit tests for cross-platform battery status reporting."""

from laptop_remote.core import power


def test_battery_macos_pmset_parsing(monkeypatch):
    monkeypatch.setattr("sys.platform", "darwin")
    output = (
        b"Now drawing from 'Battery Power'\n"
        b" -InternalBattery-0 (id=1234567)\t82%; discharging; 3:45 remaining present: true\n"
    )
    monkeypatch.setattr("subprocess.check_output", lambda *args, **kwargs: output)
    assert power.get_battery_percent() == 82


def test_battery_macos_error_returns_none(monkeypatch):
    monkeypatch.setattr("sys.platform", "darwin")
    monkeypatch.setattr("subprocess.check_output", lambda *args, **kwargs: (_ for _ in ()).throw(OSError("pmset not found")))
    assert power.get_battery_percent() is None
