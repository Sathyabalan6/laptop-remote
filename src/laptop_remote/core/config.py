import os
import sys
import json

def get_executable_dir():
    """Return the directory that holds user-editable data (presets.json).

    For a frozen (PyInstaller) build this is next to the executable; for a
    source checkout this is the repository root (where pyproject.toml lives).
    """
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    # core/config.py -> .../src/laptop_remote/core/config.py
    # Walk up until we find the project root (which contains pyproject.toml).
    current = os.path.dirname(os.path.abspath(__file__))
    for _ in range(5):
        if os.path.exists(os.path.join(current, 'pyproject.toml')) or \
           os.path.exists(os.path.join(current, 'presets.json')):
            return current
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent
    # Fallback: repo root is three levels up from core/ (src/laptop_remote/core).
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

PRESETS_PATH = os.path.join(get_executable_dir(), 'presets.json')

DEFAULT_PRESETS = {
  "youtube_hotstar": {
    "play_pause": "space",
    "skip_forward": "l",
    "skip_back": "j",
    "skip_forward_30": ["l", "l", "l"],
    "next": ["shift", "n"],
    "fullscreen": "f",
    "subtitles": "c",
    "back": ["alt", "left"],
    "search_focus": "/",
    "search_url": ["ctrl", "l"],
    "skip_intro": "s",
    "speed_up": ["shift", ">"],
    "speed_down": ["shift", "<"],
    "theater_mode": "t",
    "miniplayer": "i",
    "subtitles_size_up": "+",
    "subtitles_size_down": "-",
    "audio_track_cycle": "b"
  },
  "universal": {
    "play_pause": "space",
    "skip_forward": "right",
    "skip_back": "left",
    "skip_forward_30": ["right", "right", "right"],
    "next": "right",
    "fullscreen": "f",
    "subtitles": "c",
    "back": ["alt", "left"],
    "search_focus": "/",
    "search_url": ["ctrl", "l"],
    "skip_intro": "s",
    "speed_up": ["shift", ">"],
    "speed_down": ["shift", "<"],
    "theater_mode": "t",
    "miniplayer": "i",
    "subtitles_size_up": "+",
    "subtitles_size_down": "-",
    "audio_track_cycle": "b"
  },
  "vlc": {
    "play_pause": "space",
    "skip_forward": "right",
    "skip_back": "left",
    "skip_forward_30": ["right", "right", "right"],
    "next": ["ctrl", "right"],
    "fullscreen": "f",
    "subtitles": "v",
    "back": ["alt", "left"],
    "search_focus": "/",
    "search_url": ["ctrl", "l"],
    "speed_up": "]",
    "speed_down": "[",
    "subtitles_sync_advance": "h",
    "subtitles_sync_delay": "g",
    "audio_track_cycle": "b",
    "audio_sync_advance": "k",
    "audio_sync_delay": "j"
  }
}

def load_presets():
    if not os.path.exists(PRESETS_PATH):
        try:
            with open(PRESETS_PATH, 'w', encoding='utf-8') as f:
                json.dump(DEFAULT_PRESETS, f, indent=2)
        except Exception as e:
            print(f"⚠️ Could not write default presets: {e}")
            return DEFAULT_PRESETS
    try:
        with open(PRESETS_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            updated = False
            for k, v in DEFAULT_PRESETS.items():
                if k not in data:
                    data[k] = v
                    updated = True
            if updated:
                try:
                    with open(PRESETS_PATH, 'w', encoding='utf-8') as out_f:
                        json.dump(data, out_f, indent=2)
                except Exception:
                    pass
            return data
    except Exception as e:
        print(f"⚠️ Error reading presets.json: {e}, falling back to defaults.")
        return DEFAULT_PRESETS
