// ─────────────────────────────────────────────────────────────────
//  STATE MANAGEMENT, PRESETS, HAPTICS, WAKE LOCK, SWIPE TABS & OVERLAYS
// ─────────────────────────────────────────────────────────────────
let currentTab = localStorage.getItem('active_tab') || 'mouse';
if (currentTab === 'keyboard') currentTab = 'mouse';

let currentPreset = localStorage.getItem('player_preset') || 'universal';
let mouseSensitivity = parseFloat(localStorage.getItem('mouse_sensitivity')) || 1.0;
let screenW = 1920, screenH = 1080;
let volumeLevel = parseInt(localStorage.getItem('volume_level')) || 50;
let scrollDirection = localStorage.getItem('scroll_direction') || 'natural';
let scrollSensitivity = (typeof localStorage !== 'undefined' ? parseFloat(localStorage.getItem('scroll_sensitivity')) : null) || 1.0;
let scrollInertia = (typeof localStorage !== 'undefined' ? localStorage.getItem('scroll_inertia') : null) !== 'false';
let currentTheme = (typeof localStorage !== 'undefined' ? localStorage.getItem('app_theme') : null) || 'dark';
// Set from server state: true only when a transparent laser overlay exists.
let laserAvailable = false;

function setTheme(theme) {
  currentTheme = theme === 'oled' ? 'oled' : 'dark';
  if (typeof localStorage !== 'undefined') {
    localStorage.setItem('app_theme', currentTheme);
  }
  if (typeof document !== 'undefined' && document.documentElement) {
    if (currentTheme === 'oled') {
      document.documentElement.classList.add('theme-oled');
    } else {
      document.documentElement.classList.remove('theme-oled');
    }
  }
  if (typeof document !== 'undefined') {
    const btn = document.getElementById('themeToggleBtn');
    if (btn) {
      btn.textContent = currentTheme === 'oled' ? 'OLED Black' : 'Dark Glass';
      btn.setAttribute('data-theme', currentTheme);
    }
  }
}

function toggleTheme() {
  vibrate(15);
  setTheme(currentTheme === 'dark' ? 'oled' : 'dark');
  if (typeof showToast === 'function') {
    showToast('Theme: ' + (currentTheme === 'oled' ? 'OLED Pitch Black' : 'Dark Glass'));
  }
}

if (typeof document !== 'undefined' && document.documentElement) {
  setTheme(currentTheme);
}

function setScrollDirection(dir) {
  scrollDirection = dir === 'inverted' ? 'inverted' : 'natural';
  localStorage.setItem('scroll_direction', scrollDirection);
  const btn = document.getElementById('scrollDirToggleBtn');
  if (btn) {
    btn.textContent = scrollDirection === 'inverted' ? 'Inverted' : 'Natural';
    btn.setAttribute('data-dir', scrollDirection);
  }
}

function toggleScrollDirection() {
  vibrate(15);
  setScrollDirection(scrollDirection === 'natural' ? 'inverted' : 'natural');
  showToast('Scroll: ' + (scrollDirection === 'inverted' ? 'Inverted' : 'Natural'));
}

function setScrollSensitivity(val) {
  const clampFn = (typeof window !== 'undefined' && window.trackpadLogic && window.trackpadLogic.clampScrollSensitivity) ||
    ((v) => Math.min(3.0, Math.max(0.2, v)));
  scrollSensitivity = clampFn(typeof val === 'number' ? val : parseFloat(val) || 1.0);
  if (typeof localStorage !== 'undefined') {
    localStorage.setItem('scroll_sensitivity', scrollSensitivity);
  }
  if (typeof document !== 'undefined') {
    const s1 = document.getElementById('settingsScrollSlider');
    const l1 = document.getElementById('settingsScrollLabel');
    if (s1) s1.value = scrollSensitivity;
    if (l1) l1.textContent = scrollSensitivity.toFixed(1) + 'x';

    const s2 = document.getElementById('scrollSensitivitySlider');
    const l2 = document.getElementById('scrollPopoverLabel');
    const f2 = document.getElementById('scrollSliderFill');
    const t2 = document.getElementById('scrollSliderThumb');
    if (s2) s2.value = scrollSensitivity;
    if (l2) l2.textContent = scrollSensitivity.toFixed(1) + 'x';
    if (f2 && t2 && s2) {
      const min = parseFloat(s2.min) || 0.2;
      const max = parseFloat(s2.max) || 3.0;
      const percent = ((scrollSensitivity - min) / (max - min)) * 100;
      f2.style.width = percent + '%';
      t2.style.left = percent + '%';
    }
  }
}

