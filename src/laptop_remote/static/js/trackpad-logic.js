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

export function classifyTwoFingerIntent(
  currSpan,
  startSpan,
  centroidDist,
  pinchEnabled = true,
  spanThreshold = 12,
  centroidThreshold = 6
) {
  if (!pinchEnabled) {
    return centroidDist >= centroidThreshold ? 'scroll' : null;
  }
  const spanChange = Math.abs(currSpan - startSpan);
  if (spanChange < spanThreshold && centroidDist < centroidThreshold) {
    return null;
  }
  if (spanChange >= spanThreshold && spanChange > centroidDist * 1.2) {
    return 'zoom';
  }
  if (centroidDist >= centroidThreshold) {
    return 'scroll';
  }
  return spanChange > centroidDist ? 'zoom' : 'scroll';
}

export function computeZoomDelta(spanDelta, zoomSensitivity = 1.0, divisor = 15.0) {
  const sens = Math.min(3.0, Math.max(0.2, zoomSensitivity));
  return (spanDelta / divisor) * sens;
}

export function clampZoomDelta(delta, maxPerFrame = 3.0) {
  return Math.max(-maxPerFrame, Math.min(maxPerFrame, delta));
}

export function computeAirDelta(
  currGamma,
  currBeta,
  prevGamma,
  prevBeta,
  sensitivity = 2.0,
  deadband = 0.25,
  maxPerEvent = 25.0
) {
  if (prevGamma === null || prevBeta === null || typeof currGamma !== 'number' || typeof currBeta !== 'number') {
    return { dx: 0, dy: 0 };
  }
  let dGamma = currGamma - prevGamma;
  let dBeta = currBeta - prevBeta;

  if (dGamma > 180) dGamma -= 360;
  if (dGamma < -180) dGamma += 360;
  if (dBeta > 180) dBeta -= 360;
  if (dBeta < -180) dBeta += 360;

  const mag = Math.hypot(dGamma, dBeta);
  if (mag < deadband) {
    return { dx: 0, dy: 0 };
  }

  const dx = Math.max(-maxPerEvent, Math.min(maxPerEvent, dGamma * sensitivity));
  const dy = Math.max(-maxPerEvent, Math.min(maxPerEvent, dBeta * sensitivity));
  return { dx, dy };
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
    classifyTwoFingerIntent,
    computeZoomDelta,
    clampZoomDelta,
    computeAirDelta,
    classifyGesture
  };
}