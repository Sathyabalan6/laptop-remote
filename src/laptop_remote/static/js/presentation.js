// ─────────────────────────────────────────────────────────────────
//  PRESENTATION MODE TIMER, COUNTER & LASER POINTER LOGIC
// ─────────────────────────────────────────────────────────────────
let elapsedSeconds = 0;
let timerInterval = null;
let timerStarted = false;

function startPresentationTimer() {
  if (timerStarted) return;
  timerStarted = true;
  timerInterval = setInterval(() => {
    elapsedSeconds++;
    const mm = String(Math.floor(elapsedSeconds / 60)).padStart(2, '0');
    const ss = String(elapsedSeconds % 60).padStart(2, '0');
    const el = document.getElementById('elapsedTimer');
    if (el) el.textContent = `${mm}:${ss}`;
  }, 1000);
}

let slideIndex = 1;

function updateSlideCounter() {
  const el = document.getElementById('slideCounter');
  if (el) el.textContent = String(slideIndex);
}

function slideCtrl(action) {
  send(action);
  if (action === 'next_slide') slideIndex += 1;
  else if (action === 'prev_slide') slideIndex = Math.max(1, slideIndex - 1);
  updateSlideCounter();
}

let restartConfirmTimeout = null;

function resetPresentation() {
  const btn = document.getElementById('restartBtn');
  const label = btn ? btn.querySelector('span') : null;
  if (btn && !btn.classList.contains('confirming')) {
    btn.classList.add('confirming');
    btn.setAttribute('title', 'Tap again to reset to Slide 1');
    if (label) label.textContent = '⚠️ Tap again to confirm restart';
    vibrate(20);
    if (typeof showToast === 'function') showToast('⚠️ Tap again to reset to Slide 1');
    
    clearTimeout(restartConfirmTimeout);
    restartConfirmTimeout = setTimeout(() => {
      btn.classList.remove('confirming');
      if (label) label.textContent = 'Restart from Slide 1';
      btn.setAttribute('title', 'Restart from Slide 1');
    }, 3000);
    return;
  }

  if (btn) {
    btn.classList.remove('confirming');
    if (label) label.textContent = 'Restart from Slide 1';
    btn.setAttribute('title', 'Restart from Slide 1');
  }
  clearTimeout(restartConfirmTimeout);

  slideIndex = 1;
  updateSlideCounter();
  elapsedSeconds = 0;
  const t = document.getElementById('elapsedTimer');
  if (t) t.textContent = '00:00';
  vibrate([30, 50]);
  if (typeof showToast === 'function') showToast('⏮️ Restarted at Slide 1');
  if (typeof closeAllPopovers === 'function') closeAllPopovers();
}

let blackoutActive = false;

function toggleBlackout() {
  blackoutActive = !blackoutActive;
  const btn = document.getElementById('blackoutBtn');
  if (btn) btn.classList.toggle('active', blackoutActive);
  socketSend('blackout', { on: blackoutActive });
  vibrate(15);
}

let presenting = false;

function togglePresentation() {
  presenting = !presenting;
  const btn = document.getElementById('presentLaunchBtn');
  const label = btn ? btn.querySelector('span') : null;
  if (presenting) {
    send('present_start');
    if (btn) btn.classList.add('active');
    if (label) label.textContent = 'Exit Presentation';
  } else {
    send('present_exit');
    if (btn) btn.classList.remove('active');
    if (label) label.textContent = 'Play Slideshow';
  }
}

