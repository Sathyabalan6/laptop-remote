export function applyInertia(velocity, decay) {
  return velocity * decay;
}

export function clampSensitivity(value, min = 0.5, max = 4.0) {
  return Math.min(max, Math.max(min, value));
}

export function clampScrollSensitivity(value, min = 0.2, max = 3.0) {
  return Math.min(max, Math.max(min, value));
}

export function computeScrollDelta(
  rawDy,
  scrollSensitivity = 1.0,
  scrollDirection = 'natural',
  divisor = 18.0
) {
  const dirMultiplier = scrollDirection === 'inverted' ? -1 : 1;
  const sens = clampScrollSensitivity(scrollSensitivity);
  return (rawDy / divisor) * sens * dirMultiplier;
}

export function clampScrollDelta(delta, maxPerFrame = 4.0) {
  return Math.max(-maxPerFrame, Math.min(maxPerFrame, delta));
}

export function applyScrollInertia(velocity, decay = 0.70, minVelocity = 0.4) {
  const decayed = velocity * decay;
  return Math.abs(decayed) < minVelocity ? 0 : decayed;
}

export function isTwoFingerScrollGesture(touches, startTouches, threshold = 6) {
  if (!touches || !startTouches || touches.length < 2 || startTouches.length < 2) {
    return false;
  }
  const curYAvg = (touches[0].y + touches[1].y) / 2;
  const startYAvg = (startTouches[0].y + startTouches[1].y) / 2;
  const curXAvg = (touches[0].x + touches[1].x) / 2;
  const startXAvg = (startTouches[0].x + startTouches[1].x) / 2;
  const dist = Math.hypot(curXAvg - startXAvg, curYAvg - startYAvg);
  return dist >= threshold;
}

export function classifyGesture(
  prevPoints,
  currPoints,
  totalMovement = 0,
  movementThreshold = 2
) {
  if (currPoints.length === 2) {
    return 'scroll';
  }

  if (currPoints.length === 1 && prevPoints.length === 1) {
    return totalMovement > movementThreshold ? 'move' : 'tap';
  }

  return 'tap';
}

if (typeof window !== 'undefined') {
  window.trackpadLogic = {
    applyInertia,
    clampSensitivity,
    clampScrollSensitivity,
    computeScrollDelta,
    clampScrollDelta,
    applyScrollInertia,
    isTwoFingerScrollGesture,
    classifyGesture
  };
}