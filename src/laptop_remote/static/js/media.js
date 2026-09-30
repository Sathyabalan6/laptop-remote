// ─────────────────────────────────────────────────────────────────
//  MEDIA, KEYPAD & SEARCH SUITE LOGIC
// ─────────────────────────────────────────────────────────────────
async function send_text(text, press_enter = false) {
  if (!text && !press_enter) return;
  vibrate(10);
  return socketSend('text', { text, press_enter });
}

async function send_raw_key(keyName) {
  vibrate(12);
  return socketSend('key', { action: keyName, preset: currentPreset });
}

async function send_key_action(actionName) {
  vibrate(15);
  return socketSend('key', { action: actionName, preset: currentPreset });
}

function quickJumpSearch() {
  if (typeof openKeysSheetWithSearch === 'function') {
    openKeysSheetWithSearch();
  } else {
    focusSearchSite();
  }
}

const PRESET_ACTIONS = {
  universal: ['skip_intro', 'theater_mode', 'miniplayer', 'speed_up', 'speed_down'],
  youtube_hotstar: ['skip_intro', 'theater_mode', 'miniplayer', 'speed_up', 'speed_down'],
  vlc: ['audio_track_cycle', 'speed_up', 'speed_down']
};

function updatePresetShortcuts(preset) {
  const allowed = PRESET_ACTIONS[preset] || PRESET_ACTIONS.universal;
  document.querySelectorAll('#mediaShortcutGrid .shortcut-tile').forEach(tile => {
    const act = tile.getAttribute('data-action');
    const isAllowed = allowed.includes(act);
    tile.classList.toggle('opacity-30', !isAllowed);
    tile.classList.toggle('pointer-events-none', !isAllowed);
    tile.setAttribute('aria-disabled', isAllowed ? 'false' : 'true');
  });
}

function focusSearchSite() {
  vibrate(15);
  send_key_action('search_focus');
  const input = document.getElementById('searchInput');
  if (input) {
    input.focus();
  }
  showToast('Focused in-page search (/)');
}

function focusAddressBar() {
  vibrate(15);
  send_key_action('search_url');
  const input = document.getElementById('searchInput');
  if (input) {
    input.focus();
  }
  showToast('Focused URL address bar (Ctrl+L)');
}

function submitSearch(pressEnter = true) {
  const input = document.getElementById('searchInput');
  if (!input) return;
  // Text is already mirrored live as the user types; here we only submit.
  if (pressEnter) send_raw_key('enter');
  input.blur();
}

// ── Live typing mirror ────────────────────────────────────────────────
// Send keystrokes to the laptop as the user types, so the laptop screen
// mirrors the phone's search box in real time (including backspace).
let lastSearchValue = '';

function handleLiveTyping(input) {
  const newVal = input.value;
  const oldVal = lastSearchValue;
  if (newVal === oldVal) return;

  // Longest common prefix determines what was deleted vs. appended.
  let i = 0;
  while (i < newVal.length && i < oldVal.length && newVal[i] === oldVal[i]) i++;

  const removedCount = oldVal.length - i;
  const added = newVal.slice(i);

  for (let k = 0; k < removedCount; k++) send_raw_key('backspace');
  if (added) send_text(added, false);

  lastSearchValue = newVal;
}

function resetLiveTyping() {
  lastSearchValue = '';
}

function clearSearchInput() {
  const input = document.getElementById('searchInput');
  const clearBtn = document.getElementById('searchClearBtn');
  if (input) {
    input.value = '';
    input.focus();
  }
  resetLiveTyping();
  if (clearBtn) clearBtn.classList.remove('visible');
}

// ─────────────────────────────────────────────────────────────────
//  VOLUME SLIDER & REAL OS AUDIO MIXER SYNC
// ─────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  const volumeSlider = document.getElementById('volumeSlider');
  const volumePctText = document.getElementById('volumePct');

  if (volumeSlider && volumePctText) {
    volumeSlider.value = volumeLevel;
    volumePctText.textContent = volumeLevel + '%';

    let volumeThrottle = null;
    volumeSlider.addEventListener('input', e => {
      const val = parseInt(e.target.value);
      volumeLevel = val;
      volumePctText.textContent = val + '%';
      localStorage.setItem('volume_level', val);

      if (!volumeThrottle) {
        vibrate(8);
        volumeThrottle = setTimeout(() => {
          volumeThrottle = null;
          socketSend('volume_set', { volume: volumeLevel });
        }, 35);
      }
    });
  }
});

function updateAudioUI(audio) {
  if (!audio) return;
  const vol = typeof audio.volume === 'number' ? audio.volume : 50;
  volumeLevel = vol;
  const volumeSlider = document.getElementById('volumeSlider');
  const volumePctText = document.getElementById('volumePct');
  const volFill = document.getElementById('volume-fill');
  const volThumb = document.getElementById('volume-thumb');
  if (volumeSlider) volumeSlider.value = vol;
  if (volFill) volFill.style.width = vol + '%';
  if (volThumb) volThumb.style.left = `calc(${vol}% - 12px)`;
  if (volumePctText) volumePctText.textContent = (audio.muted ? '🔇 ' : '') + vol + '%';
  localStorage.setItem('volume_level', vol);

  const muteBtn = document.getElementById('mute-toggle');
  if (muteBtn) {
    muteBtn.setAttribute('aria-pressed', audio.muted ? 'true' : 'false');
    muteBtn.classList.toggle('bg-error-container/40', !!audio.muted);
    muteBtn.classList.toggle('text-error', !!audio.muted);
    muteBtn.classList.toggle('border-error/30', !!audio.muted);
  }
}

let ccActive = false;
let fsActive = false;

function toggleCC() {
  ccActive = !ccActive;
  const btn = document.getElementById('cc-toggle');
  if (btn) {
    btn.setAttribute('aria-pressed', ccActive ? 'true' : 'false');
    btn.classList.toggle('bg-primary/20', ccActive);
    btn.classList.toggle('text-primary', ccActive);
    btn.classList.toggle('border-primary/40', ccActive);
  }
  send('subtitles');
}

function toggleFS() {
  fsActive = !fsActive;
  const btn = document.getElementById('fs-toggle');
  if (btn) {
    btn.setAttribute('aria-pressed', fsActive ? 'true' : 'false');
    btn.classList.toggle('bg-primary/20', fsActive);
    btn.classList.toggle('text-primary', fsActive);
    btn.classList.toggle('border-primary/40', fsActive);
  }
  send('fullscreen');
}
