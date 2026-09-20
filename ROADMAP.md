# 🗺️ Roadmap

A living list of what we'd like to build next. Want to help? Pick an issue labeled
[`good first issue`](https://github.com/Sathyabalan6/laptop-remote/labels/good%20first%20issue)
or
[`help wanted`](https://github.com/Sathyabalan6/laptop-remote/labels/help%20wanted)
and comment on it.

## Near term

- [ ] **Automated tests for the web frontend** (trackpad gestures, preset switching)
- [ ] **Package for PyPI** (`pip install laptop-remote`)
- [ ] **One-command install script** for Linux/macOS
- [ ] **Configurable port + bind address** via a config file / env vars
- [ ] **Better Wayland onboarding** — detect missing `ydotool` and surface a clear in-app banner
- [ ] **Docker image** for advanced users

## Medium term

- [ ] **Continuous discovery** — auto-reconnect when Wi-Fi changes
- [ ] **Presets editor** — a web UI (served by the app) to edit key mappings without touching `presets.json`
- [ ] **Multi-monitor support** for the laser pointer
- [ ] **Screen mirroring / preview** (thumbnail of the laptop screen)
- [ ] **Bluetooth / USB tethering transport** as an alternative to Wi-Fi
- [ ] **iOS/Android native wrapper** (Capacitor) for a more app-like feel

## Longer term

- [ ] **Plugin system** for custom actions and key mappings
- [ ] **Cloud relay** (opt-in) for remote access without port forwarding
- [ ] **Accessibility improvements** (screen-reader labels, larger targets)
- [ ] **Localization / i18n** of the web UI

## Non-goals

Laptop Remote intentionally will **not**:

- Expose itself directly to the public internet by default.
- Require a cloud account for basic LAN use.
- Bundle telemetry or analytics.
