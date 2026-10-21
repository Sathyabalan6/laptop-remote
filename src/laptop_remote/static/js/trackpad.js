// ─────────────────────────────────────────────────────────────────
//  MOUSE TAB & TRACKPAD TOUCH LOGIC
// ─────────────────────────────────────────────────────────────────
let isDragLocked = false;

async function click_btn(btn) {
  if (typeof window !== 'undefined' && window.haptic) window.haptic.tap(); else vibrate(15);
  if (btn === 'left' && isDragLocked) {
    isDragLocked = false;
    const dragBtn = document.getElementById('btnDragLock');
    if (dragBtn) {
      dragBtn.classList.remove('active');
      dragBtn.setAttribute('aria-pressed', 'false');
    }
  }
  await socketSend('mouse_click', { button: btn, action: 'click' });
}

async function toggleDragLock() {
  isDragLocked = !isDragLocked;
  if (typeof window !== 'undefined' && window.haptic) {
    if (isDragLocked) window.haptic.heavy(); else window.haptic.release();
  } else {
    vibrate(isDragLocked ? 30 : [15, 40, 15]);
  }
  const btn = document.getElementById('btnDragLock');
  if (btn) {
    btn.classList.toggle('active', isDragLocked);
    btn.setAttribute('aria-pressed', isDragLocked ? 'true' : 'false');
  }
  if (typeof showToast === 'function') {
    showToast(isDragLocked ? '🔒 Drag Lock: ON' : '🔓 Drag Lock: OFF');
  }
  await socketSend('mouse_click', { button: 'left', action: isDragLocked ? 'down' : 'up' });
}

async function scroll(dy) {
  await socketSend('mouse_scroll', { dy });
}

let scrollInterval = null;
let scrollTimeout = null;