function syncScrollInertiaUI() {
  if (typeof document !== 'undefined') {
    const btn = document.getElementById('scrollInertiaToggleBtn');
    if (btn) {
      btn.textContent = scrollInertia ? 'Smooth' : 'Instant';
      btn.setAttribute('data-inertia', scrollInertia ? 'true' : 'false');
    }
  }
}

function toggleScrollInertia() {
  scrollInertia = !scrollInertia;
  if (typeof localStorage !== 'undefined') {
    localStorage.setItem('scroll_inertia', scrollInertia ? 'true' : 'false');
  }
  vibrate(15);
  syncScrollInertiaUI();
  if (typeof showToast === 'function') {
    showToast('Scroll Momentum: ' + (scrollInertia ? 'Smooth' : 'Instant'));
  }
}

async function loadPairedDevices() {
  const container = document.getElementById('pairedDevicesList');
  if (!container) return;
  const token = localStorage.getItem('session_token') || '';
  try {
    const res = await fetch('/devices', {
      headers: { 'Authorization': 'Bearer ' + token }
    });
    if (!res.ok) return;
    const data = await res.json();
    container.replaceChildren();
    if (data.devices && data.devices.length > 0) {
      data.devices.forEach(d => {
        const row = document.createElement('div');
        row.className = 'flex items-center justify-between py-1.5 border-b border-white/[0.04] last:border-0 text-xs';

        const info = document.createElement('div');
        info.className = 'flex flex-col min-w-0 pr-2';

        const nameSpan = document.createElement('span');
        nameSpan.className = 'font-semibold text-on-surface truncate';
        nameSpan.textContent = d.device_name || 'Device';

        const metaSpan = document.createElement('span');
        metaSpan.className = 'text-[10px] text-on-surface-variant font-mono';
        metaSpan.textContent = `${d.ip} · ID: ${d.id}`;

        info.appendChild(nameSpan);
        info.appendChild(metaSpan);

        const currentToken = localStorage.getItem('session_token') || '';
        const isCurrent = (d.id === currentToken.slice(0, 8));

        if (isCurrent) {
          const badge = document.createElement('span');
          badge.className = 'px-2 py-0.5 rounded text-[10px] font-semibold bg-primary/20 text-primary shrink-0';
          badge.textContent = 'This device';
          row.appendChild(info);
          row.appendChild(badge);
        } else {
          const btn = document.createElement('button');
          btn.className = 'px-2 py-1 min-h-[32px] rounded-lg bg-error-container/20 hover:bg-error-container/40 text-error text-[11px] font-semibold active:scale-95 transition-all';
          btn.textContent = 'Revoke';
          btn.onclick = () => revokeSingleDevice(d.id);
          row.appendChild(info);
          row.appendChild(btn);
        }

        container.appendChild(row);
      });
    } else {
      const emptySpan = document.createElement('span');
      emptySpan.className = 'text-xs text-on-surface-variant';
      emptySpan.textContent = 'No other devices paired';
      container.appendChild(emptySpan);
    }
  } catch {
    const fallbackSpan = document.createElement('span');
    fallbackSpan.className = 'text-xs text-on-surface-variant';
    fallbackSpan.textContent = '1 active device';
    container.replaceChildren(fallbackSpan);
  }
}

