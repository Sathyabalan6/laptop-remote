// ─────────────────────────────────────────────────────────────────
//  MOUSE TAB & TRACKPAD TOUCH LOGIC
// ─────────────────────────────────────────────────────────────────
async function click_btn(btn) {
  vibrate(30);
  await socketSend('mouse_click', { button: btn });
}

async function scroll(dy) {
  await socketSend('mouse_scroll', { dy });
}

let scrollInterval = null;
let scrollTimeout = null;

function startContinuousScroll(e, dir) {
  if (e && e.cancelable) e.preventDefault();
  stopContinuousScroll();

  const dy = dir === 'up' ? 12 : -12;
  vibrate(15);
  scroll(dy);

  scrollTimeout = setTimeout(() => {
    scrollInterval = setInterval(() => {
      vibrate(8);
      scroll(dy);
    }, 80);
  }, 250);
}

function stopContinuousScroll(e) {
  if (e && e.cancelable) e.preventDefault();
  if (scrollTimeout) {
    clearTimeout(scrollTimeout);
    scrollTimeout = null;
  }
  if (scrollInterval) {
    clearInterval(scrollInterval);
    scrollInterval = null;
  }
}

document.addEventListener('DOMContentLoaded', () => {
  const trackpadLogic = window.trackpadLogic || {};

const applyInertia =
  trackpadLogic.applyInertia || ((velocity, decay) => velocity * decay);

const clampSensitivity =
  trackpadLogic.clampSensitivity ||
  ((value, min = 0.5, max = 4.0) =>
    Math.min(max, Math.max(min, value)));

const classifyGesture =
  trackpadLogic.classifyGesture ||
  ((prevPoints, currPoints, totalMovement = 0, movementThreshold = 2) => {
    if (currPoints.length === 2) {
      return 'scroll';
    }

    if (currPoints.length === 1 && prevPoints.length === 1) {
      return totalMovement > movementThreshold ? 'move' : 'tap';
    }

    return 'tap';
  });
  const sensSlider = document.getElementById('sensitivitySlider');
  const sensLabel = document.getElementById('sensitivityLabel');

  if (sensSlider && sensLabel) {
    mouseSensitivity = clampSensitivity(mouseSensitivity);
    sensSlider.value = mouseSensitivity;
    sensLabel.textContent = mouseSensitivity.toFixed(1) + 'x';

    sensSlider.addEventListener('input', e => {
      mouseSensitivity = clampSensitivity(parseFloat(e.target.value));
      sensLabel.textContent = mouseSensitivity.toFixed(1) + 'x';
      localStorage.setItem('mouse_sensitivity', mouseSensitivity);
    });
  }

  const pad = document.getElementById('trackpad');
  const ghost = document.getElementById('cursorGhost');
  const scrollIndicator = document.getElementById('scrollIndicator');

  if (!pad) return;

  let lastTouches = [];
  let maxFingers = 0;
  let moveSent = false;
  let scrollSent = false;
  let totalMovement = 0;
  let bufferedDx = 0;
  let bufferedDy = 0;

  let pendingDx = 0, pendingDy = 0;
  let pendingScrollDy = 0;
  let moveThrottle = null;
  let scrollThrottle = null;

  let lastScrollVelocity = 0;
  let scrollInertiaId = null;
  let hasVibratedScroll = false;

  const SCROLL_SENSITIVITY = Math.min(2.5, Math.max(1.0, (window.devicePixelRatio || 1) * 1.2));
  const MOVE_THRESHOLD_PX = 2;
  const INERTIA_DECAY = 0.82;
  const INERTIA_MIN = 0.8;

  async function flushMove() {
    if (pendingDx === 0 && pendingDy === 0) {
      moveThrottle = null;
      return;
    }

    const dx = pendingDx;
    const dy = pendingDy;
    pendingDx = 0;
    pendingDy = 0;

    const ok = await socketSend('mouse_move', { dx, dy, sens: mouseSensitivity });
    if (!ok) { moveThrottle = null; return; }
    if (pendingDx !== 0 || pendingDy !== 0) {
      moveThrottle = requestAnimationFrame(flushMove);
    } else {
      moveThrottle = null;
    }
  }

  async function flushScroll() {
    if (pendingScrollDy === 0) {
      scrollThrottle = null;
      return;
    }

    const dy = Math.max(-20, Math.min(20, pendingScrollDy));
    pendingScrollDy = 0;
    lastScrollVelocity = dy;

    const ok = await socketSend('mouse_scroll', { dy });
    if (!ok) { scrollThrottle = null; return; }
    if (pendingScrollDy !== 0) {
      scrollThrottle = setTimeout(flushScroll, 16);
    } else {
      scrollThrottle = null;
    }
  }

  function runInertia() {
    lastScrollVelocity = applyInertia(lastScrollVelocity, INERTIA_DECAY);
    if (Math.abs(lastScrollVelocity) < INERTIA_MIN) {
      cancelAnimationFrame(scrollInertiaId);
      scrollInertiaId = null;
      return;
    }

    pendingScrollDy += lastScrollVelocity;
    if (!scrollThrottle) {
      scrollThrottle = setTimeout(flushScroll, 16);
    }

    scrollInertiaId = requestAnimationFrame(runInertia);
  }

  pad.addEventListener('touchstart', e => {
    e.preventDefault();

    if (scrollInertiaId) {
      cancelAnimationFrame(scrollInertiaId);
      scrollInertiaId = null;
      lastScrollVelocity = 0;
    }

    maxFingers = e.touches.length;
    moveSent = false;
    scrollSent = false;
    totalMovement = 0;
    bufferedDx = 0;
    bufferedDy = 0;
    hasVibratedScroll = false;

    const rect = pad.getBoundingClientRect();
    lastTouches = Array.from(e.touches).map(t => ({ x: t.clientX, y: t.clientY }));

    if (e.touches.length === 1 && ghost) {
      const x = e.touches[0].clientX - rect.left;
      const y = e.touches[0].clientY - rect.top;
      ghost.style.left = `${x}px`;
      ghost.style.top = `${y}px`;
      ghost.classList.add('visible');
    }

    pad.classList.add('active');
    if (scrollIndicator) scrollIndicator.classList.remove('show');
  }, { passive: false });

  pad.addEventListener('touchmove', e => {
    e.preventDefault();
    if (!lastTouches.length) return;

    maxFingers = Math.max(maxFingers, e.touches.length);
    const rect = pad.getBoundingClientRect();
    const currentPoints = Array.from(e.touches).map(t => ({
      x: t.clientX,
      y: t.clientY
    }));

    let gesture = classifyGesture(
      lastTouches,
      currentPoints,
      totalMovement,
      MOVE_THRESHOLD_PX
    );

    if (e.touches.length === 2) {
      const t0 = e.touches[0], t1 = e.touches[1];

      if (lastTouches.length < 2) {
        lastTouches = [{ x: t0.clientX, y: t0.clientY }, { x: t1.clientX, y: t1.clientY }];
        return;
      }

      const curYAvg = (t0.clientY + t1.clientY) / 2;
      const lastYAvg = (lastTouches[0].y + lastTouches[1].y) / 2;
      const dy = curYAvg - lastYAvg;

      if (!hasVibratedScroll && Math.abs(dy) > 5) {
        vibrate(8);
        hasVibratedScroll = true;
      }

      const scrollUnit = dy * SCROLL_SENSITIVITY * 1.5;
      pendingScrollDy += scrollUnit;
      scrollSent = true;

      lastTouches = [{ x: t0.clientX, y: t0.clientY }, { x: t1.clientX, y: t1.clientY }];
      if (scrollIndicator) scrollIndicator.classList.add('show');

      if (!scrollThrottle) scrollThrottle = setTimeout(flushScroll, 16);

    } else if (e.touches.length === 1) {
      const t = e.touches[0];
      const dx = (t.clientX - lastTouches[0].x);
      const dy = (t.clientY - lastTouches[0].y);

      bufferedDx += dx;
      bufferedDy += dy;
      totalMovement += Math.sqrt(dx * dx + dy * dy);
      gesture = classifyGesture(
        lastTouches,
        [{ x: t.clientX, y: t.clientY }],
        totalMovement,
        MOVE_THRESHOLD_PX
      );

      if (ghost) {
        const x = t.clientX - rect.left;
        const y = t.clientY - rect.top;
        ghost.style.left = `${x}px`;
        ghost.style.top = `${y}px`;
        ghost.classList.add('visible');
      }

      if (gesture === 'move') {
        pendingDx += bufferedDx;
        pendingDy += bufferedDy;
        bufferedDx = 0;
        bufferedDy = 0;
        moveSent = true;
        if (!moveThrottle) {
          moveThrottle = requestAnimationFrame(flushMove);
        }
      }

      lastTouches = [{ x: t.clientX, y: t.clientY }];
    }
  }, { passive: false });

  pad.addEventListener('touchend', e => {
    e.preventDefault();

    if (moveThrottle) { cancelAnimationFrame(moveThrottle); moveThrottle = null; flushMove(); }
    if (scrollThrottle) { clearTimeout(scrollThrottle); scrollThrottle = null; flushScroll(); }

    socketSend('mouse_stop');

    if (maxFingers === 1 && !moveSent) {
      click_btn('left');
    }

    if (scrollSent && Math.abs(lastScrollVelocity) >= INERTIA_MIN) {
      scrollInertiaId = requestAnimationFrame(runInertia);
    }

    if (e.touches.length === 0) {
      lastTouches = [];
      moveSent = false;
      scrollSent = false;
      maxFingers = 0;
      bufferedDx = 0;
      bufferedDy = 0;
      pad.classList.remove('active');
      if (ghost) ghost.classList.remove('visible');
      if (scrollIndicator) scrollIndicator.classList.remove('show');
    } else {
      lastTouches = Array.from(e.touches).map(t => ({ x: t.clientX, y: t.clientY }));
    }
  }, { passive: false });
});
