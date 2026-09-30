// ─────────────────────────────────────────────────────────────────
//  WEBSOCKET & HTTP NETWORK TRANSPORT
// ─────────────────────────────────────────────────────────────────
async function post(url, body = {}) {
  const token = localStorage.getItem('session_token') || '';
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 8000);
  try {
    const r = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + token
      },
      body: JSON.stringify(body),
      signal: controller.signal
    });
    if (r.status === 401) {
      showPinOverlay();
      return false;
    }
    return r.ok;
  } catch (e) {
    setStatus('offline');
    showToast('⚠️ Connection lost');
    return false;
  } finally {
    clearTimeout(timer);
  }
}

const HTTP_MAP = {
  mouse_move:   '/mouse/move',
  mouse_stop:   '/mouse/stop',
  mouse_scroll: '/mouse/scroll',
  mouse_click:  '/mouse/click',
  key:          '/key',
  text:         '/text',
  pointer_on:   '/pointer/on',
  pointer_move: '/pointer/move',
  pointer_off:  '/pointer/off',
  blackout:     '/screen/blackout'
};

let socket = null;

function setStatus(s) {
  const dot = document.getElementById('statusDot');
  const statusLabel = document.getElementById('statusLabel');
  const banner = document.getElementById('connBanner');

  const text = s === 'active' ? 'Active' : (s === 'pairing' ? 'Pairing' : 'Offline');

  if (dot) dot.className = 'status-dot ' + (s === 'active' ? 'active' : (s === 'pairing' ? 'pairing' : 'offline'));
  if (statusLabel) statusLabel.textContent = text;

  if (s === 'active' || s === 'pairing') {
    if (banner) banner.classList.remove('visible');
  } else {
    if (banner) banner.classList.add('visible');
  }
}

function updateBattery(pct) {
  const chip = document.getElementById('batteryLowChip');
  const text = document.getElementById('batteryLowText');
  const settingsBattery = document.getElementById('settingsBattery');

  if (settingsBattery) {
    settingsBattery.textContent = (pct !== null && pct !== undefined) ? (pct + '%') : '--';
  }

  if (pct === null || pct === undefined) {
    if (chip) {
      chip.classList.add('hidden');
      chip.classList.remove('flex');
    }
  } else {
    const isLow = pct <= 20;
    if (chip && text) {
      text.textContent = pct + '%';
      if (isLow) {
        chip.classList.remove('hidden');
        chip.classList.add('flex');
      } else {
        chip.classList.add('hidden');
        chip.classList.remove('flex');
      }
    }
  }
}


function presetDisplayName(p) {
  if (p === 'vlc') return 'VLC';
  if (p === 'youtube_hotstar') return 'YouTube / Hotstar';
  return 'Universal';
}

let batteryPollTimer = null;

function connectSocket(token) {
  if (socket) { socket.disconnect(); socket = null; }
  if (batteryPollTimer) { clearInterval(batteryPollTimer); batteryPollTimer = null; }
  if (typeof io === 'undefined') return;
  socket = io({ auth: { token }, reconnection: true, reconnectionDelay: 1000, reconnectionDelayMax: 8000 });
  socket.on('connect', () => {
    if (batteryPollTimer) clearInterval(batteryPollTimer);
    batteryPollTimer = setInterval(() => {
      if (socket && socket.connected) {
        socket.emit('get_battery');
      }
    }, 10000);
  });
  socket.on('state', onServerState);
  socket.on('battery_update', d => {
    if (d && 'battery' in d) {
      updateBattery(d.battery);
    }
  });
  socket.on('audio_state', updateAudioUI);
  socket.on('preset_changed', d => {
    if (d && d.preset && d.preset !== currentPreset) {
      setPreset(d.preset, true);
      showToast('🎯 Auto-preset: ' + presetDisplayName(d.preset));
    }
  });
  socket.on('disconnect', () => {
    if (batteryPollTimer) { clearInterval(batteryPollTimer); batteryPollTimer = null; }
    if (typeof stopDpadRepeat === 'function') stopDpadRepeat();
    setStatus('offline');
  });
  socket.on('connect_error', () => setStatus('offline'));
}