async function revokeSingleDevice(deviceId) {
  vibrate(20);
  const token = localStorage.getItem('session_token') || '';
  try {
    const res = await fetch('/revoke', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + token
      },
      body: JSON.stringify({ device_id: deviceId })
    });
    if (res.ok) {
      showToast('🔒 Device revoked');
      if (token && token.startsWith(deviceId)) {
        localStorage.removeItem('session_token');
        if (typeof showPinOverlay === 'function') showPinOverlay();
        closeSettingsModal();
      } else {
        loadPairedDevices();
      }
    }
  } catch { }
}

function setPreset(name, isAuto = false) {
  currentPreset = name;
  localStorage.setItem('player_preset', name);
  if (!isAuto) vibrate(15);

  document.querySelectorAll('.preset-btn').forEach(btn => {
    const isActive = btn.id === 'preset-btn-' + name;
    btn.classList.toggle('active', isActive);
    btn.setAttribute('aria-checked', isActive ? 'true' : 'false');
  });

  if (typeof updatePresetShortcuts === 'function') {
    updatePresetShortcuts(name);
  }

  const descEl = document.getElementById('presetDescription');
  if (descEl && window.presetLogic?.getPresetDescription) {
    descEl.textContent = window.presetLogic.getPresetDescription(name);
  }

  if (!isAuto) {
    const displayName = window.presetLogic?.getPresetDisplayName
      ? window.presetLogic.getPresetDisplayName(name)
      : (name === 'youtube_hotstar'
        ? 'YouTube / Hotstar'
        : name === 'vlc'
          ? 'VLC Player'
          : 'Universal / Netflix');
    showToast('Preset: ' + displayName);
  }
}

function vibrate(ms = 20) {
  if (navigator.vibrate) navigator.vibrate(ms);
}

let wakeLock = null;
async function requestWakeLock() {
  try {
    if ('wakeLock' in navigator) {
      wakeLock = await navigator.wakeLock.request('screen');
    }
  } catch { }
}

requestWakeLock();
document.addEventListener('visibilitychange', () => {
  if (wakeLock !== null && document.visibilityState === 'visible') {
    requestWakeLock();
  }
});

function switchTab(name) {
  if (currentTab === name) return;
  currentTab = name;
  localStorage.setItem('active_tab', name);
  vibrate(15);

  const tabTitles = {
    mouse: 'Trackpad',
    media: 'Media Remote',
    remote: 'Remote & Keys',
    present: 'Presentation'
  };
  const titleEl = document.getElementById('headerTitle');
  if (titleEl && tabTitles[name]) {
    titleEl.textContent = tabTitles[name];
  }

  document.querySelectorAll('.nav-item').forEach(btn => {
    const isActive = btn.id === 'tab-btn-' + name;
    btn.classList.toggle('active', isActive);
    btn.setAttribute('aria-selected', isActive ? 'true' : 'false');
    if (isActive) {
      btn.classList.add('bg-surface-variant', 'text-primary', 'shadow-[0_2px_8px_rgba(0,0,0,0.35)]');
      btn.classList.remove('text-on-surface-variant');
    } else {
      btn.classList.remove('bg-surface-variant', 'text-primary', 'shadow-[0_2px_8px_rgba(0,0,0,0.35)]');
      btn.classList.add('text-on-surface-variant');
    }
  });

  document.querySelectorAll('.tab-panel').forEach(panel => {
    const isActive = panel.id === 'tab-' + name;
    panel.classList.toggle('active', isActive);
    panel.classList.toggle('hidden', !isActive);
  });
}

function getTabOrder() {
  return ['mouse', 'media', 'remote', 'present'];
}

function swipeTab(direction) {
  const tabs = getTabOrder();
  const index = tabs.indexOf(currentTab);
  if (index === -1) return;

  if (direction === 'left' && index < tabs.length - 1) {
    switchTab(tabs[index + 1]);
  } else if (direction === 'right' && index > 0) {
    switchTab(tabs[index - 1]);
  }
}

