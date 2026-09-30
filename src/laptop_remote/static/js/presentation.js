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
  if (btn && !btn.classList.contains('confirming')) {
    btn.classList.add('confirming');
    btn.setAttribute('title', 'Tap again to reset to Slide 1');
    const origHtml = btn.innerHTML;
    btn.dataset.origHtml = origHtml;
    btn.innerHTML = '<span class="text-xs font-bold text-amber-400">⚠️ Tap again to confirm restart to Slide 1</span>';
    vibrate(20);
    if (typeof showToast === 'function') showToast('⚠️ Tap again to reset to Slide 1');
    
    clearTimeout(restartConfirmTimeout);
    restartConfirmTimeout = setTimeout(() => {
      btn.classList.remove('confirming');
      if (btn.dataset.origHtml) btn.innerHTML = btn.dataset.origHtml;
      btn.setAttribute('title', 'Restart from Slide 1');
    }, 3000);
    return;
  }

  if (btn) {
    btn.classList.remove('confirming');
    if (btn.dataset.origHtml) btn.innerHTML = btn.dataset.origHtml;
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

const PRESENT_ON_HTML =
  '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="currentColor" stroke="none"><polygon points="8 5 19 12 8 19 8 5"/></svg>' +
  '<span>Start Presentation</span>';
const PRESENT_OFF_HTML =
  '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="currentColor" stroke="none"><rect x="6" y="6" width="12" height="12" rx="1"/></svg>' +
  '<span>Exit Presentation</span>';

let presenting = false;

function togglePresentation() {
  presenting = !presenting;
  const btn = document.getElementById('presentLaunchBtn');
  if (presenting) {
    send('present_start');
    if (btn) { btn.classList.add('active'); btn.innerHTML = PRESENT_OFF_HTML; }
  } else {
    send('present_exit');
    if (btn) { btn.classList.remove('active'); btn.innerHTML = PRESENT_ON_HTML; }
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

  presentPad.addEventListener('touchstart', e => {
    e.preventDefault();
    vibrate(15);
    startPresentationTimer();
    if (!laserAvailable) return;   // no server overlay on this platform
    laserDot.style.display = 'block';
    updateLaserDot(e);
    socketSend('pointer_on');
    queuePointerMove(e);
  }, { passive: false });

  presentPad.addEventListener('touchmove', e => {
    e.preventDefault();
    if (!laserAvailable) return;
    updateLaserDot(e);
    queuePointerMove(e);
  }, { passive: false });

  presentPad.addEventListener('touchend', e => {
    e.preventDefault();
    if (!laserAvailable) return;
    if (pointerThrottle) { clearTimeout(pointerThrottle); flushPointer(); }
    if (e.touches.length === 0) {
      laserDot.style.display = 'none';
      socketSend('pointer_off');
    }
  }, { passive: false });

  applyLaserAvailability();
});

// Show or hide the laser pad depending on server overlay availability.
function applyLaserAvailability() {
  const section = document.getElementById('presentLaserSection');
  if (section) {
    section.style.display = laserAvailable ? 'flex' : 'none';
  }
}