document.addEventListener('DOMContentLoaded', () => {
  const presentPad = document.getElementById('presentPad');
  const laserDot = document.getElementById('laserDot');

  if (!presentPad || !laserDot) return;

  function updateLaserDot(e) {
    const rect = presentPad.getBoundingClientRect();
    const touch = e.touches[0];
    if (touch) {
      const x = touch.clientX - rect.left;
      const y = touch.clientY - rect.top;
      laserDot.style.left = `${x}px`;
      laserDot.style.top = `${y}px`;
    }
  }

  let pendingPointer = null;
  let pointerThrottle = null;
  let lastPresentTouch = null;

  function queuePointerMove(e) {
    if (e.touches.length === 0) return;
    const rect = presentPad.getBoundingClientRect();
    const t = e.touches[0];
    const xPct = Math.max(0, Math.min(1, (t.clientX - rect.left) / rect.width));
    const yPct = Math.max(0, Math.min(1, (t.clientY - rect.top) / rect.height));
    pendingPointer = { x: xPct * screenW, y: yPct * screenH };
    if (!pointerThrottle) pointerThrottle = setTimeout(flushPointer, 20);
  }

  function flushPointer() {
    pointerThrottle = null;
    if (pendingPointer) {
      const p = pendingPointer;
      pendingPointer = null;
      socketSend('pointer_move', p);
    }
  }

  // ── Hardware Gyroscope / Air Motion Implementation ─────────────────────
  let isAimingAir = false;
  let prevAirGamma = null;
  let prevAirBeta = null;
  let airThrottle = null;
  let sensorWatchdogTimer = null;
  const pendingAirDelta = { dx: 0, dy: 0 };
  const currentLaserPos = { x: screenW / 2, y: screenH / 2 };

  async function requestOrientationPermission() {
    if (typeof DeviceOrientationEvent !== 'undefined' && typeof DeviceOrientationEvent.requestPermission === 'function') {
      try {
        const resp = await DeviceOrientationEvent.requestPermission();
        return resp === 'granted';
      } catch {
        return false;
      }
    }
    return true;
  }

  function handleOrientationEvent(e) {
    if (!isAimingAir) return;
    if (sensorWatchdogTimer) {
      clearTimeout(sensorWatchdogTimer);
      sensorWatchdogTimer = null;
    }
    const currGamma = e.gamma;
    const currBeta = e.beta;
    if (typeof currGamma !== 'number' || typeof currBeta !== 'number') return;

    if (prevAirGamma === null || prevAirBeta === null) {
      prevAirGamma = currGamma;
      prevAirBeta = currBeta;
      return;
    }

    const computeAir = (window.trackpadLogic && window.trackpadLogic.computeAirDelta) ||
      ((cg, cb, pg, pb) => ({ dx: (cg - pg) * 2.0, dy: (cb - pb) * 2.0 }));

    const sens = (typeof airSensitivity !== 'undefined' ? airSensitivity : 1.8);
    const delta = computeAir(currGamma, currBeta, prevAirGamma, prevAirBeta, sens, 0.22);
    prevAirGamma = currGamma;
    prevAirBeta = currBeta;

    if (delta.dx === 0 && delta.dy === 0) return;

    pendingAirDelta.dx += delta.dx;
    pendingAirDelta.dy += delta.dy;

    if (!airThrottle) {
      airThrottle = requestAnimationFrame(flushAirMotion);
    }
  }

  function flushAirMotion() {
    airThrottle = null;
    if (pendingAirDelta.dx === 0 && pendingAirDelta.dy === 0) return;

    const dx = pendingAirDelta.dx;
    const dy = pendingAirDelta.dy;
    pendingAirDelta.dx = 0;
    pendingAirDelta.dy = 0;

    const currentMode = (typeof airMode !== 'undefined' ? airMode : 'cursor');
    if (currentMode === 'cursor') {
      socketSend('mouse_move', { dx, dy, sens: 1.0 });
    } else if (laserAvailable) {
      currentLaserPos.x = Math.max(0, Math.min(screenW, currentLaserPos.x + dx * 2.5));
      currentLaserPos.y = Math.max(0, Math.min(screenH, currentLaserPos.y + dy * 2.5));
      socketSend('pointer_move', currentLaserPos);
    }
  }

  async function startAirAim() {
    const granted = await requestOrientationPermission();
    if (!granted) {
      if (typeof showToast === 'function') showToast('⚠️ Gyroscope permission denied');
      return;
    }

    if (typeof window !== 'undefined' && !window.isSecureContext && window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
      if (typeof showToast === 'function') {
        showToast('🔒 HTTPS required for sensors: restart with laptop-remote --ssl');
      }
    }

    isAimingAir = true;
    prevAirGamma = null;
    prevAirBeta = null;
    pendingAirDelta.dx = 0;
    pendingAirDelta.dy = 0;
    vibrate(20);

    const btn = document.getElementById('btnAirAim');
    if (btn) {
      btn.classList.add('border-primary', 'bg-primary/20');
      const label = document.getElementById('airAimLabel');
      if (label) label.textContent = '🎯 Aiming... Tilt Phone in Air';
    }

    const currentMode = (typeof airMode !== 'undefined' ? airMode : 'cursor');
    if (currentMode === 'laser' && laserAvailable) {
      socketSend('pointer_on');
    }

    clearTimeout(sensorWatchdogTimer);
    sensorWatchdogTimer = setTimeout(() => {
      if (isAimingAir && prevAirGamma === null) {
        if (typeof showToast === 'function') {
          showToast('⚠️ No sensor events. Browsers block motion on plain HTTP (use --ssl)');
        }
      }
    }, 1200);

    window.addEventListener('deviceorientation', handleOrientationEvent, { passive: true });
  }

  function stopAirAim() {
    if (!isAimingAir) return;
    isAimingAir = false;
    window.removeEventListener('deviceorientation', handleOrientationEvent);

    if (sensorWatchdogTimer) {
      clearTimeout(sensorWatchdogTimer);
      sensorWatchdogTimer = null;
    }

    if (airThrottle) {
      cancelAnimationFrame(airThrottle);
      flushAirMotion();
    }

    const btn = document.getElementById('btnAirAim');
    if (btn) {
      btn.classList.remove('border-primary', 'bg-primary/20');
      const label = document.getElementById('airAimLabel');
      if (label) label.textContent = 'Hold to Aim (Air Pointer)';
    }

    const currentMode = (typeof airMode !== 'undefined' ? airMode : 'cursor');
    if (currentMode === 'laser' && laserAvailable) {
      socketSend('pointer_off');
    } else {
      socketSend('mouse_stop');
    }
  }

  const btnAir = document.getElementById('btnAirAim');
  if (btnAir) {
    btnAir.addEventListener('pointerdown', e => {
      e.preventDefault();
      try {
        if (typeof btnAir.setPointerCapture === 'function') {
          btnAir.setPointerCapture(e.pointerId);
        }
      } catch {}
      startAirAim();
    });
    btnAir.addEventListener('pointerup', e => {
      e.preventDefault();
      try {
        if (typeof btnAir.releasePointerCapture === 'function') {
          btnAir.releasePointerCapture(e.pointerId);
        }
      } catch {}
      stopAirAim();
    });
    btnAir.addEventListener('pointercancel', stopAirAim);
  }

  presentPad.addEventListener('touchstart', e => {
    e.preventDefault();
    vibrate(15);
    startPresentationTimer();
    const currentMode = (typeof airMode !== 'undefined' ? airMode : 'cursor');
    if (currentMode === 'laser') {
      if (!laserAvailable) return;
      laserDot.style.display = 'block';
      updateLaserDot(e);
      socketSend('pointer_on');
      queuePointerMove(e);
    } else {
      lastPresentTouch = { x: e.touches[0].clientX, y: e.touches[0].clientY };
    }
  }, { passive: false });

  presentPad.addEventListener('touchmove', e => {
    e.preventDefault();
    const currentMode = (typeof airMode !== 'undefined' ? airMode : 'cursor');
    if (currentMode === 'laser') {
      if (!laserAvailable) return;
      updateLaserDot(e);
      queuePointerMove(e);
    } else if (lastPresentTouch && e.touches[0]) {
      const dx = e.touches[0].clientX - lastPresentTouch.x;
      const dy = e.touches[0].clientY - lastPresentTouch.y;
      lastPresentTouch = { x: e.touches[0].clientX, y: e.touches[0].clientY };
      socketSend('mouse_move', { dx, dy, sens: 1.0 });
    }
  }, { passive: false });

  presentPad.addEventListener('touchend', e => {
    e.preventDefault();
    const currentMode = (typeof airMode !== 'undefined' ? airMode : 'cursor');
    if (currentMode === 'laser') {
      if (!laserAvailable) return;
      if (pointerThrottle) { clearTimeout(pointerThrottle); flushPointer(); }
      if (e.touches.length === 0) {
        laserDot.style.display = 'none';
        socketSend('pointer_off');
      }
    } else {
      lastPresentTouch = null;
      socketSend('mouse_stop');
    }
  }, { passive: false });

  applyLaserAvailability();
});

// Show or hide the laser controls depending on server overlay availability.
function applyLaserAvailability() {
  const section = document.getElementById('presentLaserSection');
  if (section) {
    section.style.display = 'flex';
  }
  const btnLaser = document.getElementById('airModeLaserBtn');
  if (btnLaser) {
    if (!laserAvailable) {
      btnLaser.classList.add('opacity-50', 'cursor-not-allowed');
      btnLaser.title = 'Laser overlay unavailable on this desktop compositor';
      if (typeof airMode !== 'undefined' && airMode === 'laser' && typeof setAirMode === 'function') {
        setAirMode('cursor');
      }
    } else {
      btnLaser.classList.remove('opacity-50', 'cursor-not-allowed');
      btnLaser.removeAttribute('title');
    }
  }
  if (typeof syncAirUI === 'function') {
    syncAirUI();
  }
}

if (typeof window !== 'undefined') {
  window.slideCtrl = slideCtrl;
  window.resetPresentation = resetPresentation;
  window.toggleBlackout = toggleBlackout;
  window.togglePresentation = togglePresentation;
  window.startPresentationTimer = startPresentationTimer;
  window.applyLaserAvailability = applyLaserAvailability;
}