// ── Overlay Manager (Keys Sheet, Settings Modal) ──────────────────────
let activeOverlay = null;

function setBackgroundInert(isInert) {
  if (typeof document === 'undefined') return;
  ['header', 'main', 'nav'].forEach(tag => {
    const el = document.querySelector(tag);
    if (el) {
      if (isInert) {
        el.setAttribute('inert', '');
      } else {
        el.removeAttribute('inert');
      }
    }
  });
}

function openOverlay(overlayId, focusElId) {
  closeAllPopovers();
  const backdrop = document.getElementById(overlayId + 'Backdrop');
  const panel = document.getElementById(overlayId);
  if (!panel) return;

  if (activeOverlay && activeOverlay !== overlayId) {
    closeOverlay(activeOverlay, false, true);
  }

  activeOverlay = overlayId;
  setBackgroundInert(true);
  if (backdrop) backdrop.classList.add('active');
  panel.classList.add('active');

  try {
    history.pushState({ remoteOverlay: overlayId }, '');
  } catch { }

  if (focusElId) {
    setTimeout(() => {
      const el = document.getElementById(focusElId);
      if (el) el.focus();
    }, 150);
  } else {
    setTimeout(() => {
      const focusable = panel.querySelector('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
      if (focusable) focusable.focus();
    }, 100);
  }
}

function closeOverlay(overlayId, fromPopState = false, skipHistory = false) {
  const targetId = overlayId || activeOverlay;
  if (!targetId) return;

  const backdrop = document.getElementById(targetId + 'Backdrop');
  const panel = document.getElementById(targetId);

  if (backdrop) backdrop.classList.remove('active');
  if (panel) panel.classList.remove('active');

  if (activeOverlay === targetId || !activeOverlay) {
    activeOverlay = null;
    const pinOverlay = document.getElementById('pinOverlay');
    const isPinActive = pinOverlay && pinOverlay.classList.contains('visible');
    if (!isPinActive) {
      setBackgroundInert(false);
    }
  }

  if (!fromPopState && !skipHistory && history.state && history.state.remoteOverlay === targetId) {
    try {
      history.back();
    } catch { }
  }
}

function openKeysSheet() {
  vibrate(15);
  openOverlay('keysSheet');
}

function closeKeysSheet() {
  closeOverlay('keysSheet');
}

function openKeysSheetWithSearch() {
  vibrate(15);
  openOverlay('keysSheet', 'searchInput');
}

function openSettingsModal() {
  vibrate(15);
  setTheme(currentTheme);
  setScrollDirection(scrollDirection);
  setScrollSensitivity(scrollSensitivity);
  syncScrollInertiaUI();
  loadPairedDevices();
  openOverlay('settingsModal');
}

function closeSettingsModal() {
  closeOverlay('settingsModal');
}

function openHelpModal() {
  vibrate(15);
  openOverlay('helpModal');
}

function closeHelpModal() {
  closeOverlay('helpModal');
}

let editorPresets = null;
let editorActivePreset = 'universal';

const PRESET_LABEL_MAP = {
  play_pause: 'Play / Pause',
  skip_forward: 'Skip Forward 10s',
  skip_back: 'Skip Back 10s',
  fullscreen: 'Fullscreen',
  subtitles: 'Subtitles / CC',
  theater_mode: 'Theater Mode',
  miniplayer: 'Miniplayer',
  speed_up: 'Speed Up',
  speed_down: 'Speed Down',
  skip_intro: 'Skip Intro'
};

function openPresetsModal() {
  vibrate(15);
  openOverlay('presetsModal');
  loadPresetsEditor();
}

function closePresetsModal() {
  closeOverlay('presetsModal');
}

function selectEditorPreset(presetName) {
  vibrate(10);
  editorActivePreset = presetName;
  if (typeof document !== 'undefined') {
    document.querySelectorAll('.preset-editor-tab-btn').forEach(btn => {
      const isActive = btn.getAttribute('data-preset') === presetName;
      btn.classList.toggle('active', isActive);
      btn.classList.toggle('bg-primary', isActive);
      btn.classList.toggle('text-white', isActive);
      btn.classList.toggle('bg-surface-variant', !isActive);
    });
  }
  renderPresetEditorActions();
}

async function loadPresetsEditor() {
  const container = typeof document !== 'undefined' ? document.getElementById('presetEditorList') : null;
  if (!container) return;
  const token = typeof localStorage !== 'undefined' ? (localStorage.getItem('session_token') || '') : '';
  try {
    const res = await fetch('/presets', {
      headers: { 'Authorization': 'Bearer ' + token }
    });
    if (res.ok) {
      editorPresets = await res.json();
    }
  } catch {
    editorPresets = null;
  }
  if (!editorPresets) {
    editorPresets = {
      universal: { play_pause: 'space', skip_forward: 'right', skip_back: 'left', fullscreen: 'f', subtitles: 'c' },
      youtube_hotstar: { play_pause: 'space', skip_forward: 'l', skip_back: 'j', fullscreen: 'f', subtitles: 'c' },
      vlc: { play_pause: 'space', skip_forward: 'right', skip_back: 'left', fullscreen: 'f', subtitles: 'c' }
    };
  }
  renderPresetEditorActions();
}

function renderPresetEditorActions() {
  const container = typeof document !== 'undefined' ? document.getElementById('presetEditorList') : null;
  if (!container || !editorPresets) return;
  container.replaceChildren();

  const currentMap = editorPresets[editorActivePreset] || {};
  const actions = Object.keys(PRESET_LABEL_MAP);

  actions.forEach(action => {
    const row = document.createElement('div');
    row.className = 'flex items-center justify-between py-2 border-b border-white/[0.04] last:border-0 text-xs';

    const label = document.createElement('span');
    label.className = 'font-medium text-on-surface';
    label.textContent = PRESET_LABEL_MAP[action] || action;

    const input = document.createElement('input');
    input.type = 'text';
    input.className = 'w-24 px-2 py-1 rounded-lg bg-surface-variant text-primary font-mono text-xs text-center border border-white/[0.08] focus:border-primary focus:outline-none';
    const val = currentMap[action];
    input.value = Array.isArray(val) ? val.join('+') : (val || '');
    input.oninput = (e) => {
      const trimmed = e.target.value.trim();
      if (trimmed.includes('+')) {
        currentMap[action] = trimmed.split('+').map(k => k.trim());
      } else {
        currentMap[action] = trimmed;
      }
    };

    row.appendChild(label);
    row.appendChild(input);
    container.appendChild(row);
  });
}

async function savePresetsEditor() {
  vibrate(20);
  if (!editorPresets) return;
  const token = typeof localStorage !== 'undefined' ? (localStorage.getItem('session_token') || '') : '';
  try {
    const res = await fetch('/presets', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + token
      },
      body: JSON.stringify(editorPresets)
    });
    if (res.ok) {
      showToast('✅ Presets saved');
      closePresetsModal();
    } else {
      showToast('⚠️ Failed to save presets');
    }
  } catch {
    showToast('⚠️ Network error');
  }
}

