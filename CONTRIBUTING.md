# Contributing to Laptop Remote

Thanks for your interest in improving Laptop Remote! 🎉
This guide will get you productive quickly.

## Ways to contribute

- 🐛 **Report bugs** — open an issue using the bug report template.
- ✨ **Suggest features** — open an issue using the feature request template.
- 📝 **Improve docs** — README, DOCUMENTATION.md, and code comments.
- 🧪 **Add tests** — the more coverage, the safer the project is to change.
- 🌍 **Test on your OS** — Windows, macOS, X11, and Wayland are all valuable.

## Development setup

```bash
# 1. Fork and clone
git clone https://github.com/<your-username>/laptop-remote.git
cd laptop-remote

# 2. Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Install in editable mode with dev tools
pip install -e ".[dev]"

# 4. Run the tests
pytest
```

## Running the app locally

```bash
# Run the server (terminal edition)
python -m laptop_remote
```

## Project layout

```
src/laptop_remote/
├── server/         # Flask + Socket.IO server (routes, websocket, discovery)
├── core/           # Platform backends (input, auth, audio, overlay, ...)
├── static/         # Web frontend (HTML/CSS/JS — the phone UI)
├── cli.py          # Terminal entry point
└── __main__.py     # python -m laptop_remote
tests/              # pytest suite
```

## Coding guidelines

- Target **Python 3.10+**.
- Keep imports **relative within the package** (e.g. `from .core import ...`).
- Pure logic should be **testable without a display** — isolate platform calls.
- Match the existing style; run `ruff check src/` if you have ruff installed.
- Keep pull requests **focused** — one feature or fix per PR.

## Platform-specific notes

| Platform | Input backend | Notes |
|---|---|---|
| Windows | `win32api` | Native, no extra setup |
| macOS | `Quartz` | Native, needs Accessibility permission |
| Linux (X11) | `pyautogui` / XTest | Works out of the box |
| Linux (Wayland) | `ydotool` / `dotool` | Requires one-time `setup_linux.sh` |

If you touch `core/input.py`, please test on as many of these as you can and note what you tested in the PR.

## Commit messages

Use clear, imperative messages, e.g.:

```
fix: prevent cursor jump on first trackpad touch under Wayland
feat: add per-app preset auto-detection for Firefox
docs: clarify pairing PIN rotation
```

## Pull request process

1. Create a branch: `git checkout -b fix/short-description`
2. Make your change and add/adjust tests.
3. Run `pytest` — all tests must pass.
4. Open the PR and fill in the template.

We aim to review PRs promptly. Beginner-friendly PRs are very welcome!

## Questions?

Open a [discussion](https://github.com/Sathyabalan6/laptop-remote/discussions) — there are no silly questions.