function onServerState(data) {
  if (data.authorized) {
    setStatus('active');
    hidePinOverlay();
    if (data.screen_w) screenW = data.screen_w;
    if (data.screen_h) screenH = data.screen_h;

    // Dynamically update real host telemetry in header and settings modal
    const devName = data.device_name || data.hostname || 'Laptop';
    const platform = data.platform ? (' · ' + data.platform) : '';
    const fullDisplayName = devName + platform;

    const headerName = document.getElementById('headerDeviceName');
    if (headerName) headerName.textContent = fullDisplayName;

    const settingsDev = document.getElementById('settingsDeviceName');
    if (settingsDev) settingsDev.textContent = devName;

    const settingsPlat = document.getElementById('settingsPlatform');
    if (settingsPlat) settingsPlat.textContent = data.platform || 'Unknown';

    // The Present tab is always available (slide controls, timer, blackout).
    // Only the laser pad depends on a server-side transparent overlay.
    laserAvailable = !!data.overlay_available;
    const tabBtnPresent = document.getElementById('tab-btn-present');
    if (tabBtnPresent) tabBtnPresent.style.display = 'flex';
    if (typeof applyLaserAvailability === 'function') applyLaserAvailability();

    if (data.detected_preset && data.detected_preset !== currentPreset) {
      setPreset(data.detected_preset, true);
      showToast('🎯 Auto-preset: ' + presetDisplayName(data.detected_preset));
    }
    updateBattery(data.battery);
    if (data.audio) {
      updateAudioUI(data.audio);
    }
    blackoutActive = !!data.blackout;
    const bb = document.getElementById('blackoutBtn');
    if (bb) bb.classList.toggle('active', blackoutActive);
  } else {
    setStatus('pairing');
    showPinOverlay();
    updateBattery(null);
  }
}

async function socketSend(type, payload) {
  if (socket && socket.connected) {
    socket.emit(type, payload);
    return true;
  }
  const url = HTTP_MAP[type];
  return url ? post(url, payload || {}) : false;
}

const labels = {
  play_pause: '⏯ Play / Pause', 
  skip_forward: '⏩ +10 sec', 
  skip_back: '⏪ −10 sec',
  skip_forward_30: '⏭ +30 sec', 
  fullscreen: '⛶ Fullscreen',
  mute: '🔇 Mute', 
  vol_up: '🔊 Volume +', 
  vol_down: '🔉 Volume −', 
  subtitles: '💬 Subtitles',
  back: '🔙 Go Back',
  next: '⏭ Next Slide',
  next_slide: '⏭ Next Slide',
  prev_slide: '⏪ Previous Slide',
  present_start: '▶ Presentation started',
  present_exit: '⏹ Presentation exited'
};

async function send(action) {
  vibrate(25);
  await socketSend('key', { action, preset: currentPreset });
}

function disconnectSession() {
  if (socket && socket.connected) {
    socket.disconnect();
    setStatus('offline');
    showToast('🔌 Disconnected');
  } else {
    connectSocket(localStorage.getItem('session_token') || '');
    showToast('🔄 Reconnecting...');
  }
}

let forgetTimeout = null;
async function forgetDevice() {
  const btn = document.querySelector('.forget-device-btn');
  if (btn && !btn.classList.contains('confirming')) {
    btn.classList.add('confirming');
    const span = btn.querySelector('span');
    if (span) span.textContent = 'Tap again to revoke';
    vibrate(20);
    clearTimeout(forgetTimeout);
    forgetTimeout = setTimeout(() => {
      btn.classList.remove('confirming');
      if (span) span.textContent = 'Forget This Device';
    }, 3500);
    return;
  }
  if (btn) {
    btn.classList.remove('confirming');
    const span = btn.querySelector('span');
    if (span) span.textContent = 'Forget This Device';
  }
  clearTimeout(forgetTimeout);
  vibrate(30);
  await post('/revoke');
  localStorage.removeItem('session_token');
  showPinOverlay();
  showToast('🔒 Device forgotten');
  connectSocket('');
}

async function checkConnection() {
  connectSocket(localStorage.getItem('session_token') || '');
  const token = localStorage.getItem('session_token') || '';
  try {
    const r = await fetch('/ping', {
      headers: {
        'Authorization': 'Bearer ' + token
      }
    });
    if (r.ok) {
      const data = await r.json();
      if (data.authorized) setStatus('active');
      else setStatus('pairing');
    } else {
      throw new Error();
    }
  } catch (e) {
    setStatus('offline');
  }
}