async function resetPresetsEditor() {
  vibrate(20);
  const defaults = {
    universal: {
      play_pause: "space", skip_forward: "right", skip_back: "left", fullscreen: "f",
      subtitles: "c", theater_mode: "t", miniplayer: "i", speed_up: ["shift", ">"], speed_down: ["shift", "<"]
    },
    youtube_hotstar: {
      play_pause: "space", skip_forward: "l", skip_back: "j", fullscreen: "f",
      subtitles: "c", theater_mode: "t", miniplayer: "i", speed_up: ["shift", ">"], speed_down: ["shift", "<"]
    },
    vlc: {
      play_pause: "space", skip_forward: "right", skip_back: "left", fullscreen: "f",
      subtitles: "c", theater_mode: "t", miniplayer: "i", speed_up: "]", speed_down: "["
    }
  };
  editorPresets = defaults;
  renderPresetEditorActions();
  await savePresetsEditor();
}

// Popovers management (Speed popover and Present menu)
function toggleSpeedPopover(e) {
  if (e) e.stopPropagation();
  const popover = document.getElementById('speedPopover');
  const btn = document.getElementById('btnSpeedPill');
  if (!popover) return;
  const isHidden = popover.classList.contains('hidden');
  closeAllPopovers();
  if (isHidden) {
    popover.classList.remove('hidden');
    if (btn) btn.setAttribute('aria-expanded', 'true');
  }
}

