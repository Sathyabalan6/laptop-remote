// ─────────────────────────────────────────────────────────────────
//  STATE MANAGEMENT, PRESETS, HAPTICS, WAKE LOCK, SWIPE TABS
// ─────────────────────────────────────────────────────────────────
let currentTab = 'media';
let currentPreset = localStorage.getItem('player_preset') || 'universal';
let mouseSensitivity = parseFloat(localStorage.getItem('mouse_sensitivity')) || 1.0;
let screenW = 1920, screenH = 1080;
let volumeLevel = parseInt(localStorage.getItem('volume_level')) || 50;

function setPreset(name, isAuto = false) {
  currentPreset = name;
  localStorage.setItem('player_preset', name);
  if (!isAuto) vibrate(15);
  
  document.querySelectorAll('.preset-btn').forEach(btn => {
    const isActive = btn.id === 'preset-btn-' + name;
    btn.classList.toggle('active', isActive);
    btn.setAttribute('aria-checked', isActive ? 'true' : 'false');
  });

  if (!isAuto) {
    let displayName = 'Universal / Netflix';
    if (name === 'youtube_hotstar') displayName = 'YouTube / Hotstar';
    if (name === 'vlc') displayName = 'VLC Player';
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
  } catch (_) {}
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
  vibrate(15);

  document.querySelectorAll('.nav-item').forEach(btn => {
    const isActive = btn.id === 'tab-btn-' + name;
    btn.classList.toggle('active', isActive);
    btn.setAttribute('aria-selected', isActive ? 'true' : 'false');
  });
  document.querySelectorAll('.tab-panel').forEach(panel => {
    panel.classList.toggle('active', panel.id === 'tab-' + name);
  });
}

function getTabOrder() {
  const tabs = ['media', 'mouse', 'keyboard'];
  const presentBtn = document.getElementById('tab-btn-present');
  if (presentBtn && presentBtn.style.display !== 'none') {
    tabs.push('present');
  }
  return tabs;
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

let swiperStartX = 0, swiperStartY = 0, swiperValid = false;

document.addEventListener('touchstart', e => {
  if (e.touches.length > 1 || 
      e.target.closest('#trackpad') || 
      e.target.closest('#presentPad') || 
      e.target.closest('#tab-keyboard') || 
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
  if (!t) return;
  t.textContent = msg;
  t.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => t.classList.remove('show'), 1500);
}