function startContinuousScroll(e, dir) {
  if (e && e.cancelable) e.preventDefault();
  stopContinuousScroll();

  const dy = dir === 'up' ? 3 : -3;
  vibrate(15);
  scroll(dy);

  scrollTimeout = setTimeout(() => {
    scrollInterval = setInterval(() => {
      vibrate(8);
      scroll(dir === 'up' ? 2 : -2);
    }, 90);
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

  const clampScrollSensitivity =
    trackpadLogic.clampScrollSensitivity ||
    ((value, min = 0.2, max = 3.0) => Math.min(max, Math.max(min, value)));

  const computeScrollDelta =
    trackpadLogic.computeScrollDelta ||
    ((rawDy, sens = 1.0, dir = 'natural', div = 18.0) =>
      (rawDy / div) * sens * (dir === 'inverted' ? -1 : 1));

  const clampScrollDelta =
    trackpadLogic.clampScrollDelta ||
    ((delta, max = 4.0) => Math.max(-max, Math.min(max, delta)));

  const applyScrollInertia =
    trackpadLogic.applyScrollInertia ||
    ((velocity, decay = 0.70, min = 0.35) => {
      const d = velocity * decay;
      return Math.abs(d) < min ? 0 : d;
    });

  const isTwoFingerScrollGesture =
    trackpadLogic.isTwoFingerScrollGesture ||
    ((touches, startTouches, threshold = 6) => {
      if (!touches || !startTouches || touches.length < 2 || startTouches.length < 2) return false;
      const curY = (touches[0].y + touches[1].y) / 2;
      const startY = (startTouches[0].y + startTouches[1].y) / 2;
      const curX = (touches[0].x + touches[1].x) / 2;
      const startX = (startTouches[0].x + startTouches[1].x) / 2;
      return Math.hypot(curX - startX, curY - startY) >= threshold;
    });

  const classifyTwoFingerIntent =
    trackpadLogic.classifyTwoFingerIntent ||
    ((currSpan, startSpan, centroidDist, pinchEnabled = true, spanThresh = 12, centThresh = 6) => {
      if (!pinchEnabled) return centroidDist >= centThresh ? 'scroll' : null;
      const spanChange = Math.abs(currSpan - startSpan);
      if (spanChange < spanThresh && centroidDist < centThresh) return null;
      if (spanChange >= spanThresh && spanChange > centroidDist * 1.2) return 'zoom';
      if (centroidDist >= centThresh) return 'scroll';
      return spanChange > centroidDist ? 'zoom' : 'scroll';
    });

  const computeZoomDelta =
    trackpadLogic.computeZoomDelta ||
    ((spanDelta, sens = 1.0, div = 15.0) => (spanDelta / div) * sens);

  const clampZoomDelta =
    trackpadLogic.clampZoomDelta ||
    ((delta, max = 3.0) => Math.max(-max, Math.min(max, delta)));

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
  const speedPopoverLabel = document.getElementById('speedPopoverLabel');
  const sensFill = document.getElementById('speedSliderFill');
  const sensThumb = document.getElementById('speedSliderThumb');

  function updateSpeedUI(val) {
    if (sensLabel) sensLabel.textContent = val.toFixed(1) + 'x';
    if (speedPopoverLabel) speedPopoverLabel.textContent = val.toFixed(1) + 'x';
    if (sensFill && sensThumb && sensSlider) {
      const min = parseFloat(sensSlider.min) || 0.5;
      const max = parseFloat(sensSlider.max) || 4.0;
      const percent = ((val - min) / (max - min)) * 100;
      sensFill.style.width = percent + '%';
      sensThumb.style.left = percent + '%';
    }
  }

  if (sensSlider) {
    mouseSensitivity = clampSensitivity(mouseSensitivity);
    sensSlider.value = mouseSensitivity;
    updateSpeedUI(mouseSensitivity);

    sensSlider.addEventListener('input', e => {
      mouseSensitivity = clampSensitivity(parseFloat(e.target.value));
      updateSpeedUI(mouseSensitivity);
      localStorage.setItem('mouse_sensitivity', mouseSensitivity);
    });
  }

  const scrollSlider = document.getElementById('scrollSensitivitySlider');
  const scrollPopoverLabel = document.getElementById('scrollPopoverLabel');
  const scrollFill = document.getElementById('scrollSliderFill');
  const scrollThumb = document.getElementById('scrollSliderThumb');

  function updateScrollSpeedUI(val) {
    if (scrollPopoverLabel) scrollPopoverLabel.textContent = val.toFixed(1) + 'x';
    const settingsLabel = document.getElementById('settingsScrollLabel');
    if (settingsLabel) settingsLabel.textContent = val.toFixed(1) + 'x';
    const settingsSlider = document.getElementById('settingsScrollSlider');
    if (settingsSlider) settingsSlider.value = val;
    if (scrollFill && scrollThumb && scrollSlider) {
      const min = parseFloat(scrollSlider.min) || 0.2;
      const max = parseFloat(scrollSlider.max) || 3.0;
      const percent = ((val - min) / (max - min)) * 100;
      scrollFill.style.width = percent + '%';
      scrollThumb.style.left = percent + '%';
    }
  }

  if (scrollSlider) {
    const curSens = typeof scrollSensitivity !== 'undefined' ? scrollSensitivity : 1.0;
    scrollSlider.value = curSens;
    updateScrollSpeedUI(curSens);

    scrollSlider.addEventListener('input', e => {
      const val = parseFloat(e.target.value);
      if (typeof setScrollSensitivity === 'function') {
        setScrollSensitivity(val);
      }
      updateScrollSpeedUI(val);
    });
  }

  const pad = document.getElementById('trackpad');
  const ghost = document.getElementById('cursorGhost');
  const scrollIndicator = document.getElementById('scrollIndicator');
  const zoomIndicator = document.getElementById('zoomIndicator');
  const zoomIndicatorText = document.getElementById('zoomIndicatorText');

  if (!pad) return;

  let lastTouches = [];
  let twoFingerStartTouches = null;
  let twoFingerMode = null; // null | 'scroll' | 'zoom'
  let twoFingerStartSpan = 0;
  let twoFingerLastSpan = 0;
  let maxFingers = 0;
  let moveSent = false;
  let scrollSent = false;
  let zoomSent = false;
  let totalMovement = 0;
  let bufferedDx = 0;
  let bufferedDy = 0;

  let pendingDx = 0, pendingDy = 0;
  let pendingScrollDy = 0;
  let pendingZoomDelta = 0;
  let moveThrottle = null;
  let scrollThrottle = null;
  let zoomThrottle = null;
  let zoomHideTimer = null;

  let lastScrollVelocity = 0;
  let scrollInertiaId = null;
  let inertiaFrames = 0;
  let hasVibratedScroll = false;
  const MAX_INERTIA_FRAMES = 8;
  const MOVE_THRESHOLD_PX = 2;

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

    const dy = clampScrollDelta(pendingScrollDy, 4.0);
    pendingScrollDy -= dy;
    lastScrollVelocity = dy;

    const ok = await socketSend('mouse_scroll', { dy });
    if (!ok) { scrollThrottle = null; return; }
    if (Math.abs(pendingScrollDy) >= 0.1) {
      scrollThrottle = requestAnimationFrame(flushScroll);
    } else {
      pendingScrollDy = 0;
      scrollThrottle = null;
    }
  }

  async function flushZoom() {
    if (pendingZoomDelta === 0) {
      zoomThrottle = null;
      return;
    }

    const delta = clampZoomDelta(pendingZoomDelta, 3.0);
    pendingZoomDelta -= delta;

    const ok = await socketSend('mouse_zoom', { delta });
    if (!ok) { zoomThrottle = null; return; }
    if (Math.abs(pendingZoomDelta) >= 0.1) {
      zoomThrottle = requestAnimationFrame(flushZoom);
    } else {
      pendingZoomDelta = 0;
      zoomThrottle = null;
    }
  }

  function runInertia() {
    const inertiaAllowed = typeof scrollInertia !== 'undefined' ? scrollInertia : true;
    if (!inertiaAllowed || inertiaFrames >= MAX_INERTIA_FRAMES) {
      cancelAnimationFrame(scrollInertiaId);
      scrollInertiaId = null;
      lastScrollVelocity = 0;
      inertiaFrames = 0;
      return;
    }

    lastScrollVelocity = applyScrollInertia(lastScrollVelocity, 0.70, 0.35);
    if (lastScrollVelocity === 0) {
      cancelAnimationFrame(scrollInertiaId);
      scrollInertiaId = null;
      lastScrollVelocity = 0;
      inertiaFrames = 0;
      return;
    }

    inertiaFrames++;
    pendingScrollDy += lastScrollVelocity;
    if (!scrollThrottle) {
      scrollThrottle = requestAnimationFrame(flushScroll);
    }

    scrollInertiaId = requestAnimationFrame(runInertia);
  }

  pad.addEventListener('touchstart', e => {
    e.preventDefault();

    if (scrollInertiaId) {
      cancelAnimationFrame(scrollInertiaId);
      scrollInertiaId = null;
      lastScrollVelocity = 0;
      inertiaFrames = 0;
    }

    maxFingers = e.touches.length;
    moveSent = false;
    scrollSent = false;
    zoomSent = false;
    twoFingerMode = null;
    totalMovement = 0;
    bufferedDx = 0;
    bufferedDy = 0;
    hasVibratedScroll = false;

    const rect = pad.getBoundingClientRect();
    lastTouches = Array.from(e.touches).map(t => ({ x: t.clientX, y: t.clientY }));
    twoFingerStartTouches = e.touches.length === 2 ? [...lastTouches] : null;

    if (e.touches.length === 2) {
      const t0 = e.touches[0], t1 = e.touches[1];
      twoFingerStartSpan = Math.hypot(t1.clientX - t0.clientX, t1.clientY - t0.clientY);
      twoFingerLastSpan = twoFingerStartSpan;
    } else {
      twoFingerStartSpan = 0;
      twoFingerLastSpan = 0;
    }

    if (e.touches.length === 1 && ghost) {
      const x = e.touches[0].clientX - rect.left;
      const y = e.touches[0].clientY - rect.top;
      ghost.style.left = `${x}px`;
      ghost.style.top = `${y}px`;
      ghost.classList.add('visible');
    }

    pad.classList.add('active');
    if (scrollIndicator) scrollIndicator.classList.remove('show');

    if (typeof closeAllPopovers === 'function') closeAllPopovers();

    const centerPrompt = document.getElementById('centerPrompt');
    if (centerPrompt && !centerPrompt.classList.contains('opacity-0')) {
      centerPrompt.classList.add('opacity-0', 'pointer-events-none');
      setTimeout(() => { centerPrompt.style.display = 'none'; }, 300);
    }
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

    if (e.touches.length === 2) {
      if (ghost) ghost.classList.remove('visible');
      const t0 = e.touches[0], t1 = e.touches[1];
      const currentTwo = [{ x: t0.clientX, y: t0.clientY }, { x: t1.clientX, y: t1.clientY }];

      if (!twoFingerStartTouches) {
        twoFingerStartTouches = currentTwo;
        twoFingerStartSpan = Math.hypot(t1.clientX - t0.clientX, t1.clientY - t0.clientY);
        twoFingerLastSpan = twoFingerStartSpan;
        lastTouches = currentTwo;
        return;
      }

      const currSpan = Math.hypot(t1.clientX - t0.clientX, t1.clientY - t0.clientY);
      const curCentroidX = (t0.clientX + t1.clientX) / 2;
      const curCentroidY = (t0.clientY + t1.clientY) / 2;
      const startCentroidX = (twoFingerStartTouches[0].x + twoFingerStartTouches[1].x) / 2;
      const startCentroidY = (twoFingerStartTouches[0].y + twoFingerStartTouches[1].y) / 2;
      const centroidDist = Math.hypot(curCentroidX - startCentroidX, curCentroidY - startCentroidY);

      if (!twoFingerMode) {
        const isZoomEnabled = typeof pinchZoomEnabled !== 'undefined' ? pinchZoomEnabled : true;
        const intent = classifyTwoFingerIntent(currSpan, twoFingerStartSpan, centroidDist, isZoomEnabled, 12, 6);
        if (!intent) {
          return;
        }
        twoFingerMode = intent;
        if (!hasVibratedScroll) {
          vibrate(10);
          hasVibratedScroll = true;
        }
      }

      if (twoFingerMode === 'zoom') {
        const spanDelta = currSpan - twoFingerLastSpan;
        twoFingerLastSpan = currSpan;

        const zoomDelta = computeZoomDelta(spanDelta, 1.0, 15.0);
        pendingZoomDelta += zoomDelta;
        zoomSent = true;

        if (zoomIndicator) {
          zoomIndicator.classList.remove('opacity-0');
          if (zoomIndicatorText) {
            zoomIndicatorText.textContent = spanDelta >= 0 ? '🔍 Zoom In' : '🔍 Zoom Out';
          }
          clearTimeout(zoomHideTimer);
          zoomHideTimer = setTimeout(() => {
            if (zoomIndicator) zoomIndicator.classList.add('opacity-0');
          }, 600);
        }

        if (!zoomThrottle) zoomThrottle = requestAnimationFrame(flushZoom);
        lastTouches = currentTwo;
        return;
      }

      // twoFingerMode === 'scroll':
      if (lastTouches.length < 2) {
        lastTouches = currentTwo;
        return;
      }

      const curYAvg = (t0.clientY + t1.clientY) / 2;
      const lastYAvg = (lastTouches[0].y + lastTouches[1].y) / 2;
      const dy = curYAvg - lastYAvg;

      const curSens = typeof scrollSensitivity !== 'undefined' ? scrollSensitivity : 1.0;
      const curDir = typeof scrollDirection !== 'undefined' ? scrollDirection : 'natural';
      const scrollUnit = computeScrollDelta(dy, curSens, curDir, 18.0);

      pendingScrollDy += scrollUnit;
      scrollSent = true;

      lastTouches = currentTwo;
      if (scrollIndicator) scrollIndicator.classList.add('show');

      if (!scrollThrottle) scrollThrottle = requestAnimationFrame(flushScroll);

    } else if (e.touches.length === 1) {
      twoFingerStartTouches = null;
      twoFingerMode = null;
      twoFingerStartSpan = 0;
      twoFingerLastSpan = 0;

      const t = e.touches[0];
      const dx = (t.clientX - lastTouches[0].x);
      const dy = (t.clientY - lastTouches[0].y);

      bufferedDx += dx;
      bufferedDy += dy;
      totalMovement += Math.sqrt(dx * dx + dy * dy);
      const gesture = classifyGesture(
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

  const handleTouchEndOrCancel = e => {
    e.preventDefault();

    if (moveThrottle) { cancelAnimationFrame(moveThrottle); moveThrottle = null; flushMove(); }
    if (scrollThrottle) { cancelAnimationFrame(scrollThrottle); scrollThrottle = null; flushScroll(); }
    if (zoomThrottle) { cancelAnimationFrame(zoomThrottle); zoomThrottle = null; flushZoom(); }

    socketSend('mouse_stop');

    // 1-finger tap -> Left Click
    if (e.type === 'touchend' && maxFingers === 1 && !moveSent) {
      click_btn('left');
    }

    // 2-finger tap without scroll or zoom -> Right Click
    if (e.type === 'touchend' && maxFingers === 2 && !scrollSent && !zoomSent && !twoFingerMode) {
      if (typeof window !== 'undefined' && window.haptic) window.haptic.rightClick(); else vibrate([20, 30, 20]);
      click_btn('right');
    }

    // Natural momentum if actively scrolling
    if (scrollSent && Math.abs(lastScrollVelocity) >= 0.5) {
      inertiaFrames = 0;
      scrollInertiaId = requestAnimationFrame(runInertia);
    }

    if (e.touches.length === 0) {
      lastTouches = [];
      twoFingerStartTouches = null;
      twoFingerMode = null;
      twoFingerStartSpan = 0;
      twoFingerLastSpan = 0;
      moveSent = false;
      scrollSent = false;
      zoomSent = false;
      maxFingers = 0;
      bufferedDx = 0;
      bufferedDy = 0;
      pad.classList.remove('active');
      if (ghost) ghost.classList.remove('visible');
      if (scrollIndicator) scrollIndicator.classList.remove('show');
      if (zoomIndicator) zoomIndicator.classList.add('opacity-0');
    } else {
      lastTouches = Array.from(e.touches).map(t => ({ x: t.clientX, y: t.clientY }));
      if (e.touches.length !== 2) {
        twoFingerStartTouches = null;
        twoFingerMode = null;
        twoFingerStartSpan = 0;
        twoFingerLastSpan = 0;
      }
    }
  };

  pad.addEventListener('touchend', handleTouchEndOrCancel, { passive: false });
  pad.addEventListener('touchcancel', handleTouchEndOrCancel, { passive: false });
});