function togglePresentMenu(e) {
  if (e) e.stopPropagation();
  const menu = document.getElementById('presentMenu');
  const btn = document.getElementById('btnPresentMenu');
  if (!menu) return;
  const isHidden = menu.classList.contains('hidden');
  closeAllPopovers();
  if (isHidden) {
    menu.classList.remove('hidden');
    if (btn) btn.setAttribute('aria-expanded', 'true');
  }
}

function closeAllPopovers() {
  const speed = document.getElementById('speedPopover');
  if (speed) speed.classList.add('hidden');
  const speedBtn = document.getElementById('btnSpeedPill');
  if (speedBtn) speedBtn.setAttribute('aria-expanded', 'false');

  const presentMenu = document.getElementById('presentMenu');
  if (presentMenu) presentMenu.classList.add('hidden');
  const presentBtn = document.getElementById('btnPresentMenu');
  if (presentBtn) presentBtn.setAttribute('aria-expanded', 'false');
}

if (typeof window !== 'undefined' && typeof window.addEventListener === 'function') {
  window.addEventListener('click', () => {
    closeAllPopovers();
  });

  window.addEventListener('popstate', () => {
    if (activeOverlay) {
      closeOverlay(activeOverlay, true);
    }
  });

  window.addEventListener('keydown', e => {
    if (e.key === 'Escape') {
      closeAllPopovers();
      if (activeOverlay) {
        closeOverlay(activeOverlay);
      }
    } else if (e.key === 'Tab' && activeOverlay) {
      const panel = document.getElementById(activeOverlay);
      if (panel) {
        const focusables = panel.querySelectorAll('button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])');
        if (focusables.length > 0) {
          const first = focusables[0];
          const last = focusables[focusables.length - 1];
          if (e.shiftKey && document.activeElement === first) {
            e.preventDefault();
            last.focus();
          } else if (!e.shiftKey && document.activeElement === last) {
            e.preventDefault();
            first.focus();
          }
        }
      }
    }
  });
}

// ── D-Pad auto-repeat management ──────────────────────────────────────
let dpadRepeatTimer = null;
let dpadRepeatInterval = null;

function startDpadRepeat(key) {
  stopDpadRepeat();
  if (typeof send_raw_key === 'function') {
    send_raw_key(key);
  }
  dpadRepeatTimer = setTimeout(() => {
    dpadRepeatInterval = setInterval(() => {
      if (typeof send_raw_key === 'function') {
        send_raw_key(key);
      }
    }, 100);
  }, 350);
}

function stopDpadRepeat() {
  if (dpadRepeatTimer) {
    clearTimeout(dpadRepeatTimer);
    dpadRepeatTimer = null;
  }
  if (dpadRepeatInterval) {
    clearInterval(dpadRepeatInterval);
    dpadRepeatInterval = null;
  }
}

