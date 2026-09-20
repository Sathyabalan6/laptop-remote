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
  switchTab('keyboard');
  setTimeout(() => {
    focusSearchSite();
  }, 150);
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
  if (volumeSlider) volumeSlider.value = vol;
  if (volumePctText) volumePctText.textContent = (audio.muted ? '🔇 ' : '') + vol + '%';
  localStorage.setItem('volume_level', vol);
}
