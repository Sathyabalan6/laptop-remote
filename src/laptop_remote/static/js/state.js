// ─────────────────────────────────────────────────────────────────
//  STATE MANAGEMENT, PRESETS, HAPTICS, WAKE LOCK, SWIPE TABS & OVERLAYS
// ─────────────────────────────────────────────────────────────────
let currentTab = localStorage.getItem('active_tab') || 'mouse';
if (currentTab === 'keyboard') currentTab = 'mouse';

let currentPreset = localStorage.getItem('player_preset') || 'universal';
let mouseSensitivity = parseFloat(localStorage.getItem('mouse_sensitivity')) || 1.0;
let screenW = 1920, screenH = 1080;
let volumeLevel = parseInt(localStorage.getItem('volume_level')) || 50;
// Set from server state: true only when a transparent laser overlay exists.
let laserAvailable = false;

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
  } catch (_) { }
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
    media: 'Media',
    present: 'Present'
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
  return ['mouse', 'media', 'present'];
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
  } catch (_) { }

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

  if (activeOverlay === targetId) {
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
    } catch (_) { }
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
  openOverlay('settingsModal');
}

function closeSettingsModal() {
  closeOverlay('settingsModal');
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