if (typeof document !== 'undefined' && typeof document.addEventListener === 'function') {
  document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.dpad-btn').forEach(btn => {
      const key = btn.getAttribute('data-key');
      if (!key) return;

      btn.addEventListener('pointerdown', e => {
        e.preventDefault();
        startDpadRepeat(key);
      });

      btn.addEventListener('pointerup', stopDpadRepeat);
      btn.addEventListener('pointercancel', stopDpadRepeat);
      btn.addEventListener('pointerleave', stopDpadRepeat);
    });

    if (typeof window !== 'undefined' && typeof window.addEventListener === 'function') {
      window.addEventListener('pointerup', stopDpadRepeat);
      window.addEventListener('pointercancel', stopDpadRepeat);
      window.addEventListener('blur', stopDpadRepeat);
    }
    document.addEventListener('visibilitychange', () => {
      if (document.hidden) stopDpadRepeat();
    });
  });
}

// ── Swipe gestures between tabs ───────────────────────────────────────
let swiperStartX = 0, swiperStartY = 0, swiperValid = false;

document.addEventListener('touchstart', e => {
  if (e.touches.length > 1 ||
    e.target.closest('#trackpad') ||
    e.target.closest('#presentPad') ||
    e.target.closest('#keysSheet') ||
    e.target.closest('#settingsModal') ||
    e.target.closest('#speedPopover') ||
    e.target.closest('#presentMenu') ||
    e.target.closest('.control-btn-circle') ||
    e.target.closest('.control-pill') ||
    e.target.closest('.preset-btn') ||
    e.target.closest('.toggle-btn') ||
    e.target.closest('.mouse-click-btn') ||
    e.target.closest('.slide-ctrl-btn') ||
    e.target.closest('.volume-slider') ||
    e.target.closest('.sensitivity-slider') ||
    e.target.closest('.nav-item') ||
    e.target.closest('.pin-overlay')) {
    swiperValid = false;
    return;
  }
  swiperValid = true;
  swiperStartX = e.touches[0].clientX;
  swiperStartY = e.touches[0].clientY;
}, { passive: true });

document.addEventListener('touchmove', e => {
  if (e.touches.length > 1) swiperValid = false;
}, { passive: true });

document.addEventListener('touchend', e => {
  if (!swiperValid) return;
  const dx = e.changedTouches[0].clientX - swiperStartX;
  const dy = e.changedTouches[0].clientY - swiperStartY;
  if (Math.abs(dx) > 80 && Math.abs(dx) > Math.abs(dy)) {
    swipeTab(dx > 0 ? 'right' : 'left');
  }
}, { passive: true });

let toastTimer;
function showToast(msg) {
  const t = document.getElementById('toast');
  const msgEl = document.getElementById('toastMsg') || t;
  if (!t) return;
  if (msgEl) msgEl.textContent = msg;
  t.classList.remove('opacity-0');
  t.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    t.classList.add('opacity-0');
    t.classList.remove('show');
  }, 1500);
}

if (typeof window !== 'undefined') {
  window.openPresetsModal = openPresetsModal;
  window.closePresetsModal = closePresetsModal;
  window.selectEditorPreset = selectEditorPreset;
  window.savePresetsEditor = savePresetsEditor;
  window.resetPresetsEditor = resetPresetsEditor;
  window.toggleTheme = toggleTheme;
  window.setTheme = setTheme;
  window.toggleScrollDirection = toggleScrollDirection;
  window.setScrollSensitivity = setScrollSensitivity;
  window.toggleScrollInertia = toggleScrollInertia;
  window.syncScrollInertiaUI = syncScrollInertiaUI;
  window.revokeSingleDevice = revokeSingleDevice;
  window.loadPairedDevices = loadPairedDevices;
  window.openSettingsModal = openSettingsModal;
  window.closeSettingsModal = closeSettingsModal;
  window.openHelpModal = openHelpModal;
  window.closeHelpModal = closeHelpModal;
  window.openKeysSheet = openKeysSheet;
  window.closeKeysSheet = closeKeysSheet;
  window.openKeysSheetWithSearch = openKeysSheetWithSearch;
  window.setPreset = setPreset;
  window.toggleSpeedPopover = toggleSpeedPopover;
  window.togglePresentMenu = togglePresentMenu;
}
