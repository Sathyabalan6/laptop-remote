# 🗺️ Roadmap

A living list of what we'd like to build next. Want to help? Pick an issue labeled
[`good first issue`](https://github.com/Sathyabalan6/laptop-remote/labels/good%20first%20issue)
or
[`help wanted`](https://github.com/Sathyabalan6/laptop-remote/labels/help%20wanted)
and comment on it.

## Completed in v1.0.x

- [x] **Zero-install launch**: Run directly without installing via `uvx laptop-remote`
- [x] **PyPI Package**: Available globally via `pipx install laptop-remote` or `pip install laptop-remote`
- [x] **Standalone Windows executable**: Automated PyInstaller builds (`LaptopRemote-CLI.exe`) with smoke test verification
- [x] **Full test suites**: Comprehensive Pytest (backend) and Vitest (frontend touch physics & gestures)
- [x] **Two-finger gestures**: Calibrated natural/inverted scroll with inertia dampening and two-finger pinch-to-zoom
- [x] **Multi-device session isolation**: PIN pairing, active device list, individual device revocation with self-revoke protection
- [x] **OLED Pitch Black & Dark Glass themes**: High contrast and pure black themes inspired by Apple HIG
- [x] **Presets Customizer**: Web UI editor to customize media and navigation hotkeys stored in `presets.json`
- [x] **Multi-monitor virtual screen bounds**: Seamless cursor bounds handling across Windows virtual screen, macOS AppKit, and Linux X11/Wayland
- [x] **Standardized Python logging**: Clean terminal output with `--verbose` (`-v`) and `--quiet` (`-q`) flags
- [x] **PWA Service Worker Precaching**: Full offline asset precaching with release-versioned cache invalidation

## Next Up

- [ ] **Hardware Gyroscope Air Mouse**: Tilt and wave the phone in the air to control the cursor or presentation laser
- [ ] **Screen Thumbnail / Slide Preview**: Low-fps, low-bandwidth compressed snapshot of slides in Presentation Mode
- [ ] **Docker image**: Containerized setup for headless Linux workstations
- [ ] **Bluetooth / USB tethering transport**: Direct transport fallback when Wi-Fi router isolation is active

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
